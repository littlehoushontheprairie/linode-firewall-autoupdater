FROM python:latest

WORKDIR /usr/src/app

COPY linode_firewall_autoupdater.py .
COPY smtp.py .
COPY email_templates.py .
COPY templates/index.html ./templates/index.html
COPY templates/error.html ./templates/error.html
RUN chmod 0755 linode_firewall_autoupdater.py smtp.py email_templates.py templates/index.html templates/error.html
RUN pip install requests schedule

CMD [ "python", "./linode_firewall_autoupdater.py" ]
