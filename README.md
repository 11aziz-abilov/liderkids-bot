# 🦁 LiderKids — «Ota-ona paneli» Telegram Boti

Ushbu bot **LiderKids** ta'lim platformasidagi foydalanuvchilarning ota-onalari uchun maxsus ishlab chiqilgan.

---

## 🌟 Asosiy Imkoniyatlar

1. **🔗 6 xonali kod orqali bolani bog'lash:**
   - Ota-ona LiderKids ilovasidagi 6 xonali maxsus kodni botga kiritadi.
   - Bot avtomatik ravishda umumiy Firebase bazasidan bolani topadi va ota-onaga ulaydi.
   - Bir nechta farzandni ulash va ular o'rtasida o'tish imkoniyati mavjud.

2. **📊 Kunlik Natijalar va Xulosalar:**
   - Bugun yechilgan testlar soni;
   - To'g'ri javoblar foizi (aniqlik darajasi);
   - Zaif (xato qilingan va mustahkamlash talab etiladigan) mavzular ro'yxati;
   - Ketma-ketlik (Streak) va to'plangan tangalar/XP.

3. **🌙 Har kuni kechqurun avtomatik hisobot (Scheduler):**
   - Bot har kuni kechqurun soat **20:00** da (sozlanishi mumkin) ota-onaga bolaning kunlik faoliyati va natijalari haqida xabar jo'natadi.

4. **⭐️ Premium Ta'lim Paketi va Chek Tasdiqlash:**
   - "Premium olish" tugmasi bosilganda to'lov summasi, karta raqami va karta egasi ko'rsatiladi.
   - Ota-ona to'lov cheki (skrinshot) rasmini yuboradi.
   - Chek darhol admin (siz)ga `✅ Tasdiqlash` va `❌ Rad etish` tugmalari bilan yuboriladi.
   - Admin tasdiqlashi bilan Firebase umumiy bazasida shu bolaning `plan` maydoni **`"premium"`** ga o'zgaradi va ota-onaga xushxabar boradi!

---

## 🚀 O'rnatish va Ishga Tushirish

### 1. Sozlamalarni kiritish (.env):
`.env` faylini oching va quyidagi parametrlarni kiriting:
```env
BOT_TOKEN=7123456789:AAF...  # Telegram @BotFather dan olingan bot tokeni
ADMIN_ID=123456789          # Sizning Telegram ID (@userinfobot dan olish mumkin)

FIREBASE_DB_URL=https://liderkids-afad8-default-rtdb.firebaseio.com
CARD_NUMBER=9860 1201 2345 6789
CARD_HOLDER=LiderKids Platformasi
PREMIUM_PRICE=50 000 so'm / oy

REPORT_HOUR=20              # Kechki 20:00
REPORT_MINUTE=00
TIMEZONE=Asia/Tashkent
```

### 2. Botni ishga tushirish:
Virtual muhit (venv) faollashtirilgan holda:
```bash
python main.py
```
yoki Windows'da to'g'ridan-to'g'ri `run.bat` ni ikki marta bosing!

---

## 🗂 Loyiha Tuzilishi:
```
LiderKids bot/
│
├── config.py           # Sozlamalar va .env parametrlarini boshqarish
├── database.py         # Firebase Realtime Database asinxron muloqot moduli
├── keyboards.py        # Asosiy menyu, inline tugmalar va admin paneli klaviaturalari
├── states.py           # FSM holatlari (kod kiritish, chek yuborish)
├── scheduler.py        # Har kuni soat 20:00 da hisobot jo'natuvchi rejalashtiruvchi
├── main.py             # Botni ishga tushiruvchi asosiy fayl
├── test_db.py          # Firebase bazasi ulanishini tekshirish skripti
├── run.bat             # Qulay bitta bosishda ishga tushirish fayli
├── requirements.txt    # Kerakli Python kutubxonalari
└── .env                # Maxfiy kalitlar va sozlamalar
```
