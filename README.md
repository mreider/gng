# gng
Grab-N-Go - a little python tool to download files from Pivotal Network and upload them to one or many Ops Managers.

## Setup

Python uses a package manager called pip - you will need this to install everything. Test if you have it by typing `pip` on a command line. If you don't have it try:

```
$ sudo easy_install pip
```

If that doesn't work - go read [this](http://www.dabapps.com/blog/introduction-to-pip-and-virtualenv-python/). If you have dependency or permission problems your best bet is to use virtualenv (described in that link).

You need to edit conf.toml and enter your Pivotal Network API key:

Get your Pivotal Network API Key by logging into http://network.pivotal.io - it's at the bottom of your profile page.

Edit the conf.toml file and replace the dummy key:

```
api_key = "AG_u1blahblahblahMHqnF"
```

## Update local product list

The first thing you need to do before downloading / uploading pivotal products is to update a local database of products. We will use the database for the other commands that follow.

```
$ python gng.py --update
```

## Dump the product list to a text file

Now that your local database is updated you can dump the contents to a file. I should just make this part of the update step. Next release perhaps?

```
$ python gng.py --dump-list [filename]
```

## Cut and paste the files you want to download

Open the dump you created, and cut / paste the lines that contain the files you want to download. You can name this new file whatever you want. Here's what it might look like:

```
Riak CS                                   1.5.7.0                     p-riak-cs-1.5.7.0.pivotal
Redis                                     1.5.2                       p-redis-1.5.2.0.pivotal
RabbitMQ                                  1.4.9                       p-rabbitmq-1.4.9.0.pivotal
Elastic Runtime                           1.6.8                       cf-1.6.8.pivotal
```

## Download the files you want

Now you have a list of files to download. Create a download directory and run the download command as follows:

```
$ mkdir [directory]
$ python gng.py --download [download-list-filename] --path [directory]
```

## Upload all the files to all the Ops Managers

You can upload these files to more than one Ops Manager. Just create a TOML file of your choosing. We'll call ours `opsmanager.toml`

```
[[opsmanager]]
url = "54.86.17.2"
username = "admin"
password = "donkeybrain7"
[[opsmanager]]
url = "52.91.206.10"
username = "admin"
password = "monkeyhead8"
```

The upload command is as follows:

```
$ python gng.py --upload [ops-manager-list-toml-file] --path [directory]
```

