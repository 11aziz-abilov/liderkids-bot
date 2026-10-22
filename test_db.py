import asyncio
import sys
from database import db, generate_child_code

# Windows terminal UTF-8 sozlamasi
sys.stdout.reconfigure(encoding='utf-8')

async def test_firebase_connection():
    print("Firebase bilan aloqa tekshirilmoqda...")
    learners = await db.get_all_learners()
    print(f"Jami o'quvchilar soni: {len(learners)}")

    sample_count = 0
    for key, val in learners.items():
        if isinstance(val, dict):
            name = val.get("name", "Noma'lum")
            grade = val.get("grade", 1)
            child_id = val.get("id", key)
            code = val.get("parentCode") or generate_child_code(str(child_id))
            print(f"- {name} ({grade}-sinf): ID={child_id} -> 6 xonali kod: {code}")
            sample_count += 1
            if sample_count >= 5:
                break

    # Birinchi kod bilan qidirib ko'ramiz
    if sample_count > 0:
        first_key = list(learners.keys())[0]
        first_val = learners[first_key]
        test_code = first_val.get("parentCode") or generate_child_code(str(first_val.get("id", first_key)))
        print(f"\nQidiruv testi: kod={test_code}")
        found = await db.find_learner_by_code(test_code)
        if found:
            print(f"✅ Muvaffaqiyatli topildi: {found.get('name')}")
            perf = await db.get_child_performance(found.get("firebase_key"))
            print(f"Hisobot: Testlar: {perf['total_quizzes']}, Aniqlik: {perf['correct_percentage']}%, Zaif mavzular: {perf['weak_topics']}")
        else:
            print("❌ Topilmadi!")

if __name__ == "__main__":
    asyncio.run(test_firebase_connection())
