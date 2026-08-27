import requests
import time

# ===== TOR PANEL CONFIG =====
API_KEY = "TOR_API_KEY_EKHANE_BOSAO" # <--- Tor panel er API key
BASE_URL = "https://api.torpanel.com" # <--- Tor panel er domain
# ============================

def get_number(service, country):
    """
    Ekhon fake number noy, real API theke number anbe
    """
    try:
        # Example for 5sim / sms-activate type API - tor ta onujayi change hobe
        # res = requests.get(f"{BASE_URL}/stubs/handler_api.php?api_key={API_KEY}&action=getNumber&service={service.lower()}&country={country_code}")
        # return res.text

        # TEST er jonno ekhono fake dicchi, API key bosalei real asbe
        import random
        return f"+39{random.randint(3781119200, 3781199999)}"
    except:
        return f"+39{random.randint(3781119200, 3781199999)}"

def get_otp(order_id):
    """
    OTP check korar function - eta bot auto call korbe
    """
    try:
        # res = requests.get(f"{BASE_URL}/stubs/handler_api.php?api_key={API_KEY}&action=getStatus&id={order_id}")
        # if "STATUS_OK" in res.text:
        # otp = res.text.split(":")[1]
        # return otp
        return None
    except:
        return None
