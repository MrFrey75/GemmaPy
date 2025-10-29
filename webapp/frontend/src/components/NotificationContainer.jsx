import React from 'react';
import { useNotification } from '../hooks/useNotification';

const Notification = ({ notification, onClose }) => {
  const baseClasses =
    'px-6 py-4 rounded-lg shadow-lg flex items-center justify-between mb-4 animate-slideIn';
  const typeClasses = {
    success: 'bg-green-100 text-green-800 border-l-4 border-green-500',
    error: 'bg-red-100 text-red-800 border-l-4 border-red-500',
    warning: 'bg-yellow-100 text-yellow-800 border-l-4 border-yellow-500',
    info: 'bg-blue-100 text-blue-800 border-l-4 border-blue-500',
  };

  return (
    <div className={`${baseClasses} ${typeClasses[notification.type]}`}>
      <span>{notification.message}</span>
      <button
        onClick={onClose}
        className="ml-4 font-bold hover:opacity-75"
      >
        ×
      </button>
    </div>
  );
};

export const NotificationContainer = () => {
  const { notifications, removeNotification } = useNotification();

  return (
    <div className="fixed top-4 right-4 z-50 w-96 max-w-full">
      {notifications.map((notification) => (
        <Notification
          key={notification.id}
          notification={notification}
          onClose={() => removeNotification(notification.id)}
        />
      ))}
    </div>
  );
};

export default NotificationContainer;
