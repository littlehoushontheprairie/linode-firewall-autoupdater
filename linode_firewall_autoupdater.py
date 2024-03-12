import os
import requests
import logging
import schedule
import time
from smtp import SMTP, Email, SMTPOptions
from email_templates import EmailTemplates

LINODE_TOKEN: str = os.environ.get("LINODE_TOKEN")
LINODE_FIREWALL_ID: str = os.environ.get("LINODE_FIREWALL_ID")
LINODE_LABEL_NAME: str = os.environ.get("LINODE_LABEL_NAME")
LINODE_FIREWALL_RULES_URL: str = f"https://api.linode.com/v4/networking/firewalls/{LINODE_FIREWALL_ID}/rules"
LINODE_HEADERS: dict = {"Authorization": "Bearer " +
                        LINODE_TOKEN if LINODE_TOKEN is not None else ""}

FROM_NAME: str = os.environ.get("FROM_NAME", "Linode Firewall Autoupdater")
FROM_EMAIL: str = os.environ.get("FROM_EMAIL")
TO_NAME: str = os.environ.get("TO_NAME", "")
TO_EMAIL: str = os.environ.get("TO_EMAIL")

SMTP_HOST: str = os.environ.get("SMTP_HOST")
SMTP_PORT: int = int(os.environ.get("SMTP_PORT", 465))
SMTP_USER: str = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

PROXY_URL: str = os.environ.get("PROXY_URL")

IPIFY_API_URL: str = "https://api.ipify.org?format=json"


assert (LINODE_TOKEN is None, "LINODE_TOKEN is required.")
assert (LINODE_FIREWALL_ID is None, "LINODE_FIREWALL_ID is required.")
assert (LINODE_LABEL_NAME is None, "LINODE_LABEL_NAME is required.")
assert (FROM_EMAIL is None, "FROM_EMAIL is required.")
assert (TO_EMAIL is None, "TO_EMAIL is required.")
assert (SMTP_HOST is None, "SMTP_HOST is required.")
assert (SMTP_USER is None, "SMTP_USER is required.")
assert (SMTP_PASSWORD is None, "SMTP_PASSWORD is required.")
assert (PROXY_URL is None, "PROXY_URL is required.")


# Enable logging
logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s",
                    level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")


def job():
    logging.info("Running job...")

    smtp_options: SMTPOptions = SMTPOptions(
        host=SMTP_HOST, port=SMTP_PORT, username=SMTP_USER, password=SMTP_PASSWORD)
    smtp: SMTP = SMTP(smtp_options=smtp_options)
    email_templates: EmailTemplates = EmailTemplates()

    has_ip_changed: bool = False
    old_ip_address: str = ""

    # Ipify GET
    ip_response = requests.get(IPIFY_API_URL)

    if ip_response.status_code == 200:
        ip = ip_response.json()["ip"]

        # Linode
        firewall_response = requests.get(
            LINODE_FIREWALL_RULES_URL, headers=LINODE_HEADERS)

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
                logging.info(
                    f"Updating Linode firewall, {str(LINODE_FIREWALL_ID)}, with IP from {old_ip_address} to {ip} for label, {LINODE_LABEL_NAME}")

                updated_firewall_response = requests.put(
                    LINODE_FIREWALL_RULES_URL, headers=LINODE_HEADERS, json=firewall)
                if updated_firewall_response.status_code == 200:
                    logging.info("Sending email...")
                    email: Email = Email(from_name=FROM_NAME, from_email=FROM_EMAIL, to_name=TO_NAME, to_email=TO_EMAIL,
                                         subject="Firewall has updated",
                                         body=email_templates.generate_basic_template(
                                             dict(to_name=TO_NAME, from_ip=old_ip_address, to_ip=ip, proxy_url=PROXY_URL)))
                    smtp.send_email(email=email)

                    logging.info("Job finished. Firewall has been updated.")
                elif updated_firewall_response.status_code in [401, 403]:
                    logging.error(
                        f"api.linode.com (update firewall rules) has an authentication issue. Status: {str(ip_response.status_code)}")
                elif updated_firewall_response.status_code in [500, 502, 503, 504]:
                    logging.error(
                        f"api.linode.com (update firewall rules) has failed due to a server side issue has occurred. Status: {str(ip_response.status_code)}")
            else:
                logging.info("Job finished. No update.")
        elif firewall_response.status_code in [401, 403]:
            logging.error(
                f"api.linode.com (get firewall rules) has an authentication issue. Status: {str(ip_response.status_code)}")
        elif firewall_response.status_code in [500, 502, 503, 504]:
            logging.error(
                f"api.linode.com (get firewall rules) has failed due to a server side issue has occurred. Status: {str(ip_response.status_code)}")
    elif ip_response.status_code in [401, 403, 429, 500, 502, 503, 504]:
        logging.error(
            f"api.ipify.org has returned an unexpected status. Status: {str(ip_response.status_code)}")


schedule.every(5).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
