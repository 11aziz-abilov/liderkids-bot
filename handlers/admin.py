import math
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.filters import Command

from config import ADMIN_ID
from database import db, generate_child_code
from keyboards import get_admin_panel_keyboard, get_admin_pagination_keyboard

router = Router()

ITEMS_PER_PAGE = 8

def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id == ADMIN_ID and ADMIN_ID != 0

async def fetch_user_data():
    """Foydalanuvchilar va ota-onalar ma'lumotlarini saralab olish"""
    learners_raw = await db.get_all_learners()
    parents_raw = await db.get_all_parents()

    premium_list = []
    free_list = []
    all_learners = []

    for key, val in learners_raw.items():
        if not isinstance(val, dict):
            continue
        item = dict(val)
        item["firebase_key"] = key
        child_id = item.get("id") or key
        item["resolved_code"] = item.get("parentCode") or item.get("linkCode") or generate_child_code(str(child_id))
        
        plan = item.get("plan", "free")
        if plan == "premium":
            premium_list.append(item)
        else:
            free_list.append(item)
        all_learners.append(item)

    parents_list = []
    for pid, pdata in parents_raw.items():
        if isinstance(pdata, dict):
            pcopy = dict(pdata)
            pcopy["tg_id"] = pid
            parents_list.append(pcopy)

    stats = {
        "total_count": len(all_learners),
        "premium_count": len(premium_list),
        "free_count": len(free_list),
        "parents_count": len(parents_list),
    }

    return stats, premium_list, free_list, all_learners, parents_list

def build_dashboard_text(stats: dict) -> str:
    """Admin panel boshqaruv matni"""
    return (
        f"👑 <b>LiderKids — Administrator Boshqaruv Paneli</b>\n\n"
        f"📊 <b>Foydalanuvchilar statistikasi:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👦 <b>Jami o'quvchilar:</b> {stats['total_count']} ta\n"
        f"⭐️ <b>Pulli (Premium) o'quvchilar:</b> {stats['premium_count']} ta\n"
        f"🆓 <b>Tekin (Standart) o'quvchilar:</b> {stats['free_count']} ta\n"
        f"👥 <b>Botdagi ota-onalar:</b> {stats['parents_count']} ta\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"Quyidagi tugmalar orqali tekin yoki pulli foydalanuvchilar ro'yxatini ko'rishingiz "
        f"yoki fayl ko'rinishida yuklab olishingiz mumkin:"
    )

# --- ADMIN PANEL BOSHQARUV TUGMASI VA KOMANDALAR ---

@router.message(F.text == "👑 Admin Panel")
@router.message(Command("admin"))
@router.message(Command("stats"))
async def admin_panel_entry(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔️ <b>Kirish taqiqlangan!</b>\n"
            "Ushbu bo'lim faqat bot administratori uchun mo'ljallangan.",
            parse_mode="HTML"
        )
        return

    stats, _, _, _, _ = await fetch_user_data()
    text = build_dashboard_text(stats)
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_panel_keyboard(stats))

@router.callback_query(F.data.in_(["admin_panel_home", "admin_refresh"]))
async def admin_panel_home_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    stats, _, _, _, _ = await fetch_user_data()
    text = build_dashboard_text(stats)

    try:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_admin_panel_keyboard(stats)
        )
        await callback.answer("Ma'lumotlar yangilandi! 🔄")
    except Exception:
        await callback.answer("O'zgarish yo'q.")

# --- RO'YXATLARNI SAHIFALAB KO'RSATISH ---

