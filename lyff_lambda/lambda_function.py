'''Lambda function for booking a Lyft with Lyff'''

import logging
import lyft

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)


# --- Helpers that build all of the responses ---


def elicit_slot(session_attrs, intent_name, slots, slot_to_elicit, message):
    """
    Elicit a slot in Lex.
    """
    return {
        'sessionAttributes': session_attrs,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': {'contentType': 'PlainText', 'content': message}
        }
    }


def confirm_intent(session_attrs, intent_name, slots, message):
    """
    Confirm intent in Lex.
    """
    return {
        'sessionAttributes': session_attrs,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attrs, fulfillment_state, message):
    """
    Close session in Lex.
    """
    response = {
        'sessionAttributes': session_attrs,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attrs, slots):
    """
    Delegate slots in Lex.
    """
    return {
        'sessionAttributes': session_attrs,
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

def book_lyft(intent_req):
    """
    Performs dialog management and fulfillment for booking a Lyft.
    """

    name = intent_req['currentIntent']['name']
    slots = intent_req['currentIntent']['slots']
    session_attrs = intent_req['sessionAttributes'] if intent_req['sessionAttributes'] else {}

    LOGGER.debug(intent_req)


    if slots['PickupAddress'] is None or slots['PickupAddressConfirm'].lower() == 'no':
        session_attrs['PickupAddressConfirm'] = 'no'
        return elicit_slot(session_attrs, name, slots, 'PickupAddress',
                           'At what address would you like to be picked up?')
    if slots['PickupAddressConfirm'] is None or
       session_attrs['PickupAddressConfirm'].lower() == 'no':
        return elicit_slot(session_attrs, name, slots, 'PickupAddressConfirm',
                           'Was that %s?' % slots['PickupAddress'])
    if 'PickupAddressValidated' not in session_attrs:
        try:
            lyft.geocode(slots['PickupAddress'])
            session_attrs['PickupAddressValidated'] = True
        except IndexError:
            return elicit_slot(session_attrs, name, slots, 'PickupAddress',
                               'The pickup address you specified, %s, could not be found. '
                               'Try again.' % slots['PickupAddress'])


    if slots['DropoffAddress'] is None or slots['DropoffAddressConfirm'].lower() == 'no':
        session_attrs['PickupAddressConfirm'] = 'no'
        return elicit_slot(session_attrs, name, slots, 'DropoffAddress',
                           'At what address would you like to be dropped off?')
    if slots['PickupAddressConfirm'] is None or
    session_attrs['DropoffAddressConfirm'].lower() == 'no':
        return elicit_slot(session_attrs, name, slots, 'PickupAddressConfirm',
                           'Was that %s?' % slots['PickupAddress'])
    if 'DropoffAddressValidated' not in session_attrs:
        try:
            lyft.geocode(slots['DropoffAddress'])
            session_attrs['DropoffAddressValidated'] = True
        except IndexError:
            return elicit_slot(session_attrs, name, slots, 'DropoffAddress',
                               'The dropoff address you specified, %s, could not be found. '
                               'Try again.' % slots['DropoffAddress'])


    if slots['RideType'] is None:
        estimates = lyft.get_estimates(slots['PickupAddress'], slots['DropoffAddress'])
        return elicit_slot(session_attrs, name, slots, 'RideType',
                           lyft.format_estimates(estimates))

    if intent_req['confirmationStatus'] == 'None':
        msg = 'Should I confirm your ride from %s to %s, arriving in %s minutes, for $%s?'
        pickup, dropoff = slots['PickupAddress'], slots['DropoffAddress']
        eta, cost = session_attrs['ETA'], session_attrs['$']
        msg = msg % (pickup, dropoff, eta, cost)
        return confirm_intent(session_attrs, name, slots, msg)


# --- Intents ---


def dispatch(intent_req):
    """
    Called when the user specifies an intent for this bot.
    """

    userid = intent_req['userId']
    name = intent_req['currentIntent']['name']

    LOGGER.debug('dispatch userId=%s, intentName=%s', userid, name)

    intent_name = intent_req['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'BookLyft':
        return book_lyft(intent_req)

    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    LOGGER.debug('event.bot.name=%s', event['bot']['name'])

    return dispatch(event)
