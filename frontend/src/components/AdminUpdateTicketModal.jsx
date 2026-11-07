import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { X, HardHat, Wrench, AlertTriangle, ShieldCheck, CheckCircle2, ArrowRight, Lock } from 'lucide-react';

export default function AdminUpdateTicketModal({ ticket, isOpen, onClose, onUpdated }) {
  const { token } = useAuth();
  
  const [status, setStatus] = useState(ticket?.status || 'OPEN');
  const [servicemenList, setServicemenList] = useState([]);
  const [staffList, setStaffList] = useState([]);
  const [assignedServicemanId, setAssignedServicemanId] = useState(ticket?.assigned_serviceman_id?.toString() || '');
  const [assignedStaffId, setAssignedStaffId] = useState(ticket?.assigned_staff_id?.toString() || '');
  const [remark, setRemark] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    if (isOpen && ticket) {
      setStatus(ticket.status);
      setAssignedServicemanId(ticket.assigned_serviceman_id ? ticket.assigned_serviceman_id.toString() : '');
      setAssignedStaffId(ticket.assigned_staff_id ? ticket.assigned_staff_id.toString() : '');
      setRemark('');
      setErrorMsg(null);

      // Load matching servicemen for this ticket's category
      const smUrl = ticket.category_name 
        ? `/api/servicemen?category=${encodeURIComponent(ticket.category_name)}`
        : '/api/servicemen';
      
      fetch(smUrl, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.ok ? res.json() : [])
        .then(data => setServicemenList(Array.isArray(data) ? data : []))
        .catch(() => console.warn('Failed to fetch category servicemen'));

      // Also load legacy staff records as backup
      fetch('/api/staff', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.ok ? res.json() : [])
        .then(data => setStaffList(Array.isArray(data) ? data : []))
        .catch(() => console.warn('Failed to fetch staff roster.'));
    }
  }, [isOpen, ticket, token]);

  if (!isOpen || !ticket) return null;

  const handleServicemanChange = (e) => {
    const val = e.target.value;
    setAssignedServicemanId(val);
    // If ticket is currently OPEN, auto-advance to IN PROGRESS on serviceman triage assignment
    if (val && status === 'OPEN') {
      setStatus('IN PROGRESS');
    }
  };

  const handleQuickManualClose = () => {
    setStatus('CLOSED');
    if (!remark) {
      setRemark('Ticket closed manually by administrator.');
    }
  };

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
      assigned_serviceman_id: assignedServicemanId ? parseInt(assignedServicemanId) : null,
      assigned_staff_id: assignedStaffId ? parseInt(assignedStaffId) : (assignedServicemanId ? parseInt(assignedServicemanId) : null),
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
              <h3 className="font-bold text-sm">Triage Grievance #{ticket.ticket_id}</h3>
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
        <form onSubmit={handleUpdate} className="p-6 space-y-4 max-h-[85vh] overflow-y-auto">
          {errorMsg && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl p-3 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Quick Info Pill */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs space-y-1">
            <div className="flex justify-between text-slate-600">
              <span><strong>Category:</strong> {ticket.category_name}</span>
              <span><strong>Current Status:</strong> <span className="font-semibold text-slate-900">{ticket.status}</span></span>
            </div>
            <div className="text-slate-700">
              <strong>Description:</strong> {ticket.description}
            </div>
          </div>

          {/* Cascading Closure Notice (F11) */}
          {isClosingParentWithDuplicates && (
            <div className="bg-purple-50 border border-purple-200 text-purple-900 text-xs rounded-xl p-3 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
              <div>
                <strong>Cascading Closure Notice:</strong> Closing this parent ticket will automatically cascade status '{status}' to all <strong>{ticket.duplicate_count}</strong> linked duplicate ticket(s).
              </div>
            </div>
          )}

          {/* Serviceman Assignment (Category-matched) */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center space-x-1.5">
                <Wrench className="w-3.5 h-3.5 text-teal-600" />
                <span>Assign {ticket.category_name} Serviceman</span>
              </span>
              <span className="text-[10px] text-teal-600 bg-teal-50 px-2 py-0.5 rounded-full font-medium">Role-based</span>
            </label>
            <select
              value={assignedServicemanId}
              onChange={handleServicemanChange}
              className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="">-- Select Serviceman to Assign --</option>
              {servicemenList.map((sm) => (
                <option key={sm.id} value={sm.id}>
                  {sm.name} ({sm.category}) {sm.phone ? `• ${sm.phone}` : ''}
                </option>
              ))}
            </select>
            {servicemenList.length === 0 && (
              <p className="text-[11px] text-amber-600 mt-1">No servicemen registered specifically for '{ticket.category_name}'.</p>
            )}
          </div>

          {/* Status Selection & Quick Close */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700">
                Ticket Lifecycle Status
              </label>
              <button
                type="button"
                onClick={handleQuickManualClose}
                className="text-[11px] font-semibold text-rose-600 hover:text-rose-700 bg-rose-50 hover:bg-rose-100 px-2 py-0.5 rounded-lg transition-colors flex items-center space-x-1"
              >
                <Lock className="w-3 h-3" />
                <span>Admin Force Close</span>
              </button>
            </div>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <option value="OPEN">OPEN (Awaiting Action)</option>
              <option value="IN PROGRESS">IN PROGRESS (Serviceman Assigned / Work Underway)</option>
              <option value="PENDING CONFIRMATION">PENDING CONFIRMATION (Fix Completed, Awaiting Student)</option>
              <option value="RESOLVED">RESOLVED (Confirmed by Student)</option>
              <option value="CLOSED">CLOSED (Completed / Manually Closed)</option>
            </select>
          </div>

          {/* Mandatory Remark */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Admin Triage / Action Remark *
            </label>
            <textarea
              rows={3}
              value={remark}
              onChange={(e) => setRemark(e.target.value)}
              placeholder="State the assignment instructions, reason for manual closure, or inspection directives."
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
              <span>{loading ? 'Saving Changes...' : 'Save & Update Ticket'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}