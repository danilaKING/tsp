import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import LoginPage from './pages/LoginPage';
import { startInterview, sendAnswer, generateFeedback, getUserInterviews } from './api';

// Types
interface Message {
    id: string;
    text: string;
    type: 'user' | 'assistant' | 'report';
}

interface FeedbackData {
    score: number;
    pros: string[];
    cons: string[];
    recommendations: { topic: string; description: string }[];
}

interface InterviewHistoryItem {
    id: string;
    stack: string;
    difficulty: string;
    status: string;
    started_at: string;
    finished_at: string | null;
    score: number | null;
}

const App: React.FC = () => {
    // Auth state
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [history, setHistory] = useState<InterviewHistoryItem[]>([]);

    // Interview state
    const [messages, setMessages] = useState<Message[]>([
        { id: '0', text: '👋 Нажмите «Начать интервью», чтобы начать собеседование. Выберите стек и сложность.', type: 'assistant' }
    ]);
    const [stack, setStack] = useState('Python');
    const [difficulty, setDifficulty] = useState('Лёгкий');
    const [answer, setAnswer] = useState('');

    const [interviewId, setInterviewId] = useState<string | null>(null);
    const [isInterviewActive, setIsInterviewActive] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [statusText, setStatusText] = useState('⏳ Ожидание начала интервью');
    const [feedback, setFeedback] = useState<FeedbackData | null>(null);

    const chatContainerRef = useRef<HTMLDivElement>(null);

    // Check for existing token on mount
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            setIsAuthenticated(true);
        }
    }, []);

    // Auto-scroll chat to bottom
    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const handleLogin = (token: string) => {
        setIsAuthenticated(true);
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        setIsAuthenticated(false);
        resetInterview();
    };

    const resetInterview = () => {
        setMessages([
            { id: '0', text: '👋 Нажмите «Начать интервью», чтобы начать собеседование. Выберите стек и сложность.', type: 'assistant' }
        ]);
        setInterviewId(null);
        setIsInterviewActive(false);
        setFeedback(null);
        setStatusText('⏳ Ожидание начала интервью');
    };

    // Start interview
    const handleStartInterview = async () => {
        setMessages([{ id: Date.now().toString(), text: '⏳ Запуск интервью... Пожалуйста, подождите.', type: 'assistant' }]);
        setIsLoading(true);
        setIsInterviewActive(false);
        setFeedback(null);

        try {
            const data = await startInterview(stack, difficulty);
            setInterviewId(data.interview_id);
            setMessages([{ id: Date.now().toString(), text: data.message, type: 'assistant' }]);
            setIsInterviewActive(true);
            setStatusText('🎙️ Интервью идёт. Отвечайте на вопросы.');
        } catch (err: any) {
            setMessages([{ id: Date.now().toString(), text: `❌ Ошибка: ${err.message}`, type: 'assistant' }]);
        } finally {
            setIsLoading(false);
        }
    };

    // Send answer
    const handleSendAnswer = async () => {
        if (!answer.trim() || !isInterviewActive || !interviewId) return;

        const userAnswer = answer;
        setMessages(prev => [...prev, { id: Date.now().toString(), text: userAnswer, type: 'user' }]);
        setAnswer('');
        setIsLoading(true);
        setStatusText('🤔 ИИ анализирует ответ...');

        try {
            const data = await sendAnswer(interviewId, userAnswer);

            // Add AI reaction
            if (data.ai_reaction) {
                setMessages(prev => [...prev, { id: Date.now().toString(), text: data.ai_reaction, type: 'assistant' }]);
            }

            if (data.type === 'finished') {
                // Interview completed
                setIsInterviewActive(false);
                setStatusText('✅ Интервью завершено. Генерация отчёта...');
                
                // Generate feedback
                try {
                    const feedbackData = await generateFeedback(interviewId);
                    setFeedback(feedbackData.analysis);
                    setStatusText('✅ Интервью завершено. Отчёт готов!');
                } catch (err: any) {
                    setMessages(prev => [...prev, { id: Date.now().toString(), text: `❌ Ошибка генерации отчёта: ${err.message}`, type: 'assistant' }]);
                }
            } else {
                // Next question
                if (data.next_question) {
                    setMessages(prev => [...prev, { id: Date.now().toString(), text: data.next_question, type: 'assistant' }]);
                }
                setStatusText('🎙️ Интервью идёт.');
            }
        } catch (err: any) {
            setMessages(prev => [...prev, { id: Date.now().toString(), text: `❌ Ошибка: ${err.message}`, type: 'assistant' }]);
        } finally {
            setIsLoading(false);
        }
    };

    // Load interview history
    const handleLoadHistory = async () => {
        try {
            const data = await getUserInterviews();
            setHistory(data);
            setShowHistory(true);
        } catch (err: any) {
            alert(`Ошибка загрузки истории: ${err.message}`);
        }
    };

    if (!isAuthenticated) {
        return <LoginPage onLogin={handleLogin} />;
    }

    return (
        <div className="container">
            <header className="app-header">
                <h1>AI Mock Interview</h1>
                <div className="header-actions">
                    <button onClick={handleLoadHistory} className="btn-secondary">
                        📋 История
                    </button>
                    <button onClick={handleLogout} className="btn-logout">
                        Выйти
                    </button>
                </div>
            </header>

            {showHistory ? (
                <div className="history-page">
                    <h2>История интервью</h2>
                    <button onClick={() => setShowHistory(false)} className="btn-secondary">
                        ← Назад
                    </button>
                    {history.length === 0 ? (
                        <p className="no-data">У вас пока нет прошедших интервью.</p>
                    ) : (
                        <table className="history-table">
                            <thead>
                                <tr>
                                    <th>Дата</th>
                                    <th>Стек</th>
                                    <th>Сложность</th>
                                    <th>Статус</th>
                                    <th>Оценка</th>
                                </tr>
                            </thead>
                            <tbody>
                                {history.map((item) => (
                                    <tr key={item.id}>
                                        <td>{new Date(item.started_at).toLocaleDateString('ru-RU')}</td>
                                        <td>{item.stack}</td>
                                        <td>{item.difficulty}</td>
                                        <td>{item.status === 'completed' ? '✅ Завершено' : item.status === 'active' ? '🔄 Активно' : '❌ Прервано'}</td>
                                        <td>{item.score !== null ? `${item.score}/100` : '—'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            ) : (
                <>
                    <div className="controls">
                        <select value={stack} onChange={(e) => setStack(e.target.value)} disabled={isInterviewActive}>
                            <option value="Python">Python</option>
                            <option value="JavaScript">JavaScript</option>
                            <option value="SQL">SQL</option>
                            <option value="Алгоритмы">Алгоритмы</option>
                        </select>
                        <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} disabled={isInterviewActive}>
                            <option value="Лёгкий">Лёгкий</option>
                            <option value="Средний">Средний</option>
                            <option value="Сложный">Сложный</option>
                        </select>
                        <button onClick={handleStartInterview} disabled={isInterviewActive || isLoading} className="btn-primary">
                            {isInterviewActive ? 'Интервью идёт...' : 'Начать интервью'}
                        </button>
                    </div>

                    <div className="chat-box" ref={chatContainerRef}>
                        {messages.map((msg) => (
                            <div key={msg.id} className={`message ${msg.type}`}>
                                <div className="message-bubble">{msg.text}</div>
                            </div>
                        ))}
                        {isLoading && <div className="loading-indicator">{statusText}</div>}
                    </div>

                    {isInterviewActive && (
                        <div className="input-area">
                            <input
                                type="text"
                                value={answer}
                                onChange={(e) => setAnswer(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSendAnswer()}
                                className="answer-input"
                                placeholder="Ваш ответ..."
                                disabled={!isInterviewActive || isLoading}
                            />
                            <button onClick={handleSendAnswer} disabled={!isInterviewActive || isLoading} className="btn-primary">
                                Отправить
                            </button>
                        </div>
                    )}

                    {feedback && (
                        <div className="feedback-section">
                            <h2>📊 Результаты интервью</h2>
                            <div className="score-display">{feedback.score}/100</div>
                            
                            <div className="feedback-grid">
                                <div className="feedback-card pros">
                                    <h3>✅ Сильные стороны</h3>
                                    <ul>
                                        {feedback.pros.map((pro, idx) => (
                                            <li key={idx}>{pro}</li>
                                        ))}
                                    </ul>
                                </div>
                                
                                <div className="feedback-card cons">
                                    <h3>⚠️ Зоны роста</h3>
                                    <ul>
                                        {feedback.cons.map((con, idx) => (
                                            <li key={idx}>{con}</li>
                                        ))}
                                    </ul>
                                </div>
                            </div>

                            <div className="recommendations">
                                <h3>📚 Рекомендации</h3>
                                {feedback.recommendations.map((rec, idx) => (
                                    <div key={idx} className="recommendation-item">
                                        <strong>{rec.topic}</strong>
                                        <p>{rec.description}</p>
                                    </div>
                                ))}
                            </div>

                            <button onClick={resetInterview} className="btn-primary">
                                Начать новое интервью
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default App;