@router.callback_query(F.data.startswith("admin_view_"))
async def admin_view_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    # admin_view_{category}_{page}
    parts = callback.data.split("_")
    if len(parts) < 4:
        return
    category = parts[2]
    try:
        page = int(parts[3])
    except ValueError:
        page = 1

    stats, premium_list, free_list, all_learners, parents_list = await fetch_user_data()

    if category == "premium":
        items = premium_list
        title = "⭐️ <b>Pulli (Premium) foydalanuvchilar ro'yxati</b>"
    elif category == "free":
        items = free_list
        title = "🆓 <b>Tekin (Standart) foydalanuvchilar ro'yxati</b>"
    elif category == "all":
        items = all_learners
        title = "📋 <b>Barcha o'quvchilar ro'yxati</b>"
    elif category == "parents":
        items = parents_list
        title = "👥 <b>Botdagi ota-onalar ro'yxati</b>"
    else:
        await callback.answer("Noma'lum bo'lim!", show_alert=True)
        return

    total_items = len(items)
    total_pages = max(1, math.ceil(total_items / ITEMS_PER_PAGE))
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_items = items[start_idx:end_idx]

    content = f"{title}\n"
    content += f"<i>Jami: {total_items} ta | Sahifa: {page}/{total_pages}</i>\n"
    content += "━━━━━━━━━━━━━━━━━━━\n\n"

    if not current_items:
        content += "<i>Hozircha ushbu bo'limda foydalanuvchilar yo'q.</i>"
    else:
        if category in ("premium", "free", "all"):
            for idx, u in enumerate(current_items, start=start_idx + 1):
                name = u.get("name", "Noma'lum")
                grade = u.get("grade", 1)
                code = u.get("resolved_code", "------")
                plan = u.get("plan", "free")
                plan_tag = "⭐️ Premium" if plan == "premium" else "🆓 Tekin"
                parent_tg = u.get("parentTelegramId")
                parent_info = f"<code>{parent_tg}</code>" if parent_tg else "<i>Ulanmagan</i>"
                xp = u.get("xp", 0)

                content += (
                    f"<b>{idx}. {name}</b> ({grade}-sinf) — {plan_tag}\n"
                    f"   🔑 Ulanish kodi: <code>{code}</code>\n"
                    f"   📱 Ota-ona TG: {parent_info} | ⚡️ XP: {xp}\n\n"
                )
        else: # parents
            for idx, p in enumerate(current_items, start=start_idx + 1):
                p_name = p.get("name", "Ota-ona")
                p_id = p.get("telegram_id") or p.get("tg_id")
                children = p.get("children", [])
                ch_names = ", ".join([f"{c.get('name', 'Bola')} ({c.get('grade', 1)}-sinf)" for c in children]) or "Farzand ulanmagan"

                content += (
                    f"<b>{idx}. {p_name}</b>\n"
                    f"   🆔 Telegram ID: <code>{p_id}</code>\n"
                    f"   👦 Farzandlari: {ch_names}\n\n"
                )

    await callback.message.edit_text(
        content,
        parse_mode="HTML",
        reply_markup=get_admin_pagination_keyboard(category, page, total_pages)
    )
    await callback.answer()

@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()

# --- FAYL KO'RINISHIDA YUKLAB OLISH (.TXT) ---

