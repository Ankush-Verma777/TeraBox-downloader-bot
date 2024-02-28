import logging
from urllib.parse import parse_qs, urlparse
import requests
import time
from tqdm import tqdm
import random
from pathlib import Path
import time
import os
import random
import string
import argparse
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from telegram_handler import TelegramBot
from sqlite_custom import SQLiteCustomDatabase
from custom_config import TRANSFERLOGFILE, BOTTOKEN, DBFILE, DOWNLOADSDIRECTORY, COOKIE_DICT

logging.basicConfig(level=logging.DEBUG,format = '%(asctime)s - %(levelname)s -%(message)s',
                    filename=TRANSFERLOGFILE)

class TransfersHandler:
    def __init__(self,database,bot):
        self.database = database
        self.bot = bot
    
    def make_get_request(self,endpoint, params=None, headers=None, cookies=None):
        try:
            session = requests.Session()
            if cookies:
                session.cookies.update(cookies)
            response = session.get(endpoint, params=params, headers=headers)
            response.raise_for_status()  # Raise HTTPError for bad responses
            return response
        except requests.exceptions.RequestException as e:
            logging.error(f"GET Request Error: {e}")
            return None

    def make_post_request(self,endpoint, data=None, headers=None):
        try:
            response = requests.post(endpoint, json=data, headers=headers)
            response.raise_for_status()  # Raise HTTPError for bad responses
            return response
        except requests.exceptions.RequestException as e:
            logging.error(f"POST Request Error: {e}")
            return None
    def find_between(self,s, start, end):
        try:
            start_index = s.find(start) + len(start)
            end_index = s.find(end, start_index)
            return s[start_index:end_index]
        except Exception as e:
            logging.error(f"Error Occured in Js Token - {e}")
            return None
    def getInfoData(self,link):
        try:
            custom_headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6",
                "Connection": "keep-alive",            
                "DNT": "1",
                "Host": "www.1024tera.com",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
                "sec-ch-ua": '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            }
            cookie_dict = COOKIE_DICT
            
            response_js_logid = self.make_get_request(link,headers=custom_headers,cookies=cookie_dict)
            if response_js_logid:
                data_js_logid = response_js_logid.content.decode('utf-8')            
                js_token = self.find_between(data_js_logid, "fn%28%22", "%22%29")
                response_url = response_js_logid.url
                if js_token:
                    logid = self.find_between(data_js_logid, "dp-logid=", "&")
                    if logid:
                        parsed_url = urlparse(response_url)
                        surl = parse_qs(parsed_url.query).get('surl', [''])[0]
                        params = {
                            'app_id': '250528',
                            'web': '1',
                            'channel': 'dubox',
                            'clienttype': '0',
                            'jsToken': js_token,
                            'dplogid': logid,
                            'page': '1',
                            'num': '20',
                            'order': 'time',
                            'desc': '1',
                            'site_referer': response_url,
                            'shorturl': surl,
                            'root': '1'
                        }
                        
                        share_url = 'https://www.1024tera.com/share/list'
                        response = self.make_get_request(share_url,headers=custom_headers,params=params,cookies=cookie_dict)
                        if response:
                            dataJ = response.json() 
                            data = dataJ['list'][0]                                 
                            if "isdir" in data.keys():
                                if str(data["isdir"]) != '0':
                                    return None
                            
                            if "server_filename" in data.keys() and "dlink" in data.keys() and "size" in data.keys():
                                filesize = float(data["size"])/1024/1024
                                filename = data["server_filename"]
                                filelink = data["dlink"]
                                if filelink and len(filename) > 0:
                                    return {"link" : filelink, "name" : filename, "size" : filesize}
        except Exception as e:
            print(e)
            logging.error(f"Error Occured in InfoData - {e}")
        return None
    
    def create_progress_bar(self,type,pbar, file_size, start_time, length=50): 
        speed_formatted=""
        time_formatted=""
        size_formatted=0
        total_size=file_size

        fraction = pbar.n / file_size 
        filled_length = int(length * fraction) 
        bar = f"[{'|' * filled_length}{' ' * (length - filled_length)}]"

        progress_percentage = (pbar.n / file_size) * 100 
        elapsed_time = time.time() - start_time 
        remaining_size = file_size - pbar.n 
        download_speed = pbar.n / elapsed_time if elapsed_time > 0  else pbar.n
        remaining_time = (remaining_size / download_speed) if download_speed > 0 else 0
        def size_speed_formatter(size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024

        if remaining_time < 60:
            time_formatted =  f"{remaining_time:.2f} seconds"
        elif remaining_time < 3600:
            time_formatted =  f"{remaining_time/60:.2f} minutes"
        else:
            time_formatted =  f"{remaining_time/3600:.2f} hours"
        
        size_formatted = size_speed_formatter(remaining_size)
        total_size = size_speed_formatter(file_size)
        speed_formatted = size_speed_formatter(download_speed)+"/s"   

        
        bar_with_details = ( f"File Size: {total_size}\n"
                    f"{bar}\n" 
                    f"{type} progress: {progress_percentage:.2f}%\n" 
                    f"{type} speed: {speed_formatted}\n" 
                    f"Remaining size: {size_formatted}\n"
                    f"Remaining time: {time_formatted}")
        return bar_with_details

    def get_random_user_agent(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
            "Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36"
        ]
        return random.choice(user_agents)        
        
        
    def download_file(self, url, download_path, filename,og_f_name):   
        user_agent = self.get_random_user_agent()
        headers_info = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': user_agent,
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        cookie_dict = COOKIE_DICT
        

        try:
            # session = requests.Session()
            # session.cookies.update(cookie_dict)
            response = requests.get(url,stream=True,headers=headers_info, cookies=cookie_dict,allow_redirects=True)
            response.raise_for_status()  # Raise an exception if the response status is not 200
            
            file_size = int(response.headers.get('content-length', 0))
            downloaded_file_path = os.path.join(download_path, filename)
            self.bot.delete_message(self.chat_id,self.main_message_id)
            download_notif_message=self.bot.send_message(self.chat_id,"Attempting to download file..",reply_to_message_id=self.sub_message_id)
            self.main_message_id = download_notif_message["result"]["message_id"]        
            start_time = time.time()
            track_time = time.time()
            with open(downloaded_file_path, 'wb') as f, tqdm(
                desc=og_f_name,
                total=file_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                miniters=1,
                disable=False
            ) as pbar:
                i = 0
                for chunk in response.iter_content(chunk_size= 3 * 1024 * 1024):               
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
                        progress_bar = self.create_progress_bar("Download",pbar,file_size,start_time)                    
                        if(i == 0):
                            self.bot.edit_message(self.chat_id,self.main_message_id,str(progress_bar))
                        if(i > 0 and ((time.time() - track_time) >= 5)):
                            self.bot.edit_message(self.chat_id,self.main_message_id,str(progress_bar))                     
                            track_time = track_time + 5
                    i = i + 1  
                                                             
            
            logging.info("Downloaded file: %s", downloaded_file_path)
            self.bot.delete_message(self.chat_id,self.main_message_id)
            download_complete_notif_message=self.bot.send_message(self.chat_id,"Downloaded Completed..",reply_to_message_id=self.sub_message_id)
            self.main_message_id = download_complete_notif_message["result"]["message_id"]
            return downloaded_file_path
        except requests.exceptions.RequestException as e:
            logging.error("Failed to download file: %s", str(e))
            return None
        
    def upload_to_telgram_file_progress(self,bar,file_size,start_time):
        progress_bar = self.create_progress_bar("Upload",bar,file_size,start_time)
        if not hasattr(self,"track_time"):
            self.bot.edit_message(self.chat_id,self.main_message_id,progress_bar)
            self.track_time = time.time()
    
        if time.time() - self.track_time >= 5:
            self.bot.edit_message(self.chat_id,self.main_message_id,progress_bar)
            self.track_time = self.track_time + 5

    def upload_to_telgram_file_stream(self, media_type, media_path,caption=None):
        try:
            self.xz = 0
            url = f"{self.bot.base_url}/send{media_type}"
            data = {
                'chat_id': str(self.chat_id),
                'caption': caption,
                "reply_to_message_id": str(self.sub_message_id)
            }
            path = Path(media_path)
            total_size = path.stat().st_size
            filename = path.name

            start_time = time.time()
            with tqdm(
                desc=filename,
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                with open(media_path, "rb") as f:
                    data[media_type.lower()] = (filename, f)
                    e = MultipartEncoder(fields=data)
                    m = MultipartEncoderMonitor(
                        e, 
                        lambda monitor: bar.update(monitor.bytes_read - bar.n) or self.upload_to_telgram_file_progress(bar,total_size,start_time) 
                    )
                    
                    headers = {"Content-Type": m.content_type}
                    response = requests.post(url, data=m, headers=headers)                    
            
            logging.info("File uploaded via requests.")           
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending media: {e}")
            return None

    def upload_to_telegram(self,file_path,file_name):
        try:
            self.bot.delete_message(self.chat_id,self.main_message_id)
            update_notif_message=self.bot.send_message(self.chat_id,"Uploading file...",reply_to_message_id=self.sub_message_id)
            self.main_message_id=update_notif_message["result"]["message_id"] 
            media_type = "Document"
            
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                media_type = "Photo"
            elif file_name.lower().endswith(('.mp4', '.avi', '.mkv')):
                media_type = "Video"
            
            response = self.upload_to_telgram_file_stream(media_type,file_path,caption=file_name)
            if(response):
                if str(response["ok"]) == "True":
                    return "ok"
            return None
                        
        except Exception as e:
            logging.error("Failed to upload file to Telegram: %s", str(e))
        return None
    

    def process_transfers(self,link):
        response = {}
        try:   
            infoData = self.getInfoData(link)
            if infoData:
                directory = DOWNLOADSDIRECTORY
                filename = infoData["name"]
                downloadlink = infoData["link"]
                filesize = infoData["size"]
                if filesize <= 2000:
                    letters = string.ascii_letters
                    random_string = ''.join(random.choice(letters) for _ in range(20))
                    d_file_path = random_string+os.path.splitext(filename)[-1]
                    file_download = self.download_file(downloadlink,directory,d_file_path,filename)
                    if file_download:
                        new_file_path = directory+"/"+d_file_path                        
                        # os.replace(file_download,new_file_path)
                        uploader = self.upload_to_telegram(new_file_path,filename)
                        if(uploader == "ok"):
                            if(os.path.exists(new_file_path)):
                                os.remove(new_file_path)
                            response["status"] = "success"
                            response["msg"] = filename
                            response["link"] = link
                            response['downloadlink'] = downloadlink
                            return response
                        else:
                            response["status"] = "error"
                            response["msg"] = "Failed to upload File.."
                    else:
                        response["status"] = "error"
                        response["msg"] = "Failed to get the file.. Try again later..."
                else:
                    response["status"] = "error"
                    response["msg"] = "Cant Download!..File size is greater than 2GB.."
            else:
                response["status"] = "error"
                response["msg"] = "Failed to get Download Link.. Try again later..."
                
        except Exception as e:
            response["status"] = "error"
            response["msg"] = "Error Occured While Processing..."
            logging.error("Error occured in handle transfers: %s", str(e))
            print(e)
        return response
        
    def handle_transfers(self,update_id,chat_id,main_message_id, sub_message_id,link):
        try:
            self.update_id = update_id
            self.main_message_id = main_message_id
            self.sub_message_id = sub_message_id
            self.chat_id = chat_id
            process = self.process_transfers(link)
            if process["status"] == "success":
                # self.save_updates("update",self.update_id,self.chat_id,self.main_message_id,self.sub_message_id,process["link"],process["downloadlink"],1)
                self.bot.delete_message(self.chat_id,self.main_message_id)
            elif process['status'] == 'error':
                # self.save_updates("update",self.update_id,self.chat_id,self.main_message_id,self.sub_message_id,"null","null",4)
                self.bot.delete_message(self.chat_id,self.main_message_id)                
                self.bot.send_message(self.chat_id,process["msg"],self.sub_message_id)
            else:
                logging.info("Skipping..")
        except Exception as e:
            logging.error("Error occured in handle transfers: %s", str(e))
            print(e)
        return process
    
    # def save_updates(self, type, update_id, chat_id=0, main_message_id=0, sub_message_id=0, message_link="null", download_link="null", status="0"):
    #     try:
    #         query = ""
    #         params = ""
    #         if type == "insert":
    #             query = '''
    #                 INSERT INTO tasks (update_id, chat_id, main_message_id, sub_message_id, message_link, download_link, status)
    #                 VALUES (?, ?, ?, ?, ?, ?, ?)
    #             '''
    #             params = (update_id, chat_id, main_message_id, sub_message_id, message_link, download_link, status,)
    #         elif type == "update":
    #             query = "UPDATE tasks set chat_id = ?, main_message_id = ?,  sub_message_id = ?, message_link = ?, download_link = ?, status = ? WHERE update_id = ?"
    #             params = (chat_id, main_message_id,sub_message_id,message_link,download_link,status,update_id)
    #         else:
    #             return None
    #         status = self.database.execute_query(query, params)
    #         if status != None:
    #             return status
    #     except Exception as e:
    #         logging.error(f"Error Occured in Save Updates - {e}")                
    #     return None
    
    # def verify_updates(self):
    #     try:
    #         query = "SELECT * FROM tasks WHERE update_id = ? AND status = 2 ORDER BY id ASC"
    #         params = (self.update_id,)
    #         result = self.database.execute_query(query,params)
    #         if result:
    #             if len(result) > 0:
    #                 if "update_id" in result[0].keys():
    #                     if result[0]['update_id'] == self.update_id:
    #                         return result
    #     except Exception as e:
    #         logging.error(f"Error occured at verify_updates - {e}")
    #     return None
    

    

database =SQLiteCustomDatabase(DBFILE)

try:
    parser = argparse.ArgumentParser(description="Transfers Handler")
    parser.add_argument('-u_id', help="Update Id")
    parser.add_argument('-c_id', help="Chat Id")
    parser.add_argument('-m_id', help="Main Message Id")
    parser.add_argument('-s_id', help="Sub Message Id")
    parser.add_argument('-link', help="Link")

    args = parser.parse_args()

    update_id = args.u_id
    chat_id = args.c_id
    main_message_id = args.m_id
    sub_message_id = args.s_id
    link = args.link

    logging.info(f"updates - {update_id, chat_id, main_message_id, sub_message_id, link}")

    handler = TransfersHandler(database,TelegramBot(BOTTOKEN))
    handler.handle_transfers(update_id,chat_id,main_message_id,sub_message_id,link)
except Exception as e:
    logging.error(f"Error occured in transfers handler - {e}")
    print(e)


