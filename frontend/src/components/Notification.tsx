import React, { useEffect } from 'react';
import './Notification.css';

export interface NotificationProps {
  id: string;
  type: 'error' | 'success' | 'warning' | 'info';
  message: string;
  duration?: number; // ms, 0 = persistent
  onClose: (id: string) => void;
}

const Notification: React.FC<NotificationProps> = ({ id, type, message, duration = 4000, onClose }) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => onClose(id), duration);
      return () => clearTimeout(timer);
    }
  }, [id, duration, onClose]);

  const icons = {
    error: '❌',
    success: '✅',
    warning: '⚠️',
    info: 'ℹ️',
  };

  return (
    <div className={`notification notification-${type}`}>
      <span className="notification-icon">{icons[type]}</span>
      <span className="notification-message">{message}</span>
      <button className="notification-close" onClick={() => onClose(id)}>
        ✕
      </button>
    </div>
  );
};

export default Notification;
