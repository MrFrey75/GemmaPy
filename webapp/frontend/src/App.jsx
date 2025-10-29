import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { NotificationProvider } from './context/NotificationContext';
import ProtectedRoute from './components/ProtectedRoute';
import Header from './components/Header';
import NotificationContainer from './components/NotificationContainer';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import './styles/globals.css';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NotificationProvider>
          <div className="min-h-screen bg-gray-50">
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <>
                      <Header />
                      <HomePage />
                    </>
                  </ProtectedRoute>
                }
              />

              {/* Add more routes here as you build more pages */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
          <NotificationContainer />
        </NotificationProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
