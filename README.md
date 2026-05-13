## О проекте

Данный проект был создан во время учеьного курса "Технология ситсемного программирования" .

**AI Mock Interviewer** — это веб-приложение для проведения технических собеседований с использованием LLM. 
### Ключевые возможности

- 🔐 **JWT-аутентификация** — регистрация и вход с защитой данных 
- 📚 **База из 15+ вопросов** — по Python, JavaScript, SQL и алгоритмам
- 🤖 **AI-оценка ответов** — через GigaChat API
- 📊 **Структурированный отчёт** — score (0–100), pros, cons, рекомендации
- 📜 **История интервью** — отслеживание прогресса
- 💰 **Экономия токенов** — вопросы из БД, GigaChat вызывается только для оценки (~1150 токенов на интервью vs 4000+)
---

## Содержание

1. [Быстрый старт через Docker](#быстрый-старт-через-docker)
2. [Локальная разработка без Docker](#локальная-разработка-без-docker)
3. [Переменные окружения](#переменные-окружения)
4. [Структура проекта](#структура-проекта)
5. [История изменений](#история-изменений)

---

## Быстрый старт через Docker

### Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 24.0
- Docker Compose ≥ 2.20 (входит в Docker Desktop)

### Шаги

#### 1. Клонировать репозиторий

```bash
git clone <url-репозитория>
cd tsp-review
```

#### 2. Создать `.env` для бэкенда

Скопируйте шаблон и заполните нужные значения:

```bash
cp .env.example backend/.env
```

Обязательно задайте свой `JWT_SECRET` (любая случайная строка ≥ 32 символа).
`GIGACHAT_CREDENTIALS` — опционально, без него приложение работает на заглушке.

#### 3. Запустить все сервисы

```bash
docker compose up --build
```

Первый запуск скачает образы и соберёт контейнеры (~3–5 минут).
При последующих запусках пересборка не нужна:

```bash
docker compose up
```

#### 4. Открыть приложение

| Сервис    | URL                        |
|-----------|----------------------------|
| Фронтенд  | http://localhost            |
| Бэкенд API | http://localhost:5000      |
| Swagger UI | http://localhost:5000/docs |

#### Остановить

```bash
docker compose down
```

Данные PostgreSQL сохраняются в Docker-томе `postgres_data`.
Чтобы удалить данные тоже:

```bash
docker compose down -v
```

---

### Архитектура Docker-окружения

```
┌─────────────────────────────────────────────┐
│                   HOST                      │
│                                             │
│  браузер → localhost:80 ──────► frontend    │
│                   (nginx, React SPA)        │
│                                             │
│  браузер → localhost:5000 ────► backend     │
│                   (FastAPI + uvicorn)       │
│                                             │
│  backend ──────────────────────► db         │
│              (PostgreSQL:5432,              │
│               внутренняя сеть)              │
└─────────────────────────────────────────────┘
```

- **db** — PostgreSQL 16. Данные хранятся в именованном томе.
- **backend** — при старте автоматически создаёт таблицы и засевает вопросы (`seed_questions.py`), затем запускает uvicorn.
- **frontend** — собирается через Node 20 (Vite), отдаётся Nginx 1.27.

### Деплой на удалённый сервер

Если фронтенд и бэкенд размещаются на одном сервере с публичным IP или доменом, передайте реальный адрес API при сборке:

```bash
docker compose build \
  --build-arg VITE_API_URL=https://api.your-domain.com \
  frontend
docker compose up -d
```

Либо измените значение `VITE_API_URL` в `docker-compose.yml` перед запуском.

> **Важно:** `VITE_API_URL` встраивается в JavaScript-бандл на этапе сборки (`npm run build`). Изменение переменной после сборки не даст эффекта — нужна пересборка образа.

---

## Локальная разработка без Docker

### Требования

- Python 3.11+
- Node.js 20+
- PostgreSQL 14+ (запущенный локально или через Docker)

### Бэкенд

```bash
cd backend

# Создать и активировать виртуальное окружение
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

# Установить зависимости
pip install -r requirements.txt

# Скопировать и настроить .env
cp ../.env.example .env
# Убедитесь, что DATABASE_URL указывает на локальный PostgreSQL

# Создать таблицы и засеять вопросы
python seed_questions.py

# Запустить сервер
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

API будет доступен по адресу `http://localhost:5000`.
Swagger-документация — `http://localhost:5000/docs`.

### Фронтенд

```bash
cd frontend

npm install
npm run dev
```

Приложение откроется по адресу `http://localhost:5173`.

---

## Переменные окружения

Все переменные задаются в файле `backend/.env`.

| Переменная             | Обязательно | Описание                                                         | Пример                                              |
|------------------------|-------------|------------------------------------------------------------------|-----------------------------------------------------|
| `DATABASE_URL`         | Да          | Строка подключения к PostgreSQL                                  | `postgresql://user:pass@localhost:5432/mockinterview` |
| `JWT_SECRET`           | Да          | Секрет для подписи JWT-токенов. Поменяйте перед деплоем!         | `my_super_secret_32chars_min`                       |
| `JWT_EXPIRE_MINUTES`   | Нет         | Время жизни токена в минутах (по умолчанию 10080 = 7 дней)      | `10080`                                             |
| `GIGACHAT_CREDENTIALS` | Нет         | API-ключ GigaChat (Sber). Без него — mock-режим                  | `ключ с портала developers.sber.ru`                 |

### Получение GigaChat API-ключа

1. Зарегистрируйтесь на [developers.sber.ru](https://developers.sber.ru)
2. Создайте проект, подключите сервис GigaChat API
3. Скопируйте Client Secret в поле `GIGACHAT_CREDENTIALS`
4. Раскомментируйте инициализацию клиента в `backend/services/gigachat_service.py`:

```python
self.client = GigaChat(
    credentials=self.credentials,
    verify_ssl_certs=False,
    model="GigaChat:latest",
    timeout=30
)
```

---

## Структура проекта

```
tsp-review/
├── backend/                    # FastAPI бэкенд (Python)
│   ├── routers/
│   │   ├── auth_router.py      # Регистрация / логин
│   │   ├── interview_router.py # Логика интервью
│   │   ├── feedback_router.py  # Генерация отчёта
│   │   └── metrics_router.py   # CSAT / CES / NPS
│   ├── services/
│   │   ├── gigachat_service.py # Интеграция с GigaChat
│   │   └── question_service.py # Выборка вопросов
│   ├── main.py                 # Точка входа FastAPI
│   ├── models.py               # SQLAlchemy модели
│   ├── schemas.py              # Pydantic схемы
│   ├── database.py             # Настройка БД
│   ├── auth.py                 # JWT авторизация
│   ├── seed_questions.py       # Начальные данные
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env                    # Не коммитить!
│   └── .env.example
├── frontend/                   # React + TypeScript (Vite)
│   ├── src/
│   │   ├── App.tsx             # Главный компонент
│   │   ├── api.ts              # HTTP-клиент
│   │   ├── pages/
│   │   │   └── LoginPage.tsx
│   │   └── components/
│   │       ├── CodeEditorModal.tsx
│   │       ├── Notification.tsx
│   │       └── NotificationContainer.tsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── .env.example
├── README.md
└── CHANGELOG.md
```

---
