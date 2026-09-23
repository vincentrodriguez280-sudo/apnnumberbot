
import os
import requests
import json
import re
import time

BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"
API_KEY = os.getenv("VOLTX_API_KEY", "") or os.getenv("MAUTHAPI_KEY", "") or os.getenv("API_KEY_2OO9", "") or os.getenv("PANEL_API_KEY", "")

_orders = {}
_otp_cache = {}
_last_otp_fetch = 0

def get_headers():
    return {"mauthapi": API_KEY, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}

def load_ranges():
    for path in ["/data/ranges.json", "./ranges.json", "ranges.json", "/app/ranges.json", "/app/data/ranges.json"]:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    if data:
                        return data
            except:
                pass
    return {}

def get_rid_for_country(country_code, service="FACEBOOK"):
    ranges = load_ranges()
    if not ranges:
        return None
    service_upper = service.upper()
    country_upper = country_code.upper().strip()
    if service_upper in ranges and isinstance(ranges[service_upper], dict):
        if country_upper in ranges[service_upper]:
            return str(ranges[service_upper][country_upper])
    for srv, cmap in ranges.items():
        if isinstance(cmap, dict) and country_upper in cmap:
            return str(cmap[country_upper])
    if country_upper in ranges and isinstance(ranges[country_upper], (str, int)):
        return str(ranges[country_upper])
    return None

def create_order(service, country_code):
    global _orders
    if not API_KEY:
        print("[ERROR] VOLTX_API_KEY not set!")
        return None
    rid = get_rid_for_country(country_code, service)
    if not rid:
        print(f"[ERROR] No rid for {country_code}")
        return None
    rid_clean = rid.replace("XXX", "").strip()
    print(f"[GETNUM] {service}/{country_code} rid={rid_clean}")
    try:
        url = f"{BASE_URL}/getnum"
        resp = requests.post(url, json={"rid": rid_clean}, headers=get_headers(), timeout=20)
        print(f"[GETNUM] {resp.status_code}: {resp.text[:500]}")
        if resp.status_code != 200:
            return None
        data = resp.json()
        meta = data.get("meta", {})
        if meta.get("code") == 2946:
            print(f"[GETNUM] Out of stock rid={rid_clean}")
            return None
        if meta.get("code") != 200:
            return None
        payload = data.get("data")
        if not payload:
            return None
        full_number = payload.get("full_number") or payload.get("no_plus_number")
        no_plus = payload.get("no_plus_number") or re.sub(r'\D', '', full_number or "")
        if not full_number:
            return None
        result = {"number": no_plus, "full_number": full_number, "no_plus_number": no_plus, "id": no_plus, "country": country_code, "service": service, "rid": rid_clean}
        _orders[no_plus] = result
        print(f"[GETNUM] OK: {full_number}")
        return result
    except Exception as e:
        print(f"[GETNUM ERR] {e}")
        return None

def get_otp(order_id):
    global _otp_cache, _last_otp_fetch
    if not API_KEY:
        return None
    search_number = str(order_id).replace("+", "").strip()
    try:
        now = time.time()
        # Reduced cache - only 2 sec to avoid missing OTPs
        # Cache only for same number, and only if OTP already found
        if search_number in _otp_cache:
            cached = _otp_cache[search_number]
            # If we already found OTP for this number, return it (avoid duplicate fetch)
            # But only if cached recently (5 min)
            if now - cached.get("_time", 0) < 300:
                # Return cached OTP if we already have it - don't refetch
                # This prevents missing but also avoids re-sending same OTP
                # Actually we should return None if already sent, to avoid duplicate
                # But for watcher that already returned, it won't check again
                pass
        
        url = f"{BASE_URL}/success-otp"
        resp = requests.get(url, headers=get_headers(), timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("meta", {}).get("code") != 200:
            return None
        otps = data.get("data", {}).get("otps", [])
        # Debug log
        if len(otps) > 0:
            print(f"[OTP] Checking {search_number} in {len(otps)} total OTPs")
        
        for entry in otps:
            otp_number = str(entry.get("number", "")).replace("+", "").strip()
            # Match exact or contains
            if otp_number == search_number or search_number in otp_number or otp_number in search_number:
                msg = entry.get("message", "")
                # Try multiple patterns for OTP
                # Pattern 1: 4-8 digit code
                m = re.search(r'\b(\d{4,8})\b', msg)
                if m:
                    code = m.group(1)
                    # Avoid returning phone number parts as OTP
                    if code != otp_number and len(code) >= 4 and len(code) <= 8:
                        # Check if code is not part of phone number
                        if code not in otp_number or len(otp_number) - len(code) > 4:
                            print(f"[OTP FOUND] {search_number} -> {code} | {msg[:80]}")
                            _otp_cache[search_number] = {"otp": code, "_time": now, "msg": msg}
                            _last_otp_fetch = now
                            return code
                
                # Pattern 2: Facebook style "FB-123456" or "123456 is your code"
                m2 = re.findall(r'(?:FB-|code is |OTP is |code:)\s*(\d{4,8})', msg, re.I)
                for code in m2:
                    if len(code) >= 4:
                        print(f"[OTP FOUND2] {search_number} -> {code}")
                        _otp_cache[search_number] = {"otp": code, "_time": now}
                        return code
        
        _last_otp_fetch = now
        return None
    except Exception as e:
        print(f"[OTP ERR] {e}")
        import traceback
        traceback.print_exc()
        return None

def get_all_countries(service):
    ranges = load_ranges()
    service_upper = service.upper()
    countries = []
    if service_upper in ranges and isinstance(ranges[service_upper], dict):
        countries = list(ranges[service_upper].keys())
    else:
        for srv, cmap in ranges.items():
            if isinstance(cmap, dict):
                for c in cmap.keys():
                    if c not in countries:
                        countries.append(c)
    unique = []
    seen = set()
    for c in countries:
        cu = c.upper().strip()
        if cu and cu not in seen:
            unique.append(cu)
            seen.add(cu)
    return unique

def get_display_name(country_code):
    try:
        code = country_code.upper().strip()
        clean = code.replace("_FB", "").replace("_WS", "").replace("_NEW_ACCOUNT", " NEW ACCOUNT").replace("_", " ")
        clean = re.sub(r'(?i)(NEWACCOUNT)', ' NEW ACCOUNT', clean)
        return " ".join([w.title() for w in clean.split()]).strip()
    except:
        return country_code.replace("_", " ").title()

print("[PANEL] Voltx ONLY")
print(f"[PANEL] API Key: {'SET' if API_KEY else 'NOT SET'}")
