# gng
Grab-N-Go - a little python tool to download files from Pivotal Network and upload them to Ops Manager

## Setup

Get your Pivotal Network API Key by logging into http://network.pivotal.io and looking at the bottom of your profile page.

Once you have your key, edit the conf.toml file and replace the dummy key:

```
api_key = "AG_u1blahblahblahMHqnF"
```

Recommended you use virtualenv

```
pip install virtualenv
git clone git@github.com:mreider/gng.git
cd gng
virtualenv .
source bin/activate
pip install -r requirements.txt
```

## Update local product list

The first thing you need to do before downloading / uploading pivotal products is to update your product list. This local database is kind of like homebrew, aptitude, or yum's list of packages. Except there are no dependencies. And no packages. Ok, ok, it has nothing at all in common with homebrew.

```
$ python gng.py --update
```

## Dump the product list to a text file

Now that your local database is updated you can dump the contents to a file - think of that file like a restaurant menu. You want a redis? Cut and paste the redis. You want an Elastic Runtime, it goes well with a bold cabernet. We'll get to that part afterwards.

```
$ python gng.py --dump-list [filename]
```

## Cut and paste the files you want to download

We sort of explained this in the last section. That was a spoiler! Open the dump of file names you created, cut and paste the files you need into a new file. You can name that new file whatever you want. We'll call it `download-list.txt` Here is an example of what that file might look like:

```
Riak CS                                   1.5.7.0                     p-riak-cs-1.5.7.0.pivotal
Redis                                     1.5.2                       p-redis-1.5.2.0.pivotal
RabbitMQ                                  1.4.9                       p-rabbitmq-1.4.9.0.pivotal
Elastic Runtime                           1.6.8                       cf-1.6.8.pivotal
```

## Download the files you want

Now you have a list of things you want to download, and you can start downloading them. If you are going to upload this stuff to Ops Manager, it's a good idea to create a seperate download list, and a seperate directory of files to download. In this case we are creating a directory called `tmp`

```
mkdir tmp
$ python gng.py --download [download-list-filename] --path tmp
```

## Upload all the files to all the Ops Managers

Here's a cool thing. You can upload these files to more than one Ops Manager! Nifty nom nom nicklehead! All you need to do is create yourself a TOML file of your choosing. We'll call ours `opsmanager.toml`

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

With this file we can upload some files to Ops Managers of your choice:

```
$ python gng.py --upload opsmanager.toml --path tmp
```

All the files will be uploaded to all the Ops Managers. Joy!
