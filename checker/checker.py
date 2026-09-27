import os
import json
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv
from telegram import Bot
from db import get_pool, get_usernames
from telethon.tl.functions.channels import UpdateUsernameRequest

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = "checker_session"
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("OWNER_ID"))
NOTIFIED_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'notified.json')
CHANNELS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'channels.json')

def load_notified():
    if os.path.exists(NOTIFIED_FILE):
        with open(NOTIFIED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_notified(notified):
    os.makedirs(os.path.dirname(NOTIFIED_FILE), exist_ok=True)
    with open(NOTIFIED_FILE, "w") as f:
        json.dump(list(notified), f)

def load_channel_links():
    with open(CHANNELS_FILE, "r") as f:
        return json.load(f)

async def is_username_available(client, username):
    try:
        await client.get_entity(username)
        return False
    except Exception:
        return True

async def notify_available(username):
    print(f"[NOTIFY] Akan mengirim notifikasi untuk: {username}")
    if not username.startswith('@'):
        username = '@' + username
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Successfully keep: {username}")
    print(f"[NOTIFY] Notifikasi terkirim untuk: {username}")

async def keep_username_to_channel(client, channel_link, username):
    try:
        entity = await client.get_entity(channel_link)
        # Cek apakah channel sudah punya username publik
        if getattr(entity, "username", None):
            print(f"Channel {channel_link} sudah punya username: {entity.username}")
            return False
        await client(UpdateUsernameRequest(channel=entity, username=username))
        print(f"Berhasil keep {username} ke channel {channel_link}")
        return True
    except Exception as e:
        print(f"Gagal keep {username} ke channel {channel_link}: {e}")
        return False

async def check_usernames():
    pool = await get_pool()
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        notified = load_notified()
        # Use a lock to protect the notified set and file writes when running batches concurrently
        lock = asyncio.Lock()
        while True:
            usernames = await get_usernames(pool)
            # Menjalankan cek dalam batch 30 username setiap 20 detik
            print("Usernames terbaru:", usernames)
            if not usernames:
                await asyncio.sleep(5)
                continue

            batch_size = 10

            async def process_batch(batch, batch_index):
                channel_links = load_channel_links()
                for username in batch:
                    username_clean = username.lstrip('@')
                    # Fast-check under lock to avoid duplicate processing
                    async with lock:
                        if username_clean in notified:
                            continue
                    if await is_username_available(client, username_clean):
                        print(f"{username_clean} available")
                        keep_success = False
                        for channel_link in channel_links:
                            result = await keep_username_to_channel(client, channel_link, username_clean)
                            if result:
                                keep_success = True
                        if keep_success:
                            await notify_available(username_clean)
                            async with lock:
                                notified.add(username_clean)
                                save_notified(notified)

            # Create all batch tasks and run them concurrently
            tasks = []
            batch_index = 1
            for batch_start in range(0, len(usernames), batch_size):
                batch = usernames[batch_start:batch_start + batch_size]
                tasks.append(asyncio.create_task(process_batch(batch, batch_index)))
                batch_index += 1

            # Wait for all batches to finish, then sleep once before next cycle
            if tasks:
                await asyncio.gather(*tasks)
            await asyncio.sleep(5)

async def start_checker():
    await check_usernames()