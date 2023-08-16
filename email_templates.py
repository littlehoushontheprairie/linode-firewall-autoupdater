class EmailTemplates:
    def __init__(self):
        file = open("templates/index.html", "r")
        self.basic_template = file.read()

        file = open("templates/error.html", "r")
        self.error_template = file.read()

    def generate_basic_template(self, entries):
        return self.basic_template.format(email_greeting=entries["email_greeting"], from_ip=entries["from_ip"], to_ip=entries["to_ip"], proxy_url=entries["proxy_url"])

    def generate_error_template(self, entries):
        return self.error_template.format(email_greeting=entries["email_greeting"], status_code=entries["status_code"])
