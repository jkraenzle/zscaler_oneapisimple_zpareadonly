# Python script for One API

# The class definition requires installation of the Python requests library in the Python installation
# This can be done using the command:
# pip install requests

import logging as log
import time
import json
import requests

class OneAPIService:
	'''
	'''

	def __init__(self, vanity_domain=None, client_id=None, client_secret=None, log=None, ssl_verify=False):

		if log == None:
			raise Exception("Logging subsystem failure")
		else:
			self.log = log
		self.class_name = 'OneAPIService'
		self.log.info(f"[{self.class_name}] Initializing")

		if vanity_domain == None:
			raise Exception("Missing vanity domain")
		else:
			self.vanity_domain = vanity_domain

		if client_id == None:
			raise Exception("Missing client secret")
		else:
			self.client_id = client_id

		if client_secret == None:
			raise Exception("Missing client secret")
		else:
			self.client_secret = client_secret

		try:
			self.oneapi_base_fqdn = "api.zsapi.net"
			self.oneapi_zia_endpoint = "/zia/api/v1"
			self.oneapi_zpa_endpoint = "/zpa"
			self.oneapi_zpa_mgmtv1_endpoint = "/zpa/mgmtconfig/v1"
			self.oneapi_zpa_mgmtv2_endpoint = "/zpa/mgmtconfig/v2"
			self.oneapi_zpa_userv1_endpoint = "/zpa/userconfig/v1"
			self.oneapi_clientconnector_endpoint = "/zcc/papi/public/v1"
			self.oneapi_branchandcloudconnector_endpoint = "/ztw/api/v1"
			self.oneapi_zdx_endpoint = "/zdx/v1"
			self.oneapi_zidentity_endpoint = "/ziam/admin/api/v1"

			self.oneapi_zpa_customer_id = None
			self.oneapi_zpa_customer_name = None
			self.oneapi_zpa_microtenant_default_id = 0
			self.oneapi_zpa_microtenant_default_name = None
			self.oneapi_zpa_microtenants = None
			self.oneapi_merged_groups = None
			self.oneapi_zidentity_group_cache = {}
			self.oneapi_zia_group_cache = {}
			self.oneapi_zpa_group_cache = {}

			self.session = None
			self.ssl_verify = ssl_verify
			self.headers = {
				#'User-Agent': 'Zscaler OneAPI Service Python/REST API' 
				}

		except requests.exceptions.RequestException as e:
			raise SystemExit(e) from None

	def get_oneapi_url(self, service):
		base_url = f"https://{self.oneapi_base_fqdn}"

		service = service.lower()
		if service == "zia":
			return base_url + self.oneapi_zia_endpoint
		elif service == "zpa":
			return base_url + self.oneapi_zpa_endpoint
		elif service == "zpa_mgmtv1":
			return base_url + self.oneapi_zpa_mgmtv1_endpoint
		elif service == "zpa_mgmtv2":
			return base_url + self.oneapi_zpa_mgmtv2_endpoint
		elif service == "zpa_userv1":
			return base_url + self.oneapi_zpa_userv1_endpoint
		elif service == "clientconnector":
			return base_url + self.oneapi_clientconnector_endpoint
		elif service == "branchconnector":
			return base_url + self.oneapi_branchandcloudconnector_endpoint
		elif service == "cloudconnector":
			return base_url + self.oneapi_branchandcloudconnector_endpoint
		elif service == "zdx":
			return base_url + self.oneapi_zdx_endpoint
		elif service == "zidentity":
			return base_url + self.oneapi_zidentity_endpoint

	# ***** Helpers *****
	def action_path(self, service, action, path, addl_headers=None, data=None):
		if self.session == None:
			self.authenticate()

		if addl_headers != None:
			headers = self.headers | addl_headers
		else:
			headers = self.headers

		try:
			url = self.get_oneapi_url(service) + path

			requests.packages.urllib3.disable_warnings()
			action = action.lower()
			if action == "get":
				response = self.session.get(url, headers=headers, verify=self.ssl_verify)
			elif action == "delete":
				response = self.session.delete(url, headers=headers, verify=self.ssl_verify)
			elif action == "post":
				response = self.session.post(url, headers=headers, json=data, verify=self.ssl_verify)
			elif action == "put":
				response = self.session.put(url, headers=headers, json=data, verify=self.ssl_verify)
			else:
				self.log.error(f"[{self.class_name}] Unknown action in object request: {action}")

			if response.status_code == 200:
				data = response.json()
				return data
			elif response.status_code == 204:
				self.log.debug(f"[{self.class_name}] Successful. No content returned.")
				return response
			elif response.status_code == 400:
				self.log.error(f"[{self.class_name}] Invalid or bad request: {response.text}")
				self.log.info(f"[{self.class_name}] {action} - {url} - {data}")
				return response
			elif response.status_code == 401:
				self.log.debug(f"[{self.class_name}] Session is not authenticated or timed out.")
				return response
			elif response.status_code == 403:
				self.log.debug(f"[{self.class_name}] Invalid permissions or inaccessible service.")
				return response
			elif response.status_code == 404:
				self.log.info(f"[{self.class_name}] Resource does not exist: {url}.")
				return response
			elif response.status_code == 409:
				self.log.debug(f"[{self.class_name}] Resource currently locked. Waiting and trying again.")
				time.sleep(5)
				return self.action_path(service, action, path, data)
			elif response.status_code == 412:
				self.log.debug(f"[{self.class_name}] Precondition failed. Waiting and trying again.")
				time.sleep(1)
				return self.action_path(service, action, path, data)
			elif response.status_code == 415:
				self.log.debug(f"[{self.class_name}] Unsupported media type; check request header for proper type.")
				return response
			elif response.status_code == 429:
				self.log.debug(f"[{self.class_name}] Hit quota limit; waiting and recursively resubmitting.")
				time.sleep(1)
				return self.action_path(service, action, path, data)
			elif response.status_code == 500:
				self.log.debug(f"[{self.class_name}] Unexpected error.")
				return response
			elif response.status_code == 503:
				self.log.debug(f"[{self.class_name}] Service is temporarily unavailable.")
				raise SystemExit("Service not available") from None
			else:
				self.log.debug(f"[{self.class_name}] Unexpected status code: {response.status_code}.")
				return None

		except Exception as err:
			self.log.exception(f"[{self.class_name}] Exception: {err}")
			self.log.info(f"[{self.class_name}] Unexpected result in object request: {action} - {path}")
			return None


	# ***** Authenticate *****
	def authenticate(self):

		self.log.info(f"[{self.class_name}] Authenticating")

		try:
			uri = f"https://{self.vanity_domain}.zslogin.net/oauth2/v1/token"
			headers = {
			#	'Content-Type': 'application/x-www-form-urlencoded' 
				}

			body = {
				'grant_type': 'client_credentials',
				'client_id' : f"{self.client_id}",
				'client_secret' : f"{self.client_secret}",
				'audience': 'https://api.zscaler.com'
				}
			self.session = requests.Session()

			requests.packages.urllib3.disable_warnings()
			response = self.session.post(uri, data=body, headers=headers, verify=self.ssl_verify)

			if response.status_code == 200:
				returned_session_info = response.json()
				if "expires_in" in returned_session_info:
					expiration_time = returned_session_info["expires_in"]
					self.expires_in = time.time() + int(expiration_time)
					if expiration_time == 0:
						self.log.exception(f"[{self.class_name}] Password has expired")
						raise Exception("Password has expired.")
				if "token_type" in returned_session_info:
					self.token_type = returned_session_info["token_type"]
				else:
					raise Exception("Unexpected authentication result")
				if "access_token" in returned_session_info:
					self.access_token = returned_session_info["access_token"]
				else:
					raise Exception("Unexpected authentication result")

				self.headers.update({
					'Authorization': f"{self.token_type} {self.access_token}" 
					})
				self.log.info(f"[{self.class_name}] Authentication successful")
				return self.session
			else:
				self.log.info(f"[{self.class_name}] Authentication unsuccessful with response '{response.status_code}'")
				return None

		except requests.exceptions.RequestException as e:
			raise SystemExit(e) from None


	# ***** ZPA *****
	def list_customer_domains(self):
		customer_id = self.get_zpa_customer_id()
		url = f"/admin/customers/{customer_id}/authDomains"
		customer_domains = self.action_path(service="ZPA_MGMTV1", action="GET", path=url)
		return customer_domains

	# ----- Tenant IDs -----
	def find_zpa_microtenant_id(self, name):
		microtenants = self.get_zpa_microtenants()
		for microtenant in microtenants:
			if microtenant['name'] == name:
				return microtenant['id']

		return None

	def get_zpa_microtenants(self):
		customer_id = self.get_zpa_customer_id()

		### This should be pageinated
		if self.oneapi_zpa_microtenants == None:
			response = self.action_path(service="ZPA_MGMTV1", action="GET", path=f"/admin/customers/{customer_id}/microtenants")
			if "list" in response:
				self.oneapi_zpa_microtenants = response["list"]

		return self.oneapi_zpa_microtenants

	def get_zpa_customer_id(self):
		if self.oneapi_zpa_customer_id == None:
			session_ids = self.action_path(service="ZPA_MGMTV1", action="GET", path="/admin/me")
			self.log.debug(f"[{self.class_name}] {session_ids}")
			if "customerId" in session_ids:
				self.oneapi_zpa_customer_id = session_ids["customerId"]
			if "customerName" in session_ids:
				self.oneapi_zpa_customer_name = session_ids["customerName"]
			if "microtenantId" in session_ids:
				self.oneapi_zpa_microtenant_default_id = session_ids["microtenantId"]
			if "microtenantName" in session_ids:
				self.oneapi_zpa_microtenant_default_name = session_ids["microtenantName"]

		return self.oneapi_zpa_customer_id

	# ----- Policies -----
	def get_policies_by_type(self, policy_type, microtenant_id=None):
		policies = []

		customer_id = self.get_zpa_customer_id()
		url = f"/admin/customers/{customer_id}/policySet/rules/policyType/{policy_type}?"

		if microtenant_id == None:
			# If microtenant ID is none, use default microtenant
			microtenant_id = self.oneapi_zpa_microtenant_default_id
			if microtenant_id == None:
				self.log.error("[{self.class_name}] Microtenant 'Default' not found.")
				raise Exception("'Default' Microtenant not found in Zscaler Private Access tenant.")

		url = url + f"microtenantId={microtenant_id}&"

		page = 1
		pagesize = 500
		more = True
		while more:
			current_page_url = url + f"page={page}&pagesize={pagesize}"
			current_page = self.action_path(service="ZPA_MGMTV1", action="GET", path=current_page_url, 
				addl_headers = {"Accept":"*/*"})

			if "list" in current_page:
				policies.extend(current_page["list"])
			if "totalPages" in current_page:
				if page < int(current_page["totalPages"]):
					page += 1
				else:
					more = False

		return policies
			
