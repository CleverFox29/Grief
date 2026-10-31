import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Inbox, Users, Layers, AlertTriangle } from 'lucide-react';
import AdminTicketQueue from './AdminTicketQueue';

export default function AdminDashboard() {
  const { user, token } = useAuth();
  const [stats, setStats] = useState({ total: 0, open: 0, in_progress: 0 });

  useEffect(() => {
    if (token) {
      fetch('/api/tickets/admin-queue', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(r => r.json())
        .then(tickets => {
          if (Array.isArray(tickets)) {
            const total = tickets.length;
            const open = tickets.filter(t => t.status === 'OPEN').length;
            const in_progress = tickets.filter(t => t.status === 'IN PROGRESS').length;
            setStats({ total, open, in_progress });
          }
        })
        .catch(console.error);
    }
  }, [token]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-amber-400 bg-amber-400/10 px-2.5 py-1 rounded-full border border-amber-400/20">
              Admin Portal &bull; {user?.admin_level || 'STANDARD'}
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-2">
              Central Grievance Queue
            </h2>
            <p className="text-sm text-slate-300 mt-1">
              Logged in as <span className="font-semibold text-white">{user?.name}</span> ({user?.user_id}) &bull; Dept: <span className="text-white font-medium">{user?.department}</span>
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs bg-slate-800 border border-slate-700 text-slate-300 px-3 py-1.5 rounded-xl font-medium">
              15-Min Inactivity Active
            </span>
          </div>
        </div>
      </div>

      {/* Admin Operations Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Queue Total</span>
            <Inbox className="w-5 h-5 text-indigo-500" />
          </div>
          <p className="text-2xl font-bold text-slate-800">{stats.total}</p>
          <span className="text-[11px] text-slate-500">Primary tickets (F9)</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Awaiting Action</span>
            <AlertTriangle className="w-5 h-5 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-amber-600">{stats.open}</p>
          <span className="text-[11px] text-amber-600 font-medium">Status: OPEN</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">In Progress</span>
            <Users className="w-5 h-5 text-teal-500" />
          </div>
          <p className="text-2xl font-bold text-teal-600">{stats.in_progress}</p>
          <span className="text-[11px] text-teal-600 font-medium">Work underway</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Auditing</span>
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
          </div>
          <p className="text-2xl font-bold text-slate-800">Immutable</p>
          <span className="text-[11px] text-slate-500">Non-editable logs (F15)</span>
        </div>
      </div>

      {/* Unified Ticket Queue Component (F9, F10, F11, U5, U6) */}
      <AdminTicketQueue />

    </div>
  );
}
