import subprocess
import os
import string

now_Position = os.getcwd()

# Define the commands to run
commands = [
    "pip install -r need.txt",
   "cd  /data/data/com.termux/files/home",
    "pkg install telegram-bot-api",
     
    "telegram-bot-api --local --api-hash YourTelegramBotApiHash --api-id YourTelegramBot-Api-Id",
    f"cd {now_Position}",
    "python RUN_WEBHOOK.py",
    "python txbot.py",
]

# Create a list to hold the subprocess objects
processes = []

# Start each command in a separate subprocess
for command in commands:
    process = subprocess.Popen(command, shell=True)
    processes.append(process)

# Wait for all processes to finish
for process in processes:
    process.wait()
