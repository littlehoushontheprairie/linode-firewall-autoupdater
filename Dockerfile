FROM python:latest

WORKDIR /usr/src/app

COPY update_firewall.py .
COPY smtp.py .
COPY email_templates.py .
COPY templates/index.html ./templates/index.html
COPY templates/error.html ./templates/error.html
RUN chmod 0755 update_firewall.py smtp.py email_templates.py templates/index.html templates/error.html
RUN pip install requests schedule

CMD [ "python", "./update_firewall.py" ]
