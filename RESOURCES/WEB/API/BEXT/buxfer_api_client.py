import urllib2
import sys
import re
import base64
import simplejson

# XXX WARNING: only a sample; please do NOT hard-code your username 
# or passwords in this manner in your API clients

username = "username"
password = "password"

#############

def checkError(response):
    result = simplejson.load(response)
    response = result['response']
    if response['status'] != "OK":
        print("An error occured: %s" % response['status'].replace('ERROR: ', ''))
        sys.exit(1)

    return response

base = "https://www.buxfer.com/api";
url  = base + "/login?userid=" + username + "&password=" + password;

req = urllib2.Request(url=url)
response = checkError(urllib2.urlopen(req))
token = response['token']

url  = base + "/budgets?token=" + token;
req = urllib2.Request(url=url)
response = checkError(urllib2.urlopen(req))
for budget in response['budgets']:
    print("%12s %8s %10.2f %10.2f" % (budget['name'], budget['currentPeriod'], budget['limit'], budget['remaining']))

sys.exit(0)
