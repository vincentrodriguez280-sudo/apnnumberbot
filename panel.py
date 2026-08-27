import json, random
with open('config.json') as f: CFG = json.load(f)

def get_number(service, country):
    # Ekhon demo number dibe
    # Pore ekhane tor panel er API call bosabi
    # Example: requests.get(f"{CFG['PANEL_URL']}/getNumber?service={service}&country={country}&apikey={CFG['PANEL_KEY']}")
    return f"+39378{random.randint(1100000,1299999)}"

def get_otp(number):
    # Pore ekhane OTP check er API bosbe
    return "123456"
