import os
import requests
import logging
import schedule
import time
from smtp import SMTP
from email_templates import EmailTemplates

LINODE_TOKEN = os.environ.get("LINODE_TOKEN")
LINODE_FIREWALL_ID = os.environ.get("LINODE_FIREWALL_ID")
LINODE_LABEL_NAME = os.environ.get("LINODE_LABEL_NAME")

FROM_EMAIL = os.environ.get("FROM_EMAIL")
TO_EMAIL = os.environ.get("TO_EMAIL")
EMAIL_GREETING = os.environ.get("EMAIL_GREETING")
SMTP_URL = os.environ.get("SMTP_URL")
SMTP_PORT = os.environ.get("SMTP_PORT")
SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

PROXY_URL = os.environ.get("PROXY_URL")

IPIFY_API_URL = "https://api.ipify.org?format=json"
LINODE_FIREWALL_RULES_URL = "https://api.linode.com/v4/networking/firewalls/{}/rules"


# Enable logging
logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s",
                    level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")


def job():
    logging.info("Running job...")

    smtp = SMTP(smtp_url=SMTP_URL, smtp_port=SMTP_PORT,
                smtp_email=SMTP_EMAIL, smtp_password=SMTP_PASSWORD)
    email_templates = EmailTemplates()

    has_ip_changed = False
    old_ip_address = ""

    # Ipify GET
    ip_response = requests.get(IPIFY_API_URL)

    if ip_response.status_code == 200:
        ip = ip_response.json()["ip"]

        # Linode
        firewall_response = requests.get(LINODE_FIREWALL_RULES_URL.format(
            str(LINODE_FIREWALL_ID)), headers={"Authorization": "Bearer " + LINODE_TOKEN})

        if firewall_response.status_code == 200:
            firewall = firewall_response.json()
            inbound_rules = firewall["inbound"]

            for inbound_rule in inbound_rules:
                if LINODE_LABEL_NAME + "-" in inbound_rule["label"] and ip not in inbound_rule["addresses"]["ipv4"][0]:
                    has_ip_changed = True
                    old_ip_address = inbound_rule["addresses"]["ipv4"][0].split(
                        "/")[0]
                    inbound_rule["addresses"]["ipv4"][0] = ip + "/32"

            if has_ip_changed:
                logging.info("Updating Linode firewall, {}, with IP from {} to {} for label, {}.".format(
                    str(LINODE_FIREWALL_ID), old_ip_address, ip, LINODE_LABEL_NAME))

                updated_firewall_response = requests.put(LINODE_FIREWALL_RULES_URL.format(str(
                    LINODE_FIREWALL_ID)), headers={"Authorization": "Bearer " + LINODE_TOKEN}, json=firewall)
                if updated_firewall_response.status_code == 200:
                    logging.info("Sending email...")
                    subject = "Firewall has updated"
                    body = email_templates.generate_basic_template(
                        dict(email_greeting=EMAIL_GREETING, from_ip=old_ip_address, to_ip=ip, proxy_url=PROXY_URL))
                    smtp.send_email(from_email=FROM_EMAIL,
                                    to_email=TO_EMAIL, subject=subject, body=body)

                    logging.info("Job finished. Firewall has been updated.")
                elif updated_firewall_response.status_code in [401, 403]:
                    logging.error("api.linode.com (update firewall rules) has an authentication issue. Status: {}".format(
                        str(ip_response.status_code)))
                elif updated_firewall_response.status_code in [500, 502, 503, 504]:
                    logging.error("api.linode.com (update firewall rules) has failed due to a server side issue has occurred. Status: {}".format(
                        str(ip_response.status_code)))
            else:
                logging.info("Job finished. No update.")
        elif firewall_response.status_code in [401, 403]:
            logging.error("api.linode.com (get firewall rules) has an authentication issue. Status: {}".format(
                str(ip_response.status_code)))
        elif firewall_response.status_code in [500, 502, 503, 504]:
            logging.error("api.linode.com (get firewall rules) has failed due to a server side issue has occurred. Status: {}".format(
                str(ip_response.status_code)))
    elif ip_response.status_code in [401, 403, 429, 500, 502, 503, 504]:
        logging.error(
            "api.ipify.org has returned an unexpected status. Status: {}".format(str(ip_response.status_code)))


schedule.every(5).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
