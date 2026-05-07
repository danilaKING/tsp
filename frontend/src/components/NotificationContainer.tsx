import React from 'react';
import Notification, { NotificationProps } from './Notification';
import './Notification.css';

interface NotificationContainerProps {
  notifications: NotificationProps[];
  onClose: (id: string) => void;
}

const NotificationContainer: React.FC<NotificationContainerProps> = ({ notifications, onClose }) => {
  return (
    <div className="notifications-container">
      {notifications.map((notification) => (
        <Notification key={notification.id} {...notification} onClose={onClose} />
      ))}
    </div>
  );
};

export default NotificationContainer;
