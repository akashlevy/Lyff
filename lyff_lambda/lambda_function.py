'''Lambda function for booking a Lyft with Lyff'''

import json
import logging
import lyft
import lyft_login
import pickle

from boto.s3.connection import S3Connection

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

    if len(intent_req['userId']) > 13:
        intent_req['userId'] = '6466230283'

    LOGGER.debug(intent_req)


    # Setup S3 for storing Lyff user tokens
    with open('rootkey.csv') as file:
        keys = [line.split('=')[1].strip() for line in file.readlines()]
    conn = S3Connection(keys[0], keys[1])
    bucket = conn.get_bucket('lyff-users', validate=False)


    # Precursory state logic
    if 'state' not in session_attrs:
        key = bucket.get_key(intent_req['userId'])
        if key is not None:
            access_keys = json.loads(key.get_contents_as_string())
            session_attrs['access_token'] = access_keys['access_token']
            session_attrs['refresh_token'] = access_keys['refresh_token']
            session_attrs['state'] = 'get_pickup_address'
        else:
            session_attrs['state'] = 'get_pin'

    if session_attrs['state'] == 'post_confirm_pickup_address':
        if slots['PickupAddressConfirm'] is None or slots['PickupAddressConfirm'].lower() == 'no':
            session_attrs['state'] = 'get_pickup_address'
        else:
            session_attrs['state'] = 'validate_pickup_address'

    if session_attrs['state'] == 'post_confirm_dropoff_address':
        if slots['DropoffAddressConfirm'] is None or slots['DropoffAddressConfirm'].lower() == 'no':
            session_attrs['state'] = 'get_dropoff_address'
        else:
            session_attrs['state'] = 'validate_dropoff_address'

    if session_attrs['state'] == 'confirmation':
        if not (slots['Confirmation'] is None or slots['Confirmation'].lower() == 'no'):
            session_attrs['state'] = 'book_lyft'


    # Main state logic
    if session_attrs['state'] == 'get_pin':
        session_attrs['state'] = 'get_pin_continue'
        headers, cookies = lyft_login.login_start(intent_req['userId'])
        session_attrs['lyft_headers'] = pickle.dumps(headers)
        session_attrs['lyft_cookies'] = pickle.dumps(cookies)
        return elicit_slot(session_attrs, name, slots, 'LyftPIN',
                           'A Lyft PIN was just texted to you, please say the 4 digits.')
    if session_attrs['state'] == 'get_pin_continue':
        token1 = lyft_login.login_continue(
            pickle.loads(session_attrs['lyft_headers']),
            pickle.loads(session_attrs['lyft_cookies']),
            intent_req['userId'],
            slots['LyftPIN']
        )
        if token1 is not None:
            tokens = lyft_login.get_access_token(token1)
            key = bucket.new_key(intent_req['userId'])
            key.set_contents_from_string(json.dumps(tokens))
            session_attrs['access_token'] = tokens['access_token']
            session_attrs['refresh_token'] = tokens['refresh_token']
            session_attrs['state'] = 'get_pickup_address'
        if 'access_token' not in session_attrs:
            return elicit_slot(session_attrs, name, slots, 'LyftPIN',
                               'There was an error with the PIN you entered %s.'
                               'Please reenter the 4 digits.' %
                               slots['LyftPIN'])

    if session_attrs['state'] == 'get_pickup_address':
        try:
            del session_attrs['lyft_headers']
            del session_attrs['lyft_cookies']
        except KeyError:
            pass
        session_attrs['state'] = 'confirm_pickup_address'
        return elicit_slot(session_attrs, name, slots, 'PickupAddress',
                           'At what address would you like to be picked up?')
    if session_attrs['state'] == 'confirm_pickup_address':
        session_attrs['state'] = 'post_confirm_pickup_address'
        return elicit_slot(session_attrs, name, slots, 'PickupAddressConfirm',
                           'Was that %s?' % slots['PickupAddress'])
    if session_attrs['state'] == 'validate_pickup_address':
        try:
            lyft.geocode(slots['PickupAddress'])
            session_attrs['state'] = 'get_dropoff_address'
        except IndexError:
            session_attrs['state'] = 'confirm_pickup_address'
            return elicit_slot(session_attrs, name, slots, 'PickupAddress',
                               'The pickup address you specified, %s, could not be found. '
                               'Try again.' % slots['PickupAddress'])


    if session_attrs['state'] == 'get_dropoff_address':
        session_attrs['state'] = 'confirm_dropoff_address'
        return elicit_slot(session_attrs, name, slots, 'DropoffAddress',
                           'At what address would you like to be dropped off?')
    if session_attrs['state'] == 'confirm_dropoff_address':
        session_attrs['state'] = 'post_confirm_dropoff_address'
        return elicit_slot(session_attrs, name, slots, 'DropoffAddressConfirm',
                           'Was that %s?' % slots['DropoffAddress'])
    if session_attrs['state'] == 'validate_dropoff_address':
        try:
            lyft.geocode(slots['DropoffAddress'])
            session_attrs['state'] = 'get_ride_type'
        except IndexError:
            session_attrs['state'] = 'confirm_dropoff_address'
            return elicit_slot(session_attrs, name, slots, 'DropoffAddress',
                               'The dropoff address you specified, %s, could not be found. '
                               'Try again.' % slots['DropoffAddress'])


    if session_attrs['state'] == 'get_ride_type':
        estimates = lyft.get_estimates(slots['PickupAddress'], slots['DropoffAddress'])
        #session_attrs['estimates'] = json.dumps(estimates)
        session_attrs['state'] = 'confirmation'
        return elicit_slot(session_attrs, name, slots, 'RideType',
                           lyft.format_estimates(estimates))

    if session_attrs['state'] == 'confirmation':
        msg = 'Should I confirm your %s ride from %s to %s?'
        rtype, pickup, dropoff = slots['RideType'], slots['PickupAddress'], slots['DropoffAddress']
        msg = msg % (rtype, pickup, dropoff)
        return elicit_slot(session_attrs, name, slots, 'Confirmation', msg)

    if session_attrs['state'] == 'book_lyft':
        ride = lyft.request_ride(
            lyft.geocode(slots['PickupAddress']),
            lyft.geocode(slots['DropoffAddress']),
            slots['RideType'].lower().split().join('_'),
            session_attrs['access_token'],
            None
        )
        if 'ride_id' not in ride:
            return close(session_attrs, 'Failed', 'Ride could not be booked.')
        session_attrs['ride_id'] = ride['ride_id']
        session_attrs['state'] = 'status'
        return elicit_slot(session_attrs, name, slots, 'Confirmation', "Ride booked! "
                           "Say \"status\" to retrieve the status of your ride.")

    if session_attrs['state'] == 'status':
        status = lyft.check_ride(session_attrs['access_token'], session_attrs['ride_id'])
        ride_status = status['rideStatus']
        return elicit_slot(session_attrs, name, slots, 'Status', "Status: " % ride_status)


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
