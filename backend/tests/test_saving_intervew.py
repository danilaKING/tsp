import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
from uuid import UUID

# Добавляем корневую директорию проекта в путь Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from database import Base, get_db
from models import User, Interview, Question

# Используем SQLite базу данных в памяти для тестирования
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаём таблицы базы данных
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_db():
    # Очищаем базу данных перед и после тестов
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Добавляем тестовые вопросы
    db = TestingSessionLocal()
    
    test_questions = [
        Question(
            stack="Python",
            difficulty="Средний",
            text="Что такое GIL (Global Interpreter Lock)?",
            answer_hint="GIL - это механизм, который позволяет только одному потоку выполнять Python байткод одновременно"
        ),
        Question(
            stack="Python",
            difficulty="Средний",
            text="Объясните разницу между list и tuple",
            answer_hint="list - изменяемый, tuple - неизменяемый объект"
        ),
        Question(
            stack="Python",
            difficulty="Средний",
            text="Что такое декоратор?",
            answer_hint="Декоратор - это функция, которая принимает функцию и возвращает модифицированную функцию"
        ),
        Question(
            stack="Python",
            difficulty="Средний",
            text="Как работают list comprehensions?",
            answer_hint="List comprehension - это компактный способ создания списков с фильтрацией и преобразованием"
        ),
        Question(
            stack="Python",
            difficulty="Средний",
            text="Что такое виртуальное окружение?",
            answer_hint="Виртуальное окружение - это изолированная среда Python с собственными пакетами"
        ),
    ]
    
    for question in test_questions:
        db.add(question)
    
    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)


def test_start_interview_regression():
    """
    Регрессионный тест для эндпоинта /interviews/start.
    """
    # 1. Сначала создаём пользователя
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    user_data = response.json()
    assert "access_token" in user_data

    access_token = user_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. Запускаем интервью
    response = client.post(
        "/interviews/start",
        json={"stack": "Python", "difficulty": "Средний"},
        headers=headers,
    )
    # Добавим отладочный вывод при ошибке
    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        print(f"Ответ: {response.text}")
    assert response.status_code == 200, f"Неудачный запрос: {response.text}"
    interview_data = response.json()
    assert "interview_id" in interview_data
    assert "message" in interview_data
    assert "question_number" in interview_data
    assert interview_data["question_number"] == 1
    assert interview_data["total_questions"] == 5

    # 3. Проверяем, что интервью сохранено в базе данных
    db = TestingSessionLocal()
    interview = db.query(Interview).filter(Interview.id == UUID(interview_data["interview_id"])).first()
    db.close()

    assert interview is not None
    assert interview.stack == "Python"
    assert interview.difficulty == "Средний"
    assert interview.status == "active"


if __name__ == "__main__":
    # Запуск тестов через pytest
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v"],
        cwd=os.path.dirname(__file__)
    )
    exit(result.returncode)
