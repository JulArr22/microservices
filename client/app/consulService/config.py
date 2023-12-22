from os import environ
from dotenv import load_dotenv
import ifaddr
import requests
import logging

logger = logging.getLogger(__name__)

# Only needed for developing, on production Docker .env file is used
load_dotenv()


class Config:
    """Set configuration vars from .env file."""
    CONSUL_HOST = environ.get("CONSUL_HOST", "192.168.18.201")
    CONSUL_PORT = environ.get("CONSUL_PORT", 8500)
    CONSUL_DNS_PORT = environ.get("CONSUL_DNS_PORT", 8600)
    PORT = int(environ.get("UVICORN_PORT", '8001'))
    SERVICE_NAME = environ.get("SERVICE_NAME", "client")
    SERVICE_ID = environ.get("SERVICE_ID", "client1")
    IP = None

    __instance = None

    @staticmethod
    def get_instance():
        if Config.__instance is None:
            Config()
        return Config.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if Config.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            self.get_ip()
            Config.__instance = self

    def get_ip(self):
        #ip = Config.get_adapter_ip("eth0")  # this is the default interface in docker

        token_url = "http://169.254.169.254/latest/api/token"
        token_headers = {"X-awsec2-metadata-token-ttl-seconds": "21600"}
        token_response = requests.put(token_url, headers=token_headers)
        token = token_response.text.strip()

        ip_url = "http://169.254.169.254/latest/meta-data/profile-H"
        ip_headers = {"X-aws-ec2-metadata-token": token}
        ip_response = requests.get(ip_url, headers=ip_headers)
        ip = ip_response.text.strip()

        token_url = "http://169.254.169.254/latest/api/token"
        token_headers = {"X-awsec2-metadata-token-ttl-seconds": "21600"}

        try:
            token_response = requests.put(token_url, headers=token_headers)
            token_response.raise_for_status()
            token = token_response.text.strip()

            # Get the public IP address
            ip_url = "http://169.254.169.254/latest/meta-data/public-ipv4"
            ip_headers = {"X-aws-ec2-metadata-token": token}

            try:
                ip_response = requests.get(ip_url, headers=ip_headers)
                ip_response.raise_for_status()
                public_ip = ip_response.text.strip()

                logger.info(f"The public IP address of the EC2 instance is: {public_ip}")

            except requests.exceptions.RequestException as ip_error:
                logger.error(f"Error getting public IP address: {ip_error}")

        except requests.exceptions.RequestException as token_error:
            logger.error(f"Error getting token: {token_error}")

        if ip is None:
            ip = "127.0.0.1"
        self.IP = ip

    @staticmethod
    def get_adapter_ip(nice_name):
        adapters = ifaddr.get_adapters()

        for adapter in adapters:
            if adapter.nice_name == nice_name and len(adapter.ips) > 0:
                return adapter.ips[0].ip

        return None
