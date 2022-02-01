from slack_sdk import WebClient
import json 
import importlib.resources as pkg_resources


DEFAULT_CHANNEL = "#bot_notifications"

class SlackBot(channel = DEFAULT_CHANNEL, token = None):
    if(token is None):
        from .. import secrets as s
        with pkg_resources.path(s, "slackbot_token_secret.json") as token_path:
            with open(token_path) as json_token_file:
                token_dict = json.load(json_token_file)
                token = token_dict['slackbot_token_string']
    self.client = WebClient(token = token)
    self.channel = channel



def post_message(message):
    try:
        response = self.client.post_message(channel = self.channel, text = message)
    except SlackApiError as e:
        raise e

def upload_file(file_path, file_name = "Slackbot_File"):
    try:
        response = self.client.files_upload(channel = self.channel, file = file_path, title = file_name)
    except SlackApiError as e:
        raise e

