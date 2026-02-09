import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import mysql.connector
import requests
import re
from dotenv import load_dotenv


load_dotenv()
# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

db = mysql.connector.connect(
    host="40.233.121.197",
    user="seven",
    password=os.environ.get('DB_PASSWORD'),
    port=2469
)
cursor = db.cursor()

def log_error(error):
    app.client.chat_postMessage(
        markdown_text="An error occurred! `"+error+"`",
        channel="C0ACZLB1K5L"
    )
def send_message(message,channel):
    app.client.chat_postMessage(
        markdown_text=str(message),
        channel=str(channel)
    )

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

@app.command("/register-account")
def register_player(ack,respond,command):
    try:
        auth_disabled = bool(os.environ.get("AUTH_ENABLED"))

        ack()
        print("Register command triggered")

        username = command['text']

        if auth_disabled:
            print("Authorization to the server is currently disabled, not authorizing")
            respond("Allowlisting your account to the server is currently disabled. Please try again later, or wait for an update from the admins")
            return

        if re.findall(r"[^a-zA-Z_]", username) or len(username) > 16:
            print("Failed to register: username was invalid")
            respond("That is not a valid Minecraft username! Please try again, or if you believe this was a mistake, contact an admin,")
            return
        slack_id = command['user_id']

        cursor.execute("USE `hc-mc-auth`")

        #ai wrote the sql statement for checking if a user already exists, fight me im lazy
        cursor.execute("SELECT 1 FROM authorized_users WHERE slack_id = %s LIMIT 1", (slack_id,))
        if cursor.fetchone():
            print("Failed to register: user already has an account registered")
            respond("Error: You have already registered a minecraft account to your slack account. If you believe this is a mistake, or would like to change it, please contact an admin")
        else:
            server_running = check_server_status()
            if server_running:
                register_mc_account(username)

                sql = "INSERT INTO `authorized_users` (`slack_id`,`minecraft_username`,`registered`) VALUES (%s,%s,NOW())"
                cursor.execute(sql,(slack_id,username))

                db.commit()

                respond("Your account has been successfully registered! Join the server at `create-mc.hackclub.community`")
                print("Account successfully registered")
            else:
                print("Failed to register: server not running")
                respond("The server is not running, or something else went wrong. Check the server status, or contact an admin!")
    except Exception as e:
        log_error(str(e))
        print("An error occurred: "+str(e))
        respond("Something went very wrong! Please contact an admin, even if you can join the server! Give them the time that you ran this command.")

@app.command("/suggest-mod")
def forward_suggestion(ack, respond, command):
    try:
        ack()
        send_message(
            "A mod suggestion was made by "+str(command['user_id'])+"! The mod is called `" + str(command['text']) + "`",
            "C0ACZLB1K5L"
        )
        respond("Your suggestion has been acknowledged, please be patient and do not spam the command. If we like the suggestion, we will add it.")
        print("Suggestion logged")

    except Exception as e:
        log_error(str(e))
        print(str(e))
        respond("Something went very wrong! Please contact an admin and give them the time that you ran this command.")

if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
