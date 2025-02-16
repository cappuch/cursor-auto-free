from dotenv import load_dotenv
import os
import sys
from logger import logging


class Config:
    def __init__(self):
        # Get the root directory path of the application
        if getattr(sys, "frozen", False):
            # If it is a packaged executable file
            application_path = os.path.dirname(sys.executable)
        else:
            # If it is a development environment
            application_path = os.path.dirname(os.path.abspath(__file__))

        # Specify the path to the .env file
        dotenv_path = os.path.join(application_path, ".env")

        if not os.path.exists(dotenv_path):
            raise FileNotFoundError(f"File {dotenv_path} does not exist")

        # Load the .env file
        load_dotenv(dotenv_path)

        self.imap = False
        self.temp_mail = os.getenv("TEMP_MAIL", "").strip().split("@")[0]
        self.temp_mail_epin = os.getenv("TEMP_MAIL_EPIN", "").strip()
        self.temp_mail_ext = os.getenv("TEMP_MAIL_EXT", "").strip()
        self.domain = os.getenv("DOMAIN", "").strip()

        # If the temporary email is null, load IMAP
        if self.temp_mail == "null":
            self.imap = True
            self.imap_server = os.getenv("IMAP_SERVER", "").strip()
            self.imap_port = os.getenv("IMAP_PORT", "").strip()
            self.imap_user = os.getenv("IMAP_USER", "").strip()
            self.imap_pass = os.getenv("IMAP_PASS", "").strip()
            self.imap_dir = os.getenv("IMAP_DIR", "inbox").strip()

        self.check_config()

    def get_temp_mail(self):

        return self.temp_mail

    def get_temp_mail_epin(self):

        return self.temp_mail_epin

    def get_temp_mail_ext(self):

        return self.temp_mail_ext

    def get_imap(self):
        if not self.imap:
            return False
        return {
            "imap_server": self.imap_server,
            "imap_port": self.imap_port,
            "imap_user": self.imap_user,
            "imap_pass": self.imap_pass,
            "imap_dir": self.imap_dir,
        }

    def get_domain(self):
        return self.domain

    def check_config(self):
        """Check if the configuration items are valid

        Check rules:
        1. If using tempmail.plus, TEMP_MAIL and DOMAIN need to be configured
        2. If using IMAP, IMAP_SERVER, IMAP_PORT, IMAP_USER, IMAP_PASS need to be configured
        3. IMAP_DIR is optional
        """
        # Basic configuration check
        required_configs = {
            "domain": "Domain",
        }

        # Check basic configuration
        for key, name in required_configs.items():
            if not self.check_is_valid(getattr(self, key)):
                raise ValueError(f"{name} is not configured, please set {key.upper()} in the .env file")

        # Check email configuration
        if self.temp_mail != "null":
            # tempmail.plus mode
            if not self.check_is_valid(self.temp_mail):
                raise ValueError("Temporary email is not configured, please set TEMP_MAIL in the .env file")
        else:
            # IMAP mode
            imap_configs = {
                "imap_server": "IMAP server",
                "imap_port": "IMAP port",
                "imap_user": "IMAP username",
                "imap_pass": "IMAP password",
            }

            for key, name in imap_configs.items():
                value = getattr(self, key)
                if value == "null" or not self.check_is_valid(value):
                    raise ValueError(
                        f"{name} is not configured, please set {key.upper()}"
                    )

            # IMAP_DIR is optional, if set, check its validity
            if self.imap_dir != "null" and not self.check_is_valid(self.imap_dir):
                raise ValueError(
                    "IMAP inbox directory configuration is invalid, please set IMAP_DIR correctly in the .env file"
                )

    def check_is_valid(self, value):
        """Check if the configuration item is valid

        Args:
            value: The value of the configuration item

        Returns:
            bool: Whether the configuration item is valid
        """
        return isinstance(value, str) and len(str(value).strip()) > 0

    def print_config(self):
        if self.imap:
            logging.info(f"\033[32mIMAP server: {self.imap_server}\033[0m")
            logging.info(f"\033[32mIMAP port: {self.imap_port}\033[0m")
            logging.info(f"\033[32mIMAP username: {self.imap_user}\033[0m")
            logging.info(f"\033[32mIMAP password: {'*' * len(self.imap_pass)}\033[0m")
            logging.info(f"\033[32mIMAP inbox directory: {self.imap_dir}\033[0m")
        if self.temp_mail != "null":
            logging.info(
                f"\033[32mTemporary email: {self.temp_mail}{self.temp_mail_ext}\033[0m"
            )
        logging.info(f"\033[32mDomain: {self.domain}\033[0m")


# Example usage
if __name__ == "__main__":
    try:
        config = Config()
        print("Environment variables loaded successfully!")
        config.print_config()
    except ValueError as e:
        print(f"Error: {e}")
