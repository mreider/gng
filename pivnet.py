import zipfile

from database_manager import Database, Product, Release, ProductFile
from sqlalchemy import exc

import os
import json
import pytoml as toml
import requests
import codecs
import pycurl
import csv
import hashlib
import sys

all_products_url = '/api/v2/products'
end_point = 'https://network.pivotal.io'

proxies = {
}


class PivNetUploader:

    def __init__(self):
        self.database = Database()

    def upload_files(self, config, folder_path, force=False):
        file_names = []
        print('folder path: %s, force=%s' % (folder_path, force))
        files = os.listdir(folder_path)
        for file in files:
            # if not file.endswith(('.pivotal', '.tgz')):
            if not file.endswith(('.pivotal')):
                print(
                    'Skipping %s - only tiles (.pivotal) and stemcells (.tgz) are uploaded.' %
                    (file))
            elif not os.path.isfile(os.path.join(folder_path, file)):
                print('Skipping %s - is not a file.' % (file))
            elif not self.database.check_file_exists(file) and not force:
                print(
                    'Skipping %s - is not in product db. Either remove unknown file, or use --force to upload every file in %s whether its in the db or not.' %
                    (file, folder_path))
            else:
                file_names.append(file)
        self.upload(config, folder_path, file_names)

    def upload(self, config, dest_path, file_names):
        # print(config)
        for opsman in config["opsmanager"]:
            if not "access_token" in opsman:
                print('No Ops Manager access_token')
                return
            elif not "url" in opsman:
                print('No Ops Manager URL')
                return
            else:
                access_token = opsman["access_token"]
                url = opsman["url"]

            for filename in file_names:
                full_path = os.path.join(dest_path, filename)
                # print(
                #     'access_token = %s, url = %s, file = %s' %
                #     (access_token, url, full_path))
                # continue
                try:
                    c = pycurl.Curl()
                    c.setopt(
                        c.URL,
                        "https://" +
                        opsman["url"] +
                        "/api/v0/available_products")
                    c.setopt(
                        pycurl.HTTPHEADER, [
                            'Authorization: bearer %s' %
                            (access_token)])
                    c.setopt(pycurl.VERBOSE, 0)
                    c.setopt(c.SSL_VERIFYPEER, 0)
                    c.setopt(c.SSL_VERIFYHOST, 0)
                    c.setopt(c.NOPROGRESS, 0)
                    c.setopt(
                        c.HTTPPOST, [
                            ('product[file]', (c.FORM_FILE, full_path,)), ])
                    print('Uploading %s' % (full_path))
                    result = c.perform()
                finally:
                    c.close()


class PivNetDownloader:

    def __init__(self, api_key):
        self.token = api_key
        self.secure_url = end_point
        self.headers = {'content-type': 'application/json'}
        self.secure_headers = {
            'content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Token token=' + self.token}
        self.database = Database()
