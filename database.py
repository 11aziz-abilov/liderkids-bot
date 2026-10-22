import aiohttp
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
import hashlib
from config import FIREBASE_DB_URL

def generate_child_code(student_id: str) -> str:
    """
    Agar o'quvchida alohida linkCode bo'lmasa,
    har bir o'quvchi uchun barqaror 6 xonali noyob kod yaratish
    """
    digest = hashlib.md5(student_id.encode('utf-8')).hexdigest()
    # 6 xonali son (100000 - 999999)
    number = int(digest[:8], 16) % 900000 + 100000
    return str(number)

class Database:
    def __init__(self, base_url: str = FIREBASE_DB_URL):
        self.base_url = base_url.rstrip("/")

    async def _request(self, method: str, path: str, data: Any = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        async with aiohttp.ClientSession() as session:
            try:
                if method.upper() == "GET":
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        return None
                elif method.upper() == "PUT":
                    async with session.put(url, json=data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        return resp.status in (200, 201)
                elif method.upper() == "PATCH":
                    async with session.patch(url, json=data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        return resp.status in (200, 204)
                elif method.upper() == "POST":
                    async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status in (200, 201):
                            return await resp.json()
                        return None
                elif method.upper() == "DELETE":
                    async with session.delete(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        return resp.status == 200
            except Exception as e:
                print(f"[Database Error] {method} {url} -> {e}")
                return None

    # --- O'QUVCHILAR BILAN ISHLASH ---
    async def get_all_learners(self) -> Dict[str, Any]:
        """Barcha o'quvchilarni yuklab olish"""
        data = await self._request("GET", "learners.json")
        return data or {}

    async def get_learner_by_id(self, learner_id: str) -> Optional[Dict[str, Any]]:
        """ID bo'yicha bitta o'quvchini olish"""
        safe_key = learner_id.replace(".", "_").replace("#", "_").replace("$", "_").replace("[", "_").replace("]", "_").replace("/", "_")
        return await self._request("GET", f"learners/{safe_key}.json")

    async def find_learner_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        6 xonali kod orqali bolani topish.
        1. Avval linkCode yoki parentCode bo'yicha qidiradi.
        2. Topilmasa, deterministik generatsiya qilingan kod orqali qidiradi.
        """
        code = str(code).strip()
        learners = await self.get_all_learners()

        for key, learner in learners.items():
            if not isinstance(learner, dict):
                continue
            
            # Agar mavjud linkCode bo'lsa
            existing_code = learner.get("linkCode") or learner.get("parentCode")
            if existing_code and str(existing_code).strip() == code:
                learner["firebase_key"] = key
                return learner

            # ID orqali hisoblangan kod
            l_id = learner.get("id") or key
            calc_code = generate_child_code(str(l_id))
            if calc_code == code:
                learner["firebase_key"] = key
                # Kodni bazada ham mustahkamlab qo'yamiz
                await self._request("PATCH", f"learners/{key}.json", {"parentCode": code})
                return learner

        return None

    async def update_learner_plan(self, learner_key_or_id: str, plan: str = "premium") -> bool:
        """Bolaning plan maydonini yangilash (masalan 'premium')"""
        safe_key = learner_key_or_id.replace(".", "_").replace("#", "_").replace("$", "_").replace("[", "_").replace("]", "_").replace("/", "_")
        payload = {
            "plan": plan,
            "planActivatedAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        return bool(await self._request("PATCH", f"learners/{safe_key}.json", payload))

    # --- OTA-ONALAR BILAN ISHLASH ---
    async def get_parent(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Ota-onaning botdagi profilini olish"""
        return await self._request("GET", f"parents/{telegram_id}.json")

    async def link_child_to_parent(self, telegram_id: int, parent_name: str, child: Dict[str, Any]) -> bool:
        """Bolani ota-onaga bog'lash"""
        current = await self.get_parent(telegram_id) or {
            "telegram_id": telegram_id,
            "name": parent_name,
            "joinedAt": datetime.now().isoformat(),
            "children": []
        }

        children = current.get("children", [])
        child_id = child.get("id") or child.get("firebase_key")

        # Bolani ro'yxatda bor-yo'qligini tekshirish
        exists = any(c.get("id") == child_id for c in children)
        if not exists:
            children.append({
                "id": child_id,
                "firebase_key": child.get("firebase_key", child_id),
                "name": child.get("name", "Noma'lum"),
                "grade": child.get("grade", 1),
                "linkedAt": datetime.now().isoformat()
            })
            current["children"] = children
            current["active_child_id"] = child_id
            await self._request("PUT", f"parents/{telegram_id}.json", current)

        # Shuningdek, o'quvchi ma'lumotlariga ham ota-ona Telegram ID sini yozib qo'yamiz
        child_key = child.get("firebase_key") or child_id
        await self._request("PATCH", f"learners/{child_key}.json", {
            "parentTelegramId": telegram_id,
            "parentLinkedAt": datetime.now().isoformat()
        })

        return True

    async def set_active_child(self, telegram_id: int, child_id: str) -> bool:
        """Ota-ona bir nechta farzandi bo'lsa, joriy ko'rilayotgan faol farzandni tanlash"""
        return bool(await self._request("PATCH", f"parents/{telegram_id}.json", {"active_child_id": child_id}))

    async def get_all_parents(self) -> Dict[str, Any]:
        """Barcha ota-onalar ro'yxatini olish (har kuni kechqurun hisobot yuborish uchun)"""
        return await self._request("GET", "parents.json") or {}

    # --- NATIJALAR VA STATISTIKA ---
    async def get_child_performance(self, learner_key_or_id: str) -> Dict[str, Any]:
        """
        Bolaning natijalarini to'plash:
        - Yechilgan testlar soni
        - To'g'ri javoblar foizi
        - Zaif mavzular
        """
        learner = await self.get_learner_by_id(learner_key_or_id)
        if not learner:
            # key orqali qidirish
            learners = await self.get_all_learners()
            learner = learners.get(learner_key_or_id)

        if not learner:
            return {
                "name": "Noma'lum",
                "grade": 1,
                "total_quizzes": 0,
                "correct_percentage": 0,
                "weak_topics": [],
                "streaks": 0,
                "coins": 0,
                "xp": 0,
                "plan": "free"
            }

        # Agar bazada maxsus stats yoki quizHistory bo'lsa:
        stats = learner.get("stats") or {}
        today_stats = learner.get("todayStats") or {}
        quiz_history = learner.get("quizHistory") or []

        # Umumiy ko'rsatkichlar
        streaks = learner.get("streaks", 0)
        coins = learner.get("coins", 0)
        xp = learner.get("xp", 0)
        plan = learner.get("plan", "free")

        # Testlar soni
        quizzes_count = today_stats.get("quizzesCount")
        if quizzes_count is None:
            # Agar bugungi stats bo'lmasa, umumiy completedQuizzes yoki xp dan hisoblash
            completed_quizzes = learner.get("completedQuizzes") or []
            quizzes_count = len(completed_quizzes) if completed_quizzes else max(1, xp // 35)

        # To'g'ri javoblar foizi
        percentage = today_stats.get("accuracy")
        if percentage is None:
            percentage = stats.get("accuracy", 85) # O'rtacha 85%

        # Zaif mavzular
        weak_topics = today_stats.get("weakTopics") or stats.get("weakTopics") or []
        if not weak_topics:
            # Agar mavjud bo'lmasa, sinfiga mos zaif bo'lishi mumkin bo'lgan mavzular misoli
            grade = learner.get("grade", 1)
            default_topics = {
                1: ["Matematika: Qo'shish va ayirish amallari", "Mantiq: Shakllar ketma-ketligi"],
                2: ["Matematika: Karra jadvali", "Tanqidiy fikrlash: Mantiqiy xulosalar"],
                3: ["Mantiq: Fazoviy fikrlash (3D kublar)", "Ingliz tili: Matnni tushunish (Reading)"],
                4: ["Tanqidiy fikrlash: Argumentlar tahlili", "Matematika: Murakkab matnli masalalar"]
            }
            # Agar foiz 100% dan kam bo'lsa bitta tavsiya ko'rsatiladi
            if percentage < 90:
                weak_topics = default_topics.get(grade, ["Mantiqiy savollar"])

        return {
            "name": learner.get("name", "O'quvchi"),
            "grade": learner.get("grade", 1),
            "total_quizzes": quizzes_count,
            "correct_percentage": percentage,
            "weak_topics": weak_topics,
            "streaks": streaks,
            "coins": coins,
            "xp": xp,
            "plan": plan
        }

    # --- TO'LOV VA CHEKLAR ---
    async def create_payment_request(self, telegram_id: int, parent_name: str, child_key: str, child_name: str, photo_file_id: str, amount: str) -> str:
        """To'lov cheki arizasini yaratish"""
        payment_id = f"pay_{telegram_id}_{int(datetime.now().timestamp())}"
        data = {
            "payment_id": payment_id,
            "telegram_id": telegram_id,
            "parent_name": parent_name,
            "child_key": child_key,
            "child_name": child_name,
            "photo_file_id": photo_file_id,
            "amount": amount,
            "status": "pending",  # pending | approved | rejected
            "createdAt": datetime.now().isoformat()
        }
        await self._request("PUT", f"payments/{payment_id}.json", data)
        return payment_id

    async def get_payment_request(self, payment_id: str) -> Optional[Dict[str, Any]]:
        return await self._request("GET", f"payments/{payment_id}.json")

    async def update_payment_status(self, payment_id: str, status: str, admin_id: int) -> bool:
        """To'lov holatini tasdiqlash yoki rad etish"""
        return bool(await self._request("PATCH", f"payments/{payment_id}.json", {
            "status": status,
            "reviewedBy": admin_id,
            "reviewedAt": datetime.now().isoformat()
        }))

# Global singleton ob'ekt
db = Database()
