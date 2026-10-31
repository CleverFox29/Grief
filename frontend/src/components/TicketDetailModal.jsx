import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  X, 
  MapPin, 
  User, 
  Calendar, 
  Clock, 
  Shield, 
  CheckCircle2, 
  AlertCircle, 
  Layers, 
  HardHat, 
  Phone, 
  CopyCheck, 
  MessageSquare,
  Sparkles
} from 'lucide-react';

export default function TicketDetailModal({ ticketId, isOpen, onClose, onTicketUpdated }) {
  const { token, user } = useAuth();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && ticketId) {
      setLoading(true);
      setError(null);
      fetch(`/api/tickets/${ticketId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
        .then(res => {
          if (!res.ok) throw new Error('Failed to load ticket details.');
          return res.json();
        })
        .then(data => setTicket(data))
        .catch(err => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [isOpen, ticketId, token]);

  if (!isOpen) return null;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'OPEN':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'IN PROGRESS':
        return 'bg-amber-100 text-amber-800 border-amber-200';
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-3xl rounded-2xl shadow-2xl border border-slate-200 overflow-hidden max-h-[92vh] flex flex-col">
        
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3">
            <span className="font-mono font-bold text-sm bg-teal-500/20 text-teal-400 px-2.5 py-1 rounded-lg border border-teal-500/30">
              #{ticket?.ticket_id || 'Loading...'}
            </span>
            <div className="hidden xs:block">
              <h3 className="font-bold text-sm">{ticket?.category_name || 'Grievance Details'}</h3>
              <p className="text-[11px] text-slate-400">Campus Grievance Addressal System</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {loading && (
            <div className="text-center py-12 text-slate-400 text-sm">
              Loading ticket details & timeline...
            </div>
          )}

          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl p-3 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {!loading && ticket && (
            <>
              {/* Status & Category Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
                <div className="flex items-center space-x-2">
                  <span className={`text-xs font-bold px-3 py-1 rounded-full border ${getStatusBadge(ticket.status)}`}>
                    {ticket.status}
                  </span>
                  {ticket.is_confidential && (
                    <span className="inline-flex items-center space-x-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-300">
                      <Shield className="w-3 h-3 text-amber-600" />
                      <span>Confidential</span>
                    </span>
                  )}
                  {ticket.is_flagged_duplicate && (
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                      Flagged Duplicate
                    </span>
                  )}
                </div>

                <div className="text-xs text-slate-500 flex items-center space-x-3">
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{new Date(ticket.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </span>
                </div>
              </div>

              {/* Main Grievance Details */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Left: Description & Location (2 cols) */}
                <div className="md:col-span-2 space-y-4">
                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Campus Location
                    </h4>
                    <p className="text-sm font-semibold text-slate-800 flex items-center space-x-1.5">
                      <MapPin className="w-4 h-4 text-teal-600 shrink-0" />
                      <span>{ticket.location}</span>
                    </p>
                  </div>

                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Description
                    </h4>
                    <p className="text-sm text-slate-700 bg-slate-50 p-3.5 rounded-xl border border-slate-200 leading-relaxed whitespace-pre-wrap">
                      {ticket.description}
                    </p>
                  </div>

                  {ticket.photo_url && (
                    <div>
                      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                        Attached Photo Proof
                      </h4>
                      <div className="rounded-xl overflow-hidden border border-slate-200 max-h-56 bg-slate-100 flex items-center justify-center">
                        <img 
                          src={ticket.photo_url} 
                          alt="Grievance Attachment" 
                          className="max-h-56 object-contain"
                        />
                      </div>
                    </div>
                  )}

                  {/* Linked Duplicate Children (if parent) */}
                  {ticket.duplicate_children && ticket.duplicate_children.length > 0 && (
                    <div className="pt-2">
                      <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2 flex items-center space-x-1">
                        <CopyCheck className="w-3.5 h-3.5 text-teal-600" />
                        <span>Linked Duplicate Tickets ({ticket.duplicate_children.length})</span>
                      </h4>
                      <div className="space-y-2">
                        {ticket.duplicate_children.map(child => (
                          <div key={child.id} className="p-3 bg-purple-50/50 border border-purple-200 rounded-xl text-xs flex items-center justify-between">
                            <div>
                              <span className="font-mono font-bold text-slate-900">#{child.ticket_id}</span>
                              <span className="text-slate-500 ml-2">Filed by {child.student_name}</span>
                              <p className="text-slate-600 italic mt-0.5">"{child.description}"</p>
                            </div>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-800">
                              {child.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {ticket.parent_ticket_uid && (
                    <div className="bg-purple-50 border border-purple-200 text-purple-900 p-3 rounded-xl text-xs">
                      <strong>Child Duplicate:</strong> This ticket is linked to parent grievance <strong>#{ticket.parent_ticket_uid}</strong>. 
                      Closing the parent ticket will automatically cascade closure to this ticket.
                    </div>
                  )}
                </div>

                {/* Right: People & Assignee (1 col) */}
                <div className="space-y-4">
                  {/* Student Details */}
                  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-2">
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Submitted By
                    </h4>
                    <p className="text-xs font-bold text-slate-800 flex items-center space-x-1.5">
                      <User className="w-3.5 h-3.5 text-slate-500" />
                      <span>{ticket.student_name}</span>
                    </p>
                    <p className="text-xs text-slate-500">{ticket.student_email}</p>
                    {ticket.student_room && (
                      <p className="text-xs text-slate-500">Room: {ticket.student_room}</p>
                    )}
                  </div>

                  {/* Assigned Maintenance Worker */}
                  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-2">
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Assigned Maintenance Staff
                    </h4>
                    {ticket.assigned_staff_name ? (
                      <div>
                        <p className="text-xs font-bold text-teal-800 flex items-center space-x-1.5">
                          <HardHat className="w-4 h-4 text-teal-600" />
                          <span>{ticket.assigned_staff_name}</span>
                        </p>
                        {ticket.assigned_staff_contact && (
                          <p className="text-xs text-slate-600 mt-1 flex items-center space-x-1 font-mono">
                            <Phone className="w-3 h-3 text-slate-400" />
                            <span>{ticket.assigned_staff_contact}</span>
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400 italic">No staff assigned yet</p>
                    )}
                  </div>
                </div>

              </div>

              {/* Vertical Audit Timeline (F8, F11, NFR 4.2) */}
              <div className="pt-4 border-t border-slate-200">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center space-x-1.5">
                  <Clock className="w-4 h-4 text-teal-600" />
                  <span>Update History & Audit Timeline</span>
                </h4>

                {ticket.logs && ticket.logs.length > 0 ? (
                  <div className="relative border-l-2 border-slate-200 ml-3 space-y-6">
                    {ticket.logs.map((log, idx) => (
                      <div key={log.id} className="relative pl-6">
                        {/* Dot on timeline */}
                        <div className="absolute -left-[7px] top-1 w-3 h-3 rounded-full bg-teal-500 border-2 border-white shadow-sm"></div>

                        <div>
                          <div className="flex flex-wrap items-center space-x-2 text-xs">
                            <span className="font-bold text-slate-800">{log.action.replace('_', ' ')}</span>
                            {log.new_status && (
                              <span className={`text-[10px] font-semibold px-2 py-0.2 rounded border ${getStatusBadge(log.new_status)}`}>
                                &rarr; {log.new_status}
                              </span>
                            )}
                            <span className="text-slate-400">&bull;</span>
                            <span className="text-slate-500">{log.performed_by_name} ({log.performed_by_role})</span>
                          </div>

                          {log.remark && (
                            <p className="text-xs text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-100 mt-1.5 leading-relaxed">
                              {log.remark}
                            </p>
                          )}

                          <span className="text-[10px] text-slate-400 mt-1 block">
                            {new Date(log.timestamp).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No updates recorded yet.</p>
                )}
              </div>
            </>
          )}

        </div>

      </div>
    </div>
  );
}
