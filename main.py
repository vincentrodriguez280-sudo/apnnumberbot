import os, json, asyncio, shutil, re
from datetime import datetime, date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton, CopyTextButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from panel import create_order, get_otp, get_all_countries, get_display_name

print("[BOT] Starting with fixed OTP copy + service name + Number/Channel buttons")

TOKEN = os.getenv("BOT_TOKEN")
MUST_JOIN = ["@APNOfficial", "@APNOTP", "@Proxystore999"]
CH1 = "https://t.me/APNOfficial"
CH2 = "https://t.me/APNOTP"
CH3 = "https://t.me/Proxystore999"
OTP_GROUP = "https://t.me/APNOTP"
OTP_GROUP_ID = "@APNOTP"
SUPPORT_ID = "https://t.me/PolasChandra"
SERVICES = ["FACEBOOK", "WHATSAPP", "TIKTOK"]
COMMUNITY_URL = "https://t.me/APNOfficial"
NUMBER_BOT_URL = "https://t.me/APNNUMBERBOT"

# Railway volume - /data support
for p in ["/data", "/app/data", "."]:
    try:
        if os.path.exists(p) or p in ["/data", "/app/data"]:
            os.makedirs(p, exist_ok=True)
            if os.path.exists(p):
                BASE_DIR = p
                print(f"[DATA] Using {BASE_DIR} (Volume found)" if p=="/data" else f"[DATA] Using {BASE_DIR}")
                break
    except:
        continue
else:
    BASE_DIR = "."
    os.makedirs(BASE_DIR, exist_ok=True)

BAL_FILE = os.path.join(BASE_DIR, "balances.json")
TRAFFIC_FILE = os.path.join(BASE_DIR, "traffic.json")
SUCCESS_FILE = os.path.join(BASE_DIR, "success_traffic.json")
RANGES_FILE = os.path.join(BASE_DIR, "ranges.json")
MAINT_FILE = os.path.join(BASE_DIR, "maintenance.json")
ACTIVE_FILE = os.path.join(BASE_DIR, "active_numbers.json")
WALLET_FILE = os.path.join(BASE_DIR, "wallets.json")
SUBMIT_FILE = os.path.join(BASE_DIR, "submissions.json")
SUBMIT_TOGGLE_FILE = os.path.join(BASE_DIR, "submit_toggle.json")
SUBMIT_SHEET_FILE = os.path.join(BASE_DIR, "submitted_data.txt")

if not os.path.exists(RANGES_FILE) and os.path.exists("ranges.json"):
    try:
        shutil.copy("ranges.json", RANGES_FILE)
    except: pass

# ===== AUTO SYNC number files from Github to /data volume =====
# Railway te /data volume thakle Github er file /data te copy hobe na
# Tai auto copy system
def sync_number_files():
    """
    Sync number files from Github to /data
    FIXED: Don't recycle! If /data file exists, don't overwrite even if empty
    Because empty means numbers used up - recycling causes duplicate!
    Only copy if file doesn't exist at all
    """
    try:
        files_to_sync = ["numbers.txt", "numbers_mozambique.txt", "numbers_myanmar.txt", "numbers_nepal.txt"]
        for fname in files_to_sync:
            src_candidates = [f"./{fname}", f"{fname}", os.path.join(".", fname), f"/app/{fname}"]
            dst = os.path.join(BASE_DIR, fname)
            if BASE_DIR in ["/data", "/app/data"]:
                # Only copy if destination doesn't exist at all - DON'T overwrite empty!
                # Empty file means numbers finished - don't recycle!
                if not os.path.exists(dst):
                    for src in src_candidates:
                        if os.path.exists(src) and os.path.getsize(src) > 10:
                            try:
                                # Check src has real numbers
                                with open(src,'r') as sf:
                                    src_numbers = [l.strip() for l in sf.readlines() if l.strip() and not l.strip().startswith("#") and any(c.isdigit() for c in l)]
                                if len(src_numbers) > 0:
                                    shutil.copy(src, dst)
                                    print(f"[SYNC] Copied {src} -> {dst} ({len(src_numbers)} numbers)")
                                    break
                            except Exception as e:
                                print(f"[SYNC COPY ERR] {e}")
                                pass
                else:
                    # File exists in /data - check if it has numbers or only comments
                    # If only comments (0 numbers) and src has numbers, AND dst was never used (size small), copy
                    # But if dst was used and became empty, DON'T copy to avoid duplicate
                    try:
                        if os.path.getsize(dst) < 200:  # Small file, likely empty/template
                            with open(dst,'r') as f:
                                dst_numbers = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#") and any(c.isdigit() for c in l)]
                            if len(dst_numbers) == 0:
                                # Check if this is first time (template) vs used up
                                # If dst is template (contains # Example), allow copy from src with real numbers
                                with open(dst,'r') as f:
                                    dst_content = f.read()
                                if "# Example" in dst_content or "ADD YOUR" in dst_content:
                                    for src in src_candidates:
                                        if os.path.exists(src):
                                            with open(src,'r') as sf:
                                                src_content = sf.read()
                                                src_numbers = [l.strip() for l in src_content.split("\n") if l.strip() and not l.strip().startswith("#") and any(c.isdigit() for c in l)]
                                            # Only copy if src has REAL numbers (not just example)
                                            # Real numbers don't have # and have correct prefix
                                            real_src_numbers = [n for n in src_numbers if not n.startswith("#") and (n.startswith("258") or n.startswith("95") or n.startswith("977"))]
                                            if len(real_src_numbers) > 0 and len(real_src_numbers) > len(dst_numbers):
                                                # Check if src is not template
                                                if src_content.count("Example") < 2:
                                                    shutil.copy(src, dst)
                                                    print(f"[SYNC] Initial copy {src} -> {dst} ({len(real_src_numbers)} real numbers)")
                                                    break
                    except: pass
    except Exception as e:
        print(f"[SYNC ERR] {e}")
        import traceback
        traceback.print_exc()

sync_number_files()

ADMIN_ID = 1853202569
FLAGS = {
    "NEPAL": "🇳🇵", "NEPAL_FB": "🇳🇵",
    "CAMEROON": "🇨🇲", "GUINEA": "🇬🇳", "GUNIEA": "🇬🇳",
    "MADAGASCAR": "🇲🇬", "MONTENEGRO": "🇲🇪", "UKRAINE": "🇺🇦",
    "HAITI": "🇭🇹", "SIERRA_LEONE": "🇸🇱", "USA": "🇺🇸", "USA_FB": "🇺🇸",
    "MOROCCO": "🇲🇦", "NIGERIA": "🇳🇬", "MOZAMBIQUE": "🇲🇿", "MYANMAR": "🇲🇲", "MYANMAR_TT": "🇲🇲", "MOZAMBIQUE_TT": "🇲🇿", "ISRAEL": "🇮🇱",
    "BD": "🇧🇩", "BANGLADESH": "🇧🇩", "BANGLADESH_FB": "🇧🇩", "BD_FB": "🇧🇩", "HAD": "🇧🇩",
}
PRICES = {
    "NEPAL": "0.005$", "NEPAL_FB": "0.005$",
    "MOROCCO": "0.003$", "NIGERIA": "0.003$", "MOZAMBIQUE": "0.005$", "MYANMAR": "0.005$", "MYANMAR_TT": "0.005$", "MOZAMBIQUE_TT": "0.005$",
    "CAMEROON": "0.003$", "GUINEA": "0.003$", "MADAGASCAR": "0.003$",
    "MONTENEGRO": "0.003$", "UKRAINE": "0.003$", "HAITI": "0.003$",
    "SIERRA_LEONE": "0.003$", "USA": "0.003$", "USA_FB": "0.003$",
    "BD": "0.005$", "BANGLADESH": "0.005$", "BANGLADESH_FB": "0.005$", "BD_FB": "0.005$", "HAD": "0.005$", "MYANMAR_FB": "0.005$",
    "DEFAULT": "0.003$",
}

