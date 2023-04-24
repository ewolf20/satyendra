import copy
import os
import json 
import importlib.resources as pkg_resources
import time
import warnings

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackBot():

    """Initialization method

    Parameters:

        channel: The channel to which the bot should post. By default, goes to #bot_notifications

        token: The bot token to use to authenticate. If none is provided, it takes it from a JSON config file.

    Notes: The method also imports a JSON file listing members of BEC1 whom it would be relevant to mention, allowing 
    them to be mentioned in the post_message method.
    """

    def __init__(self, bot_name = None, bot_id = None, channel_name = None, channel_id = None, token = None, rate_limit_per_min = 50, 
                context_name = "unspecified location"):
        if(token is None):
            from .. import secrets as s
            with pkg_resources.path(s, "slackbot_token_secret.json") as token_path, pkg_resources.path(s, "slack_member_ids_secret.json") as ids_path:
                with open(token_path) as json_token_file:
                    token_dict = json.load(json_token_file)
                    token = token_dict['slackbot_token_string']
                with open(ids_path) as json_ids_file:
                    ids_dict = json.load(json_ids_file) 

        from .. import configs as c
        with pkg_resources.path(c, "slack_bot_config_local.json") as config_path:
            with open(config_path) as json_config_file:
                defaults_config_dict = json.load(json_config_file)
            

        self.client = WebClient(token = token)
        if channel_name is None:
            channel_name = defaults_config_dict["bot_channel_name"]
        if channel_id is None:
            channel_id = defaults_config_dict["bot_channel_id"]
        if bot_name is None:
            bot_name = defaults_config_dict["bot_name"] 
        if bot_id is None:
            bot_id = defaults_config_dict["bot_id"]

        self.channel_name = channel_name
        self.channel_id = channel_id
        self.bot_name = bot_name 
        self.bot_id = bot_id
        self.context_name = context_name
        self.ids_dict = ids_dict
        self.handled_message_ts_list = []
        self.last_query_time = time.time()
        self.rate_limit_per_min = rate_limit_per_min
        self.running_query_rate_per_min = 0.0


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
            if self._validate_rate_limit():
                response = self.client.chat_postMessage(channel = self.channel_name, text = message)
            else:
                warnings.warn("Rate limit: operation not performed.")
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
            if self._validate_rate_limit():
                response = self.client.files_upload(channels = self.channel_name, file = file_path, title = file_name)
            else:
                warnings.warn("Rate limit: operation not performed.")
        except SlackApiError as e:
            raise e

    def hello():
        pass


    """Gets recent mentions of the bot. 
        When called, return a list of recent messages (in order newest->oldest) sent with the intent of mentioning the bot. 

        Parameters:

        mention_string: The string which, when included in a message, signals that the bot is being addressed. Default is 
        @[bot_name]

        search_depth: The number of recent messages to search. Default is 100.
        
        Returns:
        
        A list of dicts representing individual messages, with all the metadata returned by slack."""



    def _get_recent_mentions(self, mention_string, search_depth):
        if not self._validate_rate_limit():
            warnings.warn("Rate limit; operation not performed.")
            return None
        PAGE_SIZE_LIMIT = 100
        results_queried = 0
        page_size = min(search_depth, PAGE_SIZE_LIMIT)
        current_cursor = None
        mention_message_list = []
        while results_queried < search_depth:
            response = self.client.conversations_history(channel = self.channel_id, limit = page_size, cursor = current_cursor)
            response_messages = response['messages']
            user_generated_messages = [m for m in response_messages if not self.bot_id == m['user']]
            user_generated_messages_with_mention = [m for m in user_generated_messages if mention_string in m['text']]
            mention_message_list.extend(user_generated_messages_with_mention)
            results_queried += page_size 
            current_cursor = response['response_metadata']['next_cursor']
        return mention_message_list 


    """When called, handle all mentions of the bot.
    
    When called, have the bot respond to all outstanding messages with a mention of its name in the """

    def handle_bot_mentions(self, request_string = None, request_function = None,
                            request_extra_args = None, mention_string = None, search_depth = 100):
        if mention_string is None:
            mention_string = "<@{0}>".format(self.bot_id)
        handler_string_list = copy.copy(SlackBot.DEFAULT_HANDLER_STRINGS)
        handler_func_list = copy.copy(SlackBot.DEFAULT_HANDLER_FUNCS)
        handler_extra_arg_list = copy.copy(SlackBot.DEFAULT_HANDLER_EXTRA_ARGS)
        if not request_string is None:
            handler_string_list.append(request_string)
            handler_func_list.append(request_function)
            if request_extra_args is None:
                request_extra_args = ()
            handler_extra_arg_list.append(request_extra_args)
        mentioned_messages = self._get_recent_mentions(mention_string, search_depth)
        for message in mentioned_messages:
            message_ts = message['ts']
            if message_ts in self.handled_message_ts_list:
                continue
            message_text = message['text'] 
            got_match = False
            for handler_string, handler_function, handler_extra_args in zip(handler_string_list,
                                                         handler_func_list, handler_extra_arg_list):
                if handler_string in message_text:
                    handler_function(self, message, *handler_extra_args)
                    got_match = True 
            if not got_match:
                SlackBot._no_match_handler(self, message)
            self.handled_message_ts_list.append(message_ts)


    def _lookup_user_name(self, user_id):
        NON_FOUND_USER_NAME = "Anon"
        for name in self.ids_dict:
            current_user_id = self.ids_dict[name] 
            if current_user_id == user_id:
                found_username = name
                break 
        else:
            found_username = NON_FOUND_USER_NAME
        return found_username


    def _validate_rate_limit(self):
        current_time = time.time() 
        time_diff_sec = current_time - self.last_query_time 
        adjusted_query_rate = max(self.running_query_rate_per_min - (time_diff_sec / 60) * self.rate_limit_per_min, 0) + 1
        rate_limit_ok = adjusted_query_rate < self.rate_limit_per_min
        if rate_limit_ok:
            self.last_query_time = current_time
            self.running_query_rate_per_min = adjusted_query_rate
        return rate_limit_ok

    @staticmethod
    def _greet_handler(bot, message):
        message_user_id = message['user']
        username = bot._lookup_user_name(message_user_id)
        user_first_name = username.split("_")[0] 
        bot.post_message("Hey there, {0}!".format(user_first_name))

    @staticmethod
    def _status_handler(bot, message):
        bot.post_message("Bot running from {0} is doing A-Ok!".format(bot.context_name)) 

    @staticmethod
    def _quote_handler(bot, message):
        pass

    @staticmethod
    def _no_match_handler(bot, message):
        bot.post_message("Sorry, I didn't parse any instruction there.")

    DEFAULT_HANDLER_STRINGS = ["#GREET", "#STATUS", "#QUOTE"]
    DEFAULT_HANDLER_FUNCS = [_greet_handler, _status_handler, _quote_handler]
    DEFAULT_HANDLER_EXTRA_ARGS = [(), (), ()]





