import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  MapPin, 
  Clock, 
  Calendar, 
  ListOrdered, 
  ArrowUpDown, 
  Eye, 
  HardHat,
  CopyCheck,
  PlusCircle
} from 'lucide-react';
import TicketDetailModal from './TicketDetailModal';

export default function StudentTicketList({ onOpenRaiseModal }) {
  const { token } = useAuth();
  
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortOrder, setSortOrder] = useState('desc'); // 'desc' = newest first, 'asc' = oldest first
  
  const [selectedTicketId, setSelectedTicketId] = useState(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  const fetchTickets = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (statusFilter !== 'ALL') params.append('status', statusFilter);
    params.append('sort', sortOrder);

    fetch(`/api/tickets/my-tickets?${params.toString()}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.ok ? r.json() : [])
      .then(data => setTickets(Array.isArray(data) ? data : []))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchTickets();
  }, [statusFilter, sortOrder]);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'OPEN':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'IN PROGRESS':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'PENDING CONFIRMATION':
        return 'bg-purple-100 text-purple-900 border-purple-300';
      case 'RESOLVED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'CLOSED':
        return 'bg-slate-100 text-slate-700 border-slate-300';
      case 'DUPLICATE':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      
      {/* Top Controls Bar */}
      <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        {/* Status Filter Tabs (F8, U4) */}
        <div className="flex flex-wrap gap-1 bg-slate-100 p-1 rounded-xl">
          {['ALL', 'OPEN', 'IN PROGRESS', 'PENDING CONFIRMATION', 'RESOLVED', 'CLOSED', 'DUPLICATE'].map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                statusFilter === s
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Sort Toggle */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setSortOrder(prev => (prev === 'desc' ? 'asc' : 'desc'))}
            className="inline-flex items-center space-x-1.5 text-xs font-semibold bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 px-3 py-2 rounded-xl transition-colors"
          >
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-500" />
            <span>{sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}</span>
          </button>
        </div>
      </div>

      {/* Tickets List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">
          Loading your grievances...
        </div>
      ) : tickets.length === 0 ? (
        <div className="text-center py-12 px-4 space-y-3">
          <ListOrdered className="w-10 h-10 text-slate-300 mx-auto" />
          <p className="text-sm font-semibold text-slate-700">No grievances found in this filter</p>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            {statusFilter === 'ALL'
              ? 'You have not submitted any campus tickets yet.'
              : `You have no tickets currently in status '${statusFilter}'.`}
          </p>
          {statusFilter === 'ALL' && (
            <button
              onClick={onOpenRaiseModal}
              className="inline-flex items-center space-x-1.5 text-xs font-bold text-teal-600 bg-teal-50 hover:bg-teal-100 px-4 py-2 rounded-xl transition-colors mt-2"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Raise a Grievance</span>
            </button>
          )}
        </div>
      ) : (
        <div className="divide-y divide-slate-100">
          {tickets.map((t) => (
            <div 
              key={t.id} 
              onClick={() => {
                setSelectedTicketId(t.id);
                setIsDetailOpen(true);
              }}
              className="p-5 hover:bg-slate-50/70 transition-colors cursor-pointer group"
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 mb-2">
                <div className="flex flex-wrap items-center space-x-2">
                  <span className="font-mono font-bold text-xs bg-slate-100 text-slate-900 px-2.5 py-1 rounded-md border border-slate-200">
                    #{t.ticket_id}
                  </span>
                  <span className="text-xs font-semibold bg-teal-50 text-teal-800 border border-teal-200 px-2.5 py-0.5 rounded-full">
                    {t.category_name}
                  </span>
                  <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${getStatusBadge(t.status)}`}>
                    {t.status}
                  </span>
                  {t.is_flagged_duplicate && (
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                      Flagged Duplicate
                    </span>
                  )}
                </div>

                <div className="text-xs text-slate-400 flex items-center space-x-3">
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(t.created_at).toLocaleDateString()}</span>
                  </span>
                  <button className="text-slate-400 group-hover:text-teal-600 transition-colors">
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <p className="text-sm font-semibold text-slate-800 line-clamp-2">
                {t.description}
              </p>

              <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-slate-500 pt-2">
                <span className="flex items-center space-x-1 font-medium text-slate-700">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  <span>{t.location}</span>
                </span>
                {t.assigned_staff_name && (
                  <span className="flex items-center space-x-1 text-teal-800 font-medium">
                    <HardHat className="w-3.5 h-3.5 text-teal-600" />
                    <span>Staff: {t.assigned_staff_name}</span>
                  </span>
                )}
                {t.scheduling_remark && (
                  <span className="flex items-center space-x-1 text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200 font-medium">
                    <Clock className="w-3.5 h-3.5 text-blue-600" />
                    <span>Visit: {t.scheduling_remark}</span>
                  </span>
                )}
                {t.parent_ticket_id && (
                  <span className="flex items-center space-x-1 text-purple-700 font-medium">
                    <CopyCheck className="w-3.5 h-3.5 text-purple-600" />
                    <span>Linked to Parent Ticket</span>
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Ticket Detail & Timeline Modal */}
      <TicketDetailModal
        ticketId={selectedTicketId}
        isOpen={isDetailOpen}
        onClose={() => {
          setIsDetailOpen(false);
          setSelectedTicketId(null);
        }}
        onTicketUpdated={fetchTickets}
      />

    </div>
  );
}
