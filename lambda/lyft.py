import requests
from pprint import pprint

YOUR_CLIENT_ID = 'fBS6oabCfDgN'
YOUR_CLIENT_SECRET = '2cGuUbI8XauyU0aQamoSm6NAv4Vxpg_Q'
YOUR_PERMISSION_SCOPES = 'public'

def get_token_header():
  r = requests.post('https://api.lyft.com/oauth/token', auth=(YOUR_CLIENT_ID, YOUR_CLIENT_SECRET), data={'grant_type': 'client_credentials', 'scope': 'public'})
  token = r.json()['access_token']
  return {'Authorization': 'Bearer ' + token}

def get_estimates(start, end):
  lat, lng = geocode(start)
  lat2, lng2 = geocode(end)
  print((lat, lng, lat2, lng2))
  r = requests.get('https://api.lyft.com/v1/cost?start_lat=%s&start_lng=%s&end_lat=%s&end_lng=%s' % (lat, lng, lat2, lng2), headers=get_token_header())
  return r.json()['cost_estimates']

def format_estimates(estimates):
  pass

def geocode(address):
  url = 'https://maps.googleapis.com/maps/api/geocode/json'
  params = {'sensor': 'false', 'address': address}
  r = requests.get(url, params=params)
  results = r.json()['results']
  location = results[0]['geometry']['location']
  return (location['lat'], location['lng'])


pprint(get_estimates('upenn', 'Princeton University'))
