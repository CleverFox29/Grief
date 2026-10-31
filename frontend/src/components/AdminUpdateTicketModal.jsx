import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { X, HardHat, AlertTriangle, ShieldCheck, CheckCircle2, ArrowRight } from 'lucide-react';

export default function AdminUpdateTicketModal({ ticket, isOpen, onClose, onUpdated }) {
  const { token } = useAuth();
  
  const [status, setStatus] = useState(ticket?.status || 'OPEN');
  const [staffList, setStaffList] = useState([]);
  const [assignedStaffId, setAssignedStaffId] = useState(ticket?.assigned_staff_id?.toString() || '');
  const [remark, setRemark] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    if (isOpen && ticket) {
      setStatus(ticket.status);
      setAssignedStaffId(ticket.assigned_staff_id ? ticket.assigned_staff_id.toString() : '');
      setRemark('');
      setErrorMsg(null);

      // Load staff records for ticket assignment
      fetch('/api/staff', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(data => setStaffList(data))
        .catch(() => setErrorMsg('Failed to fetch staff roster.'));
    }
  }, [isOpen, ticket, token]);

  if (!isOpen || !ticket) return null;

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!remark.trim()) {
      setErrorMsg('A remark explaining this action is mandatory (F11).');
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    const payload = {
      status,
      assigned_staff_id: assignedStaffId ? parseInt(assignedStaffId) : null,
      remark: remark.trim(),
      expected_updated_at: ticket.updated_at
    };

    try {
      const resp = await fetch(`/api/tickets/${ticket.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || 'Failed to update ticket.');
      }

      onUpdated && onUpdated(data);
      onClose();
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const isClosingParentWithDuplicates = 
    (status === 'CLOSED' || status === 'RESOLVED') && 
    ticket.duplicate_count > 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
        
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <ShieldCheck className="w-5 h-5 text-amber-400" />
            <div>
              <h3 className="font-bold text-sm">Update Grievance #{ticket.ticket_id}</h3>
              <p className="text-[11px] text-slate-400">{ticket.category_name} &bull; {ticket.location}</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleUpdate} className="p-6 space-y-4">
          {errorMsg && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl p-3 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Cascading Closure Notice (F11) */}
          {isClosingParentWithDuplicates && (
            <div className="bg-purple-50 border border-purple-200 text-purple-900 text-xs rounded-xl p-3 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
              <div>
                <strong>Cascading Closure Notice:</strong> Closing this parent ticket will automatically cascade status '{status}' to all <strong>{ticket.duplicate_count}</strong> linked duplicate ticket(s).
              </div>
            </div>
          )}

          {/* Status Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Ticket Lifecycle Status (F11)
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <option value="OPEN">OPEN (Awaiting Action)</option>
              <option value="IN PROGRESS">IN PROGRESS (Work Underway)</option>
              <option value="RESOLVED">RESOLVED (Ready for Student Rating)</option>
              <option value="CLOSED">CLOSED (Completed & Finalized)</option>
            </select>
          </div>

          {/* Staff Assignment */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center space-x-1.5">
              <HardHat className="w-3.5 h-3.5 text-amber-600" />
              <span>Assign Maintenance Personnel</span>
            </label>
            <select
              value={assignedStaffId}
              onChange={(e) => setAssignedStaffId(e.target.value)}
              className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <option value="">-- Unassigned --</option>
              {staffList.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.contact}) {s.category_name ? `- ${s.category_name}` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Mandatory Remark (F11) */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Resolution / Action Remark * (F11)
            </label>
            <textarea
              rows={3}
              value={remark}
              onChange={(e) => setRemark(e.target.value)}
              placeholder="State the maintenance action taken, materials used, or inspection outcome."
              required
              className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center space-x-1.5 px-5 py-2.5 text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white rounded-xl shadow-md transition-colors disabled:opacity-50"
            >
              <span>{loading ? 'Saving Changes...' : 'Save & Notify Student'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