BASE_DIR_FALLBACK = "."
try:
    os.makedirs(BASE_DIR, exist_ok=True)
except:
    BASE_DIR = "."

def load_json(f, default):
    for path in [f, os.path.join(".", os.path.basename(f)), os.path.join(BASE_DIR_FALLBACK, os.path.basename(f))]:
        if os.path.exists(path):
            try:
                with open(path,'r') as fp: 
                    data = json.load(fp)
                    if data: 
                        return data
            except: continue
    return default

def save_json(f, data):
    for path in [f, os.path.join(".", os.path.basename(f))]:
        try:
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path,'w') as fp: json.dump(data, fp, indent=2)
        except: pass

def is_maintenance():
    return load_json(MAINT_FILE, {"enabled": False}).get("enabled", False)

def get_user(uid):
    db = load_json(BAL_FILE, {})
    uid=str(uid)
    if uid not in db:
        db[uid]={"balance":0.0,"requests":[],"total":0,"ref":0,"referrals":0,"level":1,"wallet_method":None,"wallet_address":None,"referred_by":None}
        save_json(BAL_FILE, db)
    if "referrals" not in db[uid]: db[uid]["referrals"]=0
    if "level" not in db[uid]: db[uid]["level"]=1
    if "wallet_method" not in db[uid]: db[uid]["wallet_method"]=None
    if "wallet_address" not in db[uid]: db[uid]["wallet_address"]=None
    if "referred_by" not in db[uid]: db[uid]["referred_by"]=None
    if "balance" not in db[uid]: db[uid]["balance"]=0.0
    return db[uid]

def save_user(uid, data):
    db = load_json(BAL_FILE, {})
    db[str(uid)]=data
    save_json(BAL_FILE, db)

backup_counter = {"count": 0}

def add_request(uid, country):
    user = get_user(uid)
    user["requests"].append(datetime.now().isoformat())
    user["total"]+=1
    save_user(uid, user)
    tr = load_json(TRAFFIC_FILE, {})
    tr[country] = tr.get(country,0)+1
    save_json(TRAFFIC_FILE, tr)

def add_success(country):
    tr = load_json(SUCCESS_FILE, {})
    tr[country] = tr.get(country,0)+1
    save_json(SUCCESS_FILE, tr)

def save_active_number(uid, number, country, service):
    db = load_json(ACTIVE_FILE, {})
    uid=str(uid)
    if uid not in db: db[uid]=[]
    db[uid].append({"number": number, "country": country, "service": service, "time": datetime.now().isoformat()})
    db[uid]=db[uid][-20:]
    save_json(ACTIVE_FILE, db)

def get_active_numbers(uid):
    db = load_json(ACTIVE_FILE, {})
    return db.get(str(uid), [])

def mask_number(num):
    n = num.replace(" ", "").replace("+", "").strip()
    if len(n) <= 6: return "+" + n
    return f"+{n[:4]}XXXXXX{n[-3:]}"

# ========== FIXED: OTP ONLY IN BUTTON + COPY WORKS + SERVICE NAME FIX ==========
def format_for_inbox(country_code, full_number, service, otp_code):
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    country_name = clean.replace("_", " ").title()
    flag = FLAGS.get(clean, FLAGS.get(clean.split("_")[0], "🌍"))
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    # Service name fix - TikTok na, asol service er nam
    if service.upper() in ["FACEBOOK", "FB", "NEPAL", "NEPAL_FB"]:
        service_display = "Facebook"
    elif service.upper() in ["TIKTOK", "TT", "MOZAMBIQUE", "MOZAMBIQUE_TT"]:
        service_display = "TikTok"
    else:
        service_display = service.title()
    if "NEPAL" in clean.upper():
        earn_text = "+$0.005"
    else:
        earn_text = "+$0.003"
    # OTP sudu button e thakbe, text e thakbe na
    text = f"{flag} {country_name}\n📞 `{full_number}`\n💼 Service: {service_display}\n💳 Earned: {earn_text}"
    # Copy button - CopyTextButton diye 1 click e copy hobe (Telegram native)
    try:
        keyboard = [[InlineKeyboardButton(f"🔑 {otp_digits}", copy_text=CopyTextButton(otp_digits))]]
    except:
        keyboard = [[InlineKeyboardButton(f"📋 Copy {otp_digits}", callback_data=f"copy_{otp_digits}")]]
    return text, InlineKeyboardMarkup(keyboard)

def format_for_group(country_code, full_number, service, otp_code):
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    masked = mask_number(full_number)
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    # Service name fix - TikTok na, jetar number niso otar lekha thakbe
    if service.upper() in ["FACEBOOK", "FB", "NEPAL", "NEPAL_FB"]:
        service_display = "Facebook"
    elif service.upper() in ["TIKTOK", "TT", "MOZAMBIQUE", "MOZAMBIQUE_TT"]:
        service_display = "TikTok"
    else:
        service_display = service.title()
    # OTP sudu button e, text e box e OTP thakbe na
    text = f"APN NUMBER BOT\n💳 #{clean} 📱 {service_display}\n\n╭─────────────────╮\n  {masked}\n╰─────────────────╯\n\n🗣 Language: #English"
    try:
        otp_btn = InlineKeyboardButton(f"🔓 {otp_digits}", copy_text=CopyTextButton(otp_digits))
    except:
        otp_btn = InlineKeyboardButton(f"🔓 {otp_digits}", callback_data=f"copy_{otp_digits}")
    # Panel lekha bad diye Channel, Channel er jaygay Number
    # Number click -> bot e jabe, Channel click -> channel e jabe
    keyboard = [
        [otp_btn],
        [InlineKeyboardButton("🔢 Number", url=NUMBER_BOT_URL), InlineKeyboardButton("📢 Channel", url=COMMUNITY_URL)]
    ]
    return text, InlineKeyboardMarkup(keyboard)

async def is_joined(user_id, context):
    if user_id == ADMIN_ID: return True
    for ch in MUST_JOIN:
        try:
            m = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status in ['left','kicked']: return False
        except: continue
    return True

async def otp_watcher(bot, order_id, user_id, number, service, country_code):
    print(f"[WATCHER START] {number} {order_id} {country_code}")
    # HAD panel needs slower checking due to rate limit - 8 sec interval
    is_had = "had" in order_id.lower() or "MOZAMBIQUE" in country_code.upper() or "BD" in country_code.upper() or "BANGLADESH" in country_code.upper()
    interval = 8 if is_had else 5
    max_checks = 112 if is_had else 180  # 15 min total for both (112*8=896s, 180*5=900s)
    print(f"[WATCHER] {number} interval={interval}s max={max_checks} (is_had={is_had})")
    for i in range(max_checks):
        await asyncio.sleep(interval)
        try:
            otp = await asyncio.to_thread(get_otp, order_id)
            if otp:
                print(f"[OTP FOUND] {number} -> {otp}")
                text_inbox, markup_inbox = format_for_inbox(country_code, number, service, otp)
                text_group, markup_group = format_for_group(country_code, number, service, otp)
                try:
                    await bot.send_message(chat_id=user_id, text=text_inbox, reply_markup=markup_inbox, parse_mode="Markdown")
                except:
                    await bot.send_message(chat_id=user_id, text=text_inbox, reply_markup=markup_inbox)
                try:
                    await bot.send_message(chat_id=OTP_GROUP_ID, text=text_group, reply_markup=markup_group, parse_mode="Markdown")
                except Exception as e:
                    print(f"[FAIL GROUP] {e}")
                user = get_user(user_id)
                if "NEPAL" in country_code.upper():
                    earn = 0.005
                else:
                    earn = 0.003
                user["balance"]+=earn
                save_user(user_id, user)
                backup_counter["count"] += 1
                if backup_counter["count"] >= 20:
                    backup_counter["count"] = 0
                    try:
                        await auto_backup_task(bot)
                    except: pass
                print(f"[BALANCE] User {user_id} +${earn} -> ${user['balance']:.4f} | {country_code} {service}")
                if user.get("referred_by"):
                    ref_user = get_user(user["referred_by"])
                    refs = ref_user.get("referrals",0)
                    if refs >= 5000: comm = 0.0100
                    elif refs >= 2000: comm = 0.0070
                    elif refs >= 500: comm = 0.0006
                    elif refs >= 100: comm = 0.0005
                    else: comm = 0.0002
                    ref_user["balance"]+=comm
                    save_user(user["referred_by"], ref_user)
                add_success(country_code)
                return
        except Exception as e:
            print(f"[WATCHER ERR] {e}")
    print(f"[TIMEOUT] {number}")

