
import os
import requests
import time
import random
import json
import re

# ========== 2oo9.cloud (Voltx) API Panel - ONLY THIS PANEL ==========
# Base path from documentation
BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"

# API Key from Railway Variables
# Set in Railway: VOLTX_API_KEY or MAUTHAPI_KEY or API_KEY_2OO9
API_KEY = os.getenv("VOLTX_API_KEY", "") or os.getenv("MAUTHAPI_KEY", "") or os.getenv("API_KEY_2OO9", "") or os.getenv("PANEL_API_KEY", "")

# Store orders: order_id -> {number, country, service, time}
_orders = {}
# Cache OTPs to avoid hitting API too much
_otp_cache = {}
_last_otp_fetch = 0

def get_headers():
    return {
        "mauthapi": API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

def load_ranges():
    """Load ranges from ranges.json - maps country to rid"""
    try:
        for path in ["/data/ranges.json", "./ranges.json", "ranges.json"]:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    return data
    except:
        pass
    return {}

def get_rid_for_country(country_code, service="FACEBOOK"):
    """Get rid for country from ranges.json"""
    try:
        ranges = load_ranges()
        # ranges structure: {"FACEBOOK": {"NEPAL": "26134"}, "WHATSAPP": {...}}
        service_upper = service.upper()
        if service_upper in ranges:
            if country_code.upper() in ranges[service_upper]:
                return str(ranges[service_upper][country_code.upper()])
        # Try without service grouping
        # Also check if country_code directly in file
        for srv, countries in ranges.items():
            if isinstance(countries, dict):
                if country_code.upper() in countries:
                    return str(countries[country_code.upper()])
                # Try base name without _FB, _TT etc
                base = country_code.upper().split("_")[0]
                if base in countries:
                    return str(countries[base])
        # If ranges.json is simple dict: {"NEPAL": "26134"}
        if country_code.upper() in ranges:
            return str(ranges[country_code.upper()])
    except Exception as e:
        print(f"[RID LOOKUP ERR] {e}")
    return None

def create_order(service, country_code):
    """Allocate number from 2oo9.cloud API"""
    global _orders
    
    if not API_KEY:
        print("[2oo9] API Key not set! Set VOLTX_API_KEY in Railway Variables")
        return None
    
    rid = get_rid_for_country(country_code, service)
    
    if not rid:
        print(f"[2oo9] No rid found for {country_code} / {service}. Use /add {service} {country_code} <rid>")
        print(f"[2oo9] Example: /add FB NEPAL 26134")
        return None
    
    # Clean rid - remove XXX if present
    rid_clean = rid.replace("XXX", "").replace("xxx", "").strip()
    
    print(f"[2oo9] Creating order: service={service} country={country_code} rid={rid_clean}")
    
    try:
        url = f"{BASE_URL}/getnum"
        headers = get_headers()
        payload = {"rid": rid_clean}
        
        print(f"[2oo9] POST {url} rid={rid_clean}")
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        
        print(f"[2oo9] Response {resp.status_code}: {resp.text[:500]}")
        
        if resp.status_code != 200:
            print(f"[2oo9] HTTP Error {resp.status_code}")
            return None
        
        try:
            data = resp.json()
        except:
            print(f"[2oo9] Invalid JSON: {resp.text[:500]}")
            return None
        
        meta = data.get("meta", {})
        code = meta.get("code", 0)
        
        if code == 2946:
            print(f"[2oo9] Out of stock for rid {rid_clean}")
            return None
        
        if code != 200:
            print(f"[2oo9] API Error code={code} status={meta.get('status')} msg={data.get('message')}")
            return None
        
        payload_data = data.get("data")
        if not payload_data:
            print(f"[2oo9] No data in response")
            return None
        
        full_number = payload_data.get("full_number") or payload_data.get("no_plus_number") or payload_data.get("national_number")
        national = payload_data.get("national_number")
        no_plus = payload_data.get("no_plus_number")
        
        if not full_number:
            print(f"[2oo9] No number in data: {payload_data}")
            return None
        
        # Use no_plus_number as order_id for OTP lookup (e.g., 447404333228)
        order_id = no_plus or re.sub(r'\D', '', full_number)
        if not order_id:
            order_id = full_number
        
        # Clean number
        clean_number = full_number.replace("+", "").replace(" ", "")
        
        result = {
            "number": clean_number,
            "full_number": full_number,
            "national_number": national,
            "no_plus_number": no_plus,
            "id": order_id,
            "order_id": order_id,
            "country": country_code,
            "service": service,
            "panel": "2oo9",
            "rid": rid_clean
        }
        
        _orders[order_id] = result
        _orders[full_number] = result
        _orders[clean_number] = result
        
        print(f"[2oo9] Got number: {full_number} -> order_id={order_id}")
        return result
        
    except Exception as e:
        print(f"[2oo9 CREATE ERR] {e}")
        import traceback
        traceback.print_exc()
        return None

def get_otp(order_id):
    """Get OTP from /success-otp endpoint"""
    global _otp_cache, _last_otp_fetch
    
    if not API_KEY:
        print("[2oo9 OTP] No API key")
        return None
    
    # order_id is the phone number (no_plus_number)
    search_number = str(order_id).replace("+", "").replace(" ", "").strip()
    
    print(f"[2oo9 OTP] Searching OTP for {search_number}")
    
    try:
        # Check cache first (5 sec cache as per docs)
        now = time.time()
        if now - _last_otp_fetch < 5 and search_number in _otp_cache:
            cached = _otp_cache[search_number]
            if now - cached.get("_time", 0) < 10:
                print(f"[2oo9 OTP] Using cached OTP for {search_number}")
                return cached.get("otp")
        
        url = f"{BASE_URL}/success-otp"
        headers = get_headers()
        
        resp = requests.get(url, headers=headers, timeout=15)
        
        print(f"[2oo9 OTP] GET {url} -> {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"[2oo9 OTP] HTTP {resp.status_code}: {resp.text[:300]}")
            return None
        
        try:
            data = resp.json()
        except:
            print(f"[2oo9 OTP] Invalid JSON")
            return None
        
        meta = data.get("meta", {})
        if meta.get("code") != 200:
            print(f"[2oo9 OTP] API Error: {meta}")
            return None
        
        payload = data.get("data", {})
        otps = payload.get("otps", [])
        
        if not otps:
            print(f"[2oo9 OTP] No OTPs yet, got {len(otps)} total")
            return None
        
        # Find OTP for our number
        for otp_entry in otps:
            otp_number = str(otp_entry.get("number", "")).replace("+", "").replace(" ", "")
            if otp_number == search_number or search_number in otp_number or otp_number in search_number:
                message = otp_entry.get("message", "")
                # Extract OTP digits from message
                # Look for 4-8 digit code
                match = re.search(r'\b(\d{4,8})\b', message)
                if match:
                    otp_code = match.group(1)
                    print(f"[2oo9 OTP FOUND] {search_number} -> {otp_code} from: {message[:100]}")
                    _otp_cache[search_number] = {"otp": otp_code, "_time": now, "message": message}
                    _last_otp_fetch = now
                    return otp_code
                # If no clear code, try to extract any digits
                digits = re.findall(r'\d{4,8}', message)
                if digits:
                    # Take the most likely OTP (usually 4-6 digits, not part of phone)
                    for d in digits:
                        if d != otp_number and len(d) >= 4:
                            print(f"[2oo9 OTP FOUND] {search_number} -> {d} from: {message[:100]}")
                            _otp_cache[search_number] = {"otp": d, "_time": now, "message": message}
                            _last_otp_fetch = now
                            return d
        
        print(f"[2oo9 OTP] No OTP for {search_number} in {len(otps)} entries")
        # Debug: show first few OTPs
        for entry in otps[:3]:
            print(f"  OTP entry: {entry.get('number')} -> {entry.get('message')[:50]}")
        
        _last_otp_fetch = now
        return None
        
    except Exception as e:
        print(f"[2oo9 OTP ERR] {e}")
        import traceback
        traceback.print_exc()
        return None

def get_all_countries(service):
    """Get countries from ranges.json"""
    try:
        ranges = load_ranges()
        countries = []
        service_upper = service.upper()
        
        # If service exists in ranges
        if service_upper in ranges and isinstance(ranges[service_upper], dict):
            countries = list(ranges[service_upper].keys())
        else:
            # Collect from all services
            for srv, cmap in ranges.items():
                if isinstance(cmap, dict):
                    for c in cmap.keys():
                        if c not in countries:
                            countries.append(c)
        
        # Also include base names
        if not countries:
            # Fallback - try to read directly
            for srv, cmap in ranges.items():
                if isinstance(cmap, dict):
                    countries.extend(cmap.keys())
                elif isinstance(cmap, str):
                    countries.append(srv)
        
        # Remove duplicates, keep unique
        unique = []
        seen = set()
        for c in countries:
            base = c.upper()
            if base not in seen:
                unique.append(base)
                seen.add(base)
        
        print(f"[2oo9] Countries for {service}: {unique}")
        return unique if unique else ["NEPAL", "USA", "BD"]
    except Exception as e:
        print(f"[2oo9 GET COUNTRIES ERR] {e}")
        return ["NEPAL_FB", "USA", "BD"]

def get_display_name(country_code):
    names = {
        "NEPAL": "Nepal", "NEPAL_FB": "Nepal",
        "USA": "USA", "USA_FB": "USA",
        "BD": "Bangladesh", "BANGLADESH": "Bangladesh",
        "UK": "UK", "GB": "UK",
        "MOZAMBIQUE": "Mozambique", "MYANMAR": "Myanmar",
        "CAMEROON": "Cameroon", "CAMBODIA": "Cambodia"
    }
    return names.get(country_code.upper(), country_code.replace("_", " ").title())

print("[PANEL] 2oo9.cloud ONLY - Voltx API")
print(f"[PANEL] API Key: {'Set' if API_KEY else 'NOT SET - Set VOLTX_API_KEY in Railway!'}")
print(f"[PANEL] Base: {BASE_URL}")
