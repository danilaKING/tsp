# План реализации: AI Mock Interviewer (полный бэкенд)

> **Контекст:** Уже есть рабочий прототип — Flask + GigaChat (`interviewer.py`) и React-фронтенд (`App.tsx` / `App.css`).  
> Задача: добавить PostgreSQL, JWT-авторизацию и базу вопросов так, чтобы GigaChat тратил токены **только на оценку ответов**, а не на генерацию вопросов.

---

## Архитектура (итог)

```
Frontend (React + TypeScript + Vite)
        │  REST / JSON
        ▼
Backend (Python + FastAPI)           ← меняем Flask → FastAPI (по ТЗ)
   ├── auth/          JWT (register, login, me)
   ├── interviews/    start, send, finish
   ├── questions/     seed, выборка из БД
   └── feedbacks/     генерация отчёта через GigaChat
        │
        ├── PostgreSQL (SQLAlchemy ORM)
        │     users, questions, interviews, messages, feedbacks
        └── GigaChat API  ← только для оценки ответа и финального отчёта
```

**Ключевая идея экономии токенов:**
- Вопросы хранятся в таблице `questions` в БД
- GigaChat вызывается **только дважды за интервью**:
  1. После каждого ответа — короткий промпт «оцени этот ответ» (1 вызов × 5 вопросов)
  2. После окончания — финальный отчёт по всему транскрипту (1 вызов)
- Вместо полного диалогового промпта — короткие целевые запросы

---

## Структура файлов проекта

```
project/
├── backend/
│   ├── main.py                  # точка входа FastAPI
│   ├── database.py              # подключение к PostgreSQL (SQLAlchemy)
│   ├── models.py                # ORM-модели таблиц
│   ├── schemas.py               # Pydantic-схемы (валидация запросов/ответов)
│   ├── auth.py                  # JWT: регистрация, логин, декодирование токена
│   ├── routers/
│   │   ├── auth_router.py       # POST /auth/register, POST /auth/login
│   │   ├── interview_router.py  # POST /interviews/start, POST /interviews/send
│   │   └── feedback_router.py   # POST /feedbacks/generate
│   ├── services/
│   │   ├── gigachat_service.py  # вся логика вызова GigaChat
│   │   └── question_service.py  # выборка вопросов из БД
│   ├── seed_questions.py        # скрипт: заполнить таблицу questions начальными данными
│   ├── requirements.txt
│   └── .env                     # DATABASE_URL, JWT_SECRET, GIGACHAT_CREDENTIALS
└── frontend/
    └── src/
        ├── App.tsx              # уже готов
        ├── App.css              # уже готов
        ├── api.ts               # все fetch-вызовы к бэкенду + JWT-заголовок
        └── pages/
            ├── LoginPage.tsx    # форма логина/регистрации
            └── HistoryPage.tsx  # список прошлых интервью пользователя
```

---

## Шаг 1 — База данных (models.py)

Пять таблиц. Схема точно по ТЗ из презентации:

```python
# models.py

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from database import Base

class User(Base):
    __tablename__ = "users"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email         = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(Enum("user", "admin", name="user_role"), default="user")
    created_at    = Column(DateTime, default=datetime.utcnow)

class Question(Base):
    __tablename__ = "questions"
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stack      = Column(String(50), nullable=False)   # "Python", "JavaScript", "SQL", ...
    difficulty = Column(String(20), nullable=False)   # "Лёгкий", "Средний", "Сложный"
    text       = Column(Text, nullable=False)          # сам вопрос
    answer_hint = Column(Text)                         # эталонный ответ (для оценки GigaChat)

class Interview(Base):
    __tablename__ = "interviews"
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    stack      = Column(String(50))
    difficulty = Column(String(20))
    status     = Column(Enum("active", "completed", "aborted", name="interview_status"), default="active")
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

class Message(Base):
    __tablename__ = "messages"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False)
    role         = Column(Enum("user", "assistant", name="message_role"), nullable=False)
    content      = Column(Text, nullable=False)
    question_id  = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)  # какой вопрос задавался
    timestamp    = Column(DateTime, default=datetime.utcnow)

class Feedback(Base):
    __tablename__ = "feedbacks"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False)
    score        = Column(Integer)             # 0–100
    analysis     = Column(JSON)               # {"pros": [...], "cons": [...], "recommendations": [...]}
    created_at   = Column(DateTime, default=datetime.utcnow)
```

