import React from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Inbox, Users, BarChart3, Layers } from 'lucide-react';

export default function AdminDashboard() {
  const { user } = useAuth();

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 sm:p-8 shadow-sm mb-8">
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

      {/* Admin Operations Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-5 mb-8">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Queue Total</span>
            <Inbox className="w-5 h-5 text-indigo-500" />
          </div>
          <p className="text-2xl font-bold text-slate-800">0</p>
          <span className="text-[11px] text-slate-500">Unified queue (F9)</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Categories</span>
            <Layers className="w-5 h-5 text-teal-500" />
          </div>
          <p className="text-2xl font-bold text-slate-800">6</p>
          <span className="text-[11px] text-teal-600 font-medium">Default active (F14)</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Staff Roster</span>
            <Users className="w-5 h-5 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-slate-800">6</p>
          <span className="text-[11px] text-slate-500">Assigned trades</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Audit Security</span>
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
          </div>
          <p className="text-2xl font-bold text-slate-800">Active</p>
          <span className="text-[11px] text-slate-500">Immutable logging (F15)</span>
        </div>
      </div>

      {/* Admin Action Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="font-bold text-slate-800 text-base mb-1">Unified Ticket Queue (Phase 4)</h3>
          <p className="text-xs text-slate-500 mb-4">
            Sort tickets (newest/oldest), filter by category, status, and location, and assign maintenance staff.
          </p>
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 text-xs text-slate-600">
            &bull; Ready for Phase 4 queue sorting, duplicate grouping, and cascading closures.
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="font-bold text-slate-800 text-base mb-1">Master Records & Reports (Phase 6)</h3>
          <p className="text-xs text-slate-500 mb-4">
            Upload student records via CSV, manage worker records, edit categories, and export audit logs.
          </p>
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 text-xs text-slate-600">
            &bull; Ready for Phase 6 student CSV bulk import, staff management, and category protection.
          </div>
        </div>
      </div>
    </div>
  );
}
