from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from config import ADMIN_ID
from database import db
from keyboards import get_main_keyboard, get_children_selection_keyboard

router = Router()

async def get_active_child_info(telegram_id: int):
    parent = await db.get_parent(telegram_id)
    if not parent or not parent.get("children"):
        return None, None
    children = parent.get("children", [])
    active_id = parent.get("active_child_id") or children[0].get("id")
    active_child = next((c for c in children if c.get("id") == active_id), children[0])
    return parent, active_child

@router.message(F.text == "📊 Bugungi natijalar")
async def show_daily_results(message: Message):
    parent, child = await get_active_child_info(message.from_user.id)
    if not child:
        is_adm = (message.from_user.id == ADMIN_ID and ADMIN_ID != 0)
        await message.answer(
            "⚠️ Hali birorta ham farzand bog'lanmagan. Iltimos, avval 6 xonali kod orqali farzandingizni ulang.",
            reply_markup=get_main_keyboard(has_child=False, is_admin=is_adm)
        )
        return

    child_key = child.get("firebase_key") or child.get("id")
    perf = await db.get_child_performance(child_key)

    total_quizzes = perf["total_quizzes"]
    percentage = perf["correct_percentage"]
    weak_topics = perf["weak_topics"]
    plan = perf["plan"]

    status_icon = "🟢" if percentage >= 80 else ("🟡" if percentage >= 60 else "🔴")

    weak_text = ""
    if weak_topics:
        weak_text = "\n\n⚠️ <b>E'tibor qaratish kerak bo'lgan zaif mavzular:</b>\n"
        for i, topic in enumerate(weak_topics, 1):
            weak_text += f"  {i}. {topic}\n"
    else:
        weak_text = "\n\n🌟 <b>Zaif mavzular yo'q!</b> Barcha testlar a'lo darajada o'zlashtirilgan! 👏\n"

    report_text = (
        f"📊 <b>Bugungi Natijalar Xulosasi:</b>\n\n"
        f"👦 <b>O'quvchi:</b> {perf['name']} ({perf['grade']}-sinf)\n"
        f"💎 <b>Tarif:</b> {'⭐️ PREMIUM' if plan == 'premium' else 'Standart'}\n\n"
        f"📝 <b>Yechilgan testlar:</b> {total_quizzes} ta\n"
        f"🎯 <b>To'g'ri javoblar foizi:</b> {status_icon} <b>{percentage}%</b>\n"
        f"🔥 <b>Ketma-ketlik (Streak):</b> {perf['streaks']} kun\n"
        f"🪙 <b>Bugungi tangalar:</b> +{perf['coins']} ta"
        f"{weak_text}\n"
        f"💡 <i>Tavsiya: Prezident maktabi imtihonlariga tayyorgarlik uchun har kuni kamida 20 ta test yechish va zaif mavzularni takrorlash tavsiya etiladi.</i>"
    )

    await message.answer(report_text, parse_mode="HTML")

