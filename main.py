import os, json, asyncio, shutil, re
from datetime import datetime, date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton, CopyTextButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from panel import create_order, get_otp, get_all_countries, get_display_name

print("[FREE MODE] Using JSON + Auto Backup to Telegram")
TOKEN = os.getenv("BOT_TOKEN")
MUST_JOIN = ["@APNOfficial", "@APNOTP", "@Proxystore999"]
CH1 = "https://t.me/APNOfficial"
CH2 = "https://t.me/APNOTP"
CH3 = "https://t.me/Proxystore999"
OTP_GROUP = "https://t.me/APNOTP"
OTP_GROUP_ID = "@APNOTP"
SUPPORT_ID = "https://t.me/PolasChandra"
SERVICES = ["FACEBOOK", "WHATSAPP"]

for p in ["/data", "/app/data", "."]:
    try:
        if os.path.exists(p) or p in ["/data", "/app/data"]:
            os.makedirs(p, exist_ok=True)
            if os.path.exists(p):
                BASE_DIR = p
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

if not os.path.exists(RANGES_FILE) and os.path.exists("ranges.json"):
    try:
        os.makedirs(BASE_DIR, exist_ok=True)
        shutil.copy("ranges.json", RANGES_FILE)
    except: pass

ADMIN_ID = 1853202569
FLAGS = {
    "NEPAL": "🇳🇵", "NEPAL_FB": "🇳🇵",
    "CAMEROON": "🇨🇲", "GUINEA": "🇬🇳", "GUNIEA": "🇬🇳",
    "MADAGASCAR": "🇲🇬", "MONTENEGRO": "🇲🇪", "UKRAINE": "🇺🇦",
    "HAITI": "🇭🇹", "SIERRA_LEONE": "🇸🇱", "USA": "🇺🇸", "USA_FB": "🇺🇸",
    "MOROCCO": "🇲🇦", "NIGERIA": "🇳🇬", "MOZAMBIQUE": "🇲🇿", "ISRAEL": "🇮🇱",
    "TOGO": "🇹🇬", "BENIN": "🇧🇯", "CM": "🇨🇲",
}
PRICES = {
    "NEPAL": "0.005$", "NEPAL_FB": "0.005$",
    "MOROCCO": "0.003$", "NIGERIA": "0.003$", "MOZAMBIQUE": "0.003$",
    "CAMEROON": "0.003$", "GUINEA": "0.003$", "MADAGASCAR": "0.003$",
    "MONTENEGRO": "0.003$", "UKRAINE": "0.003$", "HAITI": "0.003$",
    "SIERRA_LEONE": "0.003$", "USA": "0.003$", "USA_FB": "0.003$", "DEFAULT": "0.003$",
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

# === INBOX DESIGN ===
def format_for_inbox(country_code, full_number, service, otp_code):
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    country_name = clean.replace("_", " ").title()
    flag = FLAGS.get(clean, FLAGS.get(clean.split("_")[0], ""))
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    earn_text = "+$0.005" if "NEPAL" in clean.upper() else "+$0.003"
    text = f"{flag} {country_name}\nPhone: {full_number}\nEarned: {earn_text}\n\nOTP: {otp_digits}"
    keyboard = [[InlineKeyboardButton(f"📋 {otp_digits}", callback_data=f"copy_{otp_digits}")]]
    return text, InlineKeyboardMarkup(keyboard)

# === NEW PREMIUM GROUP DESIGN LIKE 2ND PIC ===
def format_for_group(country_code, full_number, service, otp_code):
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    masked = mask_number(full_number)
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    flag = FLAGS.get(clean, FLAGS.get(clean.split("_")[0], "🌍"))
    country_display = clean.replace("_FB","").replace("_"," ")

    french_countries = ["TOGO", "CAMEROON", "GUINEA", "GUNIEA", "MADAGASCAR", "MOROCCO", "BENIN", "CM"]
    lang = "French" if any(x in clean for x in french_countries) else "English"
    
    # New design: 🇹🇬 TOGO | 📱 +2289XXXXX245 | » French
    text = f"{flag} {country_display} | 📱 {masked} | » {lang}"

    keyboard = [
        [InlineKeyboardButton("🎉 Channel", url="https://t.me/APNOfficial"), 
         InlineKeyboardButton(f"🔑 {otp_digits}", callback_data=f"copy_{otp_digits}")],
        [InlineKeyboardButton("📞 Get Number", url="https://t.me/APN_NUMBER_BOT")]
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
    print(f"[WATCHER START] {number} {order_id}")
    for i in range(180):
        await asyncio.sleep(5)
        try:
            otp = await asyncio.to_thread(get_otp, order_id)
            if otp:
                text_inbox, markup_inbox = format_for_inbox(country_code, number, service, otp)
                text_group, markup_group = format_for_group(country_code, number, service, otp)
                try:
                    await bot.send_message(chat_id=user_id, text=text_inbox, reply_markup=markup_inbox)
                except:
                    await bot.send_message(chat_id=user_id, text=text_inbox, reply_markup=markup_inbox)
                try:
                    await bot.send_message(chat_id=OTP_GROUP_ID, text=text_group, reply_markup=markup_group)
                except:
                    pass
                user = get_user(user_id)
                earn = 0.005 if "NEPAL" in country_code.upper() else 0.003
                user["balance"]+=earn
                save_user(user_id, user)
                if user.get("referred_by"):
                    ref_user = get_user(user["referred_by"])
                    refs = ref_user.get("referrals",0)
                    comm = 0.0100 if refs>=5000 else 0.0070 if refs>=2000 else 0.0006 if refs>=500 else 0.0005 if refs>=100 else 0.0002
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
    await update.message.reply_text("Bot OFF")

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    save_json(MAINT_FILE, {"enabled": False})
    await update.message.reply_text("Bot ON")

async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    status = "OFF" if is_maintenance() else "ON"
    await update.message.reply_text(f"Bot Status: {status}")

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
        await update.message.reply_text(f"Added {service} - {name} = {rid}")
    except:
        await update.message.reply_text("Use: /add FB CAMEROON 23762")

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
            await update.message.reply_text(f"Deleted {name}")
        else:
            await update.message.reply_text("Not found")
    except:
        await update.message.reply_text("Use: /del FB CAMEROON")

async def list_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
    txt = f"Ranges ({BASE_DIR}):\n\n"
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
        total_bal = sum([u.get("balance",0) for u in db.values()])
        txt = f"Auto Backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}\nUsers: {len(db)}\nTotal: ${total_bal:.4f}"
        await bot.send_message(chat_id=ADMIN_ID, text=txt)
        await bot.send_document(chat_id=ADMIN_ID, document=open(BAL_FILE, 'rb'), filename=f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}_balances.json")
    except:
        pass

async def backup_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_json(BAL_FILE, {})
    total_bal = sum([u.get("balance",0) for u in db.values()])
    txt = f"Backup Info\n\nPath: {BAL_FILE}\nUsers: {len(db)}\nTotal: ${total_bal:.4f}"
    await update.message.reply_text(txt)
    for fp in [BAL_FILE, "./balances.json"]:
        if os.path.exists(fp):
            try:
                await update.message.reply_document(document=open(fp, 'rb'), filename="balances.json")
                break
            except: continue

async def restore_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    txt = f"Data Path: {BASE_DIR}\n\n"
    for fn in ["balances.json", "traffic.json", "success_traffic.json", "ranges.json", "wallets.json"]:
        found = os.path.exists(os.path.join(BASE_DIR, fn)) or os.path.exists(fn)
        txt += f"{'OK' if found else 'Not found'} {fn}\n"
    await update.message.reply_text(txt)

async def handle_restore_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not update.message.document: return
    fname = update.message.document.file_name
    if "balances" not in fname.lower() and "backup" not in fname.lower():
        await update.message.reply_text("Please upload balances.json")
        return
    try:
        file = await context.bot.get_file(update.message.document.file_id)
        for path in [BAL_FILE, "./balances.json"]:
            try: await file.download_to_drive(path)
            except: pass
        db = load_json(BAL_FILE, {})
        await update.message.reply_text(f"Restored! Users: {len(db)}")
    except Exception as e: await update.message.reply_text(f"Restore failed: {e}")

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Get Number", callback_data="services"), InlineKeyboardButton("🌍 Status", callback_data="live")],
        [InlineKeyboardButton("📊 Active Number", callback_data="active"), InlineKeyboardButton("👨💼 Support", callback_data="support")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer"), InlineKeyboardButton("💰 Wallet", callback_data="wallet")]
    ])

def bottom_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📱 Get Number"), KeyboardButton("🌍 Status")],
            [KeyboardButton("📊 Active Number"), KeyboardButton("👨💼 Support")],
            [KeyboardButton("👥 Refer"), KeyboardButton("💰 Wallet")]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

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
                    ref_user["level"]=5 if r>=5000 else 4 if r>=2000 else 3 if r>=500 else 2 if r>=100 else 1
                    save_user(ref_id, ref_user)
        except: pass
    if is_maintenance() and uid!= ADMIN_ID:
        await update.message.reply_text("System Under Maintenance")
        return
    get_user(uid)
    if await is_joined(uid, context):
        txt = "Verification Successful!\nWelcome to our platform.\nEnjoy a smooth and secure experience.\n\nMenu:"
        await update.message.reply_text(txt, reply_markup=main_menu_keyboard())
        await update.message.reply_text("Use buttons below:", reply_markup=bottom_keyboard())
    else:
        txt = "Access Denied!\nPlease join our channels to use the bot."
        kb = [[InlineKeyboardButton("Join Channel 1", url=CH1)],[InlineKeyboardButton("Join Channel 2", url=CH2)],[InlineKeyboardButton("Join Channel 3", url=CH3)],[InlineKeyboardButton("✅ Verify", callback_data="check")]]
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    method = context.user_data.get("awaiting_wallet_for")
    if method and text not in ["📱 Get Number", "🌍 Status", "📊 Active Number", "👨💼 Support", "👥 Refer", "💰 Wallet"]:
        if len(text) < 10:
            await update.message.reply_text("Invalid address. Send valid address.")
            return
        user = get_user(uid)
        user["wallet_method"]=method
        user["wallet_address"]=text
        save_user(uid, user)
        context.user_data["awaiting_wallet_for"]=None
        txt = f"Wallet Set!\n\nMethod: {method}\nAddress:\n{text}"
        kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"), InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],[InlineKeyboardButton("⬅ Back", callback_data="wallet")]]
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        await update.message.reply_text("Menu:", reply_markup=main_menu_keyboard())
        return

    if text in ["📱 Get Number"]:
        txt = "⚙ কোন প্ল্যাটফর্মের জন্য নাম্বার নিবেন?"
        kb = []
        for s in SERVICES:
            icon = "📘" if s == "FACEBOOK" else "💬"
            name = "Facebook" if s == "FACEBOOK" else "WhatsApp"
            kb.append([InlineKeyboardButton(f"{icon} {name}", callback_data=f"s_{s}")])
        kb.append([InlineKeyboardButton("⬅ Back", callback_data="main")])
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif text in ["🌍 Status"]:
        succ_tr = load_json(SUCCESS_FILE, {})
        today = date.today().strftime("%-m/%-d/%Y")
        msg = "LIVE-STOCK STATUS\n\nFacebook\n"
        if succ_tr:
            for c, v in sorted(succ_tr.items(), key=lambda x: x[1], reverse=True)[:10]:
                flag = FLAGS.get(c.split("_")[0], "🌍")
                price = PRICES.get(c.upper(), PRICES.get(c.split("_")[0], "0.003$"))
                msg += f"- {flag} {c.replace('_FB','').title()} - {price}\n"
        else:
            msg += "- Nepal - 0.005$\n- Morocco - 0.003$\n- Nigeria - 0.003$\n"
        msg += f"----------------\nDate: {today}\n----------------"
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="main")]]))
        return
    elif text in ["📊 Active Number"]:
        actives = get_active_numbers(uid)
        if not actives:
            msg = "Active Number\n\nNo active numbers. Get a number first."
            kb = [[InlineKeyboardButton("📱 Get Number", callback_data="services")], [InlineKeyboardButton("⬅ Back", callback_data="main")]]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
            return
        last = actives[-1]
        flag = FLAGS.get(last['country'].split("_")[0], "🌍")
        msg = f"Active Number\n\n{flag} {last['country'].replace('_FB','').title()}\nPlatform: {last['service']}\nNumber: {last['number']}"
        kb = [[InlineKeyboardButton(f"{last['number']}", callback_data=f"copy_{last['number']}")],[InlineKeyboardButton("📥 View OTP", url=OTP_GROUP), InlineKeyboardButton("🔄 Change", callback_data=f"c_{last['country']}")],[InlineKeyboardButton("🔙 Back", callback_data="main")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif text in ["👨💼 Support"]:
        msg = "Contact support:"
        kb = [[InlineKeyboardButton("✉ Contact Admin", url="https://t.me/PolasChandra")], [InlineKeyboardButton("⬅ Back", callback_data="main")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif text in ["👥 Refer"]:
        user = get_user(uid)
        refs = user.get("referrals",0)
        level = user.get("level",1)
        balance = user.get("balance",0.0)
        need = 100 if level==1 else 500 if level==2 else 2000 if level==3 else 5000
        progress_bar = "█" * min(10, int(refs/20)) + "░" * (10-min(10, int(refs/20)))
        invite_link = f"https://t.me/{context.bot.username}?start=ref_{uid}"
        msg = f"Referral Dashboard\n------------------\n\nRank: Level {level}\nReferrals: {refs}\nBalance: ${balance:.4f}\nProgress: [{progress_bar}] {refs}/{need}\n\nYour Invite Link:\n{invite_link}"
        kb = [[InlineKeyboardButton("🔗 Copy Invite Link", callback_data=f"copy_{invite_link}")], [InlineKeyboardButton("⬅ Back", callback_data="main")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif text in ["💰 Wallet"]:
        user = get_user(uid)
        method = user.get("wallet_method")
        address = user.get("wallet_address")
        balance = user.get("balance",0.0)
        if method and address:
            masked = address[:8]+"••••••••••••"+address[-6:] if len(address)>20 else address
            if balance < 0.15:
                msg = f"Method: {method}\nAddress: {masked}\n\nInsufficient Balance\nBalance: ${balance:.4f}\nMinimum: $0.15"
            else:
                msg = f"Method: {method}\nAddress: {masked}\n\nBalance: ${balance:.4f}\nReady to withdraw!"
            kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"), InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")], [InlineKeyboardButton("⬅ Back", callback_data="main")]]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        else:
            msg = f"Wallet\n\nBalance: ${balance:.4f}\n\nNo wallet set. Set your payment method first.\nMinimum withdraw: $0.15"
            kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet")], [InlineKeyboardButton("⬅ Back", callback_data="main")]]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    uid = q.from_user.id
    try: await q.answer()
    except: pass

    if data.startswith("copy_"):
        val = data.split("copy_",1)[1]
        try:
            await q.answer(f"{val} Copied!", show_alert=True)
            await context.bot.send_message(chat_id=uid, text=f"{val}")
        except: await q.answer(f"{val} Copied!", show_alert=False)
        return
    if data.startswith("setmethod_"):
        method = data.replace("setmethod_","")
        context.user_data["awaiting_wallet_for"]=method
        await q.edit_message_text(f"Send your {method} wallet address:")
        return
    if is_maintenance() and uid!= ADMIN_ID:
        await q.edit_message_text("System Under Maintenance")
        return
    if data!= "check" and not await is_joined(uid, context):
        txt = "Access Denied!\nPlease join our channels to use the bot."
        kb = [[InlineKeyboardButton("Join Channel 1", url=CH1)],[InlineKeyboardButton("Join Channel 2", url=CH2)],[InlineKeyboardButton("Join Channel 3", url=CH3)],[InlineKeyboardButton("Verify", callback_data="check")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    if data == "check":
        if await is_joined(uid, context):
            txt = "Verification Successful!\nWelcome to our platform.\nEnjoy a smooth and secure experience.\n\nMenu:"
            await q.edit_message_text(txt, reply_markup=main_menu_keyboard())
            try: await context.bot.send_message(chat_id=uid, text="Use buttons below:", reply_markup=bottom_keyboard())
            except: pass
        else:
            await q.edit_message_text("Not joined yet. Please join all channels and click Verify.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Verify", callback_data="check")]]))
        return
    if data == "main":
        await q.edit_message_text("Menu:", reply_markup=main_menu_keyboard())
        return
    if data == "wallet":
        user = get_user(uid)
        method = user.get("wallet_method")
        address = user.get("wallet_address")
        balance = user.get("balance",0.0)
        if method and address:
            masked = address[:8]+"••••••••••••"+address[-6:] if len(address)>20 else address
            if balance < 0.15:
                txt = f"Method: {method}\nAddress: {masked}\n\nInsufficient Balance\nBalance: ${balance:.4f}\nMinimum: $0.15"
            else:
                txt = f"Method: {method}\nAddress: {masked}\n\nBalance: ${balance:.4f}\nReady to withdraw!"
            kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"), InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],[InlineKeyboardButton("⬅ Back", callback_data="main")]]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        else:
            txt = f"Wallet\n\nBalance: ${balance:.4f}\n\nNo wallet set. Set your payment method first.\nMinimum withdraw: $0.15"
            kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet")],[InlineKeyboardButton("⬅ Back", callback_data="main")]]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    if data == "set_wallet":
        txt = "Set Payment Method\n\nSelect your preferred payment method:"
        kb = [[InlineKeyboardButton("BEP20", callback_data="setmethod_BEP20")],[InlineKeyboardButton("Bybit", callback_data="setmethod_Bybit"), InlineKeyboardButton("Bitget", callback_data="setmethod_Bitget")],[InlineKeyboardButton("Trust Wallet", callback_data="setmethod_Trust Wallet"), InlineKeyboardButton("Binance", callback_data="setmethod_Binance")],[InlineKeyboardButton("⬅ Back", callback_data="wallet")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    if data == "withdraw":
        user = get_user(uid)
        balance = user.get("balance",0.0)
        method = user.get("wallet_method")
        address = user.get("wallet_address")
        if not method or not address:
            txt = f"No wallet set\n\nBalance: ${balance:.4f}\n\nPlease set wallet first!"
            kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet")], [InlineKeyboardButton("⬅ Back", callback_data="wallet")]]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            return
        masked = address[:8]+"••••••••••••"+address[-6:] if len(address)>20 else address
        if balance < 0.15:
            txt = f"Method: {method}\nAddress: {masked}\n\nInsufficient Balance\n\nBalance: ${balance:.4f}\nMinimum: $0.15"
            kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"), InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],[InlineKeyboardButton("⬅ Back", callback_data="wallet")]]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        else:
            txt = f"Withdraw Requested\n\nAmount: ${balance:.4f}\nMethod: {method}\nAddress: {masked}\n\nWill be processed within 24h"
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="main")]]))
            user["balance"]=0.0
            save_user(uid, user)
        return
    if data == "refer":
        user = get_user(uid)
        refs = user.get("referrals",0)
        level = user.get("level",1)
        balance = user.get("balance",0.0)
        need = 100 if level==1 else 500 if level==2 else 2000 if level==3 else 5000
        progress_bar = "█" * min(10, int(refs/20)) + "░" * (10-min(10, int(refs/20)))
        invite_link = f"https://t.me/{context.bot.username}?start=ref_{uid}"
        txt = f"Referral Dashboard\n------------------\n\nRank: Level {level}\nReferrals: {refs}\nBalance: ${balance:.4f}\nProgress: [{progress_bar}] {refs}/{need}\n\nYour Invite Link:\n{invite_link}"
        kb = [[InlineKeyboardButton("Copy Invite Link", callback_data=f"copy_{invite_link}")],[InlineKeyboardButton("Back", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    if data == "support":
        txt = "Contact support:"
        kb = [[InlineKeyboardButton("Contact Admin", url="https://t.me/PolasChandra")], [InlineKeyboardButton("Back", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    if data == "active":
        actives = get_active_numbers(uid)
        if not actives:
            txt = "Active Number\n\nNo active numbers. Get a number first."
            kb = [[InlineKeyboardButton("📱 Get Number", callback_data="services")], [InlineKeyboardButton("Back", callback_data="main")]]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            return
        last = actives[-1]
        flag = FLAGS.get(last['country'].split("_")[0], "🌍")
        txt = f"Active Number\n\n{flag} {last['country'].replace('_FB','').title()}\nPlatform: {last['service']}\nNumber: {last['number']}"
        kb = [[InlineKeyboardButton(f"{last['number']}", callback_data=f"copy_{last['number']}")],[InlineKeyboardButton("View OTP", url=OTP_GROUP), InlineKeyboardButton("Change", callback_data=f"c_{last['country']}")],[InlineKeyboardButton("Back", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    if data == "live":
        succ_tr = load_json(SUCCESS_FILE, {})
        today = date.today().strftime("%-m/%-d/%Y")
        txt = "LIVE-STOCK STATUS\n\nFacebook\n"
        if succ_tr:
            for c, v in sorted(succ_tr.items(), key=lambda x: x[1], reverse=True)[:10]:
                flag = FLAGS.get(c.split("_")[0], "🌍")
                price = PRICES.get(c.upper(), PRICES.get(c.split("_")[0], "0.003$"))
                txt += f"- {flag} {c.replace('_FB','').title()} - {price}\n"
        else: txt += "- Nepal - $0.005$\n- Morocco - $0.003$\n- Nigeria - $0.003$\n"
        txt += f"----------------\nDate: {today}\n----------------"
        kb = [[InlineKeyboardButton("Back", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    if data == "services":
        txt = "⚙ কোন প্ল্যাটফর্মের জন্য নাম্বার নিবেন?"
        kb = []
        for s in SERVICES:
            icon = "📘" if s == "FACEBOOK" else "💬"
            name = "Facebook" if s == "FACEBOOK" else "WhatsApp"
            kb.append([InlineKeyboardButton(f"{icon} {name}", callback_data=f"s_{s}")])
        kb.append([InlineKeyboardButton("⬅ Back", callback_data="main")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    if data.startswith("s_"):
        service = data[2:]
        context.user_data['service'] = service
        countries = get_all_countries(service)
        if not countries and service.upper() == "FACEBOOK": countries = ["NEPAL_FB"]
        if not countries:
            await q.edit_message_text(f"No ranges for {service}!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="services")]]))
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
        if service.upper() == "FACEBOOK": unique_countries.insert(0, "NEPAL_FB")
        platform_name = "Facebook" if service.upper() == "FACEBOOK" else service.title()
        txt = f"{platform_name} - দেশ সিলেক্ট করুন:"
        kb = []
        for code in unique_countries:
            display = get_display_name(code)
            base_key = code.upper().split("_")[0]
            flag = FLAGS.get(code.upper(), FLAGS.get(base_key, "🌍"))
            price = PRICES.get(code.upper(), PRICES.get(base_key, PRICES.get("DEFAULT", "0.003$")))
            btn_text = f"{flag} {display} {price}"
            kb.append([InlineKeyboardButton(btn_text, callback_data=f"c_{code}")])
        kb.append([InlineKeyboardButton("⬅ Back", callback_data="services")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    if data.startswith("c_"):
        country_code = data[2:]
        service = context.user_data.get('service', 'FACEBOOK')
        display = get_display_name(country_code)
        flag = FLAGS.get(country_code.upper(), FLAGS.get(country_code.upper().split("_")[0], "🌍"))
        is_nepal = "NEPAL" in country_code.upper()
        num_count = 3 if is_nepal else 6
        await q.edit_message_text(f"Fetching {num_count} numbers for {display}...")
        nums = []
        for i in range(num_count):
            try: order = await asyncio.to_thread(create_order, service, country_code)
            except: order = None
            if order:
                nums.append(order)
                add_request(uid, display)
                save_active_number(uid, order['number'], country_code, service)
                context.application.create_task(otp_watcher(context.bot, order['id'], uid, order['number'], service, country_code))
                await asyncio.sleep(0.5)
        if not nums:
            await q.edit_message_text(f"Out of Stock! {display}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Try Again", callback_data=f"s_{service}")]]))
            return
        platform_name = "Facebook" if service.upper() == "FACEBOOK" else service.title()
        header = f"{flag} {display} Fresh Number\n{platform_name}\n\nWait 5s Or Check The OTP Group"
        txt = header
        kb = []
        for o in nums:
            try: kb.append([InlineKeyboardButton(f"{o['number']}", copy_text=CopyTextButton(o['number']))])
            except: kb.append([InlineKeyboardButton(f"{o['number']}", callback_data=f"copy_{o['number']}")])
        kb.append([InlineKeyboardButton("View OTP", url=OTP_GROUP)])
        kb.append([InlineKeyboardButton("Change", callback_data=f"c_{country_code}"), InlineKeyboardButton("Back", callback_data=f"s_{service}")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

from telegram.request import HTTPXRequest
request = HTTPXRequest(connection_pool_size=20, connect_timeout=30, read_timeout=30, write_timeout=30, pool_timeout=30)
app = ApplicationBuilder().token(TOKEN).request(request).build()

async def error_handler(update, context):
    print(f"[BOT ERROR] {context.error}")

app.add_error_handler(error_handler)
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("id", get_my_id))
app.add_handler(CommandHandler("add", add_range))
app.add_handler(CommandHandler("del", del_range))
app.add_handler(CommandHandler("list", list_range))
app.add_handler(CommandHandler("off", bot_off))
app.add_handler(CommandHandler("on", bot_on))
app.add_handler(CommandHandler("botstatus", bot_status))
app.add_handler(CommandHandler("backup", backup_data))
app.add_handler(CommandHandler("data", restore_info))
app.add_handler(MessageHandler(filters.Document.ALL, handle_restore_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling(drop_pending_updates=True)