---

## Шаг 2 — База вопросов (seed_questions.py)

Структура вопроса: `stack` + `difficulty` + `text` + `answer_hint`.  
`answer_hint` нужен, чтобы GigaChat мог сравнить ответ пользователя с эталоном без лишнего контекста.

```python
# seed_questions.py — запускается один раз: python seed_questions.py

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
```

Скрипт вставки: читает `QUESTIONS`, создаёт объекты `Question`, делает `session.add_all()` и `session.commit()`.

---

## Шаг 3 — Авторизация (auth.py + auth_router.py)

### Зависимости
```
python-jose[cryptography]   # JWT
passlib[bcrypt]             # хеширование паролей
```

### Логика

**Регистрация `POST /auth/register`:**
1. Принять `{ email, password }`
2. Проверить, нет ли уже такого email в `users`
3. Хешировать пароль через `bcrypt`
4. Создать `User` в БД
5. Вернуть JWT-токен сразу (чтобы не заставлять логиниться после регистрации)

**Логин `POST /auth/login`:**
1. Принять `{ email, password }`
2. Найти пользователя по email
3. Проверить пароль через `bcrypt.verify`
4. Вернуть JWT-токен `{ access_token, token_type: "bearer" }`

**Декодирование токена (зависимость FastAPI):**
```python
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = jose.jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    user_id = payload.get("sub")
    return db.query(User).filter(User.id == user_id).first()
```

Все защищённые роуты получают `current_user = Depends(get_current_user)`.

### JWT-токен на фронтенде (api.ts)
```typescript
// Сохраняем токен после логина
localStorage.setItem("token", data.access_token);

// Добавляем в каждый запрос
headers: {
  "Content-Type": "application/json",
  "Authorization": `Bearer ${localStorage.getItem("token")}`
}
```

---

## Шаг 4 — Логика интервью (interview_router.py + question_service.py)

### `POST /interviews/start`
Тело: `{ stack: str, difficulty: str }`

1. Создать запись `Interview` в БД (status="active")
2. Выбрать **5 случайных вопросов** из таблицы `questions` по `stack` + `difficulty`:
   ```python
   questions = db.query(Question)\
       .filter_by(stack=stack, difficulty=difficulty)\
       .order_by(func.random())\
       .limit(5).all()
   ```
3. Сохранить список `question_ids` в памяти сервера (или в Redis, или в самой `Interview` как JSON-поле)
4. Взять первый вопрос, записать в `messages` (role="assistant")
5. Вернуть:
   ```json
   {
     "interview_id": "uuid",
     "question_number": 1,
     "total_questions": 5,
     "message": "Привет! Начнём. Первый вопрос: В чём разница между list и tuple?"
   }
   ```

### `POST /interviews/send`
Тело: `{ interview_id: str, answer: str }`

1. Найти интервью, проверить статус и принадлежность пользователю
2. Записать ответ пользователя в `messages` (role="user")
3. Определить текущий номер вопроса (count messages where role="user")
4. Вызвать GigaChat **с коротким промптом**:
   ```
   Вопрос: {question.text}
   Эталонный ответ: {question.answer_hint}
   Ответ кандидата: {user_answer}
   
   Оцени ответ кандидата. Если правильный — похвали и скажи "NEXT".
   Если неточный — укажи на ошибку коротко (1-2 предложения) и скажи "NEXT".
   Если совсем неверный — объясни кратко и скажи "NEXT".
   ```
5. Записать реакцию GigaChat в `messages` (role="assistant")
6. Если вопросов ещё осталось — вернуть следующий вопрос из БД
7. Если это был 5-й вопрос — вернуть `{ type: "finished" }` и поменять статус interview на "completed"

### Вернуть клиенту:
```json
{
  "type": "question",          // или "finished"
  "ai_reaction": "Верно! ...", // оценка GigaChat
  "next_question": "Что такое GIL?",
  "question_number": 2
}
```

