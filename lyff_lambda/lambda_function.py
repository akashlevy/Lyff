'''Lambda function for booking a Lyft with Lyff'''

import logging
import lyft

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)


# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Elicit a slot in Lex.
    """
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': {'contentType': 'PlainText', 'content': message}
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    """
    Confirm intent in Lex.
    """
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    """
    Close session in Lex.
    """
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    """
    Delegate slots in Lex.
    """
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---

def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None


# --- Functions that control the bot's behavior ---

def book_lyft(intent_request):
    """
    Performs dialog management and fulfillment for booking a Lyft.
    """

    name = intent_request['currentIntent']['name']
    slots = intent_request['currentIntent']['slots']
    session_attributes = intent_request['sessionAttributes']

    LOGGER.debug(intent_request)

    if slots['PickupAddress'] is None:
        return elicit_slot(session_attributes, name, slots, 'PickupAddress',
                           'At what address would you like to be picked up?')
    if 'PickupCoords' not in session_attributes:
        try:
            lyft.geocode(slots['PickupAddress'])
        except IndexError:
            return elicit_slot(session_attributes, name, slots, 'PickupAddress',
                               'The start address you specified, %s, could not be found. '
                               'Try again.' % slots['PickupAddress'])

    if slots['DropoffAddress'] is None:
        return elicit_slot({}, name, slots, 'DropoffAddress',
                           'At what address would you like to be dropped off?')
    if slots['RideType'] is None:
        return elicit_slot({}, name, slots, 'RideType',
                           'Which type of ride would you like?')


# --- Intents ---


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    userid = intent_request['userId']
    name = intent_request['currentIntent']['name']

    LOGGER.debug('dispatch userId=%s, intentName=%s', userid, name)

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'BookLyft':
        return book_lyft(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    LOGGER.debug('event.bot.name=%s', event['bot']['name'])

    return dispatch(event)
