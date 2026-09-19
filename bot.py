import re, sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# === APNA NAYA TOKEN YAHAN DALO ===
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")
# ===================================

CHANNEL = "@Markhor_Coin"
GROUP = "@MarkhorCoinChat"
TWITTER = "https://x.com/MarkhorCoinPk"

conn = sqlite3.connect('khor.db', check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, wallet TEXT, ref_by INTEGER, balance INTEGER DEFAULT 5000)")
conn.commit()

def valid_wallet(a):
        return bool(re.match(r'^0x[a-fA-F0-9]{40}$',a.strip()))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    ref_by = int(args[0]) if args and args[0].isdigit() and int(args[0])!= user.id else None

    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id=?", (user.id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (id, username, ref_by) VALUES (?,?,?)", (user.id, user.username, ref_by))
        if ref_by:
            cur.execute("UPDATE users SET balance = balance + 1000 WHERE id=?", (ref_by,))
            try:
                await context.bot.send_message(ref_by, f"🎉 Referral! +1000 KHOR. New user: @{user.username}")
            except: pass
        conn.commit()

    cur.execute("SELECT balance FROM users WHERE id=?", (user.id,))
    bal = cur.fetchone()[0]
    me = await context.bot.get_me()
    ref_link = f"https://t.me/{me.username}?start={user.id}"

    text = f"""
🦌 *MARKHOR COIN ($KHOR) AIRDROP* 🇵🇰

*Reward:* 5000 KHOR
*Per Referral:* 1000 KHOR

*Your Balance:* {bal} KHOR
*Your Referral Link:*
`{ref_link}`

👇 *Tasks Complete Karo:*
"""
    kb = [
        [InlineKeyboardButton("📢 Channel Join", url=f"https://t.me/{CHANNEL.replace('@','')}")],
        [InlineKeyboardButton("👥 Group Join", url=f"https://t.me/{GROUP.replace('@','')}")],
        [InlineKeyboardButton("🐦 Twitter Follow", url=TWITTER)],
        [InlineKeyboardButton("✅ Wallet Submit Karo", callback_data="submit")],
        [InlineKeyboardButton("💰 Balance", callback_data="bal"), InlineKeyboardButton("👥 My Referrals", callback_data="refs")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    if q.data == "submit":
        await q.message.reply_text("📤 *Apna BSC (BEP20) Wallet Bhejo*\nExample: `0x1234...`", parse_mode='Markdown')
    elif q.data == "bal":
        cur = conn.cursor()
        cur.execute("SELECT balance, wallet FROM users WHERE id=?", (uid,))
        b,w = cur.fetchone()
        await q.message.reply_text(f"💰 Balance: {b} KHOR\nWallet: {w if w else 'Not set'}")
    elif q.data == "refs":
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE ref_by=?", (uid,))
        count = cur.fetchone()[0]
        await q.message.reply_text(f"👥 Total Referrals: {count}\nEarning: {count*1000} KHOR")

async def save_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if not valid_wallet(txt):
        return
    conn.execute("UPDATE users SET wallet=? WHERE id=?", (txt, update.effective_user.id))
    conn.commit()
    await update.message.reply_text(f"✅ *Wallet Saved!*\n`{txt}`\n\nAirdrop ke time distribution hoga.", parse_mode='Markdown')

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users"); total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE wallet IS NOT NULL"); with_wallet = cur.fetchone()[0]
    await update.message.reply_text(f"📊 *Admin Panel*\nTotal: {total}\nWith Wallet: {with_wallet}\n\n/export - CSV Download", parse_mode='Markdown')

async def export_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import csv
    cur = conn.cursor()
    cur.execute("SELECT id, username, wallet, ref_by, balance FROM users WHERE wallet IS NOT NULL")
    rows = cur.fetchall()
    with open('khor_wallets.csv','w',newline='',encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['ID','Username','Wallet','RefBy','Balance']); w.writerows(rows)
    await update.message.reply_document(open('khor_wallets.csv','rb'), caption=f"📁 {len(rows)} Wallets")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("export", export_csv))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_wallet))

print("KHOR Bot Started...")
app.run_polling()
