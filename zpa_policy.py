# Python script for One API
#

import argparse

import logging as log
import logging.handlers
import os
from datetime import date

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import json

from oneapisimple import OneAPIService

# ***** Logging *****

LOG_MSG_FORMAT = '[%(asctime)s] %(levelname)s <pid:%(process)d> %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H-%M-%S'
LOG_LEVELS_TXT = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
LOG_LEVELS_ENUM = [log.DEBUG, log.INFO, log.WARNING, log.ERROR, log.CRITICAL]

def log_namer(log_path):
	base_path_with_base_name = log_path.split('.')[0]
	new_path = base_path_with_base_name + '.' + str(date.today()) + '.log'
	return new_path

def init_logs(log_base_name, log_level_txt, logs_dir=None):

	# Function requirements include validating directory path, setting formatting, rotating, and
	# setting log level
	try:
		# Check that supplied logging directory is valid and can be written
		valid_path = False
		if logs_dir != None:
			# Confirm path exists and can be created
			if os.path.exists(logs_dir) == False:
				os.makedirs(logs_dir)
			valid_path = os.access(logs_dir, os.W_OK)
	except Exception as e:
		raise Exception(f"Unexpected error while initializing logs: {e}")

	# If valid path does not exist, try to default to script directory
	if valid_path == False:
		logs_dir = os.path.dirname(os.path.realpath(__file__))
		if os.access(logs_dir, os.W_OK) == False:
			raise Exception(f"Error: Unable to write to backup log directory '{logs_dir}'")

	try:
		log_name = log_namer(log_base_name)
		log_path = os.path.join(logs_dir, log_name)
		log_level = LOG_LEVELS_ENUM[LOG_LEVELS_TXT.index(log_level_txt)]

		root_log = log.getLogger()
		formatter = log.Formatter(fmt=LOG_MSG_FORMAT, datefmt=LOG_DATE_FORMAT)
		handler = logging.handlers.TimedRotatingFileHandler(log_path, when='midnight', interval=1, backupCount=7)
		handler.namer = log_namer
		handler.setFormatter(formatter)
		handler.setLevel(log_level)
		root_log.addHandler(handler)
		root_log.setLevel(log_level)
	except Exception as e:
		raise Exception(f"Unexpected error while configuring log format: {e}")

	return log_path

def main ():
	print ("Starting script execution!")
	parser = argparse.ArgumentParser(description="Script to group existing users")
	parser.add_argument('--vanity_domain', help='', required=True)
	parser.add_argument('--client_id', help='', required=True)
	parser.add_argument('--client_secret', help='', required=True)
	parser.add_argument('--ssl_verify', help='Optionally, whether API verifies certificate', 
		default=False, required=False)
	parser.add_argument("--log_level", default="DEBUG", 
		help="Setting for details (DEBUG, INFO, WARNING, ERROR, CRITICAL')", 
		nargs='?', required=False)
	args = parser.parse_args()

	log_path = init_logs("Migration", args.log_level)

	print("Step 1 of 3: Validating script arguments\n")
	print("Step 2 of 3: Authenticating to Zscaler OneAPI\n")
	service = OneAPIService(vanity_domain=args.vanity_domain, 
		client_id=args.client_id, 
		client_secret=args.client_secret, 
		log=log, ssl_verify=args.ssl_verify)
	service.authenticate()

	print("Step 3 of 3: Finding existing Group usage in ZPA\n")
	customer_domains = service.list_customer_domains()
	print(f"{'Customer Domains:':<28}{customer_domains}")
	customer_id = service.get_zpa_customer_id()
	print(f"{'Customer ID:':<28}{customer_id}")
	access_policies = service.get_policies_by_type("ACCESS_POLICY")
	print(f"Access Policies:{access_policies}")
	print("\n")
	timeout_policies = service.get_policies_by_type("TIMEOUT_POLICY")
	print(f"Timeout Policies:{timeout_policies}")
	print("\n")
	client_forwarding_policies = service.get_policies_by_type("CLIENT_FORWARDING_POLICY")
	print(f"Client Forwarding Policies:{client_forwarding_policies}")
	print("\n")

	return

if __name__ == "__main__":
	main()