@router.callback_query(F.data == "admin_export_users")
async def admin_export_users_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    await callback.answer("Hisobot fayli tayyorlanmoqda... ⏳")
    stats, premium_list, free_list, all_learners, parents_list = await fetch_user_data()

    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("LIDERKIDS — BARCHA FOYDALANUVCHILAR RO'YXATI")
    report_lines.append(f"Hisobot vaqti: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Jami o'quvchilar: {stats['total_count']} ta")
    report_lines.append(f"⭐️ Pulli (Premium): {stats['premium_count']} ta")
    report_lines.append(f"🆓 Tekin (Standart): {stats['free_count']} ta")
    report_lines.append(f"👥 Botdagi ota-onalar: {stats['parents_count']} ta")
    report_lines.append("=" * 60)
    report_lines.append("\n")

    # 1. PULLI FOYDALANUVCHILAR
    report_lines.append("-" * 50)
    report_lines.append(f"1. ⭐️ PULLI (PREMIUM) FOYDALANUVCHILAR ({len(premium_list)} ta):")
    report_lines.append("-" * 50)
    if not premium_list:
        report_lines.append("Pulli foydalanuvchilar mavjud emas.\n")
    else:
        for i, u in enumerate(premium_list, 1):
            u_name = u.get("name", "Noma'lum")
            u_grade = u.get("grade", 1)
            u_code = u.get("resolved_code", "------")
            u_ptg = u.get("parentTelegramId", "Mavjud emas")
            u_xp = u.get("xp", 0)
            u_school = u.get("school", "Noma'lum")
            report_lines.append(
                f"{i}. Ism: {u_name} | Sinf: {u_grade} | Kod: {u_code} | "
                f"Ota-ona TG ID: {u_ptg} | XP: {u_xp} | Maktab: {u_school}"
            )
        report_lines.append("\n")

    # 2. TEKIN FOYDALANUVCHILAR
    report_lines.append("-" * 50)
    report_lines.append(f"2. 🆓 TEKIN (STANDART) FOYDALANUVCHILAR ({len(free_list)} ta):")
    report_lines.append("-" * 50)
    if not free_list:
        report_lines.append("Tekin foydalanuvchilar mavjud emas.\n")
    else:
        for i, u in enumerate(free_list, 1):
            u_name = u.get("name", "Noma'lum")
            u_grade = u.get("grade", 1)
            u_code = u.get("resolved_code", "------")
            u_ptg = u.get("parentTelegramId", "Mavjud emas")
            u_xp = u.get("xp", 0)
            report_lines.append(
                f"{i}. Ism: {u_name} | Sinf: {u_grade} | Kod: {u_code} | "
                f"Ota-ona TG ID: {u_ptg} | XP: {u_xp}"
            )
        report_lines.append("\n")

    # 3. OTA-ONALAR
    report_lines.append("-" * 50)
    report_lines.append(f"3. 👥 BOTDAGI OTA-ONALAR RO'YXATI ({len(parents_list)} ta):")
    report_lines.append("-" * 50)
    if not parents_list:
        report_lines.append("Botda hali ota-onalar ro'yxatdan o'tmagan.\n")
    else:
        for i, p in enumerate(parents_list, 1):
            children = p.get("children", [])
            ch_str = ", ".join([f"{c.get('name')} ({c.get('grade', 1)}-sinf)" for c in children]) or "Bog'lanmagan"
            p_joined = p.get("joinedAt", "Noma'lum")
            p_tg = p.get("telegram_id") or p.get("tg_id")
            p_parent_name = p.get("name", "Ota-ona")
            report_lines.append(
                f"{i}. Ism: {p_parent_name} | TG ID: {p_tg} | "
                f"Farzandlari: {ch_str} | Qo'shilgan: {p_joined}"
            )
        report_lines.append("\n")

    file_content = "\n".join(report_lines).encode("utf-8")
    doc_file = BufferedInputFile(file_content, filename=f"liderkids_foydalanuvchilar_{datetime.now().strftime('%Y%m%d_%H%M')}.txt")

    await callback.message.answer_document(
        document=doc_file,
        caption=(
            f"📄 <b>LiderKids to'liq foydalanuvchilar hisoboti</b>\n"
            f"⭐️ Pulli: <b>{len(premium_list)}</b> | 🆓 Tekin: <b>{len(free_list)}</b>\n"
            f"Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        ),
        parse_mode="HTML"
    )

# --- TO'LOV CHEKLARINI TASDIQLASH VA RAD ETISH ---

@router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    payment_id = callback.data.replace("approve_", "")
    payment = await db.get_payment_request(payment_id)

    if not payment:
        await callback.answer("To'lov arizasi topilmadi!", show_alert=True)
        return

    child_key = payment.get("child_key")
    child_name = payment.get("child_name", "O'quvchi")
    parent_id = payment.get("telegram_id")

    # 1. Firebase bazasida bolaning plan maydonini 'premium' ga o'zgartirish!
    await db.update_learner_plan(child_key, plan="premium")
    await db.update_payment_status(payment_id, status="approved", admin_id=callback.from_user.id)

    # 2. Admin interfeysini yangilash
    await callback.message.edit_caption(
        caption=(
            f"{callback.message.caption}\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>TASDIQLANDI!</b>\n"
            f"Bazada o'quvchi <b>{child_name}</b> tarifi <b>⭐️ PREMIUM</b> ga o'zgartirildi.\n"
            f"Tasdiqladi: @{callback.from_user.username or callback.from_user.id}"
        ),
        parse_mode="HTML",
        reply_markup=None
    )
    await callback.answer("To'lov tasdiqlandi va Premium yoqildi! 🎉")

    # 3. Ota-onaga xabar yuborish
    if parent_id:
        parent_notice = (
            f"🎉 <b>XUSHXABAR! To'lovingiz tasdiqlandi!</b>\n\n"
            f"Farzandingiz <b>{child_name}</b> hisobi muvaffaqiyatli <b>⭐️ PREMIUM</b> tarifiga o'tkazildi! 🚀\n\n"
            f"Endi LiderKids ilovasida barcha Prezident maktabi darslari, sun'iy intellekt murabbiyi (Shercha AI) "
            f"va eksklyuziv tahlillar to'liq ochiq!\n\n"
            f"Farzandingizga o'qishda ulkan zafarlar tilaymiz! 🦁👏"
        )
        try:
            await callback.bot.send_message(
                chat_id=parent_id,
                text=parent_notice,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[Send to Parent Error] {e}")

@router.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    payment_id = callback.data.replace("reject_", "")
    payment = await db.get_payment_request(payment_id)

    if not payment:
        await callback.answer("To'lov arizasi topilmadi!", show_alert=True)
        return

    child_name = payment.get("child_name", "O'quvchi")
    parent_id = payment.get("telegram_id")

    # Bazada statusni yangilash
    await db.update_payment_status(payment_id, status="rejected", admin_id=callback.from_user.id)

    # Admin interfeysini yangilash
    await callback.message.edit_caption(
        caption=(
            f"{callback.message.caption}\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"❌ <b>RAD ETILDI</b>\n"
            f"Rad etdi: @{callback.from_user.username or callback.from_user.id}"
        ),
        parse_mode="HTML",
        reply_markup=None
    )
    await callback.answer("To'lov cheki rad etildi.")

    # Ota-onaga xabar yuborish
    if parent_id:
        parent_notice = (
            f"⚠️ <b>Hurmatli ota-ona!</b>\n\n"
            f"Farzandingiz <b>{child_name}</b> uchun yuborilgan to'lov cheki admin tomonidan tasdiqlanmadi.\n\n"
            f"Sababi: chek to'liq ko'rinmagan yoki to'lov ma'lumotlari mos kelmagan bo'lishi mumkin.\n"
            f"Iltimos, qaytadan urinib ko'ring yoki ma'muriyat bilan bog'laning."
        )
        try:
            await callback.bot.send_message(
                chat_id=parent_id,
                text=parent_notice,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[Send to Parent Error] {e}")

