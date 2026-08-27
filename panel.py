import random

def create_order(service, country):
    # Real API bosale ekhane API call hobe
    # Example: requests.get(f"https://yourpanel.com/api?key=KEY&service={service}&country={country}")
    return {"number": f"+39{random.randint(3781119200, 3781199999)}", "id": f"{random.randint(10000,99999)}"}

def get_number(service, country):
    return create_order(service, country)['number']

def get_otp(order_id):
    # Real API: requests.get(f"https://yourpanel.com/api?key=KEY&action=getOtp&id={order_id}")
    # TEST - 20% chance OTP asbe
    if random.randint(1,5) == 1:
        return f"{random.randint(100000,999999)}"
    return None
