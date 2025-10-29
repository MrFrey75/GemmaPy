import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export const Header = () => {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="bg-white shadow">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link to="/" className="text-2xl font-bold text-blue-600">
              GemmaPy
            </Link>
          </div>

          <div className="hidden md:flex items-center space-x-4">
            <Link
              to="/chat"
              className="text-gray-600 hover:text-blue-600 transition"
            >
              Chat
            </Link>
            <Link
              to="/conversations"
              className="text-gray-600 hover:text-blue-600 transition"
            >
              Conversations
            </Link>
            {import.meta.env.VITE_ENABLE_COMPARISON === 'true' && (
              <Link
                to="/compare"
                className="text-gray-600 hover:text-blue-600 transition"
              >
                Compare Models
              </Link>
            )}
            {import.meta.env.VITE_ENABLE_METRICS === 'true' && (
              <Link
                to="/metrics"
                className="text-gray-600 hover:text-blue-600 transition"
              >
                Metrics
              </Link>
            )}
            {isAdmin && (
              <Link
                to="/admin"
                className="text-gray-600 hover:text-red-600 transition"
              >
                Admin
              </Link>
            )}
            <Link
              to="/profile"
              className="text-gray-600 hover:text-blue-600 transition"
            >
              {user?.username}
            </Link>
            <button
              onClick={handleLogout}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>
    </header>
  );
};

export default Header;