---

## Шаг 5 — Генерация отчёта (feedback_router.py)

### `POST /feedbacks/generate`
Тело: `{ interview_id: str }`

1. Достать все `messages` этого интервью из БД
2. Собрать транскрипт: вопрос → ответ пользователя → оценка AI
3. Один вызов GigaChat с промптом:
   ```
   Ты — опытный технический ментор. Ниже полный транскрипт технического интервью.
   
   {transcript}
   
   Составь структурированный отчёт строго в JSON:
   {
     "score": 0-100,
     "pros": ["список сильных сторон"],
     "cons": ["список ошибок"],
     "recommendations": [{"topic": "...", "description": "..."}]
   }
   Верни только JSON, без пояснений.
   ```
4. Распарсить JSON из ответа GigaChat
5. Сохранить в таблицу `feedbacks`
6. Вернуть клиенту

---

## Шаг 6 — Переход с Flask на FastAPI

По ТЗ указан FastAPI. Замена минимальная:

| Flask | FastAPI |
|---|---|
| `app = Flask(__name__)` | `app = FastAPI()` |
| `@app.route('/start', methods=['POST'])` | `@router.post("/interviews/start")` |
| `request.get_json()` | Pydantic-схема как параметр функции |
| `jsonify(...)` | просто `return dict` |
| `flask-jwt-extended` | `python-jose` + `Depends()` |

Запуск: `uvicorn main:app --reload --port 5000`

---

## Шаг 7 — Фронтенд: что добавить

### LoginPage.tsx
Простая форма с двумя режимами — вход / регистрация:
- Поля: email, password
- При успехе: сохранить токен в `localStorage`, редирект на главную
- При ошибке: показать сообщение

### Изменения в App.tsx
- При старте проверять наличие токена в `localStorage`
- Если нет токена — показывать `<LoginPage />`
- Добавить кнопку "Выйти" (очистить localStorage)
- В `handleStart` и `handleSend` передавать `interview_id` вместо `session_id`
- На экране отчёта добавить числовой Score и списки pros/cons

### HistoryPage.tsx (опционально)
- `GET /interviews/my` — список прошлых интервью пользователя
- Таблица: дата, стек, уровень, оценка

---

## Шаг 8 — .env и запуск

```env
# backend/.env
DATABASE_URL=postgresql://postgres:password@localhost:5432/mockinterview
JWT_SECRET=your_super_secret_key_here
JWT_EXPIRE_MINUTES=10080
GIGACHAT_CREDENTIALS=MDE5ZDRm...
```

### requirements.txt (финальный)
```
fastapi==0.111.0
uvicorn==0.30.1
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.1
gigachat==0.1.35
pydantic[email]==2.7.1
```

### Порядок первого запуска
```bash
# 1. Создать БД
psql -U postgres -c "CREATE DATABASE mockinterview;"

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Применить миграции (создать таблицы)
python -c "from database import Base, engine; from models import *; Base.metadata.create_all(engine)"

# 4. Заполнить вопросы
python seed_questions.py

# 5. Запустить бэкенд
uvicorn main:app --reload --port 5000

# 6. Запустить фронтенд (отдельный терминал)
cd frontend && npm run dev
```

---

## Итоговая схема вызовов GigaChat

```
Старый подход (много токенов):
  Каждый send → полная история диалога → GigaChat генерирует и вопрос и оценку
  ~500-1000 токенов × 5 вопросов × N пользователей

Новый подход (экономный):
  start       → 0 токенов  (вопрос берём из БД)
  send × 5   → ~150 токенов каждый (только: вопрос + hint + ответ → оценка)
  finish      → ~400 токенов (транскрипт → финальный отчёт JSON)
  Итого: ~1150 токенов на всё интервью вместо 4000+
```

---

## Что НЕ делаем в этой версии (оставляем на потом)

- Docker Compose (по ТЗ есть, но для демо не нужен)
- Admin-панель (модуль 4 из ТЗ)
- WebSocket (используем обычный HTTP polling — проще и достаточно)
- Бэкап в S3
- HTTPS (для локального демо не нужен)
