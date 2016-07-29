# gng
Grab-N-Go - a little python tool to download files from Pivotal Network and upload them to one or many Ops Managers.

## Setup

Python 3.5.1 and pip 8.1.2 were used for this release. MacOS ships with Python 2.7, so you will want to install the later version of python and pip. Visit [python.org](https://www.python.org/downloads/) for the latest downloads of python, and [pypa.io](https://pip.pypa.io/en/stable/installing/) for pip. You should put the later version in a different bin directory than those used by the system (e.g., `/usr/local/bin`). I added a couple aliases, `alias pip='pip3.5'` `alias python='python3.5'` to avoid the accedential use of the system python.

You need to edit `conf.toml` and enter your Pivotal Network API key:

Get your Pivotal Network API Key by logging into http://network.pivotal.io - it's at the bottom of your profile page.

Edit the `conf.toml` file and replace the dummy key:

```
api_key = "BlahBlahBlahBlah"
```

## Update local product list

The first thing you need to do before downloading / uploading pivotal products is to update a local database of products. We will use the database for the other commands that follow. You might create a cron script to do nightly update and email a differences.

```
$ python gng.py --update
```

## Dump the product list to a text file

The database created by update now has over 1000 records. Dump list outputs CSV, so a spreadsheet can easily be used to sort and filter the list. The CSV file includes the MD5 digest and download URL should you want to create new tools to manage your own repository of Pivotal software.

```
$ python gng.py --dump-list [filename.csv]
```

## Update and dump at night
The helper script `gngupdate.sh` is useful to run from `launchd` or `cron`. Following is an example lauchd script, which you would place in `/Users/someone/Library/LaunchAgents/net.example.launched.gng.plist`.

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>EnvironmentVariables</key>
	<dict>
		<key>PATH</key>
		<string>/Library/Frameworks/Python.framework/Versions/3.5/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/someone/bin</string>
	</dict>
	<key>Label</key>
	<string>net.example.launched.gng</string>
	<key>ProgramArguments</key>
	<array>
		<string>/Users/someone/Documents/PivotalCF/gng/gngupdate.sh</string>
	</array>
	<key>StandardErrorPath</key>
	<string>/Users/someone/Documents/PivotalCF/gngupdate.stderr</string>
	<key>StandardOutPath</key>
	<string>/Users/someone/Documents/PivotalCF/gngupdate.stdout</string>
	<key>StartCalendarInterval</key>
	<array>
		<dict>
			<key>Hour</key>
			<integer>1</integer>
			<key>Minute</key>
			<integer>13</integer>
		</dict>
	</array>
	<key>WorkingDirectory</key>
	<string>/Users/someone/Documents/PivotalCF</string>
</dict>
</plist>
```
To help out the PivNet operators, please change the time to something while you are sleeping.

## Cut and paste the files you want to download

Open the dump you created, and cut / paste the lines that contain the files you want to download. You can name this new file whatever you want. Here's what it might look like:

```
Elastic Runtime,1.7.6,cf-1.7.6-build.4.pivotal,6/14/16,6879dea005f5010c6ebc3eb00fca8a34,https://network.pivotal.io/api/v2/products/elastic-runtime/releases/1875/product_files/4964/download
MySQL,1.7.8,p-mysql-1.7.8.pivotal,5/19/16,5b89db5c9af13230e1b23847de2921f7,https://network.pivotal.io/api/v2/products/p-mysql/releases/1770/product_files/4696/download
PCF Metrics,PCF Metrics 1.0.6,apm-1.0.6.pivotal,6/10/16,c32ae281cc97306e5a40c994f25faa53,https://network.pivotal.io/api/v2/products/pcf-metrics/releases/1860/product_files/4919/download
PCF Metrics,PCF Log Search v1.0.0,p-logsearch-1.0.0.pivotal,6/6/16,40e928d67a836d4bff27c4b67e3f3e52,https://network.pivotal.io/api/v2/products/pcf-metrics/releases/1832/product_files/4856/download
PCF Metrics,PCF JMX Bridge 1.7.2,p-metrics-1.7.2.pivotal,5/20/16,07f7a1689658df4e11e5cff5925d0545,https://network.pivotal.io/api/v2/products/pcf-metrics/releases/1777/product_files/4710/download
Push Notification Service,1.4.10,p-push-notifications-1.4.10.1.pivotal,6/16/16,f04a1f1efd840036197b0ee6d3e07b98,https://network.pivotal.io/api/v2/products/push-notification-service/releases/1896/product_files/5010/download
RabbitMQ,1.6.2,p-rabbitmq-1.6.2.pivotal,6/15/16,fb57184e2eca5fba836f4a688842c327,https://network.pivotal.io/api/v2/products/pivotal-rabbitmq-service/releases/1882/product_files/4985/download
Redis,1.5.15,p-redis-1.5.15.pivotal,6/14/16,9f10214bca9a20c9039ff6bad6aa3c55,https://network.pivotal.io/api/v2/products/p-redis/releases/1876/product_files/4965/download
Session State Caching Powered by GemFire,1.2.0,p-ssc-gemfire-1.2.0.0.pivotal,6/2/16,0dfea7de7bdab6e72d980adcaff5c68b,https://network.pivotal.io/api/v2/products/p-ssc-gemfire/releases/1821/product_files/4826/download
Single Sign-On,1.1.1,Single_Sign-On_1.1.1.pivotal,5/5/16,876eab74baa2e9b82df279aff90453e8,https://network.pivotal.io/api/v2/products/p-identity/releases/1732/product_files/4526/download
Spring Cloud Services,1.0.10,p-spring-cloud-services-1.0.10.pivotal,6/14/16,ad280e91dfac1d5fbdcd55129cd4aad7,https://network.pivotal.io/api/v2/products/p-spring-cloud-services/releases/1881/product_files/4976/download
```

## Download the files you want

Download verifies the MD5 for each file. In the case of a mismatch, download will try a few times, before skipping and reporting the error. Download can be used for files, which cannot be uploaded to Ops Manager (e.g., buildpacks). Create a download directory and run the download command as follows:

```
$ mkdir [directory]
$ python gng.py --download [download-list.csv] --path [directory]
```

## Upload all the files to all the Ops Managers

You can upload these files to more than one Ops Manager. Just create a TOML file with a `[[opsmanager]]` for each Ops Manager you want to maintain. We'll call ours `ops-manager-list.toml`

```
[[opsmanager]]
url = "some domain name or IP address"
access_token = "some token"
[[opsmanager]]
url = "some other domain name or IP address"
access_token = "some other token"
```
Url is only the domain name (e.g., localhost, opsmanager.example.com, 10.0.45.67) without the scheme. Localhost is convenient running Ops Manager on a public IaaS like AWS.

See [support article](https://discuss.zendesk.com/hc/en-us/articles/217039538-How-to-download-and-upload-Pivotal-Cloud-Foundry-products-via-API) for getting the access token.

The upload command is as follows:

```
$ python gng.py --upload [ops-manager-list.toml] --path [directory]
```
## Cautions and next steps
There is minimal error handling, but you have the source!
In support of keeping the source looking consistent as it changes, please use [autopep8](https://github.com/hhatto/autopep8) before checking code into the project.

##### Feature backlog:
* Robust error handling
* Evaluate [Requests](http://docs.python-requests.org/) verses [PycURL](http://pycurl.io), a [post](http://stackoverflow.com/questions/15461995/python-requests-vs-pycurl-performance) to get started
* Handle Stemcells
* Dump list needs a "newer than date" option
* Upload needs to check if file already exists on Ops Manager before uploading to avoid "meta-data" error, and the waste of bandwidth
* auth_token expires, should check token is stll valid before iterating through the upgrades
* PycURL may timeout, while Ops Manager processes a large upgrade such as elastic runtime (rare, but error has been seen, perhaps caused by LB between utility and Ops Manager)
* Investigate if Ops Manager 1.6 and earlier need to be supported
* Once MD5 is returned by the release API, the call to `get_file_details` won't be needed. Currently, this will save over 5300 requests.

 

