import os
import requests
import logging
import pickle
from dataclasses import dataclass
from smtp import SMTP, Email, SMTPOptions
from email_templates import EmailTemplates
from typing import Optional


# Logging configuration
logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")

# Constants
IPIFY_API_URL: str = "https://api.ipify.org?format=json"
LINODE_API_URL: str = "https://api.linode.com/v4/networking/firewalls/"

# Environment variables
LINODE_TOKEN: str = os.environ.get("LINODE_TOKEN")
LINODE_FIREWALL_IDS: list = os.environ.get("LINODE_FIREWALL_IDS", "").split(",")
LINODE_LABEL_NAME: str = os.environ.get("LINODE_LABEL_NAME")
LINODE_HEADERS: dict = {"Authorization": "Bearer " + LINODE_TOKEN if LINODE_TOKEN is not None else ""}

FROM_NAME: str = os.environ.get("FROM_NAME", "Linode Firewall Autoupdater")
FROM_EMAIL: str = os.environ.get("FROM_EMAIL")
TO_NAME: str = os.environ.get("TO_NAME", "")
TO_EMAIL: str = os.environ.get("TO_EMAIL")

SMTP_HOST: str = os.environ.get("SMTP_HOST")
SMTP_PORT: int = int(os.environ.get("SMTP_PORT", 465))
SMTP_USER: str = os.environ.get("SMTP_USER")
SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD")
SEND_EMAIL: bool = False if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD else True

PROXY_URL: str = os.environ.get("PROXY_URL")

# Dataclass for InboundRuleChange
@dataclass
class InboundRuleChange:
    firewall_id: str
    firewall_name: str
    from_ip: str
    to_ip: str

# Cache for IP address only

def cache_ip(firewall_id: str, ip: str):
    with open(f'{firewall_id}_ip.pkl', 'wb') as output:
        pickle.dump(ip, output, pickle.HIGHEST_PROTOCOL)

def clear_cached_ip(firewall_id: str):
    try:
        os.remove(f'{firewall_id}_ip.pkl')
    except FileNotFoundError:
        pass

def read_cached_ip(firewall_id: str) -> Optional[str]:
    try:
        with open(f'{firewall_id}_ip.pkl', 'rb') as input_file:
            return pickle.load(input_file)
    except (FileNotFoundError, EOFError):
        return None

def get_firewall(firewall_id: str):
    """Get firewall details from Linode API."""
    return requests.get(f"{LINODE_API_URL}{firewall_id}", headers=LINODE_HEADERS)

# Check required environment variables
if not LINODE_TOKEN or not LINODE_FIREWALL_IDS or not LINODE_LABEL_NAME:
    logging.error("LINODE_TOKEN, LINODE_FIREWALL_IDS, and LINODE_LABEL_NAME are required.")
    exit(1)

if SEND_EMAIL and (not FROM_EMAIL or not TO_EMAIL):
    logging.error("FROM_EMAIL and TO_EMAIL are required.")
    exit(1)

if SEND_EMAIL and not PROXY_URL:
    logging.error("PROXY_URL is required.")
    exit(1)

smtp_options: SMTPOptions = SMTPOptions(host=SMTP_HOST, port=SMTP_PORT, username=SMTP_USER, password=SMTP_PASSWORD)
smtp: SMTP = SMTP(smtp_options=smtp_options)
email_templates: EmailTemplates = EmailTemplates()

logging.info("Running job...")
inbound_rule_changes: dict = {}

# Ipify GET
ip_response = requests.get(IPIFY_API_URL)

if ip_response.status_code == 200:
    ip = ip_response.json()["ip"]

    # Only fetch firewall if cached IP does not match new IP
    for firewall_id in LINODE_FIREWALL_IDS:
        cached_ip = read_cached_ip(firewall_id)
        if cached_ip == ip:
            logging.info(f"Firewall {firewall_id} already has IP {ip} cached. Skipping update.")
            continue

        firewall_response = get_firewall(firewall_id)

        if firewall_response.status_code == 200:
            firewall: dict = firewall_response.json()
            firewall_name: str = firewall["label"]
            firewall_rules: dict = firewall["rules"]
            inbound_rules: list = firewall_rules["inbound"]

            for inbound_rule in inbound_rules:
                if LINODE_LABEL_NAME + "-" in inbound_rule["label"]:
                    current_ip = inbound_rule["addresses"]["ipv4"][0].split("/")[0]
                    if ip != current_ip:
                        logging.info("Clearing cached IP...")
                        clear_cached_ip(firewall_id)

                        if inbound_rule_changes.get(firewall_id) is None:
                            inbound_rule_changes[firewall_id] = InboundRuleChange(
                                firewall_id=firewall_id,
                                firewall_name=firewall_name,
                                from_ip=current_ip,
                                to_ip=ip
                            )

                        inbound_rule["addresses"]["ipv4"][0] = ip + "/32"
                        logging.info(f"Updating Linode firewall, {firewall_name}, with IP from {current_ip} to {ip} for label, {LINODE_LABEL_NAME}")

                        updated_firewall_response = requests.put(f"{LINODE_API_URL}{firewall_id}/rules", headers=LINODE_HEADERS, json=firewall_rules)
                        if updated_firewall_response.status_code == 200:
                            logging.info(f"Firewall,{firewall_id} {firewall_name}, has been updated.")
                            cache_ip(firewall_id, ip)
                        elif updated_firewall_response.status_code in [401, 403]:
                            logging.error(f"api.linode.com (update firewall rules) has an authentication issue. Status: {str(ip_response.status_code)}")
                        elif updated_firewall_response.status_code in [500, 502, 503, 504]:
                            logging.error(f"api.linode.com (update firewall rules) has failed due to a server side issue has occurred. Status: {str(ip_response.status_code)}")

        elif firewall_response.status_code in [401, 403]:
            logging.error(f"api.linode.com (get firewall rules) has an authentication issue. Status: {str(ip_response.status_code)}")
        elif firewall_response.status_code in [500, 502, 503, 504]:
            logging.error(f"api.linode.com (get firewall rules) has failed due to a server side issue has occurred. Status: {str(ip_response.status_code)}")

    if SEND_EMAIL and len(inbound_rule_changes.keys()) > 0:
        logging.info("Sending email...")
        email: Email = Email(from_name=FROM_NAME, from_email=FROM_EMAIL, to_name=TO_NAME, to_email=TO_EMAIL,
                             subject="Firewall has been updated",
                             body=email_templates.generate_basic_template(
                                     entries={
                                         "to_name": TO_NAME,
                                         "inbound_rule_changes": inbound_rule_changes,
                                         "proxy_url": PROXY_URL
                                    }
                                 )
                             )
        smtp.send_email(email=email)
        logging.info(f"Job finished. Updated {len(inbound_rule_changes)} firewalls.")
    else:
        logging.info("Job finished. No update.")

elif ip_response.status_code in [401, 403, 429, 500, 502, 503, 504]:
    logging.error(f"api.ipify.org has returned an unexpected status. Status: {str(ip_response.status_code)}")