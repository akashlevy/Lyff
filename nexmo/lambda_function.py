from __future__ import print_function

import json


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    with open('ncco.json') as f:
        response = json.load(f)
    with open('rootkey.csv') as f:
        aws_key = f.readline().replace('AWSAccessKeyId=', '').replace('\n', '')
        aws_secret = f.readline().replace('AWSSecretKey=', '').replace('\n', '')

    response[1]['endpoint'][0]['headers']['aws_key'] = aws_key
    response[1]['endpoint'][0]['headers']['aws_secret'] = aws_secret
    response[1]['endpoint'][0]['uri'] = response[1]['endpoint'][0]['uri'].replace('AWSServiceRoleForLexBots', event['queryStringParameters']['from'])

    return respond(None, response)
