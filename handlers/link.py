from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import db
from states import LinkChildState
from keyboards import get_main_keyboard, get_cancel_keyboard
from config import ADMIN_ID

router = Router()

@router.message(F.text.in_(["🔗 Farzandni ulash (6 xonali kod)", "🔗 Yangi farzand ulash"]))
async def ask_child_code(message: Message, state: FSMContext):
    await state.set_state(LinkChildState.waiting_for_code)
    await message.answer(
        "📲 Farzandingizning <b>LiderKids ilovasidagi 6 xonali ulanish kodini</b> kiriting:\n\n"
        "<i>(Masalan: 582194)</i>\n\n"
        "💡 <i>Eslatma: Kodni ilovadagi o'quvchi profilidan yoki sozlamalar bo'limidan ko'rishingiz mumkin.</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

@router.message(LinkChildState.waiting_for_code)
async def process_child_code(message: Message, state: FSMContext):
    code = message.text.strip()

    if not code.isdigit() or len(code) != 6:
        await message.answer(
            "⚠️ Kod faqat <b>6 ta raqamdan</b> iborat bo'lishi kerak.\n"
            "Iltimos, qaytadan kiriting (Masalan: 482103):",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return

    # Firebase'dan qidirish
    learner = await db.find_learner_by_code(code)

    if not learner:
        await message.answer(
            f"❌ <b>Bunday 6 xonali kodga ega o'quvchi topilmadi ({code})!</b>\n\n"
            "Iltimos, ilovadagi kodni to'g'ri kiritganingizni tekshiring yoki farzandingiz ilovada ro'yxatdan o'tganligiga ishonch hosil qiling.",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return

    # Muvaffaqiyatli topildi, bolani ota-onaga bog'lash
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    await db.link_child_to_parent(user_id, user_name, learner)
    await state.clear()

    name = learner.get("name", "O'quvchi")
    grade = learner.get("grade", 1)
    plan = learner.get("plan", "free")
    plan_badge = "⭐️ PREMIUM" if plan == "premium" else "Standart (Bepul)"
    streaks = learner.get("streaks", 0)
    coins = learner.get("coins", 0)
    xp = learner.get("xp", 0)

    success_text = (
        f"🎉 <b>Farzandingiz muvaffaqiyatli bog'landi!</b>\n\n"
        f"👦 <b>Ism:</b> {name}\n"
        f"📚 <b>Sinf:</b> {grade}-sinf\n"
        f"💎 <b>Tarif:</b> {plan_badge}\n"
        f"🔥 <b>Olovchalar (Ketma-ketlik):</b> {streaks} kun\n"
        f"🪙 <b>Tangalar:</b> {coins}\n"
        f"⚡️ <b>Tajriba (XP):</b> {xp}\n\n"
        f"Endi siz ushbu bot orqali har kuni bolangizning natijalarini kuzatib borasiz "
        f"va qo'shimcha imkoniyatlardan foydalanishingiz mumkin! 🚀"
    )

    is_admin = (user_id == ADMIN_ID and ADMIN_ID != 0)
    await message.answer(
        success_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(has_child=True, is_admin=is_admin)
    )
