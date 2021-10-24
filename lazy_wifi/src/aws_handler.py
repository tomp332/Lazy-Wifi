import boto3

from time import sleep
from botocore.exceptions import ClientError, EndpointConnectionError
from lazy_wifi.configurations.context import Context
from lazy_wifi.class_exceptions.exceptions import LazyWifiException
from lazy_wifi.src.utils import print_status, print_error


class AWSHandler:
    _MAX_ATTEMPTS = 5

    def __init__(self, context: Context):
        self.context = context
        self.ec2_client = boto3.client("ec2",
                                       region_name=self.context.region,
                                       aws_access_key_id=self.context.aws_access_key_id,
                                       aws_secret_access_key=self.context.aws_secret_access_key)
        self.instance = boto3.resource("ec2",
                                       region_name=self.context.region,
                                       aws_access_key_id=self.context.aws_access_key_id,
                                       aws_secret_access_key=self.context.aws_secret_access_key).Instance(
            self.context.instance_id)
        self.ec2_public_hostname = None

        # Initializes important ec2 information
        self._setup_instance()

    def _setup_instance(self):
        """
        Initializes ec2 information
        """
        try:
            self._turn_on_instance()
            self._check_public_hostname()
        except (SystemExit, KeyboardInterrupt):
            self.aws_handler_cleanup()
            raise LazyWifiException

    def _turn_on_instance(self):
        """
        Starts the EC2 instance and waits for boot
        """
        print_status("Interacting with EC2 machine...")
        while self._MAX_ATTEMPTS != 0:
            try:
                self.instance.start()
                self.instance.wait_until_running()
                break
            except (ClientError, EndpointConnectionError):
                sleep(5)
                self._MAX_ATTEMPTS -= 1
        # Turn on availability flag for remote instance
        self.context.remote_machine_available = True
        print_status("EC2 Machine has been started")
        self.context.main_logger.info(f"EC2 instance {self.context.instance_id} has been started")

    def turn_off_instance(self):
        """
        Stops the EC2 instance if specified in the config file
        """
        if self.context.shut_down_on_finish:
            print_status("EC2 Machine has been shut down")
            self.context.main_logger.info(f"EC2 instance {self.context.instance_id} has been shut down")
            self.instance.stop()

    def _check_public_hostname(self):
        """
        Iterates through the current ec2 account and searches for the public dns name by instance ID specified,
        when done initializes the context public dns variable
        """
        response = self.ec2_client.describe_instances()
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                if instance["InstanceId"] == self.context.instance_id:
                    self.ec2_public_hostname = instance["PublicDnsName"]
        if not self.ec2_public_hostname:
            print_error("Unable to obtain public dns hostname for ec2 machine, disabling feature")
            self.context.main_logger.info("Unable to obtain public dns hostname for ec2 machine, disabling feature")
            self.aws_handler_cleanup()
            return
        self.context.ec2_public_hostname = self.ec2_public_hostname
        self.context.main_logger.info(f"Acquired public dns for ec2 machine: {self.ec2_public_hostname}")

    def aws_handler_cleanup(self):
        self.context.remote_machine_available = False
        if self.context.shut_down_on_finish:
            self.turn_off_instance()
