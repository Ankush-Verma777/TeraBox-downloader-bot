import logging
import requests
from custom_config import TG_BASE_URL


class TelegramBot:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        # self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.base_url = TG_BASE_URL+bot_token


    def send_message(self, chat_id, text, reply_to_message_id=None):
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "reply_to_message_id": reply_to_message_id
            }
            response = requests.post(url, json=payload)
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending message request: {e}")
        except Exception as e:
            logging.error(f"Error sending message: {e}")
        return None
    def send_document(self, chat_id, media_type, media_path,caption=None):
        try:
            url = f"{self.base_url}/send{media_type}"
            data = {
                'chat_id': str(chat_id),
                'caption': caption,
                "reply_to_message_id": str(self.sub_message_id)
            }
            files = {media_type : open(media_path)}
            response = requests.post(url,files=files,data=data)
            return response.json()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending Document message Request: {e}")
        except Exception as e:
            logging.error(f"Error sending document: {e}")
        return None

    def delete_message(self, chat_id, message_id):
        try:
            url = f"{self.base_url}/deleteMessage"
            payload = {
                "chat_id": chat_id,
                "message_id":message_id
            }
            response = requests.post(url, json=payload)
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error deleting message request: {e}")
        except Exception as e:
            logging.error(f"Error deleting message: {e}")
        return None
    

    def edit_message(self, chat_id, message_id, text):
        try:
            url = f"{self.base_url}/editMessageText"
            
            payload = {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text
            }
            response = requests.post(url, json=payload)
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error editing message request: {e}")
        except Exception as e:
            logging.error(f"Error editing message: {e}")
        return None