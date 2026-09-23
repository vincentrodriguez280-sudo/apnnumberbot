
import os
import requests
import time
import random
import json
import re

# Voltx API - Hidden from user
BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"
API_KEY = os.getenv("VOLTX_API_KEY", "") or os.getenv("MAUTHAPI_KEY", "") or os.getenv("API_KEY_2OO9", "") or os.getenv("PANEL_API_KEY", "")

_orders = {}
_otp_cache = {}
_last_otp_fetch = 0

def get_headers():
    return {
        "mauthapi": API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

def load_ranges():
    """Load ranges from ranges.json"""
    try:
        for path in ["/data/ranges.json", "./ranges.json", "ranges.json", "/app/ranges.json"]:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    if data:
                        return data
    except:
        pass
    return {}

def get_rid_for_country(country_code, service="FACEBOOK"):
    """Get rid for country from ranges.json"""
    try:
        ranges = load_ranges()
        service_upper = service.upper()
        country_upper = country_code.upper()
        
        # Direct: ranges[service][country] = rid
        if service_upper in ranges and isinstance(ranges[service_upper], dict):
            if country_upper in ranges[service_upper]:
                return str(ranges[service_upper][country_upper])
        
        # Search all services
        for srv, cmap in ranges.items():
            if isinstance(cmap, dict):
                if country_upper in cmap:
                    return str(cmap[country_upper])
        
        # Simple dict: ranges[country] = rid
        if country_upper in ranges and isinstance(ranges[country_upper], (str, int)):
            return str(ranges[country_upper])
            
    except Exception as e:
        print(f"[RID ERR] {e}")
    return None

def create_order(service, country_code):
    """Allocate number - user will get number, won't know panel name"""
    global _orders
    
    if not API_KEY:
        print("[API] Key not set!")
        return None
    
    rid = get_rid_for_country(country_code, service)
    
    if not rid:
        print(f"[API] No rid for {country_code}/{service}")
        return None
    
    rid_clean = rid.replace("XXX", "").strip()
    
    print(f"[GETNUM] {service}/{country_code} rid={rid_clean}")
    
    try:
        url = f"{BASE_URL}/getnum"
        resp = requests.post(url, json={"rid": rid_clean}, headers=get_headers(), timeout=20)
        
        if resp.status_code != 200:
            print(f"[GETNUM] HTTP {resp.status_code}")
            return None
        
        data = resp.json()
        meta = data.get("meta", {})
        
        if meta.get("code") == 2946:
            print(f"[GETNUM] Out of stock rid={rid_clean}")
            return None
        
        if meta.get("code") != 200:
            print(f"[GETNUM] Error {meta.get('code')}: {data.get('message')}")
            return None
        
        payload = data.get("data")
        if not payload:
            return None
        
        full_number = payload.get("full_number") or payload.get("no_plus_number")
        no_plus = payload.get("no_plus_number") or re.sub(r'\D', '', full_number or "")
        
        if not full_number or not no_plus:
            return None
        
        order_id = no_plus
        
        result = {
            "number": no_plus,
            "full_number": full_number,
            "no_plus_number": no_plus,
            "id": order_id,
            "country": country_code,
            "service": service,
            "rid": rid_clean
        }
        
        _orders[order_id] = result
        print(f"[GETNUM] OK: {full_number} -> {order_id}")
        return result
        
    except Exception as e:
        print(f"[GETNUM ERR] {e}")
        return None

def get_otp(order_id):
    """Get OTP - will be sent to inbox + group"""
    global _otp_cache, _last_otp_fetch
    
    if not API_KEY:
        return None
    
    search_number = str(order_id).replace("+", "").replace(" ", "").strip()
    
    try:
        now = time.time()
        # 5 sec cache
        if now - _last_otp_fetch < 5:
            if search_number in _otp_cache:
                cached = _otp_cache[search_number]
                if now - cached.get("_time", 0) < 15:
                    return cached.get("otp")
        
        url = f"{BASE_URL}/success-otp"
        resp = requests.get(url, headers=get_headers(), timeout=15)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        if data.get("meta", {}).get("code") != 200:
            return None
        
        otps = data.get("data", {}).get("otps", [])
        
        for entry in otps:
            otp_number = str(entry.get("number", "")).replace("+", "").strip()
            if otp_number == search_number or search_number in otp_number:
                msg = entry.get("message", "")
                m = re.search(r'\b(\d{4,8})\b', msg)
                if m:
                    code = m.group(1)
                    # Avoid returning phone number as OTP
                    if code != otp_number and len(code) >= 4:
                        print(f"[OTP] {search_number} -> {code}")
                        _otp_cache[search_number] = {"otp": code, "_time": now}
                        _last_otp_fetch = now
                        return code
        
        _last_otp_fetch = now
        return None
        
    except Exception as e:
        print(f"[OTP ERR] {e}")
        return None

def get_all_countries(service):
    """Get countries from ranges.json - buttons auto create from GitHub ranges"""
    try:
        ranges = load_ranges()
        service_upper = service.upper()
        countries = []
        
        if service_upper in ranges and isinstance(ranges[service_upper], dict):
            countries = list(ranges[service_upper].keys())
        else:
            # Collect all if service not found, or collect from all
            for srv, cmap in ranges.items():
                if isinstance(cmap, dict):
                    for c in cmap.keys():
                        if c not in countries:
                            countries.append(c)
        
        # Clean and unique
        unique = []
        seen = set()
        for c in countries:
            cu = c.upper().strip()
            if cu and cu not in seen:
                unique.append(cu)
                seen.add(cu)
        
        print(f"[COUNTRIES] {service}: {unique}")
        return unique
    except Exception as e:
        print(f"[COUNTRIES ERR] {e}")
        return []

def get_display_name(country_code):
    """Display name: MADAGASCARNEWACCOUNT -> Madagascar New Account, NEPAL_FB -> Nepal"""
    try:
        code = country_code.upper().strip()
        # Remove _FB, _WS suffix for display
        clean = code.replace("_FB", "").replace("_WS", "").replace("_NEW_ACCOUNT", " NEW ACCOUNT").replace("_", " ")
        
        # Handle cases like MADAGASCARNEWACCOUNT (no underscore)
        # Insert space before NEW, ACCOUNT, etc
        clean = re.sub(r'(?i)(NEWACCOUNT)', ' NEW ACCOUNT', clean)
        clean = re.sub(r'(?i)(NEW ACCOUNT)', ' NEW ACCOUNT', clean)
        
        # Title case
        # Special handling for multi-word
        words = clean.split()
        titled = []
        for w in words:
            if w.upper() in ["NEW", "ACCOUNT"]:
                titled.append(w.title())
            else:
                titled.append(w.title())
        
        result = " ".join(titled)
        # Fix common
        result = result.replace("Newaccount", "New Account").replace("New Account", "New Account")
        return result.strip()
    except:
        return country_code.replace("_", " ").title()
