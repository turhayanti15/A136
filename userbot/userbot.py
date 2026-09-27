import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

client = TelegramClient("userbot_session", api_id, api_hash)

async def start_userbot():
    print("[USERBOT] Starting...")
    await client.start()
    print("[USERBOT] Logged in successfully!")