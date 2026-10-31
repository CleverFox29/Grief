import React from 'react';
import { useAuth } from '../context/AuthContext';
import { PlusCircle, ListOrdered, CheckCircle, Clock, AlertCircle } from 'lucide-react';

export default function StudentDashboard() {
  const { user } = useAuth();

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 sm:p-8 shadow-sm mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-teal-400 bg-teal-400/10 px-2.5 py-1 rounded-full border border-teal-400/20">
              Student Portal
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-2">
              Welcome, {user?.name}
            </h2>
            <p className="text-sm text-slate-300 mt-1">
              Enrollment No: <span className="font-mono text-white font-medium">{user?.enrollment_no}</span> &bull; Room: <span className="text-white font-medium">{user?.hostel_room}</span>
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => alert('Phase 3 will open the New Grievance Filing Wizard with intelligent Deduplication Check.')}
              className="inline-flex items-center space-x-2 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold px-4 py-2.5 rounded-xl shadow transition-colors text-sm"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Raise Grievance</span>
            </button>
          </div>
        </div>
      </div>

      {/* Metrics & Status Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Tickets</p>
            <p className="text-2xl font-bold text-slate-800">0</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Resolved Tickets</p>
            <p className="text-2xl font-bold text-slate-800">0</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Reopen Window</p>
            <p className="text-xs text-slate-600 mt-0.5">7 days after resolution</p>
          </div>
        </div>
      </div>

      {/* Placeholder for Phase 4 Ticket Tracking */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-slate-800">My Grievances (Phase 4)</h3>
          <span className="text-xs text-slate-400 font-medium">Sorted by newest first</span>
        </div>
        <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl">
          <ListOrdered className="w-10 h-10 text-slate-300 mx-auto mb-2" />
          <p className="text-sm font-semibold text-slate-700">No active grievances filed yet</p>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
            Phase 3 will enable submitting grievances across Plumbing, Carpentry, Electrical, Masonry, Administrative, and Security.
          </p>
        </div>
      </div>
    </div>
  );
}
