import requests
import json
import os
from faker import Faker
from flask import Flask, request

app = Flask(__name__)
fake = Faker()

# Function to validate credit card number using Luhn algorithm
def validate_cc_number(cc_number):
    if not cc_number:
        return False
    cc_number = str(cc_number).strip().replace('-', '').replace(' ', '')
    if not all(c.isdigit() for c in cc_number):
        return False
    check_sum = sum(int(cc_number[i]) * (2 - (i % 2)) for i in range(len(cc_number) - 1, -1, -1))
    return check_sum % 10 == 0

# Function to check the BIN of a credit card number using the Binlist API
def check_bin(cc_number):
    if not cc_number:
        return False
    cc_number = str(cc_number).strip().replace('-', '').replace(' ', '')
    if not all(c.isdigit() for c in cc_number):
        return False
    bin_number = cc_number[:6]
    response = requests.get(f'https://lookup.binlist.net/{bin_number}')
    if response.status_code != 200:
        return False
    data = json.loads(response.text)
    return data.get('bank', {}).get('name')

# Function to check if a SK-key is valid using the Stripe API
def check_sk_key(sk_key):
    if not sk_key:
        return False
    response = requests.get(f'https://api.stripe.com/v1/account', auth=(sk_key, ''))
    return response.status_code == 200

# Function to generate a credit card number with a specific BIN using the Faker library
def generate_cc_number(bin_number):
    if not bin_number:
        return False
    cc_number = fake.credit_card_number(card_type=None)
    cc_number = bin_number + cc_number[6:]
    return cc_number

# Function to parse the checkout session ID from a Stripe checkout URL
def parse_checkout_url(checkout_url):
    if not checkout_url:
        return False
    checkout_session_id = checkout_url.split('/')[-1]
    return checkout_session_id

# Flask route to handle incoming messages
@app.route('/', methods=['POST'])
def handle_message():
    data = request.get_json()
    message = data['message']
    response = {'message': ''}
    if message.startswith('/validate_cc'):
        cc_number = message.split()[1]
        if validate_cc_number(cc_number):
            response['message'] = f'{cc_number} is a valid credit card number'
        else:
            response['message'] = f'{cc_number} is not a valid credit card number'
    elif message.startswith('/check_bin'):
        cc_number = message.split()[1]
        bank_name = check_bin(cc_number)
        if bank_name:
            response['message'] = f'The BIN {cc_number[:6]} belongs to {bank_name}'
        else:
            response['message'] = f'Could not find information for the BIN {cc_number[:6]}'
    elif message.startswith('/check_sk_key'):
        sk_key = message.split()[1]
        if check_sk_key(sk_key):
            response['message'] = f'{sk_key} is a valid Stripe secret key'
        else:
            response['message'] = f'{sk_key} is not a valid Stripe secret key'
    elif message.startswith('/generate_cc'):
        bin_number = message.split()[1]
        cc_number = generate_cc_number(bin_number)
        if cc_number:
            response['message'] = f'Generated credit card number: {cc_number}'
        else:
            response['message'] = 'Could not generate credit card number'
    elif message.startswith('/parse_checkout_url'):
        checkout_url = message.split()[1]
        checkout_session_id = parse_checkout_url(checkout_url)
        if checkout_session_id:
            response['message'] = f'Checkout session ID: {checkout_session_id}'
        else:
            response['message'] = 'Could not parse checkout session ID'
    else:
        response['message'] = 'Invalid command'
    return json.dumps(response)

# Flask route to handle home page
@app.route('/')
def home():
    return 'Welcome to the Empire Checker Bot!'

# Function to run the bot
def run_bot():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    run_bot()
