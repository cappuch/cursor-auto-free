import logging
import time
import re
from config import Config
import requests
import email
import imaplib


class EmailVerificationHandler:
    def __init__(self):
        self.imap = Config().get_imap()
        self.username = Config().get_temp_mail()
        self.epin = Config().get_temp_mail_epin()
        self.session = requests.Session()
        self.emailExtension = Config().get_temp_mail_ext()

    def get_verification_code(self, max_retries=5, retry_interval=25):
        """
        Get verification code with retry mechanism.

        Args:
            max_retries: Maximum number of retries.
            retry_interval: Retry interval in seconds.

        Returns:
            Verification code (string or None).
        """

        for attempt in range(max_retries):
            try:
                logging.info(f"Attempting to get verification code (Attempt {attempt + 1}/{max_retries})...")

                if not self.imap:
                    verify_code, first_id = self._get_latest_mail_code()
                    if verify_code is not None and first_id is not None:
                        self._cleanup_mail(first_id)
                        return verify_code
                else:
                    verify_code = self._get_mail_code_by_imap()
                    if verify_code is not None:
                        return verify_code

                if attempt < max_retries - 1:  # Wait for all attempts except the last one
                    logging.warning(f"Verification code not received, retrying in {retry_interval} seconds...")
                    time.sleep(retry_interval)

            except Exception as e:
                logging.error(f"Failed to get verification code: {e}")  # Log more general exceptions
                if attempt < max_retries - 1:
                    logging.error(f"Error occurred, retrying in {retry_interval} seconds...")
                    time.sleep(retry_interval)
                else:
                    raise Exception(f"Failed to get verification code after maximum retries: {e}") from e

        raise Exception(f"Failed to get verification code after {max_retries} attempts.")

    # Get email using IMAP
    def _get_mail_code_by_imap(self, retry = 0):
        if retry > 0:
            time.sleep(3)
        if retry >= 20:
            raise Exception("Verification code retrieval timeout")
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap['imap_server'], self.imap['imap_port'])
            mail.login(self.imap['imap_user'], self.imap['imap_pass'])
            mail.select(self.imap['imap_dir'])

            status, messages = mail.search(None, 'FROM', '"no-reply@cursor.sh"')
            if status != 'OK':
                return None

            mail_ids = messages[0].split()
            if not mail_ids:
                # If no mail is retrieved, try again
                return self._get_mail_code_by_imap(retry=retry + 1)

            latest_mail_id = mail_ids[-1]

            # Get email content
            status, msg_data = mail.fetch(latest_mail_id, '(RFC822)')
            if status != 'OK':
                return None

            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)

            # Extract email body
            body = self._extract_imap_body(email_message)
            if body:
                # Use regex to find 6-digit verification code
                code_match = re.search(r"\b\d{6}\b", body)
                if code_match:
                    code = code_match.group()
                    # Delete email
                    mail.store(latest_mail_id, '+FLAGS', '\\Deleted')
                    mail.expunge()
                    mail.logout()
                    # print(f"Verification code found: {code}")
                    return code
            # print("Verification code not found")
            mail.logout()
            return None
        except Exception as e:
            print(f"Error occurred: {e}")
            return None

    def _extract_imap_body(self, email_message):
        # Extract email body
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        return body
                    except Exception as e:
                        logging.error(f"Failed to decode email body: {e}")
        else:
            content_type = email_message.get_content_type()
            if content_type == "text/plain":
                charset = email_message.get_content_charset() or 'utf-8'
                try:
                    body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
                    return body
                except Exception as e:
                    logging.error(f"Failed to decode email body: {e}")
        return ""

    # Manually input verification code
    def _get_latest_mail_code(self):
        # Get email list
        mail_list_url = f"https://tempmail.plus/api/mails?email={self.username}{self.emailExtension}&limit=20&epin={self.epin}"
        mail_list_response = self.session.get(mail_list_url)
        mail_list_data = mail_list_response.json()
        time.sleep(0.5)
        if not mail_list_data.get("result"):
            return None, None

        # Get the latest email ID
        first_id = mail_list_data.get("first_id")
        if not first_id:
            return None, None

        # Get specific email content
        mail_detail_url = f"https://tempmail.plus/api/mails/{first_id}?email={self.username}{self.emailExtension}&epin={self.epin}"
        mail_detail_response = self.session.get(mail_detail_url)
        mail_detail_data = mail_detail_response.json()
        time.sleep(0.5)
        if not mail_detail_data.get("result"):
            return None, None

        # Extract 6-digit verification code from email text
        mail_text = mail_detail_data.get("text", "")
        mail_subject = mail_detail_data.get("subject", "")
        logging.info(f"Email subject found: {mail_subject}")
        # Modify regex to ensure the 6-digit number is not immediately preceded by letters or domain-related symbols
        code_match = re.search(r"(?<![a-zA-Z@.])\b\d{6}\b", mail_text)

        if code_match:
            return code_match.group(), first_id
        return None, None

    def _cleanup_mail(self, first_id):
        # Construct delete request URL and data
        delete_url = "https://tempmail.plus/api/mails/"
        payload = {
            "email": f"{self.username}{self.emailExtension}",
            "first_id": first_id,
            "epin": f"{self.epin}",
        }

        # Try up to 5 times
        for _ in range(5):
            response = self.session.delete(delete_url, data=payload)
            try:
                result = response.json().get("result")
                if result is True:
                    return True
            except:
                pass

            # If failed, wait 0.5 seconds and retry
            time.sleep(0.5)

        return False


if __name__ == "__main__":
    email_handler = EmailVerificationHandler()
    code = email_handler.get_verification_code()
    print(code)
