import React from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Login from './components/Login';
import StudentDashboard from './components/StudentDashboard';
import AdminDashboard from './components/AdminDashboard';
import ServicemanDashboard from './components/ServicemanDashboard';

function MainContent() {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Login />;
  }

  if (user?.role === 'ADMIN') {
    return <AdminDashboard />;
  }

  if (user?.role === 'SERVICEMAN') {
    return <ServicemanDashboard />;
  }

  return <StudentDashboard />;
}

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen flex flex-col justify-between bg-slate-50 text-slate-900 antialiased font-sans">
        <div>
          <Navbar />
          <main>
            <MainContent />
          </main>
        </div>

        <footer className="border-t border-slate-200 py-4 px-4 bg-white text-center text-xs text-slate-500">
          Campus Grievance Addressal System (CGAS) &bull; CS1207 OOP Lab Group II-8
        </footer>
      </div>
    </AuthProvider>
  );
}
