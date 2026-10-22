from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import CARD_NUMBER, CARD_HOLDER, PREMIUM_PRICE, ADMIN_ID
from database import db
from states import PaymentState
from keyboards import (
    get_main_keyboard,
    get_cancel_keyboard,
    get_premium_inline_keyboard,
    get_admin_payment_keyboard
)

router = Router()

@router.message(F.text == "⭐️ Premium olish")
async def show_premium_offer(message: Message, state: FSMContext):
    await state.clear()
    parent = await db.get_parent(message.from_user.id)
    if not parent or not parent.get("children"):
        is_adm = (message.from_user.id == ADMIN_ID and ADMIN_ID != 0)
        await message.answer(
            "⚠️ Avval farzandingizni 6 xonali kod orqali ulang, shundan so'ng Premium xizmatini faollashtirishingiz mumkin.",
            reply_markup=get_main_keyboard(has_child=False, is_admin=is_adm)
        )
        return

    children = parent.get("children", [])
    active_id = parent.get("active_child_id") or children[0].get("id")
    child = next((c for c in children if c.get("id") == active_id), children[0])

    # Bola tarifi
    child_key = child.get("firebase_key") or child.get("id")
    learner = await db.get_learner_by_id(child_key) or {}
    is_premium = learner.get("plan") == "premium"

    child_name = child.get("name", "Farzandingiz")

    if is_premium:
        await message.answer(
            f"🎉 <b>Tabriklaymiz!</b>\n\n"
            f"<b>{child_name}</b> allaqachon <b>⭐️ PREMIUM</b> tarifida!\n"
            f"Barcha darslar, tahlillar va maslahatlar to'liq ochiq.",
            parse_mode="HTML"
        )
        return

    text = (
        f"⭐️ <b>LiderKids — Premium Ta'lim Paketi</b>\n\n"
        f"Farzandingiz: <b>{child_name}</b> ({child.get('grade', 1)}-sinf)\n\n"
        f"<b>Premium bilan nimalarga ega bo'lasiz?</b>\n"
        f"✅ Prezident va ixtisoslashtirilgan maktablar uchun barcha eksklyuziv testlar;\n"
        f"✅ Har bir savolning video va matnli batafsil tahlili;\n"
        f"✅ Shercha AI sun'iy intellekt murabbiyidan cheksiz yordam;\n"
        f"✅ Zaif mavzular bo'yicha maxsus tuzilgan mustahkamlash mashqlari;\n"
        f"✅ To'liq reyting va sovrinlar tanlovlarida ishtirok etish.\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>To'lov summasi:</b> <code>{PREMIUM_PRICE}</code>\n"
        f"💳 <b>Karta raqami:</b> <code>{CARD_NUMBER}</code>\n"
        f"👤 <b>Karta egasi:</b> <b>{CARD_HOLDER}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"To'lovni amalga oshirgach, quyidagi <b>«📸 Chek rasmini yuborish»</b> tugmasini bosing va kvitansiyani yuboring:"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_premium_inline_keyboard(CARD_NUMBER)
    )

@router.callback_query(F.data == "send_receipt")
async def ask_receipt_photo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentState.waiting_for_receipt)
    await callback.message.answer(
        "📸 Iltimos, amalga oshirilgan to'lovning <b>chek (skrinshot) rasmini</b> shu yerga yuboring:\n\n"
        "<i>(Chekda sana, summa va karta raqami aniq ko'ringan bo'lishi lozim)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_payment")
async def cancel_payment_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("To'lov jarayoni bekor qilindi.")
    await callback.answer("Bekor qilindi")

@router.message(PaymentState.waiting_for_receipt, F.photo)
async def process_receipt_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    is_adm = (user_id == ADMIN_ID and ADMIN_ID != 0)
    parent = await db.get_parent(user_id)
    if not parent or not parent.get("children"):
        await state.clear()
        await message.answer("Farzand topilmadi.", reply_markup=get_main_keyboard(has_child=False, is_admin=is_adm))
        return

    children = parent.get("children", [])
    active_id = parent.get("active_child_id") or children[0].get("id")
    child = next((c for c in children if c.get("id") == active_id), children[0])
    child_key = child.get("firebase_key") or child.get("id")
    child_name = child.get("name", "O'quvchi")
    child_grade = child.get("grade", 1)

    # Eng sifatli rasm versiyasini olish
    photo_file_id = message.photo[-1].file_id

    # Bazaga to'lov arizasini saqlash
    payment_id = await db.create_payment_request(
        telegram_id=user_id,
        parent_name=message.from_user.full_name,
        child_key=child_key,
        child_name=child_name,
        photo_file_id=photo_file_id,
        amount=PREMIUM_PRICE
    )

    await state.clear()

    # Ota-onaga tasdiq xabari
    await message.answer(
        "✅ <b>To'lov chekingiz qabul qilindi!</b>\n\n"
        "To'lov admin tomonidan tez orada ko'rib chiqiladi. "
        "Tasdiqlanishi bilan sizga xabar yuboriladi va farzandingiz hisobi Premium ga o'tkaziladi. 🚀",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(has_child=True, is_admin=is_adm)
    )

    # Adminga yuborish
    if ADMIN_ID and ADMIN_ID != 0:
        admin_caption = (
            f"🔔 <b>YANGI TO'LOV CHEKI KELDI!</b>\n\n"
            f"👤 <b>Ota-ona:</b> {message.from_user.full_name} (ID: <code>{message.from_user.id}</code>)\n"
            f"👦 <b>Farzand:</b> {child_name} ({child_grade}-sinf)\n"
            f"🔑 <b>Child Key:</b> <code>{child_key}</code>\n"
            f"💵 <b>Summa:</b> {PREMIUM_PRICE}\n"
            f"🆔 <b>To'lov ID:</b> <code>{payment_id}</code>\n\n"
            f"Tasdiqlaysizmi yoki rad etasizmi?"
        )
        try:
            await message.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo_file_id,
                caption=admin_caption,
                parse_mode="HTML",
                reply_markup=get_admin_payment_keyboard(payment_id)
            )
        except Exception as e:
            print(f"[Admin Send Error] {e}")

@router.message(PaymentState.waiting_for_receipt)
async def invalid_receipt_message(message: Message):
    await message.answer(
        "⚠️ Iltimos, to'lov chekining <b>rasmini (skrinshot)</b> yuboring yoki «❌ Bekor qilish» tugmasini bosing.",
        reply_markup=get_cancel_keyboard()
    )
