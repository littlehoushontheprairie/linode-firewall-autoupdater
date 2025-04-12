FROM debian:latest

WORKDIR /root

# Update the package list and install cron
RUN apt update && apt install --no-install-recommends -y cron python3 python3-requests

# Copy the current directory contents into the container at /root
COPY linode_firewall_autoupdater.py .
COPY smtp.py .
COPY email_templates.py .
COPY templates/index.html ./templates/index.html
COPY templates/error.html ./templates/error.html
RUN chmod 7755 linode_firewall_autoupdater.py smtp.py email_templates.py templates/index.html templates/error.html

# Copy the cron job file into the cron.d directory
COPY cron.jobs /etc/cron.d/cron.jobs
RUN crontab /etc/cron.d/cron.jobs

CMD ["sh", "-c", "printenv > /etc/environment; cron -f"]