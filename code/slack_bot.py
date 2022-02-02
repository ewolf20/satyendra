from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import json 
import importlib.resources as pkg_resources


DEFAULT_CHANNEL = "#bot_notifications"

class SlackBot():

    def __init__(self, channel = DEFAULT_CHANNEL, token = None):
        if(token is None):
            from .. import secrets as s
            with pkg_resources.path(s, "slackbot_token_secret.json") as token_path, pkg_resources.path(s, "slack_member_ids_secret.json") as ids_path:
                with open(token_path) as json_token_file:
                    token_dict = json.load(json_token_file)
                    token = token_dict['slackbot_token_string']
                with open(ids_path) as json_ids_file:
                    ids_dict = json.load(json_ids_file) 

        self.client = WebClient(token = token)
        self.channel = channel
        self.ids_dict = ids_dict



    def post_message(self, message, mention = [], mention_all = False):
        try:
            if(mention_all):
                for key in self.ids_dict:
                    mention_id = self.ids_dict[key] 
                    message = "<@" + mention_id + "> " + message
            else:
                for name in mention:
                    mention_id = self.ids_dict[name] 
                    message = "<@" + mention_id + "> " + message
            response = self.client.chat_postMessage(channel = self.channel, text = message)
        except SlackApiError as e:
            raise e

    def upload_file(self, file_path, file_name = "Slackbot_File"):
        try:
            response = self.client.files_upload(channels = self.channel, file = file_path, title = file_name)
        except SlackApiError as e:
            raise e

