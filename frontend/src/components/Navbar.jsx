import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, User, ShieldCheck, GraduationCap, Wrench } from 'lucide-react';
import NotificationDrawer from './NotificationDrawer';
import logoImg from '../assets/logo.png';

export default function Navbar({ onSelectTicketFromNotification }) {
  const { user, logout } = useAuth();

  return (
    <header className="bg-slate-900 text-white shadow-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
        
        {/* Brand / Logo */}
        <div className="flex items-center space-x-3">
          <img
            src={logoImg}
            alt="NIT Warangal Logo"
            className="w-10 h-10 rounded-xl object-contain bg-white p-0.5 shadow-sm border border-slate-700 shrink-0"
          />
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base sm:text-lg font-bold tracking-tight">CGAS Portal</h1>
              <span className="hidden sm:inline-block text-[10px] uppercase font-bold tracking-wider bg-slate-800 text-teal-300 border border-teal-500/30 px-2 py-0.5 rounded-full">
                NIT Warangal
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden xs:block">Campus Grievance Addressal System</p>
          </div>
        </div>

        {/* User Info & Actions */}
        {user ? (
          <div className="flex items-center space-x-2 sm:space-x-4">
            
            {/* Notification Drawer (F12) */}
            <NotificationDrawer onSelectTicket={onSelectTicketFromNotification} />

            <div className="flex items-center space-x-2 text-right">
              <div className="hidden sm:block text-xs">
                <p className="font-semibold text-slate-100">{user.name}</p>
                <p className="text-slate-400">
                  {user.role === 'STUDENT' 
                    ? `Room: ${user.hostel_room || 'N/A'}` 
                    : user.role === 'SERVICEMAN' 
                    ? `${user.category || 'Maintenance'} Specialist` 
                    : user.department || 'Admin'}
                </p>
              </div>
              <span className={`inline-flex items-center space-x-1 text-xs font-semibold px-2.5 py-1 rounded-full border ${
                user.role === 'ADMIN'
                  ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                  : user.role === 'SERVICEMAN'
                  ? 'bg-blue-500/10 text-blue-300 border-blue-500/30'
                  : 'bg-teal-500/10 text-teal-300 border-teal-500/30'
              }`}>
                {user.role === 'ADMIN' ? (
                  <ShieldCheck className="w-3.5 h-3.5" />
                ) : user.role === 'SERVICEMAN' ? (
                  <Wrench className="w-3.5 h-3.5" />
                ) : (
                  <GraduationCap className="w-3.5 h-3.5" />
                )}
                <span>{user.role}</span>
              </span>
            </div>

            <button
              onClick={() => logout()}
              className="inline-flex items-center space-x-1.5 bg-slate-800 hover:bg-rose-950/40 text-slate-300 hover:text-rose-300 border border-slate-700 hover:border-rose-500/40 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        ) : (
          <div className="text-xs text-slate-400 font-medium">
            CS1207 OOP Lab
          </div>
        )}

      </div>
    </header>
  );
}
