import os

from flask import Flask, request
import mysql.connector
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

db = mysql.connector.connect(
    host="40.233.121.197",
    user="seven",
    password=os.environ['DB_PASSWORD'],
    port=2469
)
cursor = db.cursor()

#sends the command to pterodactyl to add a player to the allowlist
def register_mc_account(account_name):
    url = "https://oracle.mrseven.tech/api/client/servers/48c5146d/command"

    headers = {
        "Content-Type": "application/json",
        "Authorization":"Bearer "+ os.environ['PTERO_API_KEY']
    }
    payload = {"command": "whitelist add "+account_name}

    response = requests.post(url, json=payload, headers=headers)



#returns true if the server is currently running
def check_server_status():
    url = "https://oracle.mrseven.tech/api/client/servers/48c5146d/resources"

    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer "+ os.environ['PTERO_API_KEY']
    }
    response = requests.get(url, headers=headers)
    if response.json()['attributes']['current_state'] == "running":
        return True
    else:
        return False

@app.route('/api/register',methods = ['POST'])
def register_player():
    data = request.form

    slack_id = data.get("user_id")
    username = data.get("text")

    cursor.execute("USE hc-mc-auth")

    #ai wrote the sql statement for checking if a user already exists, fight me im lazy
    cursor.execute("SELECT 1 FROM authorized_users WHERE slack_user_id = %s LIMIT 1", (slack_id,))
    if cursor.fetchone():
        return "Error: You have already registered a minecraft account to your slack account. If you believe this is a mistake, or would like to change it, please contact an admin", 200
    else:
        server_running = check_server_status()
        if server_running:
            register_mc_account(username)

            sql = "INSERT INTO `authorized_users` (`slack_user_id`,`minecraft_username`) VALUES (%s,%s)"
            cursor.execute(sql,(slack_id,username))


            return "Your account has been successfully registered! Join the server at `create-mc.hackclub.community`",200
        else:
            return "The server is not running, or something else went wrong. Check the server status, or contact an admin!", 200


if __name__ == '__main__':
    app.run()
