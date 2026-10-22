from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database import db
from keyboards import get_main_keyboard
from config import ADMIN_ID

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    is_admin = (user_id == ADMIN_ID and ADMIN_ID != 0)

    parent = await db.get_parent(user_id)
    children = parent.get("children", []) if parent else []

    if not children:
        welcome_text = (
            f"Assalomu alaykum, hurmatli <b>{user_name}</b>! 🦁\n\n"
            f"<b>LiderKids — «Ota-ona paneli»</b> botiga xush kelibsiz!\n\n"
            f"Ushbu bot orqali siz:\n"
            f"• Farzandingizning kunlik test natijalarini kuzatishingiz;\n"
            f"• Qaysi mavzularda xato qilayotgani (zaif mavzular)ni bilishingiz;\n"
            f"• Prezident maktabiga tayyorgarlik darajasini monitoring qilishingiz;\n"
            f"• Premium obunani rasmiylashtirishingiz mumkin.\n\n"
            f"👇 Boshlash uchun ilovadagi <b>6 xonali kod</b> orqali farzandingizni ulang:"
        )
        if is_admin:
            welcome_text += "\n\n👑 <i>Siz tizim administratorisiz. Quyidagi menyudan boshqaruv panelini ochishingiz mumkin.</i>"

        await message.answer(
            welcome_text,
            parse_mode="HTML",
            reply_markup=get_main_keyboard(has_child=False, is_admin=is_admin)
        )
    else:
        active_id = parent.get("active_child_id") or children[0].get("id")
        active_child = next((c for c in children if c.get("id") == active_id), children[0])
        child_name = active_child.get("name", "Farzandingiz")
        child_grade = active_child.get("grade", 1)

        welcome_text = (
            f"Assalomu alaykum, <b>{user_name}</b>! 👋\n\n"
            f"Tanlangan farzand: <b>{child_name}</b> ({child_grade}-sinf)\n\n"
            f"Quyidagi menyu orqali kerakli bo'limni tanlang:"
        )
        if is_admin:
            welcome_text += "\n\n👑 <i>Administrator rejimi faol.</i>"

        await message.answer(
            welcome_text,
            parse_mode="HTML",
            reply_markup=get_main_keyboard(has_child=True, is_admin=is_admin)
        )

@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    is_admin = (user_id == ADMIN_ID and ADMIN_ID != 0)
    parent = await db.get_parent(user_id)
    children = parent.get("children", []) if parent else []
    await message.answer(
        "Amal bekor qilindi.",
        reply_markup=get_main_keyboard(has_child=bool(children), is_admin=is_admin)
    )

@router.message(F.text == "ℹ️ Bot haqida")
@router.message(F.text == "ℹ️ Yordam va Qo'llab-quvvatlash")
async def help_handler(message: Message):
    help_text = (
        "<b>LiderKids Platformasi — Ota-ona paneli</b>\n\n"
        "Platformamiz 1-4 sinf o'quvchilarini Prezident va ixtisoslashtirilgan maktablarga "
        "tayyorlashga mo'ljallangan interaktiv ta'lim tizimidir.\n\n"
        "🔹 <b>Qanday bog'lanadi?</b>\n"
        "Farzandingiz LiderKids ilovasiga kirganida uning profilida 6 xonali kod chiqadi. "
        "Shu kodni ushbu botga kiritasiz.\n\n"
        "🔹 <b>Har kuni hisobot:</b>\n"
        "Bot har kuni soat 20:00 da bolangizning kunlik yechgan testlari, foizi va zaif mavzulari haqida "
        "xabar yuboradi.\n\n"
        "📞 Savollar yoki yordam uchun: @LiderKidsAdmin\n"
        "🌐 Veb-sayt: liderkids.uz"
    )
    await message.answer(help_text, parse_mode="HTML")
