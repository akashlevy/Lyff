'''Interact with the Lyft API'''

import logging
import requests
import collections
import ssl

from lyft_creds import CLIENT_ID, CLIENT_SECRET
from pprint import pprint

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

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
    reqPrices = requests.get(
        'https://api.lyft.com/v1/cost?start_lat=%s&start_lng=%s&end_lat=%s&end_lng=%s' % (lat, lng, lat2, lng2),
        headers=get_token_header()
    )
    LOGGER.debug('Got estimates')

    reqETA = requests.get('https://api.lyft.com/v1/eta?lat=%s&lng=%s' % (lat, lng), headers=get_token_header())
    LOGGER.debug('Got ETA')

    Estimates = collections.namedtuple('Estimates', ['prices', 'eta']) 
    e = Estimates(reqPrices.json()['cost_estimates'], reqETA.json()['eta_estimates'])
    return e

def format_estimates(estimates):
    """
    Format estimates for Lex.
    """
    output = 'I found %d ride types. ' % len(estimates.prices)
    for estimate in estimates.prices:
        if estimate['estimated_cost_cents_min'] == estimate['estimated_cost_cents_max']:
            cost = str(round(estimate['estimated_cost_cents_min'] / 100))
        else:
            cost = '%d to %d' % (round(estimate['estimated_cost_cents_min'] / 100), round(estimate['estimated_cost_cents_max'] / 100))
        cost += ' dollars'
        output += 'A %s is %s ' % (estimate['display_name'], cost)
        for etaEstimate in estimates.eta:
            if estimate['ride_type'] == etaEstimate['ride_type']:
                output += 'in %d minutes. ' % (etaEstimate["eta_seconds"] / 60) 
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

def request_ride(start, end, ride_type, access_token, cost_token):
    r = requests.post(
        'https://api.lyft.com/v1/rides',
        headers={'Authorization': 'Bearer ' + access_token},
        json={
            "ride_type": ride_type,
            "origin": {
                "lat": start[0],
                "lng": start[1],
            },
            "destination": {
                "lat": end[0],
                "lng": end[1],
            },
        },
    )
    return r.json()

def check_ride(access_token, ride_id):
    r = requests.get(
        'https://api.lyft.com/v1/rides/%s' % ride_id,
        headers={'Authorization': 'Bearer ' + access_token},
    )
    return r.json()

# --- Test code ---

if __name__ == '__main__':
    # print geocode('adsjfalskdfjaslk')
    #ESTS = get_estimates('upenn', 'Princeton University')
    #LOGGER.debug(ESTS)
    #LOGGER.debug(format_estimates(ESTS))

    result = get_estimates('5049 Oceania St.', 'Princeton University')
    print(format_estimates(result))