async def bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    reason = " ".join(context.args) if context.args else "Scheduled maintenance"
    save_json(MAINT_FILE, {"enabled": True, "reason": reason})
    await update.message.reply_text("🔴 Bot OFF")

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    save_json(MAINT_FILE, {"enabled": False})
    await update.message.reply_text("🟢 Bot ON")

async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    status = "🔴 OFF" if is_maintenance() else "🟢 ON"
    await update.message.reply_text(f"Bot Status: {status} | Path: {BASE_DIR}")

async def add_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    try:
        service = context.args[0].upper()
        name = context.args[1].upper()
        rid = context.args[2]
        if service == "FB": service = "FACEBOOK"
        if service == "WS": service = "WHATSAPP"
        data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
        if service not in data: data[service] = {}
        data[service][name] = rid
        save_json(RANGES_FILE, data)
        await update.message.reply_text(f"✅ Added {service} - {name} = {rid}")
    except:
        await update.message.reply_text("❌ Use: /add FB CAMEROON 23762")

async def del_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    try:
        service = context.args[0].upper()
        name = context.args[1].upper()
        if service == "FB": service = "FACEBOOK"
        if service == "WS": service = "WHATSAPP"
        data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
        if name in data.get(service, {}):
            del data[service][name]
            save_json(RANGES_FILE, data)
            await update.message.reply_text(f"🗑 Deleted {name}")
        else:
            await update.message.reply_text("❌ Not found")
    except:
        await update.message.reply_text("❌ Use: /del FB CAMEROON")

async def list_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
    txt = f"📋 Ranges ({BASE_DIR}):\n\n"
    for srv, ranges in data.items():
        txt += f"{srv}:\n"
        for n, r in ranges.items():
            txt += f"- {n} = {r}\n"
        txt += "\n"
    await update.message.reply_text(txt)

async def auto_backup_task(bot):
    try:
        if not os.path.exists(BAL_FILE): return
        db = load_json(BAL_FILE, {})
        count = len(db)
        total_bal = sum([u.get("balance",0) for u in db.values()])
        txt = f"🔄 Auto Backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n👥 Users: {count}\n💰 Total: ${total_bal:.4f}"
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=txt)
            await bot.send_document(chat_id=ADMIN_ID, document=open(BAL_FILE, 'rb'), filename=f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}_balances.json")
        except Exception as e:
            print(f"[AUTO BACKUP ERR] {e}")
    except Exception as e:
        print(f"[AUTO BACKUP ERR] {e}")

async def backup_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        db = load_json(BAL_FILE, {})
        count = len(db)
        total_bal = sum([u.get("balance",0) for u in db.values()])
        txt = f"💾 Backup Info (FREE MODE)\n\n📁 Path: {BAL_FILE}\n👥 Users: {count}\n💰 Total Balance: ${total_bal:.4f}\n📂 Also saved in: ./balances.json"
        await update.message.reply_text(txt)
        for fp in [BAL_FILE, "./balances.json"]:
            if os.path.exists(fp):
                try:
                    await update.message.reply_document(document=open(fp, 'rb'), filename="balances.json")
                    break
                except: continue
    except Exception as e:
        await update.message.reply_text(f"❌ Backup error: {e}")

async def restore_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    txt = f"📂 Data Path: {BASE_DIR} + ./\n\nFiles:\n"
    for fn in ["balances.json", "traffic.json", "success_traffic.json", "ranges.json", "wallets.json"]:
        found = []
        for base in [BASE_DIR, "."]:
            fp = os.path.join(base, fn)
            if os.path.exists(fp):
                size = os.path.getsize(fp)
                found.append(f"{base}/{fn} ({size}b)")
        if found:
            txt += f"✅ {fn}: {' , '.join(found)}\n"
        else:
            txt += f"❌ {fn}: not found\n"
    await update.message.reply_text(txt)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    # Check if it's a file submission (user in submit mode)
    if context.user_data.get("awaiting_file_submit") or (update.message.document and not (update.effective_user.id == ADMIN_ID and ("balances" in update.message.document.file_name.lower() or "backup" in update.message.document.file_name.lower()))):
        # This is a file submission from user
        if not is_file_submit_enabled():
            await update.message.reply_text("❌ File Submit is disabled")
            context.user_data["awaiting_file_submit"] = False
            return
        
        doc = update.message.document
        if not doc:
            return
        
        # Check file type - allow xls, xlsx, txt, csv, etc
        fname = doc.file_name.lower()
        allowed = ['xls', 'xlsx', 'txt', 'csv', 'doc', 'docx']
        is_allowed = any(fname.endswith(ext) for ext in allowed)
        
        # Also allow if user is in submit mode (any file)
        if not is_allowed and not context.user_data.get("awaiting_file_submit"):
            # If not in submit mode and not balances file, ignore
            if uid != ADMIN_ID:
                return
        
        # If admin uploading balances, handle as restore
        if uid == ADMIN_ID and ("balances" in fname or "backup" in fname):
            try:
                file = await context.bot.get_file(doc.file_id)
                for path in [BAL_FILE, "./balances.json"]:
                    try:
                        await file.download_to_drive(path)
                    except: pass
                db = load_json(BAL_FILE, {})
                await update.message.reply_text(f"✅ Restored! Users: {len(db)}")
            except Exception as e:
                await update.message.reply_text(f"❌ Restore failed: {e}")
            return
        
        # File submission - save ONLY content user gave, no time detail in exported file
        try:
            # Download file
            file = await context.bot.get_file(doc.file_id)
            # Save to submissions folder
            submit_dir = os.path.join(BASE_DIR, "submitted_files")
            os.makedirs(submit_dir, exist_ok=True)
            file_path = os.path.join(submit_dir, f"{uid}_{int(datetime.now().timestamp())}_{doc.file_name}")
            await file.download_to_drive(file_path)
            
            # Read content - expect UID PASS COOKIES format
            content_text = ""
            try:
                if fname.endswith('.txt') or fname.endswith('.csv'):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content_text = f.read()
                elif fname.endswith('.xls') or fname.endswith('.xlsx'):
                    try:
                        import pandas as pd
                        df = pd.read_excel(file_path)
                        # If Excel has 3 columns, convert to UID PASS COOKIES lines
                        if len(df.columns) >= 3:
                            lines = []
                            for _, row in df.iterrows():
                                uid = str(row.iloc[0])
                                pwd = str(row.iloc[1])
                                cookies = str(row.iloc[2])
                                lines.append(f"{uid}  {pwd}  {cookies}")
                                # Push to Google Sheet
                                push_to_google_sheet(uid, pwd, cookies)
                            content_text = "\n".join(lines)
                        else:
                            content_text = df.to_string()
                    except:
                        content_text = f"Excel file: {doc.file_name}"
                else:
                    content_text = f"File: {doc.file_name}"
            except:
                content_text = f"File: {doc.file_name}"
            
            if not content_text:
                content_text = f"File: {doc.file_name}"
            
            # Parse and push to Google Sheet if it's UID PASS COOKIES format
            try:
                import re
                for line in content_text.split('\n'):
                    line = line.strip()
                    if not line or len(line) < 10:
                        continue
                    parts = re.split(r'\s{2,}|\t', line)
                    if len(parts) >= 3:
                        uid_val = parts[0].strip()
                        pwd_val = parts[1].strip()
                        cookies_val = " ".join(parts[2:]).strip()
                    else:
                        tokens = line.split()
                        if len(tokens) >= 3:
                            uid_val = tokens[0]
                            pwd_val = tokens[1]
                            cookies_val = " ".join(tokens[2:])
                        else:
                            continue
                    if uid_val and pwd_val and cookies_val:
                        push_to_google_sheet(uid_val, pwd_val, cookies_val)
            except: pass
            
            submissions = load_json(SUBMIT_FILE, [])
            submission = {
                "serial": len(submissions) + 1,
                "user_id": str(uid),
                "username": update.effective_user.username or update.effective_user.first_name or "N/A",
                "time": datetime.now().isoformat(),
                "type": f"file - {doc.file_name}",
                "content": content_text,
                "file_path": file_path,
                "file_name": doc.file_name
            }
            submissions.append(submission)
            save_json(SUBMIT_FILE, submissions)
            
            # Append to sheet - ONLY content, no time detail
            try:
                with open(SUBMIT_SHEET_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{content_text}\n")
            except: pass
            
            # Count lines in file
            file_lines = [l.strip() for l in content_text.split('\n') if l.strip()]
            file_line_count = len(file_lines)
            
            context.user_data["awaiting_file_submit"] = False
            await update.message.reply_text(f"✅ File submitted!\n\n📊 {file_line_count} lines saved from {doc.file_name}\nXLS e {file_line_count} ta row asbe", reply_markup=bottom_keyboard())
            
            # Notify admin
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"📁 New Submit #{submission['serial']} from {uid} - {doc.file_name} ({file_line_count} lines)")
            except: pass
            
        except Exception as e:
            await update.message.reply_text(f"❌ File submit failed: {e}")
        return

