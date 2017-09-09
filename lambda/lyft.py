'''Interact with the Lyft API'''

import logging
import requests

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

CLIENT_ID = 'fBS6oabCfDgN'
CLIENT_SECRET = '2cGuUbI8XauyU0aQamoSm6NAv4Vxpg_Q'
PERMISSION_SCOPES = 'public'

def get_token_header():
    """
    Get token header for making requests to Lyft.
    """
    req = requests.post(
        'https://api.lyft.com/oauth/token',
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={'grant_type': 'client_credentials', 'scope': 'public'}
    )
    token = req.json()['access_token']
    LOGGER.debug('Got token')
    return {'Authorization': 'Bearer ' + token}

def get_estimates(start, end):
    """
    Get estimate prices based on locations specified.
    """
    lat, lng = geocode(start)
    lat2, lng2 = geocode(end)
    LOGGER.debug((lat, lng, lat2, lng2))
    req = requests.get(
        'https://api.lyft.com/v1/cost?start_lat=%s&start_lng=%s&end_lat=%s&end_lng=%s' % (lat, lng, lat2, lng2),
        headers=get_token_header()
    )
    LOGGER.debug('Got estimates')
    return req.json()['cost_estimates']

def format_estimates(estimates):
    """
    Format estimates for Lex.
    """
    output = 'I found %d ride types. ' % len(estimates)
    for estimate in estimates:
        if estimate['estimated_cost_cents_min'] == estimate['estimated_cost_cents_max']:
            cost = str(round(estimate['estimated_cost_cents_min'] / 100))
        else:
            cost = 'between %d and %d' % (round(estimate['estimated_cost_cents_min'] / 100), round(estimate['estimated_cost_cents_max'] / 100))
        cost += ' dollars'
        output += 'A %s will cost %s. ' % (estimate['display_name'], cost)
    output += 'Which type of ride would you like?'
    return output

def geocode(address):
    """
    Get latitude and longitude from address.
    """
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'sensor': 'false', 'address': address}
    req = requests.get(url, params=params)
    results = req.json()['results']
    location = results[0]['geometry']['location']
    LOGGER.debug('Got geocode')
    return (location['lat'], location['lng'])


# --- Test code ---

if __name__ == '__main__':
    ESTS = get_estimates('upenn', 'Princeton University')
    LOGGER.debug(ESTS)
    LOGGER.debug(format_estimates(ESTS))
