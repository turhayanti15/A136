import os
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from db import get_pool, get_usernames, add_username, delete_username

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("ADMIN_CHAT_ID"))
PAGE_SIZE = 10

async def start(update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You can't run this bot, only be managed by the owner.")
        return
    await update.message.reply_text("Bot is ready to use, please enter your username!")

async def add(update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You can't add usernames, only the owner can.")
        return
    if not context.args:
        await update.message.reply_text("Format: /add @")
        return
    if len(context.args) > 50:
        await update.message.reply_text("Max 50!")
        return
    # Lazy init pool
    if 'db_pool' not in context.bot_data:
        context.bot_data['db_pool'] = await get_pool()
    pool = context.bot_data['db_pool']
    added = []
    for username in context.args:
        if not username.startswith('@'):
            username = '@' + username
        await add_username(pool, username)
        added.append(username)
    await update.message.reply_text(f"Added a username: {', '.join(added)}")

async def list_usernames(update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You can't view this list, only the owner can.")
        return
    # Lazy init pool
    if 'db_pool' not in context.bot_data:
        context.bot_data['db_pool'] = await get_pool()
    pool = context.bot_data['db_pool']
    usernames = await get_usernames(pool)
    if not usernames:
        await update.message.reply_text("There is not a user name in the monitoring list yet!")
        return

    # Pastikan semua username di-list dengan @ di awal
    usernames = [uname if uname.startswith('@') else '@' + uname for uname in usernames]

    page = 1
    total_pages = (len(usernames) + PAGE_SIZE - 1) // PAGE_SIZE
    await send_username_page(update, usernames, page, total_pages)

async def send_username_page(update, usernames, page, total_pages):
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_usernames = usernames[start:end]
    text = f"List Username (page {page}/{total_pages}):\n"
    text += "\n".join([f"{i+1+start}. {uname}" for i, uname in enumerate(page_usernames)])

    keyboard = []

    # Tombol nomor halaman (maksimal 5 tombol, bisa diatur sesuai kebutuhan)
    max_buttons = 5
    half = max_buttons // 2
    start_page = max(1, page - half)
    end_page = min(total_pages, start_page + max_buttons - 1)
    start_page = max(1, end_page - max_buttons + 1)

    page_buttons = [
        InlineKeyboardButton(
            str(p), callback_data=f"list_page_{p}"
        ) if p != page else InlineKeyboardButton(f"•{p}•", callback_data=f"list_page_{p}")
        for p in range(start_page, end_page + 1)
    ]
    keyboard.append(page_buttons)

    # Tombol prev/next
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"list_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"list_page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def list_page_callback(update, context):
    query = update.callback_query
    page = int(query.data.split("_")[-1])
    pool = context.bot_data['db_pool']
    usernames = await get_usernames(pool)
    total_pages = (len(usernames) + PAGE_SIZE - 1) // PAGE_SIZE
    await send_username_page(update, usernames, page, total_pages)
    await query.answer()

async def delete(update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You can't delete usernames, only the owner can.")
        return
    if not context.args:
        await update.message.reply_text("Format: /delete @")
        return
    # Lazy init pool
    if 'db_pool' not in context.bot_data:
        context.bot_data['db_pool'] = await get_pool()
    pool = context.bot_data['db_pool']
    deleted = []
    for username in context.args:
        # Pastikan username selalu diawali @
        if not username.startswith('@'):
            username = '@' + username
        await delete_username(pool, username)
        deleted.append(username)
    await update.message.reply_text(f"Deleting the username: {', '.join(deleted)}")

def build_app():
    from telegram.ext import ApplicationBuilder
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_usernames))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CallbackQueryHandler(list_page_callback, pattern=r"^list_page_\d+$"))
    return app

async def start_bot():
    print("[BOT] Starting...")
    try:
        app = build_app()
        pool = await get_pool()
        app.bot_data['db_pool'] = pool
        print(f"[BOT] BOT_TOKEN: {BOT_TOKEN}")
        print("[BOT] Running...")
        await app.run_polling()
    except Exception as e:
        print(f"[BOT] ERROR: {e}")