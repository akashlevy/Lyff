from alexa.ask.utils import VoiceHandler, ResponseBuilder as r
import json
import os

"""
In this file we specify default event handlers which are then populated into the handler map using metaprogramming
Copyright Anjishnu Kumar 2015

Each VoiceHandler function receives a ResponseBuilder object as input and outputs a Response object
A response object is defined as the output of ResponseBuilder.create_response()
"""

def default_handler(request):
    """ The default handler gets invoked if no handler is set for a request """
    return r.create_response(message="There was a problem. No handler found.")


@VoiceHandler(request_type='SessionEndedRequest')
def session_ended_request_handler(request):
    return r.create_response(message="Thanks! Goodbye!")


@VoiceHandler(intent='OrderLyft')
def order_lyft_handler(request):
    """
    Use the 'intent' field in the VoiceHandler to map to the respective intent.
    You can insert arbitrary business logic code here
    """

    # Get variables like userId, slots, intent name etc from the 'Request' object
    startAddr = request.get_slot_value("PickupAddress")
    endAddr = request.get_slot_value("DropoffAddress")

    return r.create_response("Good job!")
