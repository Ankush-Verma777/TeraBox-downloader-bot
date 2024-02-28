import os
import subprocess

# Save current working directory to a variable named "currentDir"
currentDir = os.getcwd()

def imWhereNow():
    return currentDir  # Return the current directory path

# Change directory to /data/data/com.termux/files/home
os.chdir("/data/data/com.termux/files/home")

# Call imWhereNow() function to get the current directory path
current_directory = imWhereNow()

# Define the command to run
commands = [
    f"telegram-bot-api --local --api-hash   #PASTE YOUR TELEGRAM BOT API-HASH   --api-id   #PASTE YOUR TELEGRAM API-ID",
    f"cd {current_directory} && python RUN_WEBHOOK.py && python txbot.py",  # Change directory before running the command

]

processes = []

# Start each command in a separate subprocess
for command in commands:
    process = subprocess.Popen(command, shell=True)
    processes.append(process)

# Wait for all processes to finish
for process in processes:
    process.wait()
