import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  X, 
  MapPin, 
  User, 
  Calendar, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Layers, 
  HardHat, 
  Phone, 
  CopyCheck, 
  Star,
  RotateCcw,
  Send,
  MessageSquare,
  Sparkles,
  Wrench,
  Lock,
  Trash2
} from 'lucide-react';

export default function TicketDetailModal({ ticketId, isOpen, onClose, onTicketUpdated }) {
  const { token, user } = useAuth();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Feedback states
  const [selectedRating, setSelectedRating] = useState(5);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);
  const [feedbackSuccessMsg, setFeedbackSuccessMsg] = useState(null);

  // Reopen states
  const [isReopenPromptOpen, setIsReopenPromptOpen] = useState(false);
  const [reopenReason, setReopenReason] = useState('');
  const [reopenSubmitting, setReopenSubmitting] = useState(false);
  const [actionError, setActionError] = useState(null);

  // Student Confirmation states (F13 Serviceman loop)
  const [confirmRating, setConfirmRating] = useState(5);
  const [confirmFeedback, setConfirmFeedback] = useState('');
  const [isRejectPromptOpen, setIsRejectPromptOpen] = useState(false);
  const [rejectFeedback, setRejectFeedback] = useState('');
  const [confirming, setConfirming] = useState(false);

  // Admin Manual Close states (F11)
  const [isAdminCloseOpen, setIsAdminCloseOpen] = useState(false);
  const [adminCloseRemark, setAdminCloseRemark] = useState('');
  const [adminClosing, setAdminClosing] = useState(false);

  const fetchDetails = () => {
    if (!ticketId) return;
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
      .then(data => {
        setTicket(data);
        if (data.feedback) {
          setSelectedRating(data.feedback.rating);
          setFeedbackComment(data.feedback.comment || '');
        }
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (isOpen && ticketId) {
      fetchDetails();
      setIsReopenPromptOpen(false);
      setReopenReason('');
      setFeedbackSuccessMsg(null);
      setActionError(null);
    }
  }, [isOpen, ticketId, token]);

  if (!isOpen) return null;

  const handleSubmitFeedback = async (e) => {
    e.preventDefault();
    setFeedbackSubmitting(true);
    setActionError(null);
    try {
      const resp = await fetch(`/api/tickets/${ticket.id}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          rating: selectedRating,
          comment: feedbackComment.trim() || null
        })
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Failed to submit feedback.');

      setFeedbackSuccessMsg('Thank you! Your feedback has been recorded.');
      fetchDetails();
      onTicketUpdated && onTicketUpdated();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setFeedbackSubmitting(false);
    }
  };

  const handleReopenTicket = async (e) => {
    e.preventDefault();
    if (!reopenReason.trim()) {
      setActionError('Please provide a reason why this grievance remains unresolved.');
      return;
    }

    setReopenSubmitting(true);
    setActionError(null);
    try {
      const resp = await fetch(`/api/tickets/${ticket.id}/reopen`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          reason: reopenReason.trim()
        })
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Failed to reopen ticket.');

      setIsReopenPromptOpen(false);
      setReopenReason('');
      fetchDetails();
      onTicketUpdated && onTicketUpdated();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setReopenSubmitting(false);
    }
  };

  const handleAdminClose = async (e) => {
    e.preventDefault();
    setAdminClosing(true);
    setActionError(null);
    try {
      const resp = await fetch(`/api/tickets/${ticket.id}/close`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          remark: adminCloseRemark.trim() || 'Closed manually by administrator.'
        })
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Failed to close ticket.');

      setFeedbackSuccessMsg('Ticket has been manually closed by administrator.');
      setIsAdminCloseOpen(false);
      setAdminCloseRemark('');
      fetchDetails();
      onTicketUpdated && onTicketUpdated();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setAdminClosing(false);
    }
  };

  const handleStudentConfirm = async (isFixed, rating = null, feedback = null) => {
    setConfirming(true);
    setActionError(null);
    try {
      const resp = await fetch(`/api/tickets/${ticket.id}/confirm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          is_fixed: isFixed,
          rating: rating,
          feedback: feedback
        })
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Failed to update confirmation.');

      setFeedbackSuccessMsg(isFixed ? 'Thank you! You have confirmed the resolution.' : 'Ticket returned to queue. Serviceman notified that problem persists.');
      setIsRejectPromptOpen(false);
      fetchDetails();
      onTicketUpdated && onTicketUpdated();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setConfirming(false);
    }
  };

  const handleDeleteTicket = async () => {
    if (!window.confirm(`Delete ticket #${ticket.ticket_id}? This cannot be undone.`)) return;
    setActionError(null);
    try {
      const resp = await fetch(`/api/tickets/${ticket.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!resp.ok) {
        const data = await resp.json();
        throw new Error(data.detail || 'Failed to delete ticket.');
      }
      onTicketUpdated && onTicketUpdated();
      onClose();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'OPEN':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'IN PROGRESS':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'PENDING CONFIRMATION':
        return 'bg-purple-100 text-purple-800 border-purple-200';
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

  const isStudentOwner = user && ticket && user.role === 'STUDENT' &&
    Number(user.id) === Number(ticket.student_id);
  const isPendingConfirmation = ticket?.status === 'PENDING CONFIRMATION';
  const isResolved = ticket?.status === 'RESOLVED';
  const canDeleteTicket = isStudentOwner && ticket.status === 'OPEN' &&
    !ticket.assigned_staff_id && !ticket.assigned_serviceman_id && !ticket.parent_ticket_id;

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

              {canDeleteTicket && (
                <button type="button" onClick={handleDeleteTicket}
                  className="inline-flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-100">
                  <Trash2 className="h-3.5 w-3.5" /> Delete this ticket
                </button>
              )}

              {/* ACTION ERROR BANNER */}
              {actionError && (
                <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl p-3 flex items-start space-x-2">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <span>{actionError}</span>
                </div>
              )}

              {/* SUCCESS BANNER */}
              {feedbackSuccessMsg && (
                <div className="bg-teal-50 border border-teal-200 text-teal-800 text-xs rounded-xl p-3 flex items-start space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
                  <span>{feedbackSuccessMsg}</span>
                </div>
              )}

              {/* ADMIN OVERRIDE MANUAL CLOSE (F11) */}
              {user?.role === 'ADMIN' && ticket.status !== 'CLOSED' && (
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-xs text-slate-700">
                      <Lock className="w-4 h-4 text-rose-600 shrink-0" />
                      <span><strong>Admin Control:</strong> Override and close this grievance at any point.</span>
                    </div>
                    {!isAdminCloseOpen && (
                      <button
                        type="button"
                        onClick={() => setIsAdminCloseOpen(true)}
                        className="px-3 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-300 font-bold rounded-lg transition-colors text-xs"
                      >
                        Close Ticket Manually
                      </button>
                    )}
                  </div>

                  {isAdminCloseOpen && (
                    <form onSubmit={handleAdminClose} className="pt-2 border-t border-slate-200 space-y-2">
                      <input
                        type="text"
                        value={adminCloseRemark}
                        onChange={(e) => setAdminCloseRemark(e.target.value)}
                        placeholder="State why this ticket is being closed manually (mandatory)..."
                        required
                        className="w-full text-xs p-2 rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-rose-500"
                      />
                      <div className="flex justify-end space-x-2">
                        <button
                          type="button"
                          onClick={() => setIsAdminCloseOpen(false)}
                          className="px-3 py-1 text-xs text-slate-600 hover:bg-slate-200 rounded-lg"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={adminClosing}
                          className="px-3 py-1 text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white rounded-lg transition-colors disabled:opacity-50"
                        >
                          {adminClosing ? 'Closing...' : 'Confirm Manual Close'}
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              )}

              {/* STUDENT CONFIRMATION OF SERVICEMAN WORK (F13 Serviceman Workflow) */}
              {isStudentOwner && isPendingConfirmation && (
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-2xl p-5 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                    <div>
                      <h4 className="font-bold text-sm text-purple-950 flex items-center space-x-1.5">
                        <Sparkles className="w-4 h-4 text-purple-600" />
                        <span>Serviceman Has Completed Repair Work</span>
                      </h4>
                      <p className="text-xs text-purple-800 mt-1">
                        Please review the proof of work and remarks below. Does this resolve your grievance?
                      </p>
                    </div>

                    <div className="flex items-center space-x-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => setIsRejectPromptOpen(true)}
                        className="px-3 py-1.5 text-xs font-bold text-rose-700 bg-white border border-rose-200 hover:bg-rose-50 rounded-xl transition-colors shadow-sm"
                      >
                        Issue Persists
                      </button>
                    </div>
                  </div>

                  {/* Reject / Reopen Prompt */}
                  {isRejectPromptOpen && (
                    <div className="bg-white p-4 rounded-xl border border-rose-200 shadow-sm space-y-3 animate-fadeIn">
                      <p className="text-xs font-semibold text-rose-900">
                        Please explain why this issue remains unresolved:
                      </p>
                      <textarea
                        rows={2}
                        value={rejectFeedback}
                        onChange={(e) => setRejectFeedback(e.target.value)}
                        placeholder="State what is still wrong so the serviceman can re-inspect..."
                        className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-rose-500"
                      />
                      <div className="flex justify-end space-x-2">
                        <button
                          type="button"
                          onClick={() => setIsRejectPromptOpen(false)}
                          className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          disabled={confirming}
                          onClick={() => handleStudentConfirm(false, null, rejectFeedback)}
                          className="px-4 py-1.5 text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white rounded-lg shadow-sm transition-colors"
                        >
                          {confirming ? 'Submitting...' : 'Return to Queue'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Confirmation & Rating Form */}
                  <div className="pt-2 border-t border-purple-200/60 space-y-3">
                    <p className="text-xs font-bold text-purple-950">
                      Confirm Fix & Rate Service:
                    </p>
                    <div className="flex flex-wrap items-center gap-3">
                      <div className="flex items-center space-x-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button
                            type="button"
                            key={star}
                            onClick={() => setConfirmRating(star)}
                            className="p-0.5 hover:scale-110 transition-transform"
                          >
                            <Star
                              className={`w-5 h-5 ${
                                star <= confirmRating
                                  ? 'text-amber-400 fill-amber-400'
                                  : 'text-slate-300'
                              }`}
                            />
                          </button>
                        ))}
                      </div>

                      <input
                        type="text"
                        value={confirmFeedback}
                        onChange={(e) => setConfirmFeedback(e.target.value)}
                        placeholder="Optional note for serviceman..."
                        className="flex-1 min-w-[200px] text-xs px-3 py-1.5 rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                      />

                      <button
                        type="button"
                        disabled={confirming}
                        onClick={() => handleStudentConfirm(true, confirmRating, confirmFeedback)}
                        className="inline-flex items-center space-x-1.5 px-4 py-1.5 bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold rounded-lg shadow-sm transition-colors disabled:opacity-50"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{confirming ? 'Saving...' : 'Confirm Resolution'}</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* POST-RESOLUTION ACTIONS (F13, U7) */}
              {isStudentOwner && isResolved && (
                <div className="bg-gradient-to-r from-emerald-50/80 to-teal-50/80 border border-emerald-200 rounded-2xl p-5 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div>
                      <h4 className="font-bold text-sm text-emerald-950 flex items-center space-x-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span>Resolution Completed by Administration</span>
                      </h4>
                      <p className="text-xs text-emerald-800 mt-0.5">
                        Please review the work completed. You can rate the service or reopen the ticket if the problem persists.
                      </p>
                    </div>

                    {/* Reopen Button or Expiration Badge (F13) */}
                    <div>
                      {ticket.can_reopen ? (
                        <button
                          type="button"
                          onClick={() => setIsReopenPromptOpen(!isReopenPromptOpen)}
                          className="inline-flex items-center space-x-1.5 bg-white hover:bg-rose-50 text-rose-700 border border-rose-300 font-bold px-3.5 py-1.5 rounded-xl text-xs transition-colors shadow-sm"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          <span>Problem Persists? Reopen ({ticket.reopen_remaining_days}d left)</span>
                        </button>
                      ) : (
                        <span className="text-[11px] font-semibold bg-slate-100 text-slate-500 border border-slate-200 px-3 py-1 rounded-full">
                          7-Day Reopen Window Expired
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Reopen Reason Prompt */}
                  {isReopenPromptOpen && (
                    <form onSubmit={handleReopenTicket} className="bg-white p-4 rounded-xl border border-rose-200 shadow-sm space-y-3 animate-fadeIn">
                      <p className="text-xs font-semibold text-rose-900">
                        Why does the problem persist? (Ticket will return to OPEN for admin inspection)
                      </p>
                      <textarea
                        rows={2}
                        value={reopenReason}
                        onChange={(e) => setReopenReason(e.target.value)}
                        placeholder="State why the fault is still present (e.g. Tap still drips water)..."
                        required
                        className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-rose-500"
                      />
                      <div className="flex justify-end space-x-2">
                        <button
                          type="button"
                          onClick={() => setIsReopenPromptOpen(false)}
                          className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={reopenSubmitting}
                          className="px-4 py-1.5 text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white rounded-lg shadow-sm transition-colors"
                        >
                          {reopenSubmitting ? 'Reopening...' : 'Confirm Reopen Ticket'}
                        </button>
                      </div>
                    </form>
                  )}

                  {/* Rating & Feedback Form (F13) */}
                  <div className="pt-3 border-t border-emerald-200/60">
                    <h5 className="text-xs font-bold text-emerald-950 mb-2">
                      {ticket.feedback ? 'Your Submitted Feedback:' : 'Rate the Resolution Service (1 to 5 Stars):'}
                    </h5>

                    {!ticket.feedback ? (
                      <form onSubmit={handleSubmitFeedback} className="space-y-3">
                        <div className="flex items-center space-x-1.5">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <button
                              type="button"
                              key={star}
                              onClick={() => setSelectedRating(star)}
                              className="p-1 hover:scale-110 transition-transform"
                            >
                              <Star
                                className={`w-6 h-6 ${
                                  star <= selectedRating
                                    ? 'text-amber-400 fill-amber-400'
                                    : 'text-slate-300'
                                }`}
                              />
                            </button>
                          ))}
                          <span className="text-xs font-semibold text-slate-700 ml-2">
                            {selectedRating} of 5 Stars
                          </span>
                        </div>

                        <div className="flex items-center space-x-2">
                          <input
                            type="text"
                            value={feedbackComment}
                            onChange={(e) => setFeedbackComment(e.target.value)}
                            placeholder="Optional comment (e.g. Work was clean and fast)..."
                            className="flex-1 text-xs px-3.5 py-2 rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                          />
                          <button
                            type="submit"
                            disabled={feedbackSubmitting}
                            className="inline-flex items-center space-x-1 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold rounded-xl shadow-sm transition-colors"
                          >
                            <Send className="w-3.5 h-3.5" />
                            <span>{feedbackSubmitting ? 'Saving...' : 'Submit'}</span>
                          </button>
                        </div>
                      </form>
                    ) : (
                      <div className="bg-white p-3.5 rounded-xl border border-emerald-200 flex items-center justify-between">
                        <div>
                          <div className="flex items-center space-x-1">
                            {[1, 2, 3, 4, 5].map((star) => (
                              <Star
                                key={star}
                                className={`w-4 h-4 ${
                                  star <= ticket.feedback.rating
                                    ? 'text-amber-400 fill-amber-400'
                                    : 'text-slate-200'
                                }`}
                              />
                            ))}
                            <span className="text-xs font-bold text-slate-800 ml-1.5">
                              {ticket.feedback.rating}/5 Stars
                            </span>
                          </div>
                          {ticket.feedback.comment && (
                            <p className="text-xs text-slate-600 mt-1 italic">
                              "{ticket.feedback.comment}"
                            </p>
                          )}
                        </div>
                        <span className="text-[10px] text-slate-400">
                          {new Date(ticket.feedback.submitted_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

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

                  {/* Serviceman Proof of Work Verification (F11.5) */}
                  {(ticket.proof_of_work_url || ticket.serviceman_remark) && (
                    <div className="bg-purple-50/80 border border-purple-200 rounded-xl p-4 space-y-3">
                      <h4 className="text-xs font-bold text-purple-950 flex items-center space-x-1.5 uppercase tracking-wider">
                        <CheckCircle2 className="w-4 h-4 text-purple-600" />
                        <span>Serviceman Work Verification</span>
                      </h4>

                      {ticket.serviceman_remark && (
                        <div>
                          <p className="text-[11px] font-semibold text-purple-700 mb-1">Repair Remark:</p>
                          <p className="text-xs text-purple-900 bg-white p-3 rounded-lg border border-purple-100 leading-relaxed italic">
                            &ldquo;{ticket.serviceman_remark}&rdquo;
                          </p>
                        </div>
                      )}

                      {ticket.proof_of_work_url && (
                        <div className="space-y-1">
                          <p className="text-[11px] font-semibold text-purple-700">Uploaded Work Photo:</p>
                          <div className="rounded-xl overflow-hidden border border-purple-200 max-h-56 bg-white flex items-center justify-center">
                            <img
                              src={ticket.proof_of_work_url}
                              alt="Proof of Work"
                              className="max-h-56 object-contain"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Linked Duplicate Children */}
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

                  {/* Assigned Field Serviceman */}
                  {ticket.assigned_serviceman_name && (
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-2">
                      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                        Assigned Field Serviceman
                      </h4>
                      <div>
                        <p className="text-xs font-bold text-blue-800 flex items-center space-x-1.5">
                          <Wrench className="w-4 h-4 text-blue-600" />
                          <span>{ticket.assigned_serviceman_name}</span>
                        </p>
                        {ticket.assigned_serviceman_contact && (
                          <p className="text-xs text-slate-600 mt-1 flex items-center space-x-1 font-mono">
                            <Phone className="w-3 h-3 text-slate-400" />
                            <span>{ticket.assigned_serviceman_contact}</span>
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Scheduled Visit Note */}
                  {ticket.scheduling_remark && (
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 shadow-sm space-y-1.5">
                      <h4 className="text-xs font-bold text-blue-950 flex items-center space-x-1.5 uppercase tracking-wider">
                        <Clock className="w-3.5 h-3.5 text-blue-600" />
                        <span>Scheduled Field Visit</span>
                      </h4>
                      <p className="text-xs text-blue-900 font-medium italic bg-white p-2.5 rounded-lg border border-blue-100">
                        &ldquo;{ticket.scheduling_remark}&rdquo;
                      </p>
                      {ticket.scheduled_at && (
                        <p className="text-[10px] text-blue-600">
                          Visit logged on {new Date(ticket.scheduled_at).toLocaleDateString()} at {new Date(ticket.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      )}
                    </div>
                  )}
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
