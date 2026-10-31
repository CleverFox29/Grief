import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { PlusCircle, ListOrdered, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import RaiseGrievanceModal from './RaiseGrievanceModal';

export default function StudentDashboard() {
  const { user } = useAuth();
  const [isRaiseModalOpen, setIsRaiseModalOpen] = useState(false);
  const [recentTickets, setRecentTickets] = useState([]);

  const handleTicketCreated = (newTicket) => {
    setRecentTickets(prev => [newTicket, ...prev]);
  };

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
              onClick={() => setIsRaiseModalOpen(true)}
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
            <p className="text-2xl font-bold text-slate-800">{recentTickets.length}</p>
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

      {/* Recently Created Tickets or Empty State */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-slate-800">Recent Grievances</h3>
          <span className="text-xs text-slate-400 font-medium">Full tracking list in Phase 4</span>
        </div>

        {recentTickets.length > 0 ? (
          <div className="space-y-3">
            {recentTickets.map(t => (
              <div key={t.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold text-slate-900">#{t.ticket_id}</span>
                    <span className="text-[10px] font-semibold bg-teal-100 text-teal-800 px-2 py-0.5 rounded">
                      {t.category_name}
                    </span>
                    <span className="text-[10px] font-semibold bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                      {t.status}
                    </span>
                    {t.is_flagged_duplicate && (
                      <span className="text-[10px] font-semibold bg-amber-100 text-amber-800 px-2 py-0.5 rounded">
                        Flagged Duplicate
                      </span>
                    )}
                  </div>
                  <p className="text-xs font-medium text-slate-700 mt-1">{t.location} &bull; {t.description}</p>
                </div>
                <div className="text-right text-[11px] text-slate-400">
                  {new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl">
            <ListOrdered className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-700">No grievances filed yet in this session</p>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
              Click "Raise Grievance" to submit a ticket across Plumbing, Carpentry, Electrical, Masonry, Administrative, or Security.
            </p>
            <button
              onClick={() => setIsRaiseModalOpen(true)}
              className="inline-flex items-center space-x-1.5 text-xs font-bold text-teal-600 bg-teal-50 hover:bg-teal-100 px-3.5 py-2 rounded-xl transition-colors"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Raise First Grievance</span>
            </button>
          </div>
        )}
      </div>

      {/* Raise Grievance Modal (F4-F7, U3) */}
      <RaiseGrievanceModal
        isOpen={isRaiseModalOpen}
        onClose={() => setIsRaiseModalOpen(false)}
        onTicketCreated={handleTicketCreated}
      />
    </div>
  );
}
