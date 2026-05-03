import unittest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
import sys
import os

# Добавляем корневую директорию проекта в путь Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.question_service import get_random_questions
from models import Question


class TestQuestionService(unittest.TestCase):

    def test_get_random_questions(self):
        """
        Юнит-тест для функции get_random_questions.
        """
        # Создаём мок сессии базы данных
        db_session = MagicMock(spec=Session)

        # Создаём тестовые объекты Question
        mock_questions = [
            Question(stack="Python", difficulty="Лёгкий", text="Что такое GIL?"),
            Question(stack="Python", difficulty="Лёгкий", text="Что такое list comprehension?"),
        ]

        # Настраиваем мок сессию для возврата тестовых вопросов
        db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_questions

        # Вызываем функцию с мок сессией
        questions = get_random_questions(db_session, stack="Python", difficulty="Лёгкий", limit=2)

        # Проверяем, что функция вернула ожидаемые вопросы
        self.assertEqual(len(questions), 2)
        for question in questions:
            self.assertEqual(question.stack, "Python")
            self.assertEqual(question.difficulty, "Лёгкий")


if __name__ == '__main__':
    unittest.main()
