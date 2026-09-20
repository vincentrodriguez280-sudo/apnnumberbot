
import os
import requests
import json
import time
import random
import re
from bs4 import BeautifulSoup

# ========== 151.80.19.204 PANEL - WITH MATH CAPTCHA (jog biyog) ==========
# User said: panel login e jog biyog captcha thake

NEW_PANEL_URL = "http://151.80.19.204"
NEW_PANEL_LOGIN = f"{NEW_PANEL_URL}/ints/login"

PANEL_151_USER = os.getenv("PANEL_151_USER", "")
PANEL_151_PASS = os.getenv("PANEL_151_PASS", "")

_session_151 = None
_numbers_cache_151 = {
    "numbers": [],
    "last_fetch": 0,
}

def solve_math_captcha(text, soup=None):
    """Solve jog biyog captcha like 2+3, 5-2, etc"""
    try:
        print(f"[CAPTCHA] Trying to solve from text: {text[:1000]}")
        
        # Common patterns for math captcha
        patterns = [
            r'(\d+)\s*\+\s*(\d+)\s*=\s*\?',
            r'(\d+)\s*\-\s*(\d+)\s*=\s*\?',
            r'(\d+)\s*\+\s*(\d+)',
            r'(\d+)\s*\-\s*(\d+)',
            r'(\d+)\s*\*\s*(\d+)',
            r'(\d+)\s*x\s*(\d+)',
            r'What is (\d+)\s*\+\s*(\d+)',
            r'What is (\d+)\s*\-\s*(\d+)',
            r'(\d+)\s*plus\s*(\d+)',
            r'(\d+)\s*minus\s*(\d+)',
            r'যোগ\s*(\d+)\s*\+\s*(\d+)',  # Bengali
            r'বিয়োগ\s*(\d+)\s*\-\s*(\d+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if isinstance(match, tuple) and len(match) >= 2:
                        a, b = int(match[0]), int(match[1])
                        # Determine operation from pattern
                        if '+' in pattern or 'plus' in pattern.lower() or 'যোগ' in pattern:
                            result = a + b
                            print(f"[CAPTCHA SOLVED] {a} + {b} = {result}")
                            return result
                        elif '-' in pattern or 'minus' in pattern.lower() or 'বিয়োগ' in pattern:
                            result = a - b
                            print(f"[CAPTCHA SOLVED] {a} - {b} = {result}")
                            return result
                        elif '*' in pattern or 'x' in pattern.lower():
                            result = a * b
                            print(f"[CAPTCHA SOLVED] {a} * {b} = {result}")
                            return result
                        else:
                            # Try to detect from text around match
                            # Look for + or - between numbers in original text
                            full_match = f"{match[0]} + {match[1]}" if '+' in text else f"{match[0]} - {match[1]}"
                            if '+' in text[ max(0, text.find(match[0])-5) : text.find(match[1])+5 ]:
                                result = a + b
                                print(f"[CAPTCHA SOLVED] {a} + {b} = {result}")
                                return result
                            else:
                                result = a - b if a >= b else a + b
                                print(f"[CAPTCHA SOLVED] {a} +/- {b} = {result}")
                                return result
                except Exception as e:
                    print(f"[CAPTCHA MATCH ERR] {e}")
                    continue
        
        # Try to find captcha in soup
        if soup:
            # Look for elements that might contain captcha
            captcha_elements = soup.find_all(text=re.compile(r'\d+\s*[\+\-\*]\s*\d+'))
            for elem in captcha_elements:
                print(f"[CAPTCHA ELEM] {elem}")
                for pattern in patterns:
                    m = re.search(pattern, str(elem))
                    if m:
                        try:
                            a, b = int(m.group(1)), int(m.group(2))
                            if '+' in m.group(0):
                                result = a + b
                            elif '-' in m.group(0):
                                result = a - b
                            else:
                                result = a + b
                            print(f"[CAPTCHA SOLVED from elem] {a} {'+' if '+' in m.group(0) else '-'} {b} = {result}")
                            return result
                        except:
                            continue
            
            # Look for input near captcha text
            # Common: captcha image or text near input
            inputs = soup.find_all('input')
            for inp in inputs:
                # Check placeholder or nearby text
                placeholder = inp.get('placeholder', '').lower()
                if 'captcha' in placeholder or 'result' in placeholder or 'answer' in placeholder:
                    # Find nearby text with math
                    parent = inp.parent
                    if parent:
                        parent_text = parent.get_text()
                        for pattern in patterns:
                            m = re.search(pattern, parent_text)
                            if m:
                                try:
                                    a, b = int(m.group(1)), int(m.group(2))
                                    result = a + b if '+' in m.group(0) else a - b
                                    print(f"[CAPTCHA SOLVED near input] {a} {'+' if '+' in m.group(0) else '-'} {b} = {result}")
                                    return result
                                except:
                                    continue
        
        # Try simple: find any "X + Y" or "X - Y" in text
        simple_math = re.findall(r'(\d+)\s*([\+\-])\s*(\d+)', text)
        for a, op, b in simple_math:
            try:
                a, b = int(a), int(b)
                if op == '+':
                    result = a + b
                else:
                    result = a - b
                print(f"[CAPTCHA SIMPLE] {a} {op} {b} = {result}")
                return result
            except:
                continue
        
        print("[CAPTCHA] Could not solve captcha")
        return None
        
    except Exception as e:
        print(f"[CAPTCHA SOLVE ERR] {e}")
        import traceback
        traceback.print_exc()
        return None

def get_session_151():
    """Login to 151 panel with math captcha solving"""
    global _session_151
    try:
        # Check existing session
        if _session_151:
            try:
                test = _session_151.get(f"{NEW_PANEL_URL}/ints/", timeout=5)
                if test.status_code == 200 and "login" not in test.url.lower():
                    print("[151 SESSION] Existing session valid")
                    return _session_151
            except:
                pass
        
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        
        print(f"[151 LOGIN] Fetching login page: {NEW_PANEL_LOGIN}")
        login_page = session.get(NEW_PANEL_LOGIN, timeout=15)
        print(f"[151 LOGIN PAGE] Status: {login_page.status_code}, Length: {len(login_page.text)}")
        
        soup = BeautifulSoup(login_page.text, 'html.parser')
        
        # Find login form
        csrf_token = None
        # Common CSRF field names
        for csrf_name in ['_token', 'csrf_token', '_csrf', 'csrf', 'token']:
            csrf_input = soup.find('input', {'name': csrf_name})
            if csrf_input:
                csrf_token = csrf_input.get('value')
                print(f"[151 CSRF] Found {csrf_name}: {csrf_token[:30] if csrf_token else 'None'}")
                break
        
        # Solve math captcha
        captcha_answer = solve_math_captcha(login_page.text, soup)
        print(f"[151 CAPTCHA ANSWER] {captcha_answer}")
        
        # Try different login field combinations
        # Common field names for user, pass, captcha
        user_fields = ['username', 'email', 'user', 'login', 'phone']
        pass_fields = ['password', 'pass', 'pwd']
        captcha_fields = ['captcha', 'captcha_result', 'answer', 'result', 'math', 'security_code', 'verify', 'captcha_code', 'captch', 'code']
        
        # Build login data variants
        login_variants = []
        
        for u_field in user_fields:
            for p_field in pass_fields:
                base = {u_field: PANEL_151_USER, p_field: PANEL_151_PASS}
                if csrf_token:
                    base['_token'] = csrf_token
                    base['csrf_token'] = csrf_token
                
                # Add captcha if solved
                if captcha_answer is not None:
                    for c_field in captcha_fields:
                        variant = base.copy()
                        variant[c_field] = str(captcha_answer)
                        login_variants.append(variant)
                
                # Also try without captcha (maybe not required for API)
                login_variants.append(base.copy())
        
        # Also try with common captcha field names specifically
        if captcha_answer is not None:
            print(f"[151 LOGIN] Trying {len(login_variants)} variants with captcha={captcha_answer}")
        else:
            print(f"[151 LOGIN] Trying {len(login_variants)} variants without captcha (captcha not solved)")
        
        for i, login_data in enumerate(login_variants[:15]):  # Try first 15 variants
            try:
                print(f"[151 TRY {i+1}] Fields: {list(login_data.keys())} | Data: { {k: v[:20] if k != 'password' and k != 'pass' else '***' for k,v in login_data.items() } }")
                
                # Try POST
                resp = session.post(NEW_PANEL_LOGIN, data=login_data, timeout=15, allow_redirects=True)
                print(f"[151 RESP {i+1}] Status: {resp.status_code}, URL: {resp.url}, Length: {len(resp.text)}")
                print(f"[151 RESP TEXT {i+1}] {resp.text[:1000]}")
                
                # Check if login success
                # Success indicators: redirected to dashboard, contains logout, contains numbers, no login form
                if resp.status_code in [200, 302]:
                    # Check URL
                    if "login" not in resp.url.lower() or "dashboard" in resp.url.lower() or "ints" in resp.url.lower() and "login" not in resp.url.lower():
                        # Check content
                        lower_text = resp.text.lower()
                        if any(x in lower_text for x in ['logout', 'dashboard', 'numbers', 'sms', 'inbox', 'welcome']):
                            if 'login' not in lower_text[:2000] or 'invalid' not in lower_text[:1000]:
                                print(f"[151 LOGIN SUCCESS with variant {i+1}]")
                                _session_151 = session
                                return session
                
                # Check for error messages
                if 'invalid' in resp.text.lower() or 'error' in resp.text.lower() or 'wrong' in resp.text.lower():
                    print(f"[151 LOGIN FAILED - Invalid credentials or captcha]")
                    # If invalid captcha, try to re-solve
                    new_captcha = solve_math_captcha(resp.text, BeautifulSoup(resp.text, 'html.parser'))
                    if new_captcha and new_captcha != captcha_answer:
                        print(f"[151 NEW CAPTCHA] {new_captcha}, retrying")
                        captcha_answer = new_captcha
                        # Update login data with new captcha
                        for c_field in captcha_fields:
                            if c_field in login_data:
                                login_data[c_field] = str(new_captcha)
                
            except Exception as e:
                print(f"[151 VARIANT {i+1} ERR] {e}")
                continue
        
        print("[151 LOGIN] All variants failed")
        return None
        
    except Exception as e:
        print(f"[151 GET SESSION ERR] {e}")
        import traceback
        traceback.print_exc()
        return None

def fetch_numbers_from_151_panel():
    """Fetch bulk numbers from 151 panel"""
    global _numbers_cache_151
    try:
        if time.time() - _numbers_cache_151["last_fetch"] < 60 and _numbers_cache_151["numbers"]:
            print(f"[151 CACHE] Using {len(_numbers_cache_151['numbers'])} cached numbers")
            return _numbers_cache_151["numbers"]
        
        session = get_session_151()
        if not session:
            print("[151 FETCH] No session")
            return []
        
        numbers = []
        endpoints = [
            f"{NEW_PANEL_URL}/ints/",
            f"{NEW_PANEL_URL}/ints/dashboard",
            f"{NEW_PANEL_URL}/ints/numbers",
            f"{NEW_PANEL_URL}/ints/sms",
            f"{NEW_PANEL_URL}/",
        ]
        
        for endpoint in endpoints:
            try:
                print(f"[151 FETCH] {endpoint}")
                resp = session.get(endpoint, timeout=15)
                print(f"[151 FETCH RESP] {endpoint} -> {resp.status_code}, len={len(resp.text)}")
                
                if resp.status_code != 200:
                    continue
                
                # Find phone numbers
                import re
                patterns = [
                    r'\+?258\d{9,12}',
                    r'\+?95\d{8,12}',
                    r'\+?977\d{9,12}',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, resp.text)
                    numbers.extend(matches)
                
                # Parse HTML
                try:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for elem in soup.find_all(['td', 'div', 'span']):
                        txt = elem.get_text().strip()
                        digits = re.sub(r'\D', '', txt)
                        if len(digits) >= 10 and len(digits) <= 15:
                            if digits.startswith(('258', '95', '977', '237', '1')):
                                numbers.append(txt)
                except:
                    pass
                    
            except Exception as e:
                print(f"[151 ENDPOINT ERR {endpoint}] {e}")
                continue
        
        # Clean
        cleaned = []
        seen = set()
        for num in numbers:
            clean = re.sub(r'[^\d+]', '', str(num)).strip()
            if clean and clean not in seen and len(clean) >= 10:
                seen.add(clean)
                cleaned.append(clean)
        
        print(f"[151 FINAL] {len(cleaned)} unique numbers")
        
        _numbers_cache_151["numbers"] = cleaned
        _numbers_cache_151["last_fetch"] = time.time()
        
        # Save to file
        try:
            path = "/data/numbers_151.txt" if os.path.exists("/data") else "numbers_151.txt"
            with open(path, "w") as f:
                for n in cleaned:
                    f.write(n + "\n")
        except:
            pass
        
        return cleaned
        
    except Exception as e:
        print(f"[151 FETCH ERR] {e}")
        import traceback
        traceback.print_exc()
        return []

def create_order_151_bulk(service, country_code):
    """Create order - 8 numbers bulk"""
    try:
        all_numbers = fetch_numbers_from_151_panel()
        if not all_numbers:
            print("[151 BULK] No numbers")
            return None
        
        country_prefixes = {
            "MOZAMBIQUE": "258",
            "MOZAMBIQUE_TT": "258",
            "MYANMAR": "95",
            "MYANMAR_TT": "95",
            "NEPAL": "977",
            "NEPAL_FB": "977",
            "CAMEROON": "237",
        }
        
        prefix = country_prefixes.get(country_code.upper())
        filtered = [n for n in all_numbers if prefix in re.sub(r'\D', '', n)] if prefix else all_numbers
        if not filtered:
            filtered = all_numbers
        
        if not filtered:
            return None
        
        number = random.choice(filtered)
        if number in _numbers_cache_151["numbers"]:
            _numbers_cache_151["numbers"].remove(number)
        
        order_id = f"151_{int(time.time())}_{random.randint(1000,9999)}"
        
        order_info = {
            "number": number,
            "id": order_id,
            "country": country_code,
            "service": service,
            "panel": "151_bulk",
            "time": time.time()
        }
        
        print(f"[151 BULK ORDER] {country_code} -> {number}")
        return order_info
        
    except Exception as e:
        print(f"[151 BULK ORDER ERR] {e}")
        return None

def get_otp_151_bulk(order_id):
    """Get OTP by scraping inbox"""
    try:
        session = get_session_151()
        if not session:
            return None
        
        endpoints = [
            f"{NEW_PANEL_URL}/ints/",
            f"{NEW_PANEL_URL}/ints/sms",
            f"{NEW_PANEL_URL}/ints/inbox",
        ]
        
        for endpoint in endpoints:
            try:
                resp = session.get(endpoint, timeout=15)
                if resp.status_code != 200:
                    continue
                
                # Find OTP
                otps = re.findall(r'\b\d{4,8}\b', resp.text)
                for otp in otps:
                    if len(otp) >= 4 and len(otp) <= 8:
                        # Check context
                        pos = resp.text.find(otp)
                        ctx = resp.text[max(0, pos-50):pos+50].lower()
                        if any(k in ctx for k in ['code', 'otp', 'facebook', 'fb', 'verification']):
                            print(f"[151 OTP] {otp} from {endpoint}")
                            return otp
            except:
                continue
        
        return None
    except Exception as e:
        print(f"[151 OTP ERR] {e}")
        return None

# ========== MAIN ==========

def get_all_countries(service):
    return ["NEPAL_FB", "MOZAMBIQUE", "MOZAMBIQUE_TT", "MYANMAR", "MYANMAR_TT", "CAMEROON", "USA", "BD"]

def get_display_name(code):
    names = {
        "NEPAL_FB": "Nepal",
        "MOZAMBIQUE": "Mozambique",
        "MOZAMBIQUE_TT": "Mozambique",
        "MYANMAR": "Myanmar",
        "MYANMAR_TT": "Myanmar",
        "CAMEROON": "Cameroon",
        "USA": "USA",
        "BD": "Bangladesh",
    }
    return names.get(code.upper(), code.replace("_", " ").title())

_orders_store = {}

def create_order(service, country_code):
    print(f"[CREATE ORDER] {service} {country_code}")
    
    # Try 151 bulk
    try:
        result = create_order_151_bulk(service, country_code)
        if result:
            _orders_store[result["id"]] = result
            return result
    except Exception as e:
        print(f"[ORDER 151 ERR] {e}")
    
    # Fallback file
    try:
        base_dir = "/data" if os.path.exists("/data") else "."
        file_map = {
            "MOZAMBIQUE": "numbers_mozambique.txt",
            "MOZAMBIQUE_TT": "numbers_mozambique.txt",
            "MYANMAR": "numbers_myanmar.txt",
            "MYANMAR_TT": "numbers_myanmar.txt",
            "NEPAL": "numbers_nepal.txt",
            "NEPAL_FB": "numbers_nepal.txt",
        }
        fname = file_map.get(country_code.upper(), "numbers.txt")
        fpath = os.path.join(base_dir, fname)
        
        if os.path.exists(fpath):
            with open(fpath, 'r') as f:
                lines = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#") and any(c.isdigit() for c in l)]
                if lines:
                    number = lines[0]
                    remaining = lines[1:]
                    with open(fpath, 'w') as fw:
                        for ln in remaining:
                            fw.write(ln + "\n")
                    
                    order_id = f"file_{int(time.time())}_{random.randint(1000,9999)}"
                    result = {"number": number, "id": order_id, "country": country_code, "service": service, "panel": "file"}
                    _orders_store[order_id] = result
                    print(f"[ORDER FILE] {fname} -> {number}")
                    return result
    except Exception as e:
        print(f"[ORDER FILE ERR] {e}")
    
    return None

def get_otp(order_id):
    if order_id in _orders_store and "151" in _orders_store[order_id].get("panel", ""):
        return get_otp_151_bulk(order_id)
    
    try:
        otp = get_otp_151_bulk(order_id)
        if otp:
            return otp
    except:
        pass
    
    return None

print("[PANEL] Loaded - 151.80.19.204 WITH MATH CAPTCHA SOLVER (jog biyog)")
print(f"[PANEL] User: {PANEL_151_USER[:3]}... | Pass set: {bool(PANEL_151_PASS)}")
