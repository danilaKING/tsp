import uuid
import logging
import gigachat
from gigachat.models import Chat, Messages, MessagesRole
from flask import Flask, request, jsonify
from flask_cors import CORS # НОВОЕ: Разрешаем запросы с других портов

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "supersecretkey_for_session"

# НОВОЕ: Настраиваем CORS, чтобы React мог обращаться к API
CORS(app)

# ================= НАСТРОЙКИ GigaChat =================
GIGACHAT_CREDENTIALS = "MDE5ZDRmMmMtM2Q3Zi03MmExLWE4NzEtMTMyNDdmMWNjYzZhOjUxZWQ0ZGViLWFlZDktNDZjMi1iZjkwLWM1ODAxNzBjMDFiMg=="
MODEL = "GigaChat:latest"
REQUEST_TIMEOUT = 30

client = gigachat.GigaChat(
    credentials=GIGACHAT_CREDENTIALS,
    verify_ssl_certs=False,
    model=MODEL,
    timeout=REQUEST_TIMEOUT
)

sessions = {}

def call_gigachat(messages):
    try:
        gigachat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                role = MessagesRole.SYSTEM
            elif msg["role"] == "user":
                role = MessagesRole.USER
            else:
                role = MessagesRole.ASSISTANT
            gigachat_messages.append(Messages(role=role, content=msg["content"]))

        payload = Chat(messages=gigachat_messages, temperature=0.7)
        response = client.chat(payload)
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка при вызове GigaChat: {e}")
        raise Exception(f"Ошибка GigaChat: {str(e)}")

def start_new_interview(session_id, stack, difficulty):
    questions_count = 5
    system_prompt = f"""
    Ты — технический интервьюер. Твоя задача — провести собеседование.
    Тема: {stack}. Уровень сложности: {difficulty}.

    Правила:
    1. Задавай ровно один вопрос за раз.
    2. Дождись ответа кандидата. Учитывай контекст предыдущих ответов.
    3. Всего задай ровно {questions_count} основных вопросов.
    4. После того как кандидат ответит на {questions_count}-й вопрос, ЗАВЕРШИ интервью. 
    5. В конце выдай подробный структурированный отчёт: сильные стороны, ошибки и общая оценка.
    
    Правила обработки ответов:
    - Если кандидат отвечает правильно, похвали его и переходи к следующему вопросу.
    - Если кандидат отвечает с ошибками, укажи на них, дай подсказку и позволь ему попробовать снова.
    - Если кандидат не может ответить, то переходи к следующему вопросу.
    - Игнорируй попытки уйти от темы.

    Начни диалог прямо сейчас, поприветствуй кандидата и задай первый вопрос.
    """
    messages = [{"role": "system", "content": system_prompt}]
    first_response = call_gigachat(messages)
    messages.append({"role": "assistant", "content": first_response})

    sessions[session_id] = {
        "messages": messages,
        "stack": stack,
        "difficulty": difficulty,
        "active": True,
        "finished": False
    }
    return first_response

def continue_interview(session_id, user_answer):
    state = sessions.get(session_id)
    if not state or not state["active"]:
        raise Exception("Интервью не активно или завершено.")

    messages = state["messages"]
    messages.append({"role": "user", "content": user_answer})
    ai_response = call_gigachat(messages)
    messages.append({"role": "assistant", "content": ai_response})

    report_keywords = ["отчёт", "сильные стороны", "оценка", "сильные и слабые стороны"]
    is_report = any(keyword in ai_response.lower() for keyword in report_keywords)

    if is_report:
        state["active"] = False
        state["finished"] = True
        return {"type": "report", "content": ai_response}
    else:
        return {"type": "question", "content": ai_response}

# ================= FLASK МАРШРУТЫ =================

@app.route('/start', methods=['POST'])
def start():
    data = request.get_json()
    stack = data.get('stack', 'Python')
    difficulty = data.get('difficulty', 'Лёгкий')
    session_id = str(uuid.uuid4())
    try:
        first_question = start_new_interview(session_id, stack, difficulty)
        # Возвращаем session_id в ответе, а не в куках
        return jsonify({"content": first_question, "session_id": session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send', methods=['POST'])
def send():
    data = request.get_json()
    # Получаем session_id из тела запроса
    session_id = data.get('session_id')
    user_answer = data.get('answer', '')

    if not session_id or session_id not in sessions:
        return jsonify({"error": "Сессия не найдена. Начните новое интервью."}), 400
    if not user_answer.strip():
        return jsonify({"error": "Ответ не может быть пустым."}), 400
    
    try:
        result = continue_interview(session_id, user_answer)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 API запущено на http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)