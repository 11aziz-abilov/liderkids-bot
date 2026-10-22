import asyncio
import logging
import sys

# Windows konsolida emojilar xatosiz chiqishi uchun UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from handlers import start, link, results, premium, admin
from scheduler import setup_scheduler

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def start_health_server():
    """Render.com va cron-job.org uchun 24/7 healthcheck web server"""
    port = int(os.getenv("PORT", "8080"))

    async def handle_ping(request):
        return web.Response(
            text="🦁 LiderKids Bot is running 24/7!\nStatus: OK\nService: Active",
            status=200,
            content_type="text/plain"
        )

    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    app.router.add_get("/ping", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Healthcheck server {port}-portda ishga tushdi (Render & cron-job uchun).")
    return runner

async def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN topilmadi! Iltimos, .env faylida BOT_TOKEN ni ko'rsating.")
        return

    logger.info("🦁 LiderKids «Ota-ona paneli» boti ishga tushmoqda...")

    # Render va cron-job ping'lari uchun mini web server
    web_runner = await start_health_server()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Routerlarni ro'yxatdan o'tkazish
    dp.include_router(start.router)
    dp.include_router(link.router)
    dp.include_router(results.router)
    dp.include_router(premium.router)
    dp.include_router(admin.router)

    # Kunlik kechki hisobot jo'natuvchi scheduler ni yoqish
    scheduler = setup_scheduler(bot)

    # Eski kutilmagan xabarlarni o'tkazib yuborish va polling ni boshlash
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🚀 Bot muvaffaqiyatli ishga tushdi va xabarlarni kutmoqda!")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await web_runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
