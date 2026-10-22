import asyncio
import logging
from datetime import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import REPORT_HOUR, REPORT_MINUTE, TIMEZONE
from database import db

async def send_evening_reports(bot: Bot):
    """
    Har kuni kechqurun barcha ota-onalarga farzandining natijalarini yuborish
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Kunlik kechki hisobotlar yuborilmoqda...")

    parents = await db.get_all_parents()
    if not parents:
        return

    for tg_id_str, parent_data in parents.items():
        if not isinstance(parent_data, dict):
            continue

        try:
            telegram_id = int(tg_id_str)
        except ValueError:
            continue

        children = parent_data.get("children", [])
        if not children:
            continue

        # Har bir farzand uchun hisobot tuzish
        for child in children:
            child_key = child.get("firebase_key") or child.get("id")
            if not child_key:
                continue

            perf = await db.get_child_performance(child_key)

            total_quizzes = perf["total_quizzes"]
            percentage = perf["correct_percentage"]
            weak_topics = perf["weak_topics"]
            child_name = perf["name"]
            grade = perf["grade"]

            status_icon = "🟢" if percentage >= 80 else ("🟡" if percentage >= 60 else "🔴")

            weak_text = ""
            if weak_topics:
                weak_text = "\n\n⚠️ <b>E'tibor qaratish kerak bo'lgan zaif mavzular:</b>\n"
                for i, topic in enumerate(weak_topics, 1):
                    weak_text += f"  {i}. {topic}\n"
            else:
                weak_text = "\n\n🌟 <b>Zaif mavzular aniqlanmadi!</b> Barcha testlar a'lo o'zlashtirilgan! 👏\n"

            msg = (
                f"🌙 <b>Xayrli oqshom! Farzandingizning bugungi hisoboti:</b>\n\n"
                f"👦 <b>O'quvchi:</b> {child_name} ({grade}-sinf)\n"
                f"📝 <b>Yechilgan testlar:</b> {total_quizzes} ta\n"
                f"🎯 <b>To'g'ri javoblar ko'rsatkichi:</b> {status_icon} <b>{percentage}%</b>\n"
                f"🔥 <b>Ketma-ketlik (Streak):</b> {perf['streaks']} kun\n"
                f"🪙 <b>Topilgan tangalar:</b> {perf['coins']}"
                f"{weak_text}\n"
                f"🦁 <i>LiderKids: Bolangizni bugungi mehnati uchun maqtashni unutmang!</i>"
            )

            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=msg,
                    parse_mode="HTML"
                )
                await asyncio.sleep(0.1)  # Telegram limitlariga tushmaslik uchun
            except Exception as e:
                print(f"[Daily Report Error] ID: {telegram_id} -> {e}")

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Rejalashtiruvchini sozlash va ishga tushirish"""
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        send_evening_reports,
        trigger="cron",
        hour=REPORT_HOUR,
        minute=REPORT_MINUTE,
        args=[bot]
    )
    scheduler.start()
    logging.info(f"Scheduler faollashtirildi: Har kuni soat {REPORT_HOUR:02d}:{REPORT_MINUTE:02d} da xabar yuboriladi.")
    return scheduler
