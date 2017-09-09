import os
from collections import OrderedDict, defaultdict
import json
import pkgutil
import inspect


RAW_RESPONSE = """
{
    "version": "1.0",
    "response": {
        "outputSpeech": {
            "type": "PlainText",
            "text": "Welcome to Lyff. I am ready to serve."
                },
        "shouldEndSession": False
    }
}"""


class VoiceHandler(object):
    """
    Decorator to store function metadata
    Functions that are annotated with this label are
    treated as voice handlers
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, function):
        function.voice_handler = self.kwargs
        return function


def initialize_handlers(voice_handlers, INTENT_SCHEMA, NON_INTENT_REQUESTS):
    """
    Automatically populate function handlers from the handlers in the voice_handlers module
    """
    # If no handler is specified, backoff to default handler
    init_default_handler = lambda : voice_handlers.default_handler
    all_handlers_map = defaultdict(init_default_handler)
    intent_handlers_map = defaultdict(init_default_handler)
    # Load intent schema to verify that handlers are mapped to valid intents
    all_intents = {intent["intent"] : { slot["name"] : slot["type"] for slot in intent['slots'] }
                   for intent in INTENT_SCHEMA['intents'] }
    #Loaded functions in the handlers module
    member_functions = inspect.getmembers(voice_handlers, inspect.isfunction)
    for (name, function) in member_functions:
        if hasattr(function, 'voice_handler'): #Function has been decorated as a voice_handler
            if 'request_type' in function.voice_handler:
                if function.voice_handler['request_type'] in NON_INTENT_REQUESTS:
                    # Function is a valid request voice handler
                    all_handlers_map[function.voice_handler['request_type']] = function
            elif 'intent' in function.voice_handler:
                if function.voice_handler['intent'] in all_intents:
                    # Function is a valid intent voice handler
                    intent_handlers_map[function.voice_handler['intent']] = function
    all_handlers_map['IntentRequest'] = intent_handlers_map
    return all_handlers_map


class Request(object):
    """
    Simple wrapper around the JSON request
    received by the module
    """
    def __init__(self, request_dict):
        self.request = request_dict

    def request_type(self):
        return self.request["request"]["type"]

    def intent_name(self):
        if not "intent" in self.request["request"]:
            return None
        return self.request["request"]["intent"]["name"]

    def user_id(self):
        return self.request["session"]["user"]["userId"]

    def access_token(self):
        try:
            return self.request['session']['user']['accessToken']
        except:
             return None

    def session_id(self):
        return self.request["session"]["sessionId"]

    def get_slot_value(self, slot_name):
        try:
            return self.request["request"]["intent"]["slots"][slot_name]["value"]
        except:
            """Value not found"""
            return None

    def get_slot_names(self):
        try:
            return self.request['request']['intent']['slots'].keys()
        except:
            return []

    def get_slot_map(self):
        return {slot_name : self.get_slot_value(slot_name) for slot_name in self.get_slot_names()}


class ResponseBuilder(object):
    """
    Simple class to help users to build responses
    """
    base_response = eval(RAW_RESPONSE)

    @classmethod
    def create_response(self, message=None, end_session=False, card_obj=None,
                        reprompt_message=None, is_ssml=None):
        """
        message - text message to be spoken out by the Echo
        end_session - flag to determine whether this interaction should end the session
        card_obj = JSON card object to substitute the 'card' field in the raw_response
        """
        response = self.base_response
        if message:
            response['response'] = self.create_speech(message, is_ssml)
        response['response']['shouldEndSession'] = end_session
        if card_obj:
            response['response']['card'] = card_obj
        if reprompt_message:
            response['reprompt'] = self.create_speech(reprompt_message, is_ssml)
        return response

    @classmethod
    def create_speech(cls, message=None, is_ssml=False):
        data = {}
        if is_ssml:
            data['type'] = "SSML"
            data['ssml'] = message
        else:
            data['type'] = "PlainText"
            data['text'] = message
        return {"outputSpeech" : data }

    @classmethod
    def create_card(self, title=None, subtitle=None, content=None, card_type="Simple"):
        """
        card_obj = JSON card object to substitute the 'card' field in the raw_response
        format:
        {
          "type": "Simple", #COMPULSORY
          "title": "string", #OPTIONAL
          "subtitle": "string", #OPTIONAL
          "content": "string" #OPTIONAL
        }
        """
        card = {"type": card_type}
        if title: card["title"] = title
        if subtitle: card["subtitle"] = subtitle
        if content: card["content"] = content
        return card


def chunk_list(input_list, chunksize):
    """ Helped function to chunk a list
    >>> lst = [1,2,3,4,5,6]
    >>> chunk_list(lst)
    [[1,2],[3,4],[5,6]]
    """
    return [input_list[start : end] for start, end
              in zip(range(0, len(input_list), chunksize),
                     range(chunksize, len(input_list), chunksize))]
