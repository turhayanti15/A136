import threading
from dotenv import load_dotenv
load_dotenv()
from bot.mainbot import build_app
from checker.checker import start_checker

def run_checker_in_thread():
    import asyncio
    asyncio.run(start_checker())

def main():
    app = build_app()
    checker_thread = threading.Thread(target=run_checker_in_thread, daemon=True)
    checker_thread.start()
    print("[BOT] Running polling (sync)...")
    app.run_polling()

if __name__ == '__main__':
    print("[BOT] Starting (threaded checker & polling)...")
    main()