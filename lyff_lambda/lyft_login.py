import requests
import urllib
import re

from lyft import CLIENT_ID, CLIENT_SECRET
from pprint import pprint

def login_get_xsrf_token(session):
    return session.cookies.get('XSRF-TOKEN', domain='www.lyft.com')

def login_start(phone_number):
    s = requests.Session()
    s.get(
        'https://api.lyft.com/oauth/authorize?client_id=%s&scope=public%%20profile%%20rides.read%%20rides.request%%20offline&state=state_string&response_type=code' % CLIENT_ID,
        verify=False
    )
    r = s.post(
        'https://www.lyft.com/api/lyft_auth/register_user?existingUsersOnly=true&phoneNumber=%s&resendVerificationCode=false' % urllib.quote_plus(phone_number),
        verify=False,
        headers={'X-XSRF-TOKEN': login_get_xsrf_token(s)}
    )
    if r.status_code != 200:
        return None
    return s

def login_continue(session, phone_number, code):
    r = session.post(
        'https://www.lyft.com/api/lyft_auth/verify_user?phoneNumber=%s&verificationCode=%s' % (urllib.quote_plus(phone_number), code),
        verify=False,
        headers={'X-XSRF-TOKEN': login_get_xsrf_token(session)}
    )
    if r.status_code != 200:
        return None
    r2 = session.post(
        'https://www.lyft.com/api/oauth/access_code',
        json={
            "client_id": CLIENT_ID,
            "scope": "public profile rides.read rides.request offline",
            "state": "state_string",
            "response_type": "code"
        },
        verify=False,
        headers={'X-XSRF-TOKEN': login_get_xsrf_token(session)}
    )
    url = r2.json()['immediate_redirect_uri']
    return re.search(r'\?code=([^&]+)&', url).group(1)

def get_access_token(authorization_code):
    r = requests.post(
        'https://api.lyft.com/oauth/token',
        auth=(CLIENT_ID, CLIENT_SECRET),
        verify=False,
        data={'grant_type': 'authorization_code', 'code': authorization_code}
    )
    print r.text
    return r.json()

if __name__ == '__main__' or True:
    session = None
    while session is None:
        phone_number = raw_input('enter phone number: ')
        session = login_start(phone_number)

    authorization_code = None
    while authorization_code is None:
        verify_code = raw_input('enter verification code: ')
        authorization_code = login_continue(session, phone_number, verify_code)

    print 'got authorization code: ' + authorization_code

    pprint(get_access_token(authorization_code))
