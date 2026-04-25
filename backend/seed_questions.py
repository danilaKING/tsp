"""
Seed questions script - run once to populate the database with initial questions.
Usage: python seed_questions.py
"""
import sys
import os

# Add parent directory to path so we can import from backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Base, engine
from models import Question

# Create tables
from models import User, Interview, Message, Feedback  # Import all models
Base.metadata.create_all(bind=engine)

QUESTIONS = [
    # Python / Лёгкий
    {
        "stack": "Python",
        "difficulty": "Лёгкий",
        "text": "В чём разница между списком (list) и кортежем (tuple) в Python?",
        "answer_hint": "List — изменяемый (mutable), tuple — неизменяемый (immutable). Tuple быстрее, используется для фиксированных данных."
    },
    {
        "stack": "Python",
        "difficulty": "Лёгкий",
        "text": "Что такое декоратор в Python? Приведи пример использования.",
        "answer_hint": "Декоратор — функция-обёртка, изменяющая поведение другой функции. Синтаксис @decorator. Примеры: @staticmethod, @property, логирование."
    },
    {
        "stack": "Python",
        "difficulty": "Лёгкий",
        "text": "Что такое GIL в Python и как он влияет на многопоточность?",
        "answer_hint": "GIL (Global Interpreter Lock) — мьютекс, позволяющий только одному потоку исполнять байткод. Многопоточность не даёт прироста для CPU-bound задач, но работает для I/O-bound."
    },
    # Python / Средний
    {
        "stack": "Python",
        "difficulty": "Средний",
        "text": "Объясни разницу между @staticmethod и @classmethod.",
        "answer_hint": "@staticmethod не получает ни cls, ни self. @classmethod получает cls — ссылку на класс. classmethod используется для альтернативных конструкторов."
    },
    {
        "stack": "Python",
        "difficulty": "Средний",
        "text": "Что такое генераторы в Python и в чём их преимущество перед списками?",
        "answer_hint": "Генераторы создают элементы лениво (по одному), экономят память. Используют yield. Подходят для больших или бесконечных последовательностей."
    },
    {
        "stack": "Python",
        "difficulty": "Средний",
        "text": "Как работает менеджер контекста (with) и как написать свой?",
        "answer_hint": "with вызывает __enter__ при входе и __exit__ при выходе (даже при исключении). Свой — через класс с этими методами или @contextmanager из contextlib."
    },
    # JavaScript / Лёгкий
    {
        "stack": "JavaScript",
        "difficulty": "Лёгкий",
        "text": "В чём разница между var, let и const?",
        "answer_hint": "var — функциональная область видимости, hoisting. let — блочная, нет hoisting. const — блочная, нельзя переприсвоить (но объект можно мутировать)."
    },
    {
        "stack": "JavaScript",
        "difficulty": "Лёгкий",
        "text": "Что такое замыкание (closure) в JavaScript?",
        "answer_hint": "Замыкание — функция, которая запоминает переменные из внешней области видимости даже после её завершения. Используется для инкапсуляции состояния."
    },
    {
        "stack": "JavaScript",
        "difficulty": "Лёгкий",
        "text": "Объясни разницу между == и === в JavaScript.",
        "answer_hint": "== сравнивает с приведением типов (type coercion), === — строгое сравнение без приведения. Рекомендуется всегда использовать ===."
    },
    # JavaScript / Средний
    {
        "stack": "JavaScript",
        "difficulty": "Средний",
        "text": "Что такое Event Loop в JavaScript и как он работает?",
        "answer_hint": "Event Loop — механизм обработки асинхронных задач. Call Stack, Web APIs, Callback Queue, Microtask Queue. Promise-колбеки (microtasks) выполняются раньше setTimeout (macrotasks)."
    },
    {
        "stack": "JavaScript",
        "difficulty": "Средний",
        "text": "В чём разница между Promise и async/await?",
        "answer_hint": "async/await — синтаксический сахар над Promise. Делает асинхронный код читаемым как синхронный. Под капотом — те же промисы."
    },
    # SQL / Лёгкий
    {
        "stack": "SQL",
        "difficulty": "Лёгкий",
        "text": "В чём разница между INNER JOIN, LEFT JOIN и RIGHT JOIN?",
        "answer_hint": "INNER JOIN — только совпадающие строки. LEFT JOIN — все строки левой таблицы + совпадения справа (NULL если нет). RIGHT JOIN — наоборот."
    },
    {
        "stack": "SQL",
        "difficulty": "Лёгкий",
        "text": "Что такое индекс в базе данных и когда его стоит использовать?",
        "answer_hint": "Индекс — структура (B-tree), ускоряющая поиск. Полезен для часто фильтруемых/сортируемых колонок. Минус: замедляет INSERT/UPDATE/DELETE."
    },
    # Алгоритмы / Лёгкий
    {
        "stack": "Алгоритмы",
        "difficulty": "Лёгкий",
        "text": "Объясни разницу между O(n) и O(log n) сложностью. Приведи примеры алгоритмов.",
        "answer_hint": "O(n) — линейный рост (линейный поиск). O(log n) — логарифмический (бинарный поиск, операции в сбалансированном дереве). O(log n) намного быстрее при больших n."
    },
    {
        "stack": "Алгоритмы",
        "difficulty": "Лёгкий",
        "text": "Что такое рекурсия? Каковы её плюсы и минусы?",
        "answer_hint": "Рекурсия — функция, вызывающая саму себя. Плюсы: элегантность для деревьев/графов. Минусы: риск stack overflow, обычно медленнее итерации."
    },
]


def seed_questions():
    """Insert initial questions into the database"""
    db = SessionLocal()
    
    try:
        # Check if questions already exist
        existing_count = db.query(Question).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} questions. Skipping seed.")
            return
        
        # Create question objects
        questions = [Question(**q) for q in QUESTIONS]
        
        # Add all questions
        db.add_all(questions)
        db.commit()
        
        print(f"Successfully seeded {len(questions)} questions!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding questions: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_questions()
