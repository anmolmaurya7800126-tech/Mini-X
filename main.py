import os, json, asyncio
from datetime import datetime, timedelta
import pytz
import aiohttp
from aiohttp import ClientTimeout
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- TERA DETAIL ---
BOT_TOKEN = "8916008855:AAEPcSLbG22z2ChUude6NlcR_okzVctttY0"
ALLOWED_GROUP = -1004357135899
ADMIN_ID = 7800126284
OWNER = "@Anmolmaurya"
TRACK_FILE = "like_tracking.json"
TIMEZONE = pytz.timezone("Asia/Kolkata")
RESET_HOUR = 4
RESET_MIN = 30
TIMEOUT = ClientTimeout(total=30)
DAILY_LIMIT = 20

# APIs + PROXY FIX FOR EU NODE
LIKE_APIS = [
    "https://like-api-rose.vercel.app",
    "https://like-api-black.vercel.app",
    "https://like-api-alpha.vercel.app"
]
PROXY_LIST = [
    "https://api.allorigins.win/raw?url=",
    "https://api.codetabs.com/v1/proxy?quest="
]

E = {
    "ok": "✅", "star": "⭐", "fire": "🔥", "msg": "💬", "user": "👤",
    "money": "💰", "lock": "🔒", "pin": "📍", "party": "🎉",
    "sparkle": "✨", "diamond": "💎", "crown": "👑", "heart": "❤️",
    "arrow": "➡️", "cross": "❌", "warn": "⚠️", "globe": "🌐"
}

def load_track():
    try:
        if os.path.exists(TRACK_FILE):
            with open(TRACK_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {}

def save_track(data):
    with open(TRACK_FILE, 'w') as f:
        json.dump(data, f)

def is_new_day(last_time_str):
    try:
        last = datetime.fromisoformat(last_time_str).astimezone(TIMEZONE)
        now = datetime.now(TIMEZONE)
        reset_today = now.replace(hour=RESET_HOUR, minute=RESET_MIN, second=0, microsecond=0)
        if now < reset_today:
            reset_today -= timedelta(days=1)
        return last < reset_today
    except:
        return True

def check_and_update_limit(user_id):
    data = load_track()
    uid = str(user_id)
    now_iso = datetime.now(TIMEZONE).isoformat()
    if uid not in data or is_new_day(data[uid].get("last_reset", "")):
        data[uid] = {"count": 0, "last_reset": now_iso}
    if data[uid]["count"] >= DAILY_LIMIT:
        return False, 0
    data[uid]["count"] += 1
    data[uid]["last_reset"] = data[uid].get("last_reset", now_iso)
    save_track(data)
    remaining = DAILY_LIMIT - data[uid]["count"]
    return True, remaining

async def call_like_api(uid, region="IND"):
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector, timeout=TIMEOUT) as session:
        for api_url in LIKE_APIS:
            # direct + proxy dono try karega
            urls = [f"{api_url}/like?uid={uid}&region={region}"]
            for p in PROXY_LIST:
                urls.append(f"{p}{api_url}/like?uid={uid}&region={region}")
            for url in urls:
                try:
                    async with session.get(url) as r:
                        txt = await r.text()
                        if r.status == 200 and len(txt) > 10:
                            return True, txt
                except: continue
        return False, "All APIs Failed - Try again after 2 min"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"{E['crown']} Bot Online {E['crown']}\n\n{E['user']} Owner: {OWNER}\n{E['lock']} Daily Limit: {DAILY_LIMIT}/day\n{E['pin']} Reset: 4:30 AM IST\n\n{E['arrow']} /like <uid> [region]"
    await update.message.reply_text(text)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def like_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type != "private" and chat_id != ALLOWED_GROUP:
        return
    if not context.args:
        await update.message.reply_text(f"{E['warn']} Use: /like 2822729179 IND")
        return
    target_uid = context.args[0]
    region = context.args[1] if len(context.args) > 1 else "IND"
    user_id = update.effective_user.id
    ok, remaining = check_and_update_limit(user_id)
    if not ok:
        await update.message.reply_text(f"{E['cross']} {E['lock']} Limit Khatam! {DAILY_LIMIT}/{DAILY_LIMIT}\n{E['pin']} Reset 4:30 AM")
        return
    msg = await update.message.reply_text(f"{E['fire']} Sending Like to {target_uid}...")
    success, res = await call_like_api(target_uid, region)
    if success:
        await msg.edit_text(f"{E['ok']} {E['party']} Like Sent to {target_uid} {E['sparkle']}\n{E['star']} Region: {region}\n{E['diamond']} Bache: {remaining}/{DAILY_LIMIT}")
    else:
        data = load_track()
        if str(user_id) in data:
            data[str(user_id)]["count"] -= 1
            save_track(data)
        await msg.edit_text(f"{E['cross']} Fail: {res}")

async def visit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Visit coming soon")
async def spam_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Spam coming soon")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("like", like_cmd))
app.add_handler(CommandHandler("visit", visit_cmd))
app.add_handler(CommandHandler("spam", spam_cmd))
print(f"Bot Started - Limit {DAILY_LIMIT}")
app.run_polling()
