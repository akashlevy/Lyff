# Lyff

## Inspiration
Sometimes, you find yourself without Internet or data and really need to call a Lyft. Lyff lets you call a Lyft with just a quick phone call!

## What It Does
Users can call 1-888-970-LYFF, where an automated chatbot will guide them through the process of ordering a Lyft to their final destination. Users can simply look at the street name and number of the closest building to acquire their current location.

## How It's Built
We used the Nexmo API from Vonage to handle the voice aspect, Amazon Lex to create a chatbot and parse the speech input, Amazon Lambda to implement the internal application logic, the Lyft API for obvious reasons, and Google Maps API to sanitize the locations.

## Built With
* Python
* Google Maps Geocoder API
* Nexmo API
* Amazon Lex
* Amazon Lambda
* Lyft API

## Team
This app was built at PennApps Fall 2017 by Akash Levy, Zachary Liu, Selina Wang, and David Fan. Awarded Best Use of Vonage/Nexmo API! See our DevPost page: https://devpost.com/software/lyff

![Lyff Logo](/lyff-logo.png)

## Installation Instructions

0. Clone this repository

1. Set up an S3 bucket:
    * Go to ![AWS S3 Console Home](https://s3.console.aws.amazon.com/s3/home)
    * Create a bucket for storing user Lyft access tokens (you can use the default settings)
    * Create AWS credentials for accessing this bucket and copy them into ```lyff_lambda/rootkey.csv``` in the following format:
      ```
      AWSAccessKeyId=<ACCESS_KEY>
      AWSSecretKey=<SECRET_KEY>
      ```

2. Set up your Lyft developer app:
    * ![Create your Lyft developer account](https://www.lyft.com/developers) and login
    * ![Create a new app](https://www.lyft.com/developers/apps/new)
    * Substitute your Client ID and Client Secret into ```lyff_lambda/lyff_creds.py```

3. Set up your Amazon Lambda function for the chatbot logic:
    * Go to ![AWS Lambda Home](https://console.aws.amazon.com/lambda/home)
    * Click on "Create Function"
    * Click "Author from Scratch"
    * No triggers necessary
    * Pick a name, runtime environment should be Python 2.7, use ```lambda_basic_execution``` role
    * Confirm and create function
    * Zip all the files in ```lyff_lambda/``` and upload this ZIP file as the Lambda function
    * Click "Save"

4. Set up your Amazon Lex bot:
    * Go to ![AWS Lex Home](https://console.aws.amazon.com/lex/home)
    * Create a new bot
    * Add a slot called "RideTypes" with the following settings:
    
    ![Ride Types](/setup-2.png)
    
    * Add a slot called "Status" with the following settings:
    
    ![Settings](/setup-3.png)
    
    * Add a slot called "YesNo" with the following settings:
  
    ![YesNo](/setup-4.png)
    
    * Make your setup look like this:
    
    ![Lyff Logo](/setup-1.png)
    
    * Click "Save Intent" then "Build"
    * Click "Publish" and create a new alias (we called ours "Prod")
    * Create AWS credentials for accessing this Lex bot and copy them into ```nexmo/rootkey.csv``` in the following format:
      ```
      AWSAccessKeyId=<ACCESS_KEY>
      AWSSecretKey=<SECRET_KEY>
      ```
      
4. Set up your Lex connector:
    * Run the server provided by ![Zach's lex-connector](https://github.com/zacharyliu/lex-connector) at a URL that is accessible to Nexmo. We used Amazon EC2 and configured the domain to be publicly accessible. Alternatively, once the fixes to lex-connector in Zach's fork are pulled into the ![main lex-connector branch](https://github.com/Nexmo/lex-connector), you can follow ![these instructions](https://developer.nexmo.com/voice/voice-api/guides/connecting-voice-calls-to-amazon-lex-bots) to use Nexmo's default connector to Amazon Lex.
    * Modify the ```uri``` attribute in ```nexmo/ncco.json``` to look like this:
      ```
      wss://LEX_CONNECTOR_DOMAIN_NAME_OR_IP_ADDRESS/bot/BOTNAME/alias/PUBLISH_ALIAS/user/AWSServiceRoleForLexBots/content
      ```
    * Leave the ```AWS_KEY_HERE``` and ```AWS_SECRET_HERE``` in this file untouched
    
5. Set up your Amazon Lambda function for the dynamic NCCO fetcher:
    * Go to ![AWS Lambda Home](https://console.aws.amazon.com/lambda/home)
    * Click on "Create Function"
    * Click "Author from Scratch"
    * Add an "API Gateway" trigger with default settings
    * Setup your IAM role so your endpoint is accessible to Nexmo
    * Pick a name, runtime environment should be Python 2.7, use ```lambda_basic_execution``` role
    * Confirm and create function
    * Zip all the files in ```lyff_lambda/``` and upload this ZIP file as the Lambda function
    * Click "Save"
    * Make the function publicly access

6. Set up Nexmo:
    * ![Sign up for a Nexmo account](https://dashboard.nexmo.com/sign-up) and add enough money to buy a number
    * ![Buy a number](https://dashboard.nexmo.com/buy-numbers)
    * Install the Nexmo CLI: ```npm install -g nexmo-cli```
    * Run ```nexmo app:create "Lyff" <NCCO_FETCHER_LAMBDA_FUNCTION_PUBLIC_URL> http://example.com``` and you should get your app ID
    * Link your app to your phone number with``` nexmo link:app <PHONE_NUMBER_HERE> <APP_ID_HERE>```
    
7. You're done! Try calling your phone number to make sure everything works!

## Future Work
    * Support for booking through SMS
    * Support for stateful calls
