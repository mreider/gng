import argparse

import toml,os
from argparse import ArgumentParser
from pivnet import PivNetUpdater, DBDumper, PivNetDownloader, PivNetUploader

parser = ArgumentParser()
parser.add_argument("--update",action='store_true',help="updates a local sqlite database of all products, releases, and files from Pivotal Network")
parser.add_argument("--dump-list",nargs=1,metavar='filename',action="store",help="Create a list of files from the local sql lite database so user can cut / paste the files they want to download")
parser.add_argument("--download",nargs=1,metavar="filename",help="Parse the user-created file of downloads and download them to a path")
parser.add_argument("--upload",nargs=1,metavar="filename",help="Scan a path of files, make sure they are valid (or ignore w/ --force) and upload to Ops Managers")
parser.add_argument("--path",nargs=argparse.REMAINDER,metavar="path",help="Path to which either upload or download will happen")
parser.add_argument("--force",action="store_true",help="Forcing to updload the files which are not existing in DB")

conf = "conf.toml"
args = parser.parse_args()
vargs = vars(args)
# print(vargs)
if "update" in vargs and vargs["update"]:
    msg = PivNetUpdater().update_db()
    if msg:
        print(msg)
elif "dump_list" in vargs and vargs["dump_list"]:
    filename = vargs["dump_list"][0]
    print("Going to dump list to "+filename)
    DBDumper().dump_list(filename)
elif "download" in vargs and vargs["download"]:
    if not os.path.exists(conf):
        print("no valid confi.toml with key")
        exit(-1)
    with open(conf) as conffile:
        config = toml.loads(conffile.read())
    api_key = config.get('api_key')
    if not api_key or len(api_key) <= 0:
        print("no valid confi.toml with key")
        exit(-1)
    filename = vargs["download"][0]
    if not os.path.exists(filename):
        print('download list is required')
        exit(-1)
    if "path" in vargs and vargs["path"]:

        download_path = vargs["path"][0]
        if not os.path.exists(download_path):
            print("Path is not valid")
            exit(-1)
        PivNetDownloader(api_key).download_files(filename,download_path)
    else:
        print("Path is required")
elif "upload" in vargs and vargs["upload"]:
    filename = vargs["upload"][0]
    if not filename or not os.path.exists(filename):
        print('ops manager target list is required')
        exit(-1)
    try:
        with open(filename) as conffile:
            opsmgr_config = toml.loads(conffile.read())

    except Exception:
        print('Incorrect TOML format')
        exit(-1)

    if "path" in vargs and vargs["path"]:
        upload_folder = vargs["path"][0]
        if not os.path.exists(upload_folder):
            print("Path is not valid")
            exit(-1)

        # print(type(upload_folder))
        force = vargs["force"]
        msg = PivNetUploader().upload_files(config=opsmgr_config,folder_path=upload_folder,force=force)
        if msg:
            print(msg)
            exit(-1)
    else:
        print("Path is required")
else:
    parser.print_help()
