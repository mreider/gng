import zipfile

from database_manager import Database, Product, Release, ProductFile


import os, json
import toml
import requests
import codecs
import pycurl
from tabulate import tabulate

all_products_url = '/api/v2/products'
end_point = 'https://network.pivotal.io'

proxies = {
}


class PivNetUploader:
    def __init__(self):
        self.database = Database()

    def upload_files(self,config,folder_path,force=False):
        file_names = []
        print(type(folder_path))
        files = os.listdir(folder_path)
        for file in files:
            if os.path.isfile(os.path.join(folder_path,file)):
                file_names.append(file)
        files_from_db = self.database.check_file_exists(file_names)
        if len(file_names) == len(files_from_db) or force:
            self.upload(config,folder_path)
        else:
            return "Found files in [pathname] that are not in product db. Either remove unknown files, or use --force to upload every file in [pathname] whether its in the db or not."



    def upload(self,config,dest_path):
        c = pycurl.Curl()
        print(config)
        for opsman in config["opsmanager"]:
            # for i in opsman:
            if "username" in opsman and "password" in opsman:
                username = opsman["username"]
                password = opsman["password"]
                c.setopt(pycurl.USERPWD, "%s:%s" % (username ,password))
            if "url" in opsman:
                c.setopt(c.URL, "https://" + opsman["url"] + "/api/products")
            c.setopt(pycurl.VERBOSE, 0)
            c.setopt(c.SSL_VERIFYPEER, 0)
            c.setopt(c.SSL_VERIFYHOST, 0)

            c.setopt(c.NOPROGRESS, 0)
            c.setopt(c.PROGRESSFUNCTION, self.progress)

            files = os.listdir(dest_path)
            for filename in files:
                full_path = os.path.join(dest_path,filename)
                c.setopt(c.HTTPPOST, [('product[file]', ( c.FORM_FILE, full_path,)),])
                c.perform()

    def progress(self,download_t, download_d, upload_t, upload_d):
        if upload_t > 0:
            print(" Uploaded so far {per}%".format(per=int(upload_d*100/upload_t)))

class PivNetDownloader:
    def __init__(self,api_key):
        self.token = api_key
        self.secure_url = end_point
        self.headers = {'content-type': 'application/json'}
        self.secure_headers = {'content-type': 'application/json','Accept':'application/json','Authorization':'Token token='+ self.token}
        self.database = Database()

    def download_files(self,file_name,download_path):
        file = open(file_name)

        for line in file.readlines():
            items = []
            for x in line.split("  "):
                if len(x) > 1:
                    items.append(x)
            name = items[0]
            release_version = items[1]
            file_name = items[2].strip()

            product_id,slug = self.database.get_product_details(name)
            # print('slug=%s,version=%s,file=%s'%(slug,release_version,file_name))
            data = self.database.get_release_id(slug,release_version)
            print(data)
            if data:
                release_id = data[0]
                file_data = self.database.get_file_id(release_id,file_name)
                if file_data:
                    file_id = file_data[0]
                    # print('product id =%s,release=%s,file_name=%s'%(product_id,release_id,file_name))
                    self.acceptEULA(product_id,release_id)

                    self.downloadFile(product_id,release_id,file_id,file_name,download_path)

    def acceptEULA(self, product_id, release_id):
        url = self.secure_url + "/api/v2/products/" + str(product_id) + "/releases/" + str(release_id) + "/eula_acceptance"
        r = requests.post(url, headers=self.secure_headers,proxies=proxies)
        return r


    def downloadFile(self, product_id, release_id, file_id, file_name,download_path):
        if not os.path.exists("product_files"):
            os.makedirs("product_files")
        url = self.secure_url + "/api/v2/products/" + str(product_id) + "/releases/" + str(
            release_id) + "/product_files/" + str(file_id) + "/download"
        # print(url)
        r = requests.post(url, headers=self.secure_headers, stream=True,proxies=proxies)
        # print(download_path)
        print("Going to download %s from %s"%(file_name,url))
        full_path = os.path.join(download_path,file_name)
        with open(full_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
        return file_name


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

    def dump_list(self,outfile_name):
        final_list = []
        for product in self.database.session.query(Product).order_by(Product.name).all():
            product_list = []

            for release in self.database.session.query(Release).filter(Release.product_slug==product.slug).order_by(Release.version).all():
                for file in self.database.session.query(ProductFile).filter(ProductFile.release_id==release.id).order_by(ProductFile.filename).all():
                    final_list.append([product.name,release.version,file.filename])
        if len(final_list) > 0:
            data = tabulate(final_list,tablefmt="plain")
            with open(outfile_name,'w+') as outfile:
                outfile.write(data)
            print('Product list dumped to [%s]'%outfile_name)
            print('Cut and paste files to download into my-downloads.txt and run gng --download my-downloads.txt --path foo')
        else:
            print("You need to update your Pivotal Network DB. Please run gng --update")
class PivNetUpdater:
    def __init__(self):
        self.url = 'https://network.pivotal.io'
        self.headers = {'content-type': 'application/json'}
        self.database = Database()

    def update_db(self):
        self.database.clear_all_tables()
        reader = codecs.getreader("utf-8")
        conf = "conf.toml"
        if not os.path.exists(conf):
            return "no valid confi.toml with key"
        with open(conf) as conffile:
            config = toml.loads(conffile.read())
        api_key = config.get('api_key')
        if not api_key or len(api_key) <= 0:
            return "no valid confi.toml with key"
        products = self.getProducts()
        for product in products:
            product_id = product.get('id')
            slug = product.get('slug')
            pname = product.get('name')
            p = Product(id=product_id,slug=slug,name=pname)
            self.database.session.add(p)
            # print('id=%s,slug=%s,name=%s'%(product_id,slug,pname))
            print('Found %s'%slug)
            releases = self.getReleases(slug)
            if releases:
                for release in releases:
                    rid = release.get('id')
                    version = release.get('version')
                    r = Release(id=rid,version=version,product_slug=p.slug)
                    self.database.session.add(r)
                    print('Found %s,%s'%(slug,version))
                    # print('id=%s,version=%s,slud=%s'%(rid,version,p.id))
                    files = self.getProductFiles(product_id,rid)
                    if files:
                        for file in files:
                            links = file.get('_links')
                            url = links.get('download').get('href')
                            name=file.get('aws_object_key').split('/')[-1]
                            f = ProductFile(id=file.get('id'),release_id=r.id,filename=name,download_url=url)
                            # print('id=%s,releasid=%s,filename=%s,url=%s'%(f.id,r.id,name,url))
                            self.database.session.add(f)
                            print('Found %s,%s,%s'%(slug,version,name))
            self.database.commit()
        self.database.commit()
        print("Local Pivotal Network db has been updated.")

    def getProducts(self):
        url = self.url + "/api/v2/products/"
        r = requests.get(url, headers = self.headers,proxies=proxies)
        data = json.loads(r.content.decode('utf-8'))

        return data.get('products')

    def getReleases(self, slug):
        url = self.url + "/api/v2/products/" + slug + "/releases"
        r = requests.get(url, headers=self.headers,proxies=proxies)
        data = json.loads(r.content.decode('utf-8'))
        releases = data.get('releases')
        # print(releases)
        return releases


    def getProductFiles(self, product_id, release_id):
        url = self.url + "/api/v2/products/" + str(product_id) + "/releases/" + str(release_id) + "/product_files"
        r = requests.get(url, headers=self.headers,proxies=proxies)
        data = json.loads(r.content.decode('utf-8'))
        return data.get('product_files')
