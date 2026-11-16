import aiohttp
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

logger = logging.getLogger(__name__)

# Tashkent timezone offset (+05:00)
TASHKENT_TZ = timezone(timedelta(hours=5))

class Database:
    def __init__(self, base_url: str = SUPABASE_URL, key: str = SUPABASE_SERVICE_ROLE_KEY):
        self.base_url = (base_url or "").rstrip("/")
        self.key = key or ""
        self._active_children: Dict[int, str] = {}

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    async def _request(self, method: str, table: str, params: Optional[Dict[str, str]] = None, json_data: Any = None) -> Any:
        if not self.base_url or not self.key:
            logger.warning("Supabase URL yoki API kaliti sozlanmagan!")
            return None

        url = f"{self.base_url}/rest/v1/{table}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method,
                    url,
                    headers=self._headers(),
                    params=params,
                    json=json_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status in (200, 201):
                        return await resp.json()
                    elif resp.status == 204:
                        return True
                    else:
                        text = await resp.text()
                        logger.error(f"Supabase {method} {table} error ({resp.status}): {text}")
                        return None
            except Exception as e:
                logger.error(f"Supabase connection error: {e}")
                return None

    # --- 1. FARZANDNI 6 XONALI KOD BILAN BOG'LASH ---
    async def verify_and_link_code(self, code: str, telegram_chat_id: int) -> Optional[Dict[str, Any]]:
        """
        6 xonali ulanish kodini link_codes jadvalida tekshirish (15 daqiqalik va bir martalik).
        Agar to'g'ri bo'lsa:
        1. link_codes.used = true qilib belgilanadi.
        2. parent_links jadvaliga (telegram_chat_id, student_id) saqlanadi.
        3. O'quvchi ma'lumotlari qaytariladi.
        """
        clean_code = str(code).strip()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Kodni tekshirish
        params = {
            "code": f"eq.{clean_code}",
            "used": "eq.false",
            "expires_at": f"gt.{now_iso}",
            "select": "*",
            "limit": "1",
        }
        records = await self._request("GET", "link_codes", params=params)

        if not records or len(records) == 0:
            return None

        link_record = records[0]
        code_id = link_record["id"]
        student_id = link_record["student_id"]

        # 1. Kodni ishlatilgan (used = true) deb belgilash
        patch_params = {"id": f"eq.{code_id}"}
        await self._request("PATCH", "link_codes", params=patch_params, json_data={"used": True})

        # 2. parent_links ga kiritish
        link_payload = {
            "telegram_chat_id": telegram_chat_id,
            "student_id": student_id,
            "created_at": now_iso,
        }
        # Upsert parent link
        await self._request("POST", "parent_links", json_data=link_payload)

        # 3. O'quvchi ma'lumotlarini yuklash
        return await self.get_student_by_id(student_id)

    async def get_student_by_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """O'quvchini ID orqali olish"""
        params = {"id": f"eq.{student_id}", "select": "*", "limit": "1"}
        records = await self._request("GET", "students", params=params)
        return records[0] if records and len(records) > 0 else None

    # --- 2. OTA-ONANING FARZANDLARI RO'YXATI ---
    async def get_parent_children(self, telegram_chat_id: int) -> List[Dict[str, Any]]:
        """Ushbu ota-onaga bog'langan barcha o'quvchilarni olish"""
        params = {
            "telegram_chat_id": f"eq.{telegram_chat_id}",
            "select": "student_id, students(*)",
        }
        records = await self._request("GET", "parent_links", params=params)
        if not records:
            return []

        children = []
        for r in records:
            student = r.get("students")
            if student:
                children.append(student)
            elif r.get("student_id"):
                s = await self.get_student_by_id(r["student_id"])
                if s:
                    children.append(s)
        return children

    async def get_parent(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Ota-onaning profili va bog'langan farzandlari"""
        children = await self.get_parent_children(telegram_id)
        if not children:
            return None
        active_id = self._active_children.get(telegram_id)
        if not active_id and children:
            active_id = children[0].get("id")
        return {
            "telegram_id": telegram_id,
            "children": children,
            "active_child_id": active_id
        }

    async def set_active_child(self, telegram_id: int, child_id: str):
        """Faol farzandni xotirada saqlash"""
        self._active_children[telegram_id] = child_id

    async def get_learner_by_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """get_student_by_id uchun moslik funksiyasi"""
        return await self.get_student_by_id(student_id)

    async def get_all_parents(self) -> Dict[str, Any]:
        """Barcha ota-onalarni dict formatida qaytarish"""
        records = await self.get_all_linked_parents_for_report()
        parents: Dict[str, Dict[str, Any]] = {}
        for r in records:
            tg_id = str(r.get("telegram_chat_id"))
            if not tg_id:
                continue
            if tg_id not in parents:
                parents[tg_id] = {"children": []}
            student = r.get("students")
            if student:
                parents[tg_id]["children"].append(student)
        return parents

    async def get_all_learners(self) -> List[Dict[str, Any]]:
        """Barcha o'quvchilar ro'yxati"""
        records = await self._request("GET", "students", params={"select": "*"})
        return records or []

    async def update_learner_plan(self, student_id: str, plan: str = "premium") -> bool:
        """O'quvchi rejasini yangilash"""
        res = await self._request("PATCH", "students", params={"id": f"eq.{student_id}"}, json_data={"plan": plan})
        return bool(res)

    # --- 3. NATIJALAR VA STATISTIKA (/bugun va /hafta) ---
    async def get_child_performance(self, student_id: str, period: str = "today") -> Dict[str, Any]:
        """
        O'quvchining bugungi yoki haftalik natijalarini results jadvalidan to'plash
        """
        student = await self.get_student_by_id(student_id)
        if not student:
            return {
                "name": "Noma'lum o'quvchi",
                "grade": 1,
                "total_quizzes": 0,
                "correct_answers": 0,
                "correct_percentage": 0,
                "weak_topics": [],
                "streaks": 0,
                "coins": 0,
                "xp": 0,
            }

        now_tashkent = datetime.now(TASHKENT_TZ)
        if period == "week":
            # Haftaning dushanba kunidan boshlab
            start_date = (now_tashkent - timedelta(days=now_tashkent.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Bugungi kun 00:00 dan boshlab
            start_date = now_tashkent.replace(hour=0, minute=0, second=0, microsecond=0)

        start_iso = start_date.astimezone(timezone.utc).isoformat()

        params = {
            "student_id": f"eq.{student_id}",
            "created_at": f"gte.{start_iso}",
            "select": "*",
        }
        results = await self._request("GET", "results", params=params) or []

        total_quizzes = len(results)
        total_correct = sum(r.get("correct", 0) for r in results)
        total_questions = sum(r.get("total", 0) for r in results)
        period_coins = sum(r.get("coins_earned", 0) for r in results)

        accuracy = round((total_correct / total_questions) * 100) if total_questions > 0 else 0

        # Zaif mavzular: qaysi fan/mavzuda xatolar ko'p bo'lsa
        weak_set = set()
        subject_names = {
            "math": "Matematika",
            "logic": "Muammoli masalalar (Mantiq)",
            "critical": "Tanqidiy fikrlash",
            "english": "Ingliz tili",
        }
        for r in results:
            correct = r.get("correct", 0)
            total = r.get("total", 0)
            if total > 0 and correct < total:
                subj = r.get("subject", "general")
                subj_title = subject_names.get(subj, subj.capitalize())
                weak_set.add(subj_title)

        return {
            "name": student.get("name", "O'quvchi"),
            "grade": student.get("grade", 1),
            "total_quizzes": total_quizzes,
            "total_questions": total_questions,
            "correct_answers": total_correct,
            "correct_percentage": accuracy,
            "weak_topics": list(weak_set),
            "streaks": student.get("streak", 0),
            "coins": period_coins if period_coins > 0 else student.get("coins", 0),
            "total_coins": student.get("coins", 0),
            "xp": student.get("xp", 0),
        }

    # --- 4. REJALASHTIRILGAN JOB'LAR UCHUN ---
    async def get_all_linked_parents_for_report(self) -> List[Dict[str, Any]]:
        """Har kuni soat 20:00 da hisobot jo'natish uchun barcha ota-onalar va farzandlar"""
        params = {"select": "telegram_chat_id, student_id, students(*)"}
        return await self._request("GET", "parent_links", params=params) or []

    async def get_inactive_students_for_alert(self) -> List[Dict[str, Any]]:
        """24 soatdan beri kirmagan o'quvchilarni topish"""
        threshold = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        params = {
            "last_active_at": f"lt.{threshold}",
            "select": "id, name, grade, streak, last_active_at, parent_links(telegram_chat_id)",
        }
        return await self._request("GET", "students", params=params) or []

db = Database()
