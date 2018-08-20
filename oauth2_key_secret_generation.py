#!/usr/bin/env python

"""
Original implementation is available here: https://bitbucket.org/atlassian_tutorial/atlassian-oauth-examples under python/app.py
Copied here as oauth2_key_secret_generation.py with modifications:
	* Since we are not able to resolve SSL Certification problem, let's disable ssl certificate validation for each REST api call. 
	  client.disable_ssl_certificate_validation = True
	* Strangely first time (before you approve request in browser) when you access data_url, browser returns 200 response with content of 
		zero bytes instead of 401 response. Hence I've commented out response code validation for this part.
	* Also I've refactored and removed SignatureMethod_RSA_SHA1 into it's own file. This way we can import it into any other python program!
	
Steps to create OAuth token Key and Secret:
* Generate RSA ssh public and private keys.
{code}
(jira_python)[rkadam@:rkadam-m01 oauth]$ openssl genrsa -out oauth.pem 1024
(jira_python)[rkadam@:rkadam-m01 oauth]$ openssl rsa -in oauth.pem -pubout -out oauth.pub
{code}
_jira_oauth.pub key will be used as *public key* during Application Link - Incoming Authentication setup process._

* Create Application link in order to allow our REST APIs to connect using OAtuh Credentials.
** Click on "Add Application Link"
*** Give any random application URL. Let's say "https://jira-oauth-rest-api-access" or http://example.com
*** You will see error "No response was received from the URL you entered..." _Ignore it_ and click on *Continue*
*** Application Name: JIRA OAuth REST API Access
*** Application Type: Generic Application
*** Click on *Create*
** Click *Edit* for newly created Application link with name "JIRA OAuth REST API Access"
** Click on *Configure*	-> *Incoming Authentication*
** Consumer Key:jira-oauth-rest-api-access
	Consumer Name:jira-oauth-rest-api-access
	Description: Incoming Authentication will help us to login without using Userid/Password Credentials for given user.
	Public Key: <copy it from jira_oauth.pub>
	*Rest of the fields leave empty*
** Now Incoming Authentication status should be shown as *Configured*

* Now run this program to perform *OAuth Dance* and generate OAuth key and secret.
** Make sure you have consumer_key, consumer_secret and token urls correctly.
* It should generate oauth_token and oauth_token_secret and provide link to approve request in browser.
* Make sure you are logged in as a "automatic" *user for which you want to generate* these OAuth token.
** User *automatic* should be part of *Editors* role for a project STEAM 
* After approval in browser, it should display message " Access Approved. You have successfully authorized 'jira-oauth-rest-api-access'. Please close this browser window and click continue in the client."
* Come back to this oauth generation python client and say "y" to question to "Have you authorized me? (y/n)"
* Verify REST API output to make sure access is setup correctly.

* Now onwards, you can use these tokens to make REST API calls.
"""

import oauth2
import urlparse
import argparse
import SignatureMethod_RSA_SHA1
from ConfigParser import SafeConfigParser


parser = argparse.ArgumentParser()
parser.add_argument("oauth_config_file_path", help = "Enter complete file path for oauth.config ")
args = parser.parse_args()

config = SafeConfigParser()
config.read(args.oauth_config_file_path)
jira_url = config.get("oauth_config", "jira_base_url")
jira_issue = config.get("oauth_config", "jira_issue")
consumer_key = config.get("oauth_config", "consumer_key")
oauth_public_key_file_path=config.get("oauth_config", "oauth_public_key_file_path")

consumer_secret = None
with open (oauth_public_key_file_path, 'r') as public_cert_file:
    consumer_secret = public_cert_file.read()

if jira_url[-1] == '/':
	jira_url = jira_url[0:-1]

# JIRA OAuth URLs
request_token_url = jira_url + '/plugins/servlet/oauth/request-token'
access_token_url = jira_url + '/plugins/servlet/oauth/access-token'
authorize_url = jira_url + '/plugins/servlet/oauth/authorize'
# JIRA Test URL
data_url = jira_url + '/rest/api/2/issue/' + jira_issue + '?fields=summary'

