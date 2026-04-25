# AI Mock Interviewer — AI Mock Interviewer — Платформа для проведения технических собеседований с ИИ-оценкой

Платформа для проведения технических собеседований с AI-оценкой.

## 📋 О проекте

**AI Mock Interviewer** — это веб-приложение для проведения технических собеседований с использованием искусственного интеллекта. Пользователь выбирает технологический стек (Python, JavaScript, SQL, Алгоритмы) и уровень сложности, после чего проходит интервью из 5 вопросов. После каждого ответа ИИ даёт оценку, а по завершении — формирует подробный отчёт с оценкой, сильными сторонами, зонами роста и рекомендациями.

### Ключевые возможности

- 🔐 **JWT-аутентификация** — регистрация и вход с защитой данных
- 📚 **База из 15+ вопросов** — по Python, JavaScript, SQL и алгоритмам
- 🤖 **AI-оценка ответов** — через GigaChat API
- 📊 **Структурированный отчёт** — score (0–100), pros, cons, рекомендации
- 📜 **История интервью** — отслеживание прогресса
- 💰 **Экономия токенов** — вопросы из БД, GigaChat вызывается только для оценки (~1150 токенов на интервью vs 4000+)

---

## 🛠 Технологический стек

### Backend
| Технология | Версия | Назначение |
|---|---|---|
| Python | 3.13 | Язык программирования |
| FastAPI | 0.111.0 | Веб-фреймворк |
| SQLAlchemy | 2.0.36 | ORM для работы с БД |
| PostgreSQL | 16+ | Реляционная база данных |
| python-jose | 3.3.0 | JWT-токены |
| passlib + bcrypt | 1.7.4 + 3.2.2 | Хеширование паролей |
| python-dotenv | 1.0.1 | Управление переменными окружения |
| GigaChat API | 0.1.35 | AI-оценка ответов |

### Frontend
| Технология | Версия | Назначение |
|---|---|---|
| React | 18.3.1 | UI-библиотека |
| TypeScript | 5.5+ | Типизация |
| Vite | 5.3+ | Сборщик и dev-сервер |

---

## 📁 Структура проекта

```
interviewer/
├── backend/
│   ├── main.py                  # Точка входа FastAPI
│   ├── database.py              # Подключение к PostgreSQL
│   ├── models.py                # SQLAlchemy модели (5 таблиц)
│   ├── schemas.py               # Pydantic схемы валидации
│   ├── auth.py                  # JWT-аутентификация
│   ├── routers/
│   │   ├── auth_router.py       # /auth/register, /auth/login
│   │   ├── interview_router.py  # /interviews/start, /send, /my
│   │   └── feedback_router.py   # /feedbacks/generate
│   ├── services/
│   │   ├── gigachat_service.py  # Интеграция с GigaChat API
│   │   └── question_service.py  # Выборка вопросов из БД
│   ├── seed_questions.py        # Скрипт заполнения БД вопросами
│   ├── requirements.txt         # Python-зависимости
│   └── .env                     # Переменные окружения
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Главный компонент
│   │   ├── App.css              # Стили
│   │   ├── api.ts               # API-клиент с JWT
│   │   ├── main.tsx             # Точка входа React
│   │   └── pages/
│   │       └── LoginPage.tsx    # Страница входа/регистрации
│   ├── index.html               # HTML-шаблон
│   ├── package.json             # Node.js зависимости
│   ├── vite.config.ts           # Конфигурация Vite
│   └── tsconfig.json            # Конфигурация TypeScript
├── App.tsx                      # Копия для root (legacy)
├── App.css                      # Копия для root (legacy)
├── interviewer.py               # Старый прототип на Flask
├── PLAN.md                      # План разработки
└── README.md                    # Этот файл
```

---

## 🚀 Установка и запуск

### Предварительные требования

| Требование | Минимальная версия |
|---|---|
| Python | 3.12+ |
| Node.js | 18+ |
| PostgreSQL | 14+ |
| pip / npm | последние |

### Вариант 1: Linux (Ubuntu/Debian)

#### 1. Установка PostgreSQL

```bash
# Установка PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Запуск и автозагрузка
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создание базы данных
sudo -u postgres psql -c "CREATE DATABASE mockinterview;"

# Установка пароля для пользователя postgres
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

#### 2. Настройка доступа к PostgreSQL

Отредактируйте `/etc/postgresql/<версия>/main/pg_hba.conf`:
```
# Найдите строку с host и измените метод аутентификации:
host    all    all    127.0.0.1/32    md5
```

Перезапустите PostgreSQL:
```bash
sudo systemctl restart postgresql
```

#### 3. Установка Python-зависимостей

```bash
cd backend

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

#### 4. Инициализация базы данных

```bash
# Запуск скрипта заполнения вопросов
python seed_questions.py
```

#### 5. Запуск бэкенда

```bash
# Убедитесь, что .env настроен правильно
# Затем запустите сервер
uvicorn main:app --reload --port 5000
```

#### 6. Запуск фронтенда (в отдельном терминале)

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск dev-сервера
npm run dev
```

Откройте http://localhost:5173 в браузере.

---

### Вариант 2: macOS

#### 1. Установка PostgreSQL (через Homebrew)

```bash
# Установка Homebrew (если нет)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установка PostgreSQL
brew install postgresql@16

# Запуск PostgreSQL
brew services start postgresql@16

# Создание базы данных
createdb mockinterview

# Установка пароля
psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

#### 2. Установка Python-зависимостей

```bash
cd backend

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

#### 3. Инициализация и запуск

```bash
# Заполнение базы вопросов
python seed_questions.py

