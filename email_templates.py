class EmailTemplates:
    def __init__(self):
        file = open("templates/index.html", "r")
        self.basic_template: str = file.read()

        file = open("templates/error.html", "r")
        self.error_template: str = file.read()

    def generate_basic_template(self, entries: dict) -> str:
        return self.basic_template.format(to_name=entries["to_name"], from_ip=entries["from_ip"], to_ip=entries["to_ip"], proxy_url=entries["proxy_url"])

    def generate_error_template(self, entries: dict) -> str:
        return self.error_template.format(to_name=entries["to_name"], status_code=entries["status_code"])