async def handle_restore_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Legacy - now handled in handle_document
    await handle_document(update, context)
    return
    if update.effective_user.id != ADMIN_ID: return
    if not update.message.document: return
    fname = update.message.document.file_name
    if "balances" not in fname.lower() and "backup" not in fname.lower():
        await update.message.reply_text("❌ Please upload balances.json or backup_*.json")
        return
    try:
        file = await context.bot.get_file(update.message.document.file_id)
        for path in [BAL_FILE, "./balances.json"]:
            try:
                await file.download_to_drive(path)
            except: pass
        db = load_json(BAL_FILE, {})
        await update.message.reply_text(f"✅ Restored! Users: {len(db)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Restore failed: {e}")

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")

def main_menu_keyboard(anim_frame=0):
    frames = [
        ["📱", "🌍", "📊", "👨‍💼", "👥", "💰"],
        ["📲", "🌎", "📈", "👨‍💻", "👤", "💳"],
        ["📳", "🌏", "📉", "🧑‍💼", "👫", "💵"],
    ]
    icons = frames[anim_frame % len(frames)]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{icons[0]} Get Number", callback_data="services"), InlineKeyboardButton(f"{icons[1]} Status", callback_data="live")],
        [InlineKeyboardButton(f"{icons[2]} Active Number", callback_data="active"), InlineKeyboardButton(f"{icons[3]} Support", callback_data="support")],
        [InlineKeyboardButton(f"{icons[4]} Refer", callback_data="refer"), InlineKeyboardButton(f"{icons[5]} Wallet", callback_data="wallet")]
    ])

async def animate_menu_task(context, chat_id, message_id):
    try:
        for frame in range(6):
            await asyncio.sleep(0.7)
            kb = main_menu_keyboard(anim_frame=frame)
            try:
                await context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=kb)
            except:
                break
        await context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=main_menu_keyboard(0))
    except:
        pass

def bottom_keyboard():
    # ALWAYS show File Submit button (user request: don't delete, just disable function)
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📱 Get Number"), KeyboardButton("🌍 Status")],
            [KeyboardButton("📊 Active Number"), KeyboardButton("👨‍💼 Support")],
            [KeyboardButton("👥 Refer"), KeyboardButton("💰 Wallet")],
            [KeyboardButton("📁 File Submit")]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

def is_file_submit_enabled():
    toggle = load_json(SUBMIT_TOGGLE_FILE, {"enabled": True})
    return toggle.get("enabled", True)

async def debug_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to check number files"""
    if update.effective_user.id != ADMIN_ID:
        return
    import glob
    msg = "📁 Number Files Debug:\n\n"
    for base in ["/data", "/app/data", ".", "/mnt/data"]:
        if os.path.exists(base):
            try:
                files = [f for f in os.listdir(base) if 'number' in f.lower() and f.endswith('.txt')]
                for nf in files:
                    fp = os.path.join(base, nf)
                    try:
                        with open(fp,'r') as f:
                            raw = f.read()
                            lines = [l.strip() for l in raw.split('\n') if l.strip()]
                            real = [l for l in lines if not l.startswith("#") and any(c.isdigit() for c in l)]
                            msg += f"{fp}: {len(real)} numbers\n"
                            if real:
                                msg += f"  First: {real[0]}\n"
                            else:
                                msg += f"  Content: {raw[:100]}\n"
                    except Exception as e:
                        msg += f"{fp}: error {e}\n"
            except: pass
    await update.message.reply_text(msg[:4000])

async def file_submit_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle File Submit on/off - /file_on /file_off /filesubmit - button stays but function disabled"""
    if update.effective_user.id != ADMIN_ID:
        return
    # Check command name
    cmd_name = update.message.text.lower()
    if "file_off" in cmd_name:
        save_json(SUBMIT_TOGGLE_FILE, {"enabled": False})
        await update.message.reply_text("❌ File Submit DISABLED\n📁 Button will stay but won't work - users see 'disabled' message")
        return
    elif "file_on" in cmd_name:
        save_json(SUBMIT_TOGGLE_FILE, {"enabled": True})
        await update.message.reply_text("✅ File Submit ENABLED\n📁 Button works now")
        return
    
    args = context.args
    if not args:
        status = is_file_submit_enabled()
        txt = f"📁 File Submit Status: {'🟢 ON' if status else '🔴 OFF'}\n\nButton always visible, only function toggles\n\nCommands:\n/file_on - Enable function\n/file_off - Disable function (button stays)\n/file_status - Check status\n/export_submissions - Get text file"
        await update.message.reply_text(txt)
        return
    
    cmd = args[0].lower() if args else ""
    if cmd in ["on", "enable", "1"]:
        save_json(SUBMIT_TOGGLE_FILE, {"enabled": True})
        await update.message.reply_text("✅ File Submit ENABLED - button works")
    elif cmd in ["off", "disable", "0"]:
        save_json(SUBMIT_TOGGLE_FILE, {"enabled": False})
        await update.message.reply_text("❌ File Submit DISABLED - button stays but won't work")
    else:
        status = is_file_submit_enabled()
        await update.message.reply_text(f"📁 File Submit: {'ON' if status else 'OFF'}\nUse: /file_on or /file_off")

async def file_submit_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    enabled = is_file_submit_enabled()
    submissions = load_json(SUBMIT_FILE, [])
    txt = f"📁 File Submit: {'🟢 ON' if enabled else '🔴 OFF'}\n📊 Total submissions: {len(submissions)}\n\nCommands:\n/file_on - Enable\n/file_off - Disable\n/submissions - View all\n/export_submissions - Export sheet"
    await update.message.reply_text(txt)

async def view_submissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    submissions = load_json(SUBMIT_FILE, [])
    if not submissions:
        await update.message.reply_text("📁 No submissions yet")
        return
    
    txt = f"📁 Total Submissions: {len(submissions)}\n\n"
    # Show last 10
    for i, sub in enumerate(submissions[-10:], start=max(1, len(submissions)-9)):
        txt += f"{i}. 👤 {sub.get('user_id')} | {sub.get('username','N/A')}\n"
        txt += f"   📅 {sub.get('time','')[:16]}\n"
        txt += f"   📄 {sub.get('type','')} | {sub.get('content','')[:50]}...\n\n"
    
    if len(submissions) > 10:
        txt += f"... and {len(submissions)-10} more. Use /export_submissions for full sheet"
    
    await update.message.reply_text(txt[:4000])