# Запуск бэкенда
uvicorn main:app --reload --port 5000
```

#### 4. Запуск фронтенда

```bash
cd frontend
npm install
npm run dev
```

Откройте http://localhost:5173 в браузере.

---

### Вариант 3: Windows

#### 1. Установка PostgreSQL

1. Скачайте установщик с https://www.postgresql.org/download/windows/
2. Запустите installer, следуйте инструкциям
3. Запомните пароль пользователя postgres

Откройте **SQL Shell (psql)** из меню Пуск и выполните:

```sql
CREATE DATABASE mockinterview;
ALTER USER postgres PASSWORD 'postgres';
```

Или через pgAdmin: создайте базу данных `mockinterview`.

#### 2. Установка Python и зависимостей

1. Скачайте Python 3.12+ с https://www.python.org/downloads/
2. При установке поставьте галочку **"Add Python to PATH"**

Откройте PowerShell и выполните:

```powershell
cd backend

# Создание виртуального окружения
python -m venv venv
.\venv\Scripts\Activate.ps1

# Если ошибка выполнения скриптов, запустите от администратора:
# Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Установка зависимостей
pip install -r requirements.txt
```

#### 3. Инициализация базы данных

```powershell
python seed_questions.py
```

#### 4. Запуск бэкенда

```powershell
uvicorn main:app --reload --port 5000
```

#### 5. Запуск фронтенда (в отдельном терминале)

1. Скачайте Node.js с https://nodejs.org/
2. Откройте новый PowerShell:

```powershell
cd frontend
npm install
npm run dev
```

Откройте http://localhost:5173 в браузере.

---

## ⚙️ Конфигурация

### Переменные окружения (backend/.env)

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mockinterview

# JWT
JWT_SECRET=your_super_secret_key_here
JWT_EXPIRE_MINUTES=10080

# GigaChat API (получить на https://developers.sber.ru/gigachat)
GIGACHAT_CREDENTIALS=your_credentials_here
```

### Получение GigaChat Credentials

1. Зарегистрируйтесь на https://developers.sber.ru/gigachat
2. Создайте проект и получите credentials
3. Вставьте их в `backend/.env` в поле `GIGACHAT_CREDENTIALS`

> **Примечание:** Без credentials проект работает в режиме mock — возвращает заглушки вместо реальных оценок.

---

## 📡 API Endpoints

### Аутентификация
| Метод | Путь | Описание | Тело запроса |
|---|---|---|---|
| POST | `/auth/register` | Регистрация | `{"email": "...", "password": "..."}` |
| POST | `/auth/login` | Вход | `{"email": "...", "password": "..."}` |

### Интервью
| Метод | Путь | Описание | Тело запроса |
|---|---|---|---|
| POST | `/interviews/start` | Начать интервью | `{"stack": "Python", "difficulty": "Лёгкий"}` |
| POST | `/interviews/send` | Отправить ответ | `{"interview_id": "...", "answer": "..."}` |
| GET | `/interviews/my` | История интервью | — |

### Обратная связь
| Метод | Путь | Описание | Тело запроса |
|---|---|---|---|
| POST | `/feedbacks/generate` | Сгенерировать отчёт | `{"interview_id": "..."}` |

### Служебные
| Метод | Путь | Описание |
|---|---|---|
| GET | `/` | Информация о API |
| GET | `/health` | Проверка здоровья |
| GET | `/docs` | Swagger документация |

---

## 🗄 Схема базы данных

```
┌──────────┐     ┌────────────┐     ┌──────────┐
│  users   │────<│ interviews │>────│ questions│
│          │     │            │     │          │
│ id (PK)  │     │ id (PK)    │     │ id (PK)  │
│ email    │     │ user_id(FK)│     │ stack    │
│ password │     │ stack      │     │ difficulty│
│ role     │     │ difficulty │     │ text     │
│ created  │     │ status     │     │ hint     │
└──────────     └─────┬──────┘     └──────────┘
                       │
                       │ 1:N
                       ▼
                ┌──────────┐     ┌──────────┐
                │ messages │     │ feedbacks│
                │          │     │          │
                │ id (PK)  │     │ id (PK)  │
                │ int_id(FK)│    │ int_id(FK)│
                │ role     │     │ score    │
                │ content  │     │ analysis │
                │ q_id(FK) │     │ created  │
                │ ts       │     └──────────┘
                └──────────┘
```

---

## 🔄 Типичный сценарий использования

1. **Регистрация** — создайте аккаунт на странице входа
2. **Начало интервью** — выберите стек и сложность, нажмите «Начать»
3. **Ответы на вопросы** — вводите ответы и получайте AI-оценку
4. **Завершение** — после 5 вопросов автоматически генерируется отчёт
5. **Просмотр отчёта** — score, сильные стороны, зоны роста, рекомендации
6. **История** — просмотр всех прошедших интервью через кнопку «История»

---

## 🐛 Возможные проблемы и решения

| Проблема | Решение |
|---|---|
| `bcrypt: module has no attribute '__about__'` | Установите `bcrypt==3.2.2`: `pip install bcrypt==3.2.2` |
| `Peer authentication failed` | Используйте парольную аутентификацию: `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mockinterview` |
| `password authentication failed` | Проверьте пароль в `.env` и выполните `ALTER USER postgres PASSWORD 'postgres';` |
| `CORS error` в браузере | Убедитесь, что бэкенд запущен на порту 5000 |
| `ModuleNotFoundError: No module named 'gigachat'` | Установите `pip install gigachat` |

---

## 📝 Лицензия

Проект создан в учебных целях. Используйте по своему усмотрению.

---

## 👥 Авторы

Разработано в рамках проекта AI Mock Interviewer.
