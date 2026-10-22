import asyncio
import logging
import sys

# Windows konsolida emojilar xatosiz chiqishi uchun UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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

async def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN topilmadi! Iltimos, .env faylida BOT_TOKEN ni ko'rsating.")
        return

    logger.info("🦁 LiderKids «Ota-ona paneli» boti ishga tushmoqda...")

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
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