async def export_submissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    submissions = load_json(SUBMIT_FILE, [])
    if not submissions:
        await update.message.reply_text("📁 No new submissions")
        return
    
    # User wants XLS file with 3 columns: UID, PASS, COOKIES
    xls_path = os.path.join(BASE_DIR, "submitted_data.xlsx")
    csv_path = os.path.join(BASE_DIR, "submitted_data.csv")
    
    rows = []
    for sub in submissions:
        content = sub.get('content','').strip()
        if not content:
            continue
        import re
        # FIX: User may send many lines in one submission - split by newline and handle each line
        # Example: 
        # 61593326023038  Polas@22  datr=...
        # 61593326023039  Polas@23  datr=...
        # So split content into lines first
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            # Parse: UID  PASS  COOKIES - 3 columns
            parts = re.split(r'\s{2,}|\t', line)
            if len(parts) >= 3:
                uid = parts[0].strip()
                pwd = parts[1].strip()
                cookies = " ".join(parts[2:]).strip()
            else:
                tokens = line.split()
                if len(tokens) >= 3:
                    uid = tokens[0]
                    pwd = tokens[1]
                    cookies = " ".join(tokens[2:])
                elif len(tokens) == 2:
                    uid = tokens[0]
                    pwd = tokens[1]
                    cookies = ""
                else:
                    # If can't parse, treat whole line as UID
                    uid = line
                    pwd = ""
                    cookies = ""
            # Only add if UID looks valid (numeric, 10+ digits)
            if uid and len(uid) >= 5:
                rows.append([uid, pwd, cookies])
    
    # Create XLS file
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Submissions"
        ws.append(["UID", "Password", "Cookies"])
        from openpyxl.styles import Font
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for row in rows:
            ws.append(row)
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 80
        wb.save(xls_path)
        has_xls = True
    except Exception as e:
        print(f"[XLS ERR] {e} - trying CSV fallback")
        has_xls = False
        # Create CSV as fallback
        import csv
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["UID", "Password", "Cookies"])
            writer.writerows(rows)
        xls_path = csv_path
    
    # Also create CSV always
    try:
        import csv
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["UID", "Password", "Cookies"])
            writer.writerows(rows)
    except: pass
    
    count = len(rows)
    await update.message.reply_text(f"📊 Exported {count} submissions - XLS file with 3 columns")
    try:
        if has_xls and os.path.exists(xls_path):
            await update.message.reply_document(document=open(xls_path, 'rb'), filename="submitted_data.xlsx")
        if os.path.exists(csv_path):
            await update.message.reply_document(document=open(csv_path, 'rb'), filename="submitted_data.csv")
        
        # Clear after export - next time same file won't come
        save_json(SUBMIT_FILE, [])
        try:
            with open(SUBMIT_SHEET_FILE, 'w', encoding='utf-8') as f:
                f.write("")
            if os.path.exists(xls_path) and xls_path != csv_path:
                os.remove(xls_path)
            import shutil
            submit_dir = os.path.join(BASE_DIR, "submitted_files")
            if os.path.exists(submit_dir):
                shutil.rmtree(submit_dir)
                os.makedirs(submit_dir, exist_ok=True)
        except: pass
        
        await update.message.reply_text(f"✅ Cleared! {count} rows exported and deleted\nNext export empty until new submissions")
    except Exception as e:
        await update.message.reply_text(f"Export error: {e}")
        import traceback
        traceback.print_exc()

def push_to_google_sheet(uid, pwd, cookies):
    # Disabled - user wants XLS file only
    return False

