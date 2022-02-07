from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import os
import json 
import importlib.resources as pkg_resources


DEFAULT_CHANNEL = "#bot_notifications"

class SlackBot():

    """Initialization method

    Parameters:

        channel: The channel to which the bot should post. By default, goes to #bot_notifications

        token: The bot token to use to authenticate. If none is provided, it takes it from a JSON config file.

    Notes: The method also imports a JSON file listing members of BEC1 whom it would be relevant to mention, allowing 
    them to be mentioned in the post_message method.
    """

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


    """Method for posting messages.

    Given a message, posts it to the channel configured in the __init__ file. Optionally, mentions various members of the channel (e.g. @Eric Wolf).

    Parameters:
        message (str): The message to be sent
        mention: A list of string keys indicating which users should be mentioned. Syntax is 'Firstname_Lastname', and they must match an entry in
            the slack member ids JSON file.
        mention_all (bool): If true, mentions all members listed in the member ids file.
    """


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

    """Uploads a file.

    Given a file, uploads it to slack and posts it in the channel configured for the bot.

    Parameters:
        file_path: The path to the file to be uploaded. Relative and absolute seem to work.

        file_name: The name of the file after it is uploaded to Slack. If None, the name of the file on the host system is copied.
    """

    def upload_file(self, file_path, file_name = None):
        if(file_name is None):
            file_name = os.path.basename(file_path)
        try:
            response = self.client.files_upload(channels = self.channel, file = file_path, title = file_name)
        except SlackApiError as e:
            raise e