#         print('token=%s, secure_url=%s, headers=%s, secure_headers=%s' %
#             (self.token, self.secure_url, self.headers, self.secure_headers))

    def download_files(self, file_name, download_path):
        with open(file_name) as infile:
            reader = csv.reader(infile, dialect='excel')
            for row in reader:
                # print(row)
                name = row[0].strip()
                release_version = row[1].strip()
                file_name = row[2].strip()

                data = self.database.get_product_details(name)
                if data:
                    # print(data)
                    product_id = data[0]
                    slug = data[1]
                else:
                    print('Could not get product details for %s' % (name))
                    continue

                # print(
                #     'slug=%s,version=%s,file=%s' %
                #     (slug, release_version, file_name))
                data = self.database.get_release_id(slug, release_version)
                # print(data)
                if data:
                    release_id = data[0]
                    file_data = self.database.get_file_details(
                        release_id, file_name)
                    if file_data:
                        # print(file_data)
                        file_id = file_data[0]
                        file_name = file_data[2]
                        url = file_data[3]
                        md5 = file_data[4]
                        # print(
                        #     'URL = %s, filename = %s, md5 = %s' %
                        #     (url, file_name, md5))
                        self.acceptEULA(product_id, release_id)

                        md5_download = ""
                        i = 0
                        while md5 != md5_download:
                            md5_download = self.downloadFile(
                                url,
                                file_name,
                                download_path)
                            i += 1
                            if i > 2:
                                break
                        if md5 != md5_download:
                            print(
                                'MD5 PivNet does not match download (%s != %s)' %
                                (md5, md5_download))
                    else:
                        print(
                            'Could not get release ID for release ID=%s, file name=%s' %
                            (release_id, file_name))
                else:
                    print(
                        'Could not get file details for slug=%s, version=%s' %
                        (slug, release_version))

    def acceptEULA(self, product_id, release_id):
        url = self.secure_url + "/api/v2/products/" + \
            str(product_id) + "/releases/" + str(release_id) + "/eula_acceptance"
        r = requests.post(url, headers=self.secure_headers, proxies=proxies)
        return r

    def downloadFile(
            self,
            url,
            file_name,
            download_path):
        sig = hashlib.md5()
        r = requests.post(
            url,
            headers=self.secure_headers,
            stream=True,
            proxies=proxies)
        # print(download_path)
        print("Downloading %s from %s" % (file_name, url))
        full_path = os.path.join(download_path, file_name)
        with open(full_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    sig.update(chunk)
                    f.flush()
        return sig.hexdigest().lower()

    def unzipper(self, file_name):
        path = "product_files"
        subdir = file_name[:-8]  # remove '.pivotal'
        if not os.path.exists("product_files/" + subdir):
            os.makedirs("product_files/" + subdir)
        with zipfile.ZipFile("product_files/" + file_name, "r") as z:
            z.extractall("product_files/" + subdir)
        return subdir


class DBDumper:

    def __init__(self):
        self.database = Database()

    def dump_list(self, outfile_name):
        final_list = []
        for product in self.database.session.query(
                Product).order_by(Product.name).all():
            product_list = []

            for release in self.database.session.query(Release).filter(
                    Release.product_slug == product.slug).order_by(
                    Release.version).all():
                for file in self.database.session.query(ProductFile).filter(
                        ProductFile.release_id == release.id).order_by(
                        ProductFile.filename).all():
                    final_list.append([product.name,
                                       release.version,
                                       file.filename,
                                       file.release_date,
                                       file.md5,
                                       file.download_url])
        if len(final_list) > 0:
            with open(outfile_name, 'w+', newline='') as outfile:
                writer = csv.writer(outfile, dialect='excel')
                writer.writerow(['Product Name',
                                 'Release Version',
                                 'Filename',
                                 'Release Date',
                                 'MD5',
                                 'Download URL'])
                writer.writerows(final_list)
            print('Product list dumped to [%s]' % outfile_name)
            print('Cut and paste files to download into my-downloads.csv and run gng --download my-downloads.csv --path foo')
        else:
            print("You need to update your Pivotal Network DB. Please run gng --update")


class PivNetUpdater:

    def __init__(self, api_key):
        self.token = api_key
        self.secure_url = end_point
        self.secure_headers = {
            'content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Token token=' + self.token}
        self.database = Database()
#         print('token=%s, secure_url=%s, secure_headers=%s' %
#             (self.token, self.secure_url, self.secure_headers))

    def update_db(self):
        self.database.clear_all_tables()
        products = self.getProducts()
        for product in products:
            product_id = product.get('id')
            slug = product.get('slug')
            pname = product.get('name')
            p_file_groups = product.get('_links').get(
                'file_groups').get('href')
            p_product_files = product.get('_links').get(
                'product_files').get('href')
            p = Product(
                id=product_id,
                slug=slug,
                name=pname,
                file_groups_url=p_file_groups,
                product_files_url=p_product_files)
            self.database.session.add(p)
            self.database.commit()
#             print(
#                 'Found product %s,%s,%s,%s,%s' %
#                 (product_id,
#                  slug,
#                  pname,
#                  p_file_groups,
#                  p_product_files))
#             if p_file_groups:
#                 p_groups = self.getFileGroups(p_file_groups)
#                 if p_groups:
#                     for p_group in p_groups:
#                         print(
#                             json.dumps(
#                                 p_group,
#                                 sort_keys=True,
#                                 indent=4))
#             if p_product_files:
#                 p_files = self.getProductFiles(p_product_files)
#                 if p_files:
#                     for p_file in p_files:
#                         print(
#                             json.dumps(
#                                 p_file,
#                                 sort_keys=True,
#                                 indent=4))
            releases = self.getReleases(slug)
            if releases:
                for release in releases:
                    rid = release.get('id')
                    version = release.get('version')
                    r_file_groups = release.get('_links').get(
                        'file_groups').get('href')
                    r_product_files = release.get('_links').get(
                        'product_files').get('href')
                    r = Release(
                        id=rid,
                        version=version,
                        product_slug=p.slug,
                        file_groups_url=r_file_groups,
                        product_files_url=r_product_files)
                    self.database.session.add(r)
                    self.database.commit()
#                     print(
#                         'Found release %s,%s,%s,%s,%s' %
#                         (rid, version, p.slug, r_file_groups, r_product_files))
                    if r_file_groups:
                        groups = self.getFileGroups(r_file_groups)
                        if groups:
                            for group in groups:
                                self.addFiles(
                                    group.get('product_files'), product_id, rid)
                    self.addFiles(self.getProductFiles(
                        r_product_files), product_id, rid)
        print("Local Pivotal Network db has been updated.")

    def addFiles(self, files, product_id, rid):
        if files:
            for file in files:
                try:
                    file_id = file.get('id')
                    file_detail = self.getProductFile(
                        product_id, rid, file_id)
                    url = file_detail.get('_links').get('download').get('href')
                    name = file_detail.get(
                        'aws_object_key').split('/')[-1]
                    md5 = file_detail.get('md5').lower()
                    released_at = file_detail.get('released_at')
                    f = ProductFile(
                        id=file_id,
                        release_id=rid,
                        filename=name,
                        download_url=url,
                        md5=md5,
                        release_date=released_at)
                    # print(
                    #     'file id=%s,release id=%s,filename=%s,url=%s,md5=%s,date=%s' %
                    #     (f.id, r.id, name, url, md5, released_at))
                    self.database.session.add(f)
                    self.database.commit()
                except exc.IntegrityError:
                    self.database.session.rollback()
                    print('Duplicate: %s' % (file_detail))
                except:
                    print(
                        'addFile (%s, %s, %s) exception: %s' %
                        (product_id, rid, file_id, sys.exc_info()[0]))
#                     print(
#                         json.dumps(
#                             file,
#                             sort_keys=True,
#                             indent=4))
#                     print(
#                         json.dumps(
#                             file_detail,
#                             sort_keys=True,
#                             indent=4))

    def getProducts(self):
        url = self.secure_url + "/api/v2/products/"
        for i in range(0, 3):
            try:
                r = requests.get(
                    url, headers=self.secure_headers, proxies=proxies)
                data = json.loads(r.content.decode('utf-8'))
                # print('getProducts %s' % (url))
                # print(json.dumps(data, sort_keys=True, indent=4))
                products = data.get('products')
                return products
            except requests.exceptions.RequestException as e:
                print('getProducts (i=%s) %s e=%s' % (i, url, e))
        print('getProducts giving up after %s tries' % (i))

    def getReleases(self, slug):
        url = self.secure_url + "/api/v2/products/" + slug + "/releases"
        for i in range(0, 3):
            try:
                r = requests.get(
                    url, headers=self.secure_headers, proxies=proxies)
                data = json.loads(r.content.decode('utf-8'))
                # print('getReleases %s' % (url))
                # print(json.dumps(data, sort_keys=True, indent=4))
                releases = data.get('releases')
                return releases
            except requests.exceptions.RequestException as e:
                print('getReleases (i=%s) %s e=%s' % (i, url, e))
        print('getReleases giving up after %s tries' % (i))

    def getFileGroups(self, url):
        for i in range(0, 3):
            try:
                r = requests.get(
                    url, headers=self.secure_headers, proxies=proxies)
                data = json.loads(r.content.decode('utf-8'))
                # print('getFileGroups %s' % (url))
                # print(json.dumps(data, sort_keys=True, indent=4))
                file_groups = data.get('file_groups')
                return file_groups
            except requests.exceptions.RequestException as e:
                print('getFileGroups (i=%s) %s e=%s' % (i, url, e))
        print('getFileGroups giving up after %s tries' % (i))

    def getProductFiles(self, url):
        for i in range(0, 3):
            try:
                r = requests.get(
                    url, headers=self.secure_headers, proxies=proxies)
                data = json.loads(r.content.decode('utf-8'))
                # print('getProductFiles %s' % (url))
                # print(json.dumps(data, sort_keys=True, indent=4))
                product_files = data.get('product_files')
                return product_files
            except requests.exceptions.RequestException as e:
                print('getProductFiles (i=%s) %s e=%s' % (i, url, e))
        print('getProductFiles giving up after %s tries' % (i))

    def getProductFile(self, product_id, release_id, file_id):
        url = self.secure_url + '/api/v2/products/' + str(product_id) \
            + '/releases/' + str(release_id) + '/product_files/' \
            + str(file_id)
#         print(url)
        for i in range(0, 3):
            try:
                r = requests.get(
                    url, headers=self.secure_headers, proxies=proxies)
                data = json.loads(r.content.decode('utf-8'))
                # print('getProductFile %s' % (url))
                # print(json.dumps(data, sort_keys=True, indent=4))
                product_file = data.get('product_file')
                return product_file
            except requests.exceptions.RequestException as e:
                print('getProductFile (i=%s) %s e=%s' % (i, url, e))
        print('getProductFile giving up after %s tries' % (i))
