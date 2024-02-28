import requests
import logging
import re
from flask import Flask, request
import subprocess
from sqlite_custom import SQLiteCustomDatabase
from telegram_handler import TelegramBot
from custom_config import LOGFILE, BOTTOKEN, DBFILE
from flask_ngrok import run_with_ngrok


logging.basicConfig(level=logging.DEBUG,format = '%(asctime)s - %(levelname)s -%(message)s',
                    filename=LOGFILE)

class ApiBotRequestsHandler:
    def __init__(self,bot_token,database):
        self.bot = TelegramBot(bot_token)
        self.database = database
    

    def extract_and_format_links(self,text):
        try:
            url_pattern = r'(https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,6})(/[^\s]*)?'
            matches = re.finditer(url_pattern, text)

            formatted_urls = []

            for match in matches:
                scheme = match.group(1) or "http://"
                domain = match.group(2)
                path = match.group(3) or "/"
                formatted_url = f"{scheme}{domain}{path}"
                formatted_urls.append(formatted_url)

            if formatted_urls:
                return formatted_urls
            else:
                return None

        except Exception as e:
            print("An error occurred:", e)
            logging.error(f"Error Occured in Format Links - {e}")
            return None
    
            
    def processLink(self,message,chat_id):
        response = {}
        try:
            links = self.extract_and_format_links(message)
            if links:
                domains = ["teraboxapp.com", "4funbox.com", 
                            "1024tera.com", "terabox.com","terabox.app","1024terabox.com"]
                domain_pattern = r'https?://([a-zA-Z0-9.-]+\.[a-zA-Z]{2,6})'
                match = re.search(domain_pattern, links[0])        
                if match:
                    domain = match.group(1)
                    if domain in domains:
                        response["status"] = "success"
                        response['link'] = links[0]                        
                    else:
                        response["status"] = "error"
                        response["msg"] = "Cant download from this site"
                else:
                    response["status"] = "error"
                    response["msg"] = "No domains found in message!"
            else:
                response["status"] = "error"
                response["msg"] = "No links found in message!"
        except Exception as e:
            print(e)
            logging.error(f"Error Occured in ProcessLink - {e}")
            response["status"] = "error"
            response["msg"] = "Error Occured try later!"
        return response   

    def save_updates(self, type, update_id, chat_id=0, main_message_id=0, sub_message_id=0, message_link="null", download_link="null", status="0"):
        try:
            query = ""
            params = ""
            if type == "insert":
                query = '''
                    INSERT INTO tasks (update_id, chat_id, main_message_id, sub_message_id, message_link, download_link, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                '''
                params = (update_id, chat_id, main_message_id, sub_message_id, message_link, download_link, status,)
            elif type == "update":
                query = "UPDATE tasks set chat_id = ?, main_message_id = ?,  sub_message_id = ?, message_link = ?, download_link = ?, status = ? WHERE update_id = ?"
                params = (chat_id, main_message_id,sub_message_id,message_link,download_link,status,update_id)
            else:
                return None
            status = self.database.execute_query(query, params)
            if status != None:
                return status
        except Exception as e:
            logging.error(f"Error Occured in Save Updates - {e}")                
        return None
    

    def check_updates(self, update_id):
        try:
            query = "SELECT EXISTS(SELECT update_id FROM tasks WHERE update_id = ? LIMIT 1)"
            params = (update_id,)
            result = self.database.execute_query(query, params)
            if result:
                if result[0][0] == 1:
                    return "match"
        except Exception as e:
            logging.error(f"Error occured at check upates - {e}")
        return None
            
    
    def handleInput(self,data):
        input_data = data
        if (input_data and "message" in input_data and ("text" in input_data["message"] or "caption" in input_data["message"])):         
            update_id = input_data["update_id"]
            if self.check_updates(update_id) == None: 
                if self.save_updates("insert",update_id) != None:
                    message_text = ""
                    if "text" in input_data["message"].keys():
                        message_text = input_data["message"]["text"] 
                    elif "caption" in input_data["message"].keys():
                        message_text = input_data["message"]["caption"]
                    
                    message_id = input_data["message"]["message_id"]
                    chat_id = input_data["message"]["chat"]["id"] 

                    if message_text == "/start":
                        self.bot.send_message(chat_id,"Hi!\nSend me any Terabox Link, I will download and send it to you!\n\nNB:- No directories and only one link per message..\n\nENJOY..")
                        return
                    self.sub_message_id = message_id
                    main_message = self.bot.send_message(chat_id,"Processing...",message_id)
                    self.main_message_id = main_message["result"]["message_id"]
                    response = self.processLink(message_text,chat_id)
                    print(response)
                    if(response["status"] == "success"):
                        self.save_updates("update",update_id,chat_id,self.main_message_id,self.sub_message_id,response["link"],"null",2)
                        self.bot.edit_message(chat_id,self.main_message_id,"Your request has been added to Queue")
                        download_command = ["python", "transfers_handler.py",
                                            "-u_id", str(update_id), "-c_id", str(chat_id), "-m_id", str(self.main_message_id),
                                            "-s_id",str(self.sub_message_id), "-link", str(response["link"])]
                        
                        subprocess.Popen(download_command)
                    else:                    
                        self.bot.edit_message(chat_id,self.main_message_id,response["msg"])
                else:
                    print("Save updates..")
            else:
                print("Check Update..")
                                    
        return None




database =SQLiteCustomDatabase(DBFILE)    
app = Flask("txbox")

@app.route('/api/telegram', methods=['POST'])
def telegram_webhook():
    try:
        data = request.json 
        print(data)
        handler = ApiBotRequestsHandler(BOTTOKEN,database)
        handler.handleInput(data)        
        response_data = {'status': 'success', 'message': 'Data received successfully'}
        return response_data
    except Exception as e:
        error_message = str(e)
        logging.error(f"Error Occured in telegram_webhook - {e}")
        response_data = {'status': 'error', 'message': error_message}
        return response_data
        


if __name__ == "__main__":
  

  app.run(debug=True,port=5000,threaded = True )

