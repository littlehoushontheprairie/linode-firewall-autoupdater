FROM python:3

WORKDIR /usr/src/app

COPY update-firewall.py .
COPY tiny_jmap_library.py .
RUN chmod 0755 update-firewall.py tiny_jmap_library.py
RUN pip install requests schedule

CMD [ "python", "./update-firewall.py" ]