from telethon import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
SESSION = "checker_session"

client = TelegramClient(SESSION, api_id, api_hash)

async def main():
    await client.start()
    print("Session successfully created!")

import asyncio
asyncio.run(main())