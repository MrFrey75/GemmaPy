import React from 'react';
import { useAuth } from '../hooks/useAuth';

export const HomePage = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:py-16 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">
            Welcome to GemmaPy WebApp
          </h1>
          <p className="mt-4 text-xl text-gray-600">
            Hello, {user?.username}! Start by selecting an option below.
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
          {/* Chat */}
          <a
            href="/chat"
            className="bg-white rounded-lg shadow hover:shadow-lg transition p-6"
          >
            <div className="text-3xl mb-4">💬</div>
            <h3 className="text-lg font-semibold mb-2">Chat</h3>
            <p className="text-gray-600">
              Start a new conversation with any available model
            </p>
          </a>

          {/* Conversations */}
          <a
            href="/conversations"
            className="bg-white rounded-lg shadow hover:shadow-lg transition p-6"
          >
            <div className="text-3xl mb-4">📝</div>
            <h3 className="text-lg font-semibold mb-2">Conversations</h3>
            <p className="text-gray-600">
              Manage your saved conversations and chat history
            </p>
          </a>

          {/* Model Comparison */}
          {import.meta.env.VITE_ENABLE_COMPARISON === 'true' && (
            <a
              href="/compare"
              className="bg-white rounded-lg shadow hover:shadow-lg transition p-6"
            >
              <div className="text-3xl mb-4">⚖️</div>
              <h3 className="text-lg font-semibold mb-2">Compare Models</h3>
              <p className="text-gray-600">
                Compare responses from multiple models side-by-side
              </p>
            </a>
          )}

          {/* Metrics */}
          {import.meta.env.VITE_ENABLE_METRICS === 'true' && (
            <a
              href="/metrics"
              className="bg-white rounded-lg shadow hover:shadow-lg transition p-6"
            >
              <div className="text-3xl mb-4">📊</div>
              <h3 className="text-lg font-semibold mb-2">Metrics</h3>
              <p className="text-gray-600">
                Track your API usage and performance metrics
              </p>
            </a>
          )}

          {/* RAG */}
          {import.meta.env.VITE_ENABLE_RAG === 'true' && (
            <a
              href="/rag"
              className="bg-white rounded-lg shadow hover:shadow-lg transition p-6"
            >
              <div className="text-3xl mb-4">📚</div>
              <h3 className="text-lg font-semibold mb-2">RAG</h3>
              <p className="text-gray-600">
                Upload documents and ask questions using retrieval
              </p>
            </a>
          )}

          {/* Profile */}
          <a
            href="/profile"
            className="bg-white rounded-lg shadow hover:shadow-lg transition p-6"
          >
            <div className="text-3xl mb-4">👤</div>
            <h3 className="text-lg font-semibold mb-2">Profile</h3>
            <p className="text-gray-600">
              Manage your profile and account settings
            </p>
          </a>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
