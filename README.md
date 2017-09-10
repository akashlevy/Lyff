# Lyff

## Inspiration
Sometimes, you find yourself without Internet or data and really need to call a Lyft. Lyff lets you call a Lyff with just a quick phone call!

## What It Does
Users can call 1-888-970-LYFF, where an automated chatbot will guide them through the process of ordering a Lyft to their final destination. Users can simply look at the street name and number of the closest building to acquire their current location.

## How It's Built
We used the Nexmo API from Vonage to handle the voice aspect, Amazon Lex to create a chatbot and parse the speech input, Amazon Lambda to implement the internal application logic, the Lyft API for obvious reasons, and Google Maps API to sanitize the locations.

## Built With
* Python
* Google Maps
* Nexmo API
* Amazon Lex
* Amazon Lambda
* Lyft API

## Team
This app was built at PennApps Fall 2017 by Akash Levy, Zachary Liu, Selina Wang, and David Fan.

![Lyff Logo](/lyff-logo.png)