@router.message(F.text == "📈 Zaif mavzular")
async def show_weak_topics(message: Message):
    parent, child = await get_active_child_info(message.from_user.id)
    if not child:
        is_adm = (message.from_user.id == ADMIN_ID and ADMIN_ID != 0)
        await message.answer("⚠️ Hali farzand bog'lanmagan.", reply_markup=get_main_keyboard(has_child=False, is_admin=is_adm))
        return

    child_key = child.get("firebase_key") or child.get("id")
    perf = await db.get_child_performance(child_key)
    weak_topics = perf["weak_topics"]

    if weak_topics:
        text = (
            f"🔍 <b>{perf['name']} uchun tahlil qilingan zaif mavzular:</b>\n\n"
            f"Ushbu mavzularda o'quvchi xatoliklarga yo'l qo'ygan. Ularni ilovadagi video-darslar va qo'shimcha mashqlar orqali qayta takrorlash zarur:\n\n"
        )
        for i, t in enumerate(weak_topics, 1):
            text += f"📌 <b>{t}</b>\n"
    else:
        text = (
            f"🎉 <b>{perf['name']}</b> uchun zaif mavzular aniqlanmadi!\n"
            f"Farzandingiz barcha darslarni yuqori ballga topshirmoqda. Barakasini bersin! 🚀"
        )

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "👦 Farzandim profili")
async def show_child_profile(message: Message):
    parent, child = await get_active_child_info(message.from_user.id)
    if not child:
        is_adm = (message.from_user.id == ADMIN_ID and ADMIN_ID != 0)
        await message.answer("⚠️ Hali farzand bog'lanmagan.", reply_markup=get_main_keyboard(has_child=False, is_admin=is_adm))
        return

    child_key = child.get("firebase_key") or child.get("id")
    learner = await db.get_learner_by_id(child_key) or {}

    name = learner.get("name", child.get("name", "O'quvchi"))
    grade = learner.get("grade", child.get("grade", 1))
    plan = learner.get("plan", "free")
    region = learner.get("region", "Aniqlanmagan")
    district = learner.get("district", "")
    school = learner.get("school", "Umumta'lim maktabi")
    coins = learner.get("coins", 0)
    streaks = learner.get("streaks", 0)
    xp = learner.get("xp", 0)
    badge = learner.get("badge", "Yosh Izlanuvchi 🦁")

    profile_text = (
        f"👤 <b>O'quvchi Shaxsiy Profili:</b>\n\n"
        f"👦 <b>Ism-familiya:</b> {name}\n"
        f"🎓 <b>Sinf:</b> {grade}-sinf\n"
        f"📍 <b>Hudud:</b> {region}, {district}\n"
        f"🏫 <b>Maktab:</b> {school}\n"
        f"🎖 <b>Unvon (Badge):</b> {badge}\n\n"
        f"💎 <b>Obuna tarifi:</b> {'⭐️ PREMIUM' if plan == 'premium' else 'Standart (Bepul)'}\n"
        f"🔥 <b>Ketma-ket kunlar (Streak):</b> {streaks} kun\n"
        f"🪙 <b>Jamg'arilgan tangalar:</b> {coins} 🪙\n"
        f"⚡️ <b>Tajriba ballari (XP):</b> {xp} XP\n"
    )

    await message.answer(profile_text, parse_mode="HTML")

@router.message(F.text == "🔄 Farzandni almashtirish")
async def switch_child(message: Message):
    parent = await db.get_parent(message.from_user.id)
    children = parent.get("children", []) if parent else []

    if not children:
        is_adm = (message.from_user.id == ADMIN_ID and ADMIN_ID != 0)
        await message.answer("Siz hali birorta ham farzandni bog'lamagansiz.", reply_markup=get_main_keyboard(has_child=False, is_admin=is_adm))
        return

    if len(children) == 1:
        await message.answer(
            f"Sizda faqat 1 nafar farzand bog'langan: <b>{children[0].get('name')}</b>.\n"
            "Yangi farzand qo'shish uchun <b>«🔗 Yangi farzand ulash»</b> tugmasini bosing.",
            parse_mode="HTML"
        )
        return

    await message.answer(
        "Qaysi farzandingiz natijalarini ko'rmoqchisiz? Tanlang:",
        reply_markup=get_children_selection_keyboard(children)
    )

@router.callback_query(F.data.startswith("select_child_"))
async def process_child_selection(callback: CallbackQuery):
    child_id = callback.data.replace("select_child_", "")
    await db.set_active_child(callback.from_user.id, child_id)
    await callback.answer("Farzand tanlandi!")

    parent = await db.get_parent(callback.from_user.id)
    children = parent.get("children", [])
    active = next((c for c in children if c.get("id") == child_id), None)
    c_name = active.get("name") if active else "Farzand"

    await callback.message.edit_text(
        f"✅ <b>{c_name}</b> faol o'quvchi sifatida tanlandi!\n"
        "Endi uning natijalarini ko'rishingiz mumkin.",
        parse_mode="HTML"
    )
