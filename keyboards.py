from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

def get_main_keyboard(has_child: bool = True, is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Asosiy menyu tugmalari"""
    buttons = []
    if not has_child:
        buttons.append([KeyboardButton(text="🔗 Farzandni ulash (6 xonali kod)")])
        buttons.append([KeyboardButton(text="ℹ️ Bot haqida")])
    else:
        buttons.append([KeyboardButton(text="📊 Bugungi natijalar"), KeyboardButton(text="⭐️ Premium olish")])
        buttons.append([KeyboardButton(text="👦 Farzandim profili"), KeyboardButton(text="📈 Zaif mavzular")])
        buttons.append([KeyboardButton(text="🔄 Farzandni almashtirish"), KeyboardButton(text="🔗 Yangi farzand ulash")])
        buttons.append([KeyboardButton(text="ℹ️ Yordam va Qo'llab-quvvatlash")])

    # Agar foydalanuvchi admin bo'lsa, maxsus boshqaruv tugmasi
    if is_admin:
        buttons.append([KeyboardButton(text="👑 Admin Panel")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_premium_inline_keyboard(card_number: str) -> InlineKeyboardMarkup:
    """Premium to'lov oynasidagi inline tugmalar"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Chek rasmini yuborish", callback_data="send_receipt")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_payment")]
        ]
    )

def get_admin_payment_keyboard(payment_id: str) -> InlineKeyboardMarkup:
    """Adminga chek kelganda tasdiqlash yoki rad etish tugmalari"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash (Premium yoqish)", callback_data=f"approve_{payment_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{payment_id}")
            ]
        ]
    )

def get_children_selection_keyboard(children: list) -> InlineKeyboardMarkup:
    """Bir nechta farzand bo'lsa tanlash uchun tugmalar"""
    keyboard = []
    for child in children:
        c_id = child.get("id") or child.get("firebase_key")
        c_name = child.get("name", "O'quvchi")
        c_grade = child.get("grade", 1)
        keyboard.append([
            InlineKeyboardButton(
                text=f"👦 {c_name} ({c_grade}-sinf)",
                callback_data=f"select_child_{c_id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_panel_keyboard(stats: dict) -> InlineKeyboardMarkup:
    """Admin boshqaruv paneli bosh menyusi"""
    prem_count = stats.get("premium_count", 0)
    free_count = stats.get("free_count", 0)
    parents_count = stats.get("parents_count", 0)
    total_count = stats.get("total_count", 0)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"⭐️ Pulli foydalanuvchilar ({prem_count})", callback_data="admin_view_premium_1"),
                InlineKeyboardButton(text=f"🆓 Tekin foydalanuvchilar ({free_count})", callback_data="admin_view_free_1")
            ],
            [
                InlineKeyboardButton(text=f"👥 Botdagi ota-onalar ({parents_count})", callback_data="admin_view_parents_1"),
                InlineKeyboardButton(text=f"📋 Barcha o'quvchilar ({total_count})", callback_data="admin_view_all_1")
            ],
            [
                InlineKeyboardButton(text="📥 To'liq ro'yxatni yuklab olish (.txt)", callback_data="admin_export_users")
            ],
            [
                InlineKeyboardButton(text="🔄 Statistikani yangilash", callback_data="admin_refresh")
            ]
        ]
    )

def get_admin_pagination_keyboard(category: str, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Admin ro'yxatlarini sahifalash tugmalari"""
    buttons = []
    nav_row = []

    if current_page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin_view_{category}_{current_page - 1}"))
    
    nav_row.append(InlineKeyboardButton(text=f"📄 {current_page}/{max(1, total_pages)}", callback_data="noop"))
    
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin_view_{category}_{current_page + 1}"))

    buttons.append(nav_row)
    buttons.append([
        InlineKeyboardButton(text="🔙 Admin panelga qaytish", callback_data="admin_panel_home")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

