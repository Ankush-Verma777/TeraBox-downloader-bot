import string
import subprocess 







# ngrokkalink


url = "http://localhost:8081/botPASTE YOUR TELEGRAM-BOT-TOKEN/setWebhook?url=http://localhost:5000/api/telegram"




    
# Construct the termux-open command.
command = f'termux-open-url {url}'


try:
    # Execute the termux-open command.
    subprocess.run(command, shell=True, check=True)
except subprocess.CalledProcessError as e:
    print(f"Error executing termux-open: {e}")        