async def refresh_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Refresh /data files from Github - fixes Mozambique issue"""
    if update.effective_user.id != ADMIN_ID:
        return
    msg = "🔄 Refreshing number files from Github...\n\n"
    try:
        files_to_refresh = ["numbers_mozambique.txt", "numbers_myanmar.txt", "numbers.txt"]
        for fname in files_to_refresh:
            src_candidates = [f"./{fname}", f"{fname}", f"/app/{fname}"]
            dst = os.path.join(BASE_DIR, fname)
            src_found = None
            for src in src_candidates:
                if os.path.exists(src):
                    src_found = src
                    break
            if not src_found:
                msg += f"❌ {fname}: Github file not found\n"
                continue
            
            try:
                with open(src_found,'r') as sf:
                    src_content = sf.read()
                    src_numbers = [l.strip() for l in src_content.split('\n') if l.strip() and not l.strip().startswith("#") and any(c.isdigit() for c in l)]
                
                if len(src_numbers) == 0:
                    msg += f"⚠️ {fname}: Github file empty (0 numbers)\n"
                    continue
                
                # Backup old /data file
                if os.path.exists(dst):
                    backup = dst + ".backup"
                    try:
                        shutil.copy(dst, backup)
                        msg += f"📦 Backed up {fname} ({os.path.getsize(dst)} bytes)\n"
                    except: pass
                
                # Copy new file from Github to /data
                shutil.copy(src_found, dst)
                msg += f"✅ {fname}: {len(src_numbers)} numbers copied from {src_found} -> {dst}\n"
                msg += f"   First: {src_numbers[0]}\n"
                
            except Exception as e:
                msg += f"❌ {fname}: Error {e}\n"
        
        msg += "\n✅ Refresh done! Now test Mozambique again."
    except Exception as e:
        msg += f"\n❌ Error: {e}"
    
    await update.message.reply_text(msg[:4000])

async def clear_mozambique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear Mozambique /data file to force use Github file"""
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        dst = os.path.join(BASE_DIR, "numbers_mozambique.txt")
        if os.path.exists(dst):
            os.remove(dst)
            await update.message.reply_text(f"✅ Deleted {dst}\nNow /data file gone, bot will use ./numbers_mozambique.txt (10 numbers from Github)\nRun /debug to verify")
        else:
            await update.message.reply_text(f"⚠️ {dst} not found")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args
    if args and args[0].startswith("ref_"):
        try:
            ref_id = args[0].replace("ref_","")
            if str(ref_id) != str(uid):
                user = get_user(uid)
                if not user.get("referred_by"):
                    user["referred_by"]=str(ref_id)
                    save_user(uid, user)
                    ref_user = get_user(ref_id)
                    ref_user["referrals"]=ref_user.get("referrals",0)+1
                    r = ref_user["referrals"]
                    if r >= 5000: ref_user["level"]=5
                    elif r >= 2000: ref_user["level"]=4
                    elif r >= 500: ref_user["level"]=3
                    elif r >= 100: ref_user["level"]=2
                    else: ref_user["level"]=1
                    save_user(ref_id, ref_user)
                    try:
                        await context.bot.send_message(chat_id=int(ref_id), text=f"🎉 New referral! User {uid} joined via your link.\nTotal referrals: {ref_user['referrals']}")
                    except: pass
        except: pass

    if is_maintenance() and uid!= ADMIN_ID:
        await update.message.reply_text("🛠 System Under Maintenance")
        return
    get_user(uid)
    if await is_joined(uid, context):
        try:
            await update.message.reply_text("🔥", message_effect_id="5107584321108051014")
        except:
            await update.message.reply_text("🔥🔥🔥")
        txt = "✅ Verification Successful!\nWelcome to our platform.\nEnjoy a smooth and secure experience.\n\nMenu:"
        msg = await update.message.reply_text(txt, reply_markup=main_menu_keyboard(0))
        context.application.create_task(animate_menu_task(context, msg.chat_id, msg.message_id))
        await update.message.reply_text("👇 Use buttons below:", reply_markup=bottom_keyboard())
    else:
        txt = "⚠️ Access Denied!\nPlease join our channels to use the bot."
        kb = [
            [InlineKeyboardButton("Join Channel 1", url=CH1)],
            [InlineKeyboardButton("Join Channel 2", url=CH2)],
            [InlineKeyboardButton("Join Channel 3", url=CH3)],
            [InlineKeyboardButton("✅ Verify", callback_data="check")]
        ]
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    print(f"[BOTTOM] {uid} pressed: {text}")
    
    method = context.user_data.get("awaiting_wallet_for")
    if method:
        if any(k in text for k in ["Get Number", "Status", "Active Number", "Support", "Refer", "Wallet"]):
            context.user_data["awaiting_wallet_for"] = None
        else:
            if len(text) < 10:
                await update.message.reply_text("❌ Invalid address. Send valid address.")
                return
            user = get_user(uid)
            user["wallet_method"]=method
            user["wallet_address"]=text
            save_user(uid, user)
            context.user_data["awaiting_wallet_for"]=None
            txt = f"✅ Wallet Set!\n\n💵 Method: {method}\n✉️ Address:\n{text}"
            kb = [
                [InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"), InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
                [InlineKeyboardButton("⬅️ Back", callback_data="wallet")]
            ]
            await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            await update.message.reply_text("Menu:", reply_markup=main_menu_keyboard())
            return

    # File Submit feature - button always visible, but function toggles
    if "File Submit" in text or "📁 File Submit" in text:
        if not is_file_submit_enabled():
            await update.message.reply_text("❌ File Submit is currently disabled by admin\n📁 Button stays but function is off", reply_markup=bottom_keyboard())
            return
        # Set user in file submit mode
        context.user_data["awaiting_file_submit"] = True
        txt = "📁 **File Submit**\n\n📤 Submit your file:\n\n✅ Supported:\n• Excel (xls, xlsx)\n• Text (txt)\n• Plain text\n\nJust send your file or paste text here!"
        kb = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_file_submit")]]
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        return

    # If user is in file submit mode and sends text (not a button)
    if context.user_data.get("awaiting_file_submit"):
        # Check if it's a button press that should cancel file submit mode
        if any(k in text for k in ["Get Number", "Status", "Active Number", "Support", "Refer", "Wallet"]):
            context.user_data["awaiting_file_submit"] = False
        else:
            # User submitted text content - FIX: Handle multi-line (many UID PASS COOKIES)
            if len(text) > 2 and "File Submit" not in text:
                # Count lines for feedback
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                line_count = len(lines)
                
                # Save submission - keep internal tracking but export only content
                submissions = load_json(SUBMIT_FILE, [])
                submission = {
                    "serial": len(submissions) + 1,
                    "user_id": str(uid),
                    "username": update.effective_user.username or update.effective_user.first_name or "N/A",
                    "time": datetime.now().isoformat(),
                    "type": "text",
                    "content": text  # Full content with all lines
                }
                submissions.append(submission)
                save_json(SUBMIT_FILE, submissions)
                
                # Append to sheet
                try:
                    with open(SUBMIT_SHEET_FILE, 'a', encoding='utf-8') as f:
                        f.write(f"{text}\n")
                except: pass
                
                context.user_data["awaiting_file_submit"] = False
                await update.message.reply_text(f"✅ File submitted!\n\n📊 {line_count} lines saved\nThank you! XLS e sob {line_count} ta row asbe", reply_markup=bottom_keyboard())
                
                # Notify admin
                try:
                    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📁 New Submit #{submission['serial']} from {uid}")
                except: pass
                
                return

    if "Get Number" in text:
        txt = "⚙️ কোন প্ল্যাটফর্মের জন্য নাম্বার নিবেন?"
        kb = []
        for s in SERVICES:
            if s == "FACEBOOK":
                icon = "📘"
                name = "Facebook"
            elif s == "TIKTOK":
                icon = "🎵"
                name = "TikTok"
            else:
                icon = "💬"
                name = "WhatsApp"
            kb.append([InlineKeyboardButton(f"{icon} {name}", callback_data=f"s_{s}")])
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data="main")])
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif "Status" in text:
        succ_tr = load_json(SUCCESS_FILE, {})
        today = date.today().strftime("%-m/%-d/%Y")
        msg = "🔥 LIVE-STOCK STATUS.💥\n\n📘 Facebook\n"
        if succ_tr:
            for c, v in sorted(succ_tr.items(), key=lambda x: x[1], reverse=True)[:10]:
                flag = FLAGS.get(c.split("_")[0], "🌍")
                price = PRICES.get(c.upper(), PRICES.get(c.split("_")[0], "0.003$"))
                msg += f"├─ {flag} {c.replace('_FB','').title()} — {price}\n"
        else:
            msg += "├─ 🇳🇵 Nepal — $0.005$\n├─ 🇲🇿 Mozambique — $0.003$\n├─ 🇧🇩 BD — $0.005$\n"
        msg += "────────────────────\n"
        msg += f"📅 Date: {today}\n"
        msg += "────────────────────"
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]]))
        return
    elif "Active Number" in text:
        actives = get_active_numbers(uid)
        if not actives:
            msg = "📊 Active Number\n\nNo active numbers. Get a number first."
            kb = [[InlineKeyboardButton("📱 Get Number", callback_data="services")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
            return
        last = actives[-1]
        flag = FLAGS.get(last['country'].split("_")[0], "🌍")
        msg = f"✅ Active Number\n\n{flag} {last['country'].replace('_FB','').title()}\nPlatform: {last['service']}\nNumber: {last['number']}"
        kb = [
            [InlineKeyboardButton(f"{last['number']}", copy_text=CopyTextButton(last['number']))],
            [InlineKeyboardButton("📥 View OTP", url=OTP_GROUP), InlineKeyboardButton("🔄 Change", callback_data=f"c_{last['country']}")],
            [InlineKeyboardButton("🔙 Back", callback_data="main")]
        ]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif "Support" in text:
        msg = "☎ Contact support:\n\nAdmin: @PolasChandra\nChannel: @APNOfficial"
        kb = [[InlineKeyboardButton("✉ Contact Admin", url="https://t.me/PolasChandra")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif "Refer" in text:
        user = get_user(uid)
        refs = user.get("referrals",0)
        level = user.get("level",1)
        balance = user.get("balance",0.0)
        if level==1: need=100
        elif level==2: need=500
        elif level==3: need=2000
        elif level==4: need=5000
        else: need=5000
        progress_bar = "█" * min(10, int(refs/20)) + "░" * (10-min(10, int(refs/20)))
        try:
            bot_username = (await context.bot.get_me()).username
            invite_link = f"https://t.me/{bot_username}?start=ref_{uid}"
        except:
            invite_link = f"https://t.me/APNNUMBERBOT?start=ref_{uid}"
        msg = f"👥 Referral Dashboard\n━━━━━━━━━━━━━━━━━━\n\n🔥 Rank: Level {level}\n👥 Referrals: {refs}\n💰 Balance: ${balance:.4f}\n📊 Progress: [{progress_bar}] {refs}/{need}\n\n━━━━━━━━━━━━━━━━━━\n💎 Commission Tiers\n━━━━━━━━━━━━━━━━━━\n\n🔥 L1  $0.0002/OTP  (0+ refs)\n🌊 L2  $0.0005/OTP  (100+ refs)\n🦁 L3  $0.0006/OTP  (500+ refs)\n🛡 L4  $0.0070/OTP  (2000+ refs)\n👑 L5  $0.0100/OTP  (5000+ refs)\n\n🚀 Your Invite Link:\n{invite_link}"
        kb = [[InlineKeyboardButton("🔗 Copy Invite Link", callback_data=f"copy_{invite_link}")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif "Wallet" in text:
        user = get_user(uid)
        method = user.get("wallet_method")
        address = user.get("wallet_address")
        balance = user.get("balance",0.0)
        if method and address:
            masked = address[:8]+"••••••••••••"+address[-6:] if len(address)>20 else address
            if balance < 0.15:
                msg = f"💳 Method: {method}\n✉️ Address: {masked}\n\n❌ Insufficient Balance\n\n💰 Balance: ${balance:.4f}\n🔻 Minimum: $0.15"
            else:
                msg = f"💳 Method: {method}\n✉️ Address: {masked}\n\n💰 Balance: ${balance:.4f}\n✅ Ready to withdraw!"
            kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"), InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        else:
            msg = f"💰 Wallet\n\n💰 Balance: ${balance:.4f}\n\nNo wallet set. Set your payment method first.\n🔻 Minimum withdraw: $0.15"
            kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    uid = q.from_user.id
    # FIXED: Copy button - fallback for old callback
    if data.startswith("copy_"):
        val = data.split("copy_",1)[1]
        try:
            await q.answer(f"📋 {val} Copied! Paste koro", show_alert=True)
        except:
            await q.answer()
        try:
            await context.bot.send_message(chat_id=uid, text=f"`{val}`\n👆 Tap to copy", parse_mode="Markdown")
        except: pass
        return
    try:
        await q.answer()
    except: pass

    if data.startswith("setmethod_"):
        method = data.replace("setmethod_","")
        context.user_data["awaiting_wallet_for"]=method
        await q.edit_message_text(f"✉ Send your {method} wallet address:")
        return

    if is_maintenance() and uid!= ADMIN_ID:
        await q.edit_message_text("🛠 System Under Maintenance")
        return
    if data!= "check" and not await is_joined(uid, context):
        txt = "⚠️ Access Denied!\nPlease join our channels to use the bot."
        kb = [
            [InlineKeyboardButton("Join Channel 1", url=CH1)],
            [InlineKeyboardButton("Join Channel 2", url=CH2)],
            [InlineKeyboardButton("Join Channel 3", url=CH3)],
            [InlineKeyboardButton("✅ Verify", callback_data="check")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "check":
        if await is_joined(uid, context):
            txt = "✅ Verification Successful!\nWelcome to our platform.\nEnjoy a smooth and secure experience.\n\nMenu:"
            await q.edit_message_text(txt, reply_markup=main_menu_keyboard())
            try:
                await context.bot.send_message(chat_id=uid, text="👇 Use buttons below:", reply_markup=bottom_keyboard())
            except: pass
        else:
            await q.edit_message_text("❌ Not joined yet.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Verify", callback_data="check")]]))
        return

    if data == "main":
        await q.edit_message_text("Menu:", reply_markup=main_menu_keyboard(0))
        return

    if data == "live":
        succ_tr = load_json(SUCCESS_FILE, {})
        today = date.today().strftime("%-m/%-d/%Y")
        txt = "🔥 LIVE-STOCK STATUS.💥\n\n📘 Facebook\n"
        if succ_tr:
            for c, v in sorted(succ_tr.items(), key=lambda x: x[1], reverse=True)[:10]:
                flag = FLAGS.get(c.split("_")[0], "🌍")
                price = PRICES.get(c.upper(), PRICES.get(c.split("_")[0], "0.003$"))
                txt += f"├─ {flag} {c.replace('_FB','').title()} — {price}\n"
        else:
            txt += "├─ 🇳🇵 Nepal — $0.005$\n├─ 🇲🇦 Morocco — $0.003$\n├─ 🇳🇬 Nigeria — $0.003$\n"
        txt += "────────────────────\n"
        txt += f"📅 Date: {today}\n"
        txt += "────────────────────"
        kb = [[InlineKeyboardButton("⬅️ Back", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "cancel_file_submit":
        context.user_data["awaiting_file_submit"] = False
        await q.edit_message_text("❌ File Submit cancelled", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]]))
        await context.bot.send_message(chat_id=uid, text="Menu:", reply_markup=bottom_keyboard())
        return

    if data == "support":
        txt = "☎ Contact support:"
        kb = [[InlineKeyboardButton("✉ Contact Admin", url="https://t.me/PolasChandra")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "active":
        actives = get_active_numbers(uid)
        if not actives:
            txt = "📊 Active Number\n\nNo active numbers. Get a number first."
            kb = [[InlineKeyboardButton("📱 Get Number", callback_data="services")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            return
        last = actives[-1]
        flag = FLAGS.get(last['country'].split("_")[0], "🌍")
        txt = f"✅ Active Number\n\n{flag} {last['country'].replace('_FB','').title()}\nPlatform: {last['service']}\nNumber: {last['number']}"
        kb = [
            [InlineKeyboardButton(f"{last['number']}", copy_text=CopyTextButton(last['number']))],
            [InlineKeyboardButton("📥 View OTP", url=OTP_GROUP), InlineKeyboardButton("🔄 Change", callback_data=f"c_{last['country']}")],
            [InlineKeyboardButton("🔙 Back", callback_data="main")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "wallet":
        user = get_user(uid)
        method = user.get("wallet_method")
        address = user.get("wallet_address")
        balance = user.get("balance",0.0)
        if method and address:
            masked = address[:8]+"••••••••••••"+address[-6:] if len(address)>20 else address
            if balance < 0.15:
                txt = f"💳 Method: {method}\n✉️ Address: {masked}\n\n❌ Insufficient Balance\n\n💰 Balance: ${balance:.4f}\n🔻 Minimum: $0.15"
            else:
                txt = f"💳 Method: {method}\n✉️ Address: {masked}\n\n💰 Balance: ${balance:.4f}\n✅ Ready to withdraw!"
            kb = [
                [InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"), InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
                [InlineKeyboardButton("⬅️ Back", callback_data="main")]
            ]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        else:
            txt = f"💰 Wallet\n\n💰 Balance: ${balance:.4f}\n\nNo wallet set. Set your payment method first.\n🔻 Minimum withdraw: $0.15"
            kb = [
                [InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet")],
                [InlineKeyboardButton("⬅️ Back", callback_data="main")]
            ]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "set_wallet":
        txt = "💳 Set Payment Method\n\nSelect your preferred payment method:"
        kb = [
            [InlineKeyboardButton("⬜ BEP20", callback_data="setmethod_BEP20")],
            [InlineKeyboardButton("🟣 Bybit", callback_data="setmethod_Bybit"), InlineKeyboardButton("🔷 Bitget", callback_data="setmethod_Bitget")],
            [InlineKeyboardButton("🛡 Trust Wallet", callback_data="setmethod_Trust Wallet"), InlineKeyboardButton("🟡 Binance", callback_data="setmethod_Binance")],
            [InlineKeyboardButton("⬅️ Back", callback_data="wallet")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "withdraw":
        user = get_user(uid)
        balance = user.get("balance",0.0)
        method = user.get("wallet_method")
        address = user.get("wallet_address")
        if not method or not address:
            txt = f"❌ No wallet set\n\n💰 Balance: ${balance:.4f}\n\nPlease set wallet first!"
            kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet")], [InlineKeyboardButton("⬅️ Back", callback_data="wallet")]]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            return
        masked = address[:8]+"••••••••••••"+address[-6:] if len(address)>20 else address
        if balance < 0.15:
            txt = f"💳 Method: {method}\n✉️ Address: {masked}\n\n❌ Insufficient Balance\n\n💰 Balance: ${balance:.4f}\n🔻 Minimum: $0.15"
            kb = [
                [InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"), InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
                [InlineKeyboardButton("⬅️ Back", callback_data="wallet")]
            ]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        else:
            txt = f"✅ Withdraw Requested\n\n💰 Amount: ${balance:.4f}\n💳 Method: {method}\n✉️ Address: {masked}\n\n⏳ Will be processed within 24h"
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]]))
            user["balance"]=0.0
            save_user(uid, user)
        return

    if data == "refer":
        user = get_user(uid)
        refs = user.get("referrals",0)
        level = user.get("level",1)
        balance = user.get("balance",0.0)
        if level==1: need=100
        elif level==2: need=500
        elif level==3: need=2000
        elif level==4: need=5000
        else: need=5000
        progress_bar = "█" * min(10, int(refs/20)) + "░" * (10-min(10, int(refs/20)))
        invite_link = f"https://t.me/{context.bot.username}?start=ref_{uid}"
        txt = f"👥 Referral Dashboard\n━━━━━━━━━━━━━━━━━━\n\n🔥 Rank: Level {level}\n👥 Referrals: {refs}\n💰 Balance: ${balance:.4f}\n📊 Progress: [{progress_bar}] {refs}/{need}\n\n━━━━━━━━━━━━━━━━━━\n💎 Commission Tiers\n━━━━━━━━━━━━━━━━━━\n\n🔥 L1  $0.0002/OTP  (0+ refs)  ✦\n🌊 L2  $0.0005/OTP  (100+ refs)\n🦁 L3  $0.0006/OTP  (500+ refs)\n🛡 L4  $0.0070/OTP  (2000+ refs)\n👑 L5  $0.0100/OTP  (5000+ refs)\n\n🚀 Your Invite Link:\n{invite_link}"
        kb = [
            [InlineKeyboardButton("🔗 Copy Invite Link", callback_data=f"copy_{invite_link}")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "services":
        txt = "⚙️ কোন প্ল্যাটফর্মের জন্য নাম্বার নিবেন?"
        kb = []
        for s in SERVICES:
            if s == "FACEBOOK":
                icon = "📘"
                name = "Facebook"
            elif s == "TIKTOK":
                icon = "🎵"
                name = "TikTok"
            else:
                icon = "💬"
                name = "WhatsApp"
            kb.append([InlineKeyboardButton(f"{icon} {name}", callback_data=f"s_{s}")])
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data="main")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("s_"):
        service = data[2:]
        context.user_data['service'] = service
        countries = get_all_countries(service)
        if not countries and service.upper() == "FACEBOOK":
            countries = ["NEPAL_FB"]
        if not countries:
            await q.edit_message_text(f"❌ No ranges for {service}!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="services")]]))
            return
        seen_base = set()
        unique_countries = []
        for c in countries:
            base = c.upper().split("_")[0]
            if base not in seen_base or "NEPAL" in base:
                if "NEPAL" in base:
                    if "NEPAL" not in seen_base:
                        unique_countries.append("NEPAL_FB")
                        seen_base.add("NEPAL")
                else:
                    unique_countries.append(c.upper())
                    seen_base.add(base)
        unique_countries = [c for c in unique_countries if "NEPAL" not in c]
        if service.upper() == "FACEBOOK":
            unique_countries.insert(0, "NEPAL_FB")
        countries_sorted = unique_countries
        platform_name = "Facebook" if service.upper() == "FACEBOOK" else service.title()
        txt = f"💳 {platform_name} - দেশ সিলেক্ট করুন:"
        kb = []
        for code in countries_sorted:
            display = get_display_name(code)
            base_key = code.upper().split("_")[0]
            flag = FLAGS.get(code.upper(), FLAGS.get(base_key, "🌍"))
            price = PRICES.get(code.upper(), PRICES.get(base_key, PRICES.get("DEFAULT", "0.003$")))
            btn_text = f"{flag} {display} {price}"
            kb.append([InlineKeyboardButton(btn_text, callback_data=f"c_{code}")])
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data="services")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("c_"):
        country_code = data[2:]
        service = context.user_data.get('service', 'FACEBOOK')
        display = get_display_name(country_code)
        flag = FLAGS.get(country_code.upper(), FLAGS.get(country_code.upper().split("_")[0], "🌍"))
        is_nepal = "NEPAL" in country_code.upper()
        is_tiktok_file = any(x in country_code.upper() for x in ["MOZAMBIQUE", "MYANMAR"])
        # User wants 5 numbers per click for TikTok
        if is_tiktok_file:
            num_count = 5
        else:
            num_count = 3 if is_nepal else 6
        await q.edit_message_text(f"⏳ Fetching {num_count} numbers for {display}...")
        nums = []
        # For FB/WS, try harder to get 6 numbers (retry if panel fails)
        max_attempts = num_count * 3  # Try 3x more than needed for FB/WS
        attempts = 0
        while len(nums) < num_count and attempts < max_attempts:
            attempts += 1
            try:
                order = await asyncio.to_thread(create_order, service, country_code)
            except Exception as e:
                print(f"[CREATE THREAD ERR] {e}")
                order = None
            
            if order:
                # Check duplicate - don't add same number twice
                if not any(o['number'] == order['number'] for o in nums):
                    nums.append(order)
                    add_request(uid, display)
                    save_active_number(uid, order['number'], country_code, service)
                    context.application.create_task(otp_watcher(context.bot, order['id'], uid, order['number'], service, country_code))
                    print(f"[FETCH] Got {len(nums)}/{num_count}: {order['number']} for {display}")
                else:
                    print(f"[FETCH] Duplicate skipped: {order['number']}")
            else:
                print(f"[FETCH] Failed attempt {attempts}/{max_attempts} for {display}")
            
            await asyncio.sleep(0.5)
        
        print(f"[FETCH DONE] Requested {num_count}, got {len(nums)} for {display}")
        if not nums:
            await q.edit_message_text(f"❌ Out of Stock! {display}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Try Again", callback_data=f"s_{service}")]]))
            return
        platform_name = "Facebook" if service.upper() == "FACEBOOK" else service.title()
        header = f"────────── ⋆⋅☆⋅⋆ ──────────\n{flag} {display} Fresh Number 💸\n📱 {platform_name}\n────────── ⋆⋅☆⋅⋆ ──────────\n\n💫 Wait 5s Or Check The OTP Grup 🖤"
        txt = header
        kb = []
        for o in nums:
            try:
                kb.append([InlineKeyboardButton(f"{o['number']}", copy_text=CopyTextButton(o['number']))])
            except:
                kb.append([InlineKeyboardButton(f"{o['number']}", callback_data=f"copy_{o['number']}")])
        kb.append([InlineKeyboardButton("📥 View OTP", url=OTP_GROUP)])
        kb.append([InlineKeyboardButton("🔄 Change", callback_data=f"c_{country_code}"), InlineKeyboardButton("🔙 Back", callback_data=f"s_{service}")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

from telegram.request import HTTPXRequest
request = HTTPXRequest(connection_pool_size=20, connect_timeout=30, read_timeout=30, write_timeout=30, pool_timeout=30)
app = ApplicationBuilder().token(TOKEN).request(request).build()

async def error_handler(update, context):
    print(f"[BOT ERROR] {context.error}")

app.add_error_handler(error_handler)
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("debug", debug_numbers))
app.add_handler(CommandHandler("mynumbers", debug_numbers))
app.add_handler(CommandHandler("refresh", refresh_numbers))
app.add_handler(CommandHandler("clearmoz", clear_mozambique))
app.add_handler(CommandHandler("clear_mozambique", clear_mozambique))
app.add_handler(CommandHandler("file_on", file_submit_toggle))
app.add_handler(CommandHandler("file_off", file_submit_toggle))
app.add_handler(CommandHandler("file", file_submit_toggle))
app.add_handler(CommandHandler("filesubmit", file_submit_toggle))
app.add_handler(CommandHandler("file_status", file_submit_status))
app.add_handler(CommandHandler("submissions", view_submissions))
app.add_handler(CommandHandler("export_submissions", export_submissions))
app.add_handler(CommandHandler("id", get_my_id))
app.add_handler(CommandHandler("add", add_range))
app.add_handler(CommandHandler("del", del_range))
app.add_handler(CommandHandler("list", list_range))
app.add_handler(CommandHandler("off", bot_off))
app.add_handler(CommandHandler("on", bot_on))
app.add_handler(CommandHandler("botstatus", bot_status))
app.add_handler(CommandHandler("backup", backup_data))
app.add_handler(CommandHandler("data", restore_info))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling(drop_pending_updates=True)
