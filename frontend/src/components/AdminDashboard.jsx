import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Inbox, Users, Layers, AlertTriangle, BarChart3, Database } from 'lucide-react';
import AdminTicketQueue from './AdminTicketQueue';
import AdminRecordsManagement from './AdminRecordsManagement';
import AdminReports from './AdminReports';

export default function AdminDashboard() {
  const { user, token } = useAuth();
  const [activeTab, setActiveTab] = useState('QUEUE'); // 'QUEUE', 'RECORDS', 'REPORTS'
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
  }, [token, activeTab]);

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
              Administrator Console
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

      {/* Primary Navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
        <button
          onClick={() => setActiveTab('QUEUE')}
          className={`inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'QUEUE'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 bg-white border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <Inbox className="w-4 h-4 text-amber-400" />
          <span>Ticket Queue (F9, F10, F11)</span>
          <span className="ml-1 text-[10px] bg-slate-800 px-2 py-0.5 rounded-full text-amber-300">
            {stats.total}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('RECORDS')}
          className={`inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'RECORDS'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 bg-white border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <Database className="w-4 h-4 text-teal-400" />
          <span>Master Records & CSV (F14)</span>
        </button>

        <button
          onClick={() => setActiveTab('REPORTS')}
          className={`inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'REPORTS'
              ? 'bg-slate-900 text-white shadow-sm'
              : 'text-slate-600 hover:text-slate-900 bg-white border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <BarChart3 className="w-4 h-4 text-indigo-400" />
          <span>Audit Logs & Reports (F15)</span>
        </button>
      </div>

      {/* TAB CONTENT */}
      {activeTab === 'QUEUE' && (
        <div className="space-y-6">
          {/* Quick Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Awaiting Action</span>
                <p className="text-xl font-bold text-amber-600">{stats.open}</p>
              </div>
              <AlertTriangle className="w-6 h-6 text-amber-500" />
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">In Progress</span>
                <p className="text-xl font-bold text-teal-600">{stats.in_progress}</p>
              </div>
              <Users className="w-6 h-6 text-teal-500" />
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Queue</span>
                <p className="text-xl font-bold text-slate-800">{stats.total}</p>
              </div>
              <Inbox className="w-6 h-6 text-indigo-500" />
            </div>
          </div>

          <AdminTicketQueue />
        </div>
      )}

      {activeTab === 'RECORDS' && <AdminRecordsManagement />}

      {activeTab === 'REPORTS' && <AdminReports />}

    </div>
  );
}
