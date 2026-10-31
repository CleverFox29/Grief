import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { PlusCircle, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import RaiseGrievanceModal from './RaiseGrievanceModal';
import StudentTicketList from './StudentTicketList';

export default function StudentDashboard() {
  const { user, token } = useAuth();
  const [isRaiseModalOpen, setIsRaiseModalOpen] = useState(false);
  const [ticketStats, setTicketStats] = useState({ active: 0, resolved: 0 });
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Load ticket statistics
  useEffect(() => {
    if (token) {
      fetch('/api/tickets/my-tickets', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(r => r.json())
        .then(tickets => {
          if (Array.isArray(tickets)) {
            const active = tickets.filter(t => ['OPEN', 'IN PROGRESS'].includes(t.status)).length;
            const resolved = tickets.filter(t => ['RESOLVED', 'CLOSED'].includes(t.status)).length;
            setTicketStats({ active, resolved });
          }
        })
        .catch(console.error);
    }
  }, [token, refreshTrigger]);

  const handleTicketCreated = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 sm:p-8 shadow-sm">
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
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Tickets</p>
            <p className="text-2xl font-bold text-slate-800">{ticketStats.active}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Resolved Tickets</p>
            <p className="text-2xl font-bold text-slate-800">{ticketStats.resolved}</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Reopen Policy (F13)</p>
            <p className="text-xs text-slate-600 mt-0.5">7 days window for unresolved issues</p>
          </div>
        </div>
      </div>

      {/* My Grievances Tracking List (F8, U4) */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-slate-800">My Filed Grievances (F8)</h3>
          <span className="text-xs text-slate-400 font-medium">Click any ticket to inspect full timeline and remarks</span>
        </div>
        
        <StudentTicketList 
          key={refreshTrigger}
          onOpenRaiseModal={() => setIsRaiseModalOpen(true)} 
        />
      </div>

      {/* Raise Grievance Wizard Modal (F4-F7, U3) */}
      <RaiseGrievanceModal
        isOpen={isRaiseModalOpen}
        onClose={() => setIsRaiseModalOpen(false)}
        onTicketCreated={handleTicketCreated}
      />
    </div>
  );
}
