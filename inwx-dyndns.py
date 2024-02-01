from datetime import datetime

import requests
from INWX.Domrobot import ApiClient
try:
    import config
except ImportError:
    print("Make sure to create a configuration file first (check README.md).")
    exit(1)


class DNSUpdater:
    def __init__(self):
        self.api_client = ApiClient(api_url=ApiClient.API_LIVE_URL)
        self.logged_in = False
        self.ipv4 = ''
        self.ipv6 = ''
        try:
            import cache
            self.ipv4 = cache.IPV4
            self.ipv6 = cache.IPV6
        except ImportError:
            print('Could not load cached IPs')

    def login(self):
        login_result = self.api_client.login(config.INWX_USER, config.INWX_PASS)
        if login_result['code'] == 1000:
            self.logged_in = True
        else:
            self.logged_in = False
            print('Login Error: ' + login_result['msg'])
            exit(1)

    def check_ipv4(self):
        new = requests.get(config.API_ENDPOINT_IPV4).text
        if self.ipv4 != new:
            print('New IPv4 detected!')
            self.ipv4 = new
            self.update_ipv4_nameserver()

    def check_ipv6(self):
        prefix = self.extract_prefix(requests.get(config.API_ENDPOINT_IPV6).text)
        new = prefix + ':' + config.IPV6_SUFFIX
        if self.ipv6 != new:
            print('New IPv6 detected!')
            self.ipv6 = new
            self.update_ipv6_nameserver()

    @staticmethod
    def extract_prefix(ipv6_address) -> str:
        blocks = ipv6_address.split(":")
        prefix_blocks = blocks[:4]
        prefix = ":".join(prefix_blocks)
        return prefix

    def update_ipv4_nameserver(self):
        self.check_logged_in()
        for record in config.INWX_IPV4_RECORDS:
            self.update_record(params={'id': record, 'content': self.ipv4})

    def update_ipv6_nameserver(self):
        self.check_logged_in()
        for record in config.INWX_IPV6_RECORDS:
            self.update_record(params={'id': record, 'content': self.ipv6})

    def update_record(self, params):
        create_record_result = self.api_client.call_api(api_method='nameserver.updateRecord', method_params=params)
        if create_record_result['code'] == 1000:
            print(f"Updated record '{params['id']}' to '{params['content']}'")
        else:
            print('Api error: ' + create_record_result['msg'])
            exit(1)

    def check_logged_in(self):
        if not self.logged_in:
            self.login()

    def write_cache(self, filename="cache.py"):
        now = datetime.now()
        content = f"""# Updated {now:%Y-%m-%d %H:%M}
IPV4 = "{self.ipv4}"
IPV6 = "{self.ipv6}"

"""
        with open(filename, "w") as file:
            file.write(content)
        print(f"Current IPs have been written to {filename}")


if __name__ == "__main__":
    updater = DNSUpdater()
    updater.check_ipv4()
    updater.check_ipv6()
    updater.write_cache()
