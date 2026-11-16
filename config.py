import os
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

# Telegram Bot sozlamalari
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Supabase (Postgres) sozlamalari
SUPABASE_URL = os.getenv("SUPABASE_URL", os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")).rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", ""))

# To'lov ma'lumotlari
CARD_NUMBER = os.getenv("CARD_NUMBER", "9860 1201 2345 6789")
CARD_HOLDER = os.getenv("CARD_HOLDER", "LiderKids Platformasi")
PREMIUM_PRICE = os.getenv("PREMIUM_PRICE", "50 000 so'm / oy")

# Kunlik hisobot yuborish vaqti (Toshkent vaqti bilan kechki 20:00)
REPORT_HOUR = int(os.getenv("REPORT_HOUR", "20"))
REPORT_MINUTE = int(os.getenv("REPORT_MINUTE", "00"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")