consumer = oauth2.Consumer(consumer_key, consumer_secret)
client = oauth2.Client(consumer)
client.disable_ssl_certificate_validation = True

# Without Signature we shouldn't able to access JIRA.
# Lets try to access a JIRA issue (BULK-1). We should get a 401 or Content of zero length.
resp, content = client.request(data_url, "GET")
# Strangely first time (before you approve request in browser) when you access data_url, 
# Browser returns 200 response with content of zero byte instead of 401 response.
# Hence I've commented out response code validation for this part.
"""
if resp['status'] != '401':
    raise Exception("Should have no access!")
"""

consumer = oauth2.Consumer(consumer_key, consumer_secret)
client = oauth2.Client(consumer)
client.disable_ssl_certificate_validation = True
client.set_signature_method(SignatureMethod_RSA_SHA1.SignatureMethod_RSA_SHA1())

# Step 1: Get a request token. This is a temporary token that is used for
# having the user authorize an access token and to sign the request to obtain
# said access token.

resp, content = client.request(request_token_url, "POST")
if resp['status'] != '200':
    raise Exception("Invalid response %s: %s" % (resp['status'],  content))

request_token = dict(urlparse.parse_qsl(content))

print "Step 1:"
print "Request Token:"
print "    - oauth_token        = %s" % request_token['oauth_token']
print "    - oauth_token_secret = %s" % request_token['oauth_token_secret']
print

# Step 2: Redirect to the provider. Since this is a CLI script we do not
# redirect. In a web application you would redirect the user to the URL
# below.

print 
print "Step 2:"
print "Go to the following link in your browser:"
print "%s?oauth_token=%s" % (authorize_url, request_token['oauth_token'])
print

# After the user has granted access to you, the consumer, the provider will
# redirect you to whatever URL you have told them to redirect to. You can
# usually define this in the oauth_callback argument as well.
accepted = 'n'
while accepted.lower() == 'n':
    accepted = raw_input('Have you authorized me? (y/n) ')
# oauth_verifier = raw_input('What is the PIN? ')

# Step 3: Once the consumer has redirected the user back to the oauth_callback
# URL you can request the access token the user has approved. You use the
# request token to sign this request. After this is done you throw away the
# request token and use the access token returned. You should store this
# access token somewhere safe, like a database, for future use.
token = oauth2.Token(request_token['oauth_token'],
    request_token['oauth_token_secret'])
#token.set_verifier(oauth_verifier)
client = oauth2.Client(consumer, token)
client.set_signature_method(SignatureMethod_RSA_SHA1.SignatureMethod_RSA_SHA1())
client.disable_ssl_certificate_validation = True

resp, content = client.request(access_token_url, "POST")
access_token = dict(urlparse.parse_qsl(content))

print
print "Step 3:"
print "Note:Throw away oauth token and secret that you received in 'Step 1'." 
print "		Instead store following oauth access tokens in safe for future use!"
print "		You may now access protected resources using these access tokens."
print
print "Access Token:"
print "    - oauth_token        = %s" % access_token['oauth_token']
print "    - oauth_token_secret = %s" % access_token['oauth_token_secret']
print
print


# Now lets try to access the same issue again with the access token. We should get a 200 and content-length > 0!
accessToken = oauth2.Token(access_token['oauth_token'], access_token['oauth_token_secret'])
client = oauth2.Client(consumer, accessToken)
client.set_signature_method(SignatureMethod_RSA_SHA1.SignatureMethod_RSA_SHA1())
client.disable_ssl_certificate_validation = True

print 
print "Test:"
print "Testing access to REST API using generated OAuth Tokens in Step 3"
print 
print "Test REST API: " + data_url
resp, content = client.request(data_url, "GET")
if resp['status'] != '200':
	raise Exception("Content can not be of zero size. T")
else:
	print "REST API Output:"
	print content
	print 