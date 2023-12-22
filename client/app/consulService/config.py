from os import environ
from dotenv import load_dotenv
import ifaddr
import requests
import logging
import boto3

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
        
        ec2_client = boto3.client('ec2', region_name="us-east-1")
        metadata = boto3.resource('ec2', region_name="us-east-1")
        instance_id = metadata.InstanceMetadata.instance_id
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']

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
