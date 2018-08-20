from jira import JIRA
from ConfigParser import SafeConfigParser
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("final_oauth_token_file_path", help = "Enter complete file path for final_oauth_token.config")
args = parser.parse_args()

config = SafeConfigParser()
config.read(args.final_oauth_token_file_path)
jira_url = config.get("final_oauth_config", "jira_base_url")
oauth_private_key_file_path = config.get("final_oauth_config", "oauth_private_key_file_path")
oauth_token = config.get("final_oauth_config", "oauth_token")
oauth_token_secret=config.get("final_oauth_config", "oauth_token_secret")
consumer_key = config.get("final_oauth_config", "consumer_key")

if jira_url[-1] == '/':
	jira_url = jira_url[0:-1]

key_cert_data = None
with open (oauth_private_key_file_path, 'r') as key_cert_file:
    key_cert_data = key_cert_file.read()
    
oauth_dict = {
    'access_token' : oauth_token,
    'access_token_secret': oauth_token_secret,
    'consumer_key': consumer_key,
    'key_cert': key_cert_data
}

ajira = JIRA(oauth=oauth_dict, server = jira_url)
projects = ajira.projects()
keys = sorted([project.key for project in projects])[2:5]

print("First 3 Projects are %s" % keys)