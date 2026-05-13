import React, { useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';

interface CodeEditorModalProps {
    isOpen: boolean;
    initialCode: string;
    language: string;
    onClose: () => void;
    onSave: (code: string, language: string) => void;  // добавлен язык
}

// Поддерживаемые языки
const SUPPORTED_LANGUAGES = [
    'python',
    'javascript',
    'sql',
    'typescript',
    'java',
    'c',
    'cpp',
    'csharp',
    'go',
    'rust',
];

const CodeEditorModal: React.FC<CodeEditorModalProps> = ({
    isOpen,
    initialCode,
    language,
    onClose,
    onSave,
}) => {
    const [code, setCode] = useState(initialCode);
    const [currentLanguage, setCurrentLanguage] = useState(language);

    // Синхронизируем при открытии
    useEffect(() => {
        if (isOpen) {
            setCode(initialCode);
            setCurrentLanguage(language);
        }
    }, [isOpen, initialCode, language]);

    const handleSave = () => {
        onSave(code, currentLanguage);   
        onClose();
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Escape') {
            onClose();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div
                className="modal-content code-editor-modal"
                onClick={(e) => e.stopPropagation()}
                onKeyDown={handleKeyDown}
            >
                <div className="modal-header">
                    <h3>Редактор кода</h3>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <label htmlFor="language-select" style={{ color: '#ccc', fontSize: '14px' }}>
                            Язык:
                        </label>
                        <select
                            id="language-select"
                            value={currentLanguage}
                            onChange={(e) => setCurrentLanguage(e.target.value)}
                            style={{
                                padding: '4px 8px',
                                borderRadius: '4px',
                                border: '1px solid #555',
                                background: '#2d2d2d',
                                color: '#fff',
                            }}
                        >
                            {SUPPORTED_LANGUAGES.map((lang) => (
                                <option key={lang} value={lang}>
                                    {lang.charAt(0).toUpperCase() + lang.slice(1)}
                                </option>
                            ))}
                        </select>
                    </div>
                    <button onClick={onClose} className="modal-close-btn">✕</button>
                </div>
                <div className="editor-container">
                    <Editor
                        height="100%"
                        language={currentLanguage}
                        value={code}
                        onChange={(value) => setCode(value || '')}
                        theme="vs-dark"
                        options={{
                            minimap: { enabled: false },
                            fontSize: 14,
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                            automaticLayout: true,
                        }}
                    />
                </div>
                <div className="modal-footer">
                    <button onClick={onClose} className="btn-cancel">Отмена</button>
                    <button onClick={handleSave} className="btn-save">Сохранить код</button>
                </div>
            </div>
        </div>
    );
};

export default CodeEditorModal;