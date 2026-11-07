import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Wrench, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Search, 
  Filter, 
  MapPin, 
  Calendar, 
  User, 
  Camera, 
  Upload, 
  CheckCircle2, 
  X, 
  RefreshCw, 
  Eye, 
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Star,
  MessageSquare
} from 'lucide-react';
import TicketDetailModal from './TicketDetailModal';

export default function ServicemanDashboard() {
  const { user, token } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filtering & Search
  const [activeTab, setActiveTab] = useState('ALL'); // 'ALL', 'ASSIGNED', 'PENDING_CONFIRMATION', 'RESOLVED'
  const [searchQuery, setSearchQuery] = useState('');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Selected ticket for full detail modal
  const [selectedTicketId, setSelectedTicketId] = useState(null);

  // Proof of work modal state
  const [proofModalTicket, setProofModalTicket] = useState(null);
  const [proofRemark, setProofRemark] = useState('');
  const [proofPhotoFile, setProofPhotoFile] = useState(null);
  const [proofPhotoPreview, setProofPhotoPreview] = useState(null);
  const [submittingProof, setSubmittingProof] = useState(false);
  const [proofError, setProofError] = useState(null);

  // Schedule visit modal state
  const [scheduleModalTicket, setScheduleModalTicket] = useState(null);
  const [schedulingRemark, setSchedulingRemark] = useState('');
  const [submittingSchedule, setSubmittingSchedule] = useState(false);
  const [scheduleError, setScheduleError] = useState(null);

  // Success toast message
  const [toastMsg, setToastMsg] = useState(null);

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 4000);
  };

  // Fetch Serviceman tickets
  const fetchTickets = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch('/api/tickets/serviceman-queue', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.detail || 'Failed to fetch tickets.');
      }
      const data = await resp.json();
      setTickets(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [token, refreshTrigger]);

  // Claim Ticket Handler
  const handleClaimTicket = async (ticketId) => {
    try {
      const resp = await fetch(`/api/tickets/${ticketId}/claim`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || 'Failed to claim ticket.');
      }
      showToast(`Ticket #${data.ticket_id} claimed successfully! Status set to IN PROGRESS.`);
      setRefreshTrigger(prev => prev + 1);
    } catch (err) {
      alert(`Error claiming ticket: ${err.message}`);
    }
  };

  // Proof Photo Change Handler
  const handlePhotoSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setProofError('Photo size exceeds 5MB limit.');
        return;
      }
      setProofPhotoFile(file);
      setProofPhotoPreview(URL.createObjectURL(file));
      setProofError(null);
    }
  };

  // Schedule Visit Handler
  const handleScheduleVisit = async (e) => {
    e.preventDefault();
    if (!schedulingRemark.trim() || schedulingRemark.trim().length < 3) {
      setScheduleError('Please provide a scheduling note (minimum 3 characters, e.g. "I will come on Monday at 3 PM").');
      return;
    }

    setSubmittingSchedule(true);
    setScheduleError(null);

    try {
      const resp = await fetch(`/api/tickets/${scheduleModalTicket.id}/schedule`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          scheduling_remark: schedulingRemark.trim()
        })
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || 'Failed to schedule visit.');
      }

      showToast(`Visit scheduled for #${data.ticket_id}! Status is IN PROGRESS.`);
      setScheduleModalTicket(null);
      setSchedulingRemark('');
      setRefreshTrigger(prev => prev + 1);
    } catch (err) {
      setScheduleError(err.message);
    } finally {
      setSubmittingSchedule(false);
    }
  };

  // Submit Proof of Work
  const handleSubmitProof = async (e) => {
    e.preventDefault();
    if (!proofRemark.trim() || proofRemark.trim().length < 3) {
      setProofError('Please provide a descriptive remark (minimum 3 characters).');
      return;
    }

    setSubmittingProof(true);
    setProofError(null);

    try {
      const formData = new FormData();
      formData.append('remark', proofRemark.trim());
      if (proofPhotoFile) {
        formData.append('proof_file', proofPhotoFile);
      }

      const resp = await fetch(`/api/tickets/${proofModalTicket.id}/submit-proof`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || 'Failed to submit proof of work.');
      }

      showToast(`Proof of work submitted for #${data.ticket_id}! Awaiting student verification.`);
      setProofModalTicket(null);
      setProofRemark('');
      setProofPhotoFile(null);
      setProofPhotoPreview(null);
      setRefreshTrigger(prev => prev + 1);
    } catch (err) {
      setProofError(err.message);
    } finally {
      setSubmittingProof(false);
    }
  };

  // Compute metrics
  const totalAssignedTickets = tickets.length;
  const inProgressCount = tickets.filter(t => t.status === 'IN PROGRESS').length;
  const pendingConfirmation = tickets.filter(t => t.status === 'PENDING CONFIRMATION').length;
  const resolvedCount = tickets.filter(t => ['RESOLVED', 'CLOSED'].includes(t.status)).length;

  // Filtered tickets based on active tab and search
  const filteredTickets = tickets.filter(t => {
    if (activeTab === 'IN_PROGRESS') {
      if (t.status !== 'IN PROGRESS') return false;
    } else if (activeTab === 'PENDING_CONFIRMATION') {
      if (t.status !== 'PENDING CONFIRMATION') return false;
    } else if (activeTab === 'RESOLVED') {
      if (!['RESOLVED', 'CLOSED'].includes(t.status)) return false;
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchId = t.ticket_id.toLowerCase().includes(q);
      const matchLoc = t.location.toLowerCase().includes(q);
      const matchDesc = t.description.toLowerCase().includes(q);
      const matchStudent = (t.student_name || '').toLowerCase().includes(q);
      if (!matchId && !matchLoc && !matchDesc && !matchStudent) return false;
    }

    return true;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'OPEN':
        return {
          label: 'Open / Available',
          className: 'bg-blue-50 text-blue-700 border-blue-200'
        };
      case 'IN PROGRESS':
        return {
          label: 'In Progress',
          className: 'bg-amber-50 text-amber-700 border-amber-200'
        };
      case 'PENDING CONFIRMATION':
        return {
          label: 'Pending Confirmation',
          className: 'bg-purple-50 text-purple-700 border-purple-200'
        };
      case 'RESOLVED':
        return {
          label: 'Resolved',
          className: 'bg-emerald-50 text-emerald-700 border-emerald-200'
        };
      case 'CLOSED':
        return {
          label: 'Closed',
          className: 'bg-slate-100 text-slate-700 border-slate-300'
        };
      default:
        return {
          label: status,
          className: 'bg-slate-100 text-slate-700 border-slate-200'
        };
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Toast Notification */}
      {toastMsg && (
        <div className="fixed top-20 right-6 z-50 bg-slate-900 text-white text-xs sm:text-sm font-medium px-4 py-3 rounded-xl shadow-xl border border-teal-500/40 flex items-center space-x-2 animate-bounce">
          <CheckCircle2 className="w-5 h-5 text-teal-400 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Serviceman Header Banner */}
      <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-800 text-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-800 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl pointer-events-none"></div>
        
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center space-x-2.5 mb-2.5">
              <span className="inline-flex items-center space-x-1.5 text-xs font-bold uppercase tracking-wider bg-teal-400/10 text-teal-300 border border-teal-400/20 px-3 py-1 rounded-full">
                <Wrench className="w-3.5 h-3.5" />
                <span>Field Service Portal</span>
              </span>
              <span className="text-xs font-semibold text-slate-400 bg-slate-800/80 px-2.5 py-1 rounded-full border border-slate-700">
                {user?.category || 'Maintenance'} Division
              </span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Welcome back, {user?.name}
            </h2>
            <p className="text-sm text-slate-300 mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1">
              <span>Trade: <strong className="text-teal-300 font-semibold">{user?.category}</strong></span>
              <span>Staff ID: <strong className="text-slate-100 font-mono">{user?.user_id}</strong></span>
              {user?.phone && <span>Contact: <strong className="text-slate-200">{user?.phone}</strong></span>}
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setRefreshTrigger(p => p + 1)}
              className="inline-flex items-center space-x-2 bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all shadow-sm"
              title="Refresh Queue"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Queue</span>
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <Wrench className="w-6 h-6" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Assigned to You</p>
            <p className="text-2xl font-black text-slate-800 mt-0.5">{totalAssignedTickets}</p>
            <p className="text-[11px] text-slate-500">Admin assigned</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">In Progress</p>
            <p className="text-2xl font-black text-slate-800 mt-0.5">{inProgressCount}</p>
            <p className="text-[11px] text-amber-600 font-medium">Work active</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Awaiting Review</p>
            <p className="text-2xl font-black text-slate-800 mt-0.5">{pendingConfirmation}</p>
            <p className="text-[11px] text-purple-600 font-medium">Student confirmation</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Completed Fixes</p>
            <p className="text-2xl font-black text-slate-800 mt-0.5">{resolvedCount}</p>
            <p className="text-[11px] text-emerald-600 font-medium">Confirmed resolved</p>
          </div>
        </div>

      </div>

      {/* Main Ticket Queue Section */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
        
        {/* Controls Bar: Filters & Search */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-100 pb-6">
          
          {/* Status Tabs */}
          <div className="flex flex-wrap gap-1.5 p-1 bg-slate-100 rounded-xl max-w-fit">
            <button
              onClick={() => setActiveTab('ALL')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'ALL'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              All Assigned ({tickets.length})
            </button>
            <button
              onClick={() => setActiveTab('IN_PROGRESS')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'IN_PROGRESS'
                  ? 'bg-white text-amber-700 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              In Progress ({inProgressCount})
            </button>
            <button
              onClick={() => setActiveTab('PENDING_CONFIRMATION')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'PENDING_CONFIRMATION'
                  ? 'bg-white text-purple-700 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              Awaiting Student ({pendingConfirmation})
            </button>
            <button
              onClick={() => setActiveTab('RESOLVED')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'RESOLVED'
                  ? 'bg-white text-emerald-700 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              Resolved ({resolvedCount})
            </button>
          </div>

          {/* Search Input */}
          <div className="relative min-w-[260px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by ID, room, or student..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-4 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-medium"
            />
          </div>

        </div>

        {/* Loading / Error States */}
        {loading && (
          <div className="py-16 text-center text-slate-400 text-sm">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-teal-500" />
            <span>Loading category grievance tickets...</span>
          </div>
        )}

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-2xl p-4 text-sm flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Unable to load ticket queue</p>
              <p className="text-xs mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && filteredTickets.length === 0 && (
          <div className="py-16 text-center">
            <div className="w-16 h-16 rounded-2xl bg-slate-50 border border-slate-200 text-slate-400 flex items-center justify-center mx-auto mb-3">
              <Wrench className="w-8 h-8 text-slate-300" />
            </div>
            <h3 className="text-base font-bold text-slate-800">No assigned tickets found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              Issues in your trade division ({user?.category}) will appear here once an administrator assigns them to you.
            </p>
          </div>
        )}

        {/* Tickets Grid / List */}
        {!loading && !error && filteredTickets.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {filteredTickets.map(ticket => {
              const badge = getStatusBadge(ticket.status);
              const isAssignedToMe = ticket.assigned_serviceman_id === user?.id || ticket.assigned_staff_id === user?.id;
              const canClaim = ticket.status === 'OPEN' && !ticket.assigned_serviceman_id;
              const canResolve = isAssignedToMe && ticket.status === 'IN PROGRESS';
              const canStartWork = isAssignedToMe && ticket.status === 'OPEN';

              return (
                <div
                  key={ticket.id}
                  className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:border-slate-300 transition-all flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-3">
                    
                    {/* Top Row: Ticket ID, Category, Status Badge */}
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="font-mono text-xs font-extrabold text-slate-800 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                          #{ticket.ticket_id}
                        </span>
                        <h4 className="text-sm font-bold text-slate-900 mt-1 line-clamp-1">
                          {ticket.description}
                        </h4>
                      </div>
                      
                      <span className={`inline-flex items-center text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border shrink-0 ${badge.className}`}>
                        {badge.label}
                      </span>
                    </div>

                    {/* Metadata tags */}
                    <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                      <div className="flex items-center space-x-1.5 truncate">
                        <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="truncate font-medium">{ticket.location}</span>
                      </div>
                      <div className="flex items-center space-x-1.5 truncate">
                        <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="truncate">{ticket.student_name || 'Resident Student'}</span>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <Wrench className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="font-semibold text-slate-700">{ticket.category_name}</span>
                      </div>
                    </div>

                    {/* Student Photo Preview (if attached) */}
                    {ticket.photo_url && (
                      <div className="mt-2">
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Issue Photo</p>
                        <a 
                          href={ticket.photo_url} 
                          target="_blank" 
                          rel="noreferrer" 
                          className="inline-block relative group rounded-lg overflow-hidden border border-slate-200"
                        >
                          <img 
                            src={ticket.photo_url} 
                            alt="Grievance" 
                            className="w-20 h-20 object-cover group-hover:scale-105 transition-transform" 
                          />
                        </a>
                      </div>
                    )}

                    {/* Serviceman Proof of Work Snippet (if submitted) */}
                    {ticket.proof_of_work_url && (
                      <div className="bg-purple-50/70 border border-purple-100 rounded-xl p-3 text-xs space-y-2">
                        <div className="flex items-center space-x-1.5 text-purple-900 font-bold">
                          <CheckCircle2 className="w-3.5 h-3.5 text-purple-600" />
                          <span>Submitted Proof of Work</span>
                        </div>
                        {ticket.serviceman_remark && (
                          <p className="text-purple-800 italic text-[11px]">
                            &ldquo;{ticket.serviceman_remark}&rdquo;
                          </p>
                        )}
                        <a
                          href={ticket.proof_of_work_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center space-x-1 text-[11px] text-purple-700 font-semibold underline hover:text-purple-900"
                        >
                          <Camera className="w-3 h-3" />
                          <span>View Proof Image</span>
                        </a>
                      </div>
                    )}

                    {/* Scheduled Visit Notice */}
                    {ticket.scheduling_remark && (
                      <div className="bg-blue-50/80 border border-blue-200 rounded-xl p-3 text-xs space-y-1">
                        <div className="flex items-center space-x-1.5 text-blue-900 font-bold">
                          <Clock className="w-3.5 h-3.5 text-blue-600" />
                          <span>Scheduled Field Visit</span>
                        </div>
                        <p className="text-blue-800 italic text-[11px]">
                          &ldquo;{ticket.scheduling_remark}&rdquo;
                        </p>
                        {ticket.scheduled_at && (
                          <p className="text-[10px] text-blue-600">
                            Visit logged on {new Date(ticket.scheduled_at).toLocaleDateString()} at {new Date(ticket.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Student Feedback Snippet (if resolved) */}
                    {ticket.student_rating && (
                      <div className="bg-emerald-50/70 border border-emerald-100 rounded-xl p-3 text-xs space-y-1">
                        <div className="flex items-center space-x-1 text-emerald-900 font-bold">
                          <div className="flex text-amber-500">
                            {[1, 2, 3, 4, 5].map(star => (
                              <Star
                                key={star}
                                className={`w-3.5 h-3.5 ${
                                  star <= ticket.student_rating ? 'fill-amber-400 text-amber-400' : 'text-slate-300'
                                }`}
                              />
                            ))}
                          </div>
                          <span className="ml-1 text-xs">Student Rating ({ticket.student_rating}/5)</span>
                        </div>
                        {ticket.student_feedback && (
                          <p className="text-emerald-800 text-[11px] italic mt-0.5">
                            &ldquo;{ticket.student_feedback}&rdquo;
                          </p>
                        )}
                      </div>
                    )}

                  </div>

                  {/* Action Buttons Footer */}
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                    
                    <button
                      onClick={() => setSelectedTicketId(ticket.id)}
                      className="inline-flex items-center space-x-1 text-xs font-semibold text-slate-600 hover:text-slate-900 py-1.5 px-2.5 rounded-lg hover:bg-slate-100 transition-colors"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Timeline</span>
                    </button>

                    <div className="flex items-center space-x-2">
                      {/* Start Work Button for OPEN assigned tickets */}
                      {canStartWork && (
                        <button
                          onClick={() => {
                            setScheduleModalTicket(ticket);
                            setSchedulingRemark('Starting work on this issue.');
                            setScheduleError(null);
                          }}
                          className="inline-flex items-center space-x-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold py-1.5 px-3 rounded-xl transition-colors shadow-sm"
                          title="Begin work and move to IN PROGRESS"
                        >
                          <Clock className="w-3.5 h-3.5" />
                          <span>Start Work</span>
                        </button>
                      )}

                      {/* Schedule Visit Button */}
                      {ticket.status === 'IN PROGRESS' && (
                        <button
                          onClick={() => {
                            setScheduleModalTicket(ticket);
                            setSchedulingRemark(ticket.scheduling_remark || '');
                            setScheduleError(null);
                          }}
                          className="inline-flex items-center space-x-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 text-xs font-bold py-1.5 px-3 rounded-xl transition-colors shadow-sm"
                          title="Schedule inspection or service visit"
                        >
                          <Clock className="w-3.5 h-3.5 text-blue-600" />
                          <span>{ticket.scheduling_remark ? 'Reschedule' : 'Schedule Visit'}</span>
                        </button>
                      )}

                      {/* Mark as Resolved Button (only when IN PROGRESS) */}
                      {canResolve && (
                        <button
                          onClick={() => {
                            setProofModalTicket(ticket);
                            setProofRemark(ticket.serviceman_remark || '');
                            setProofError(null);
                          }}
                          className="inline-flex items-center space-x-1.5 bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold py-1.5 px-3 rounded-xl shadow-sm transition-colors"
                          title="Mark issue as resolved and submit proof for student check"
                        >
                          <CheckCircle className="w-3.5 h-3.5" />
                          <span>Mark as Resolved</span>
                        </button>
                      )}

                      {ticket.status === 'PENDING CONFIRMATION' && (
                        <span className="text-[11px] font-semibold text-purple-700 bg-purple-50 px-2 py-1 rounded-md border border-purple-200">
                          Waiting for Student Confirmation
                        </span>
                      )}
                    </div>

                  </div>

                </div>
              );
            })}
          </div>
        )}

      </div>

      {/* Proof of Work Submission Modal */}
      {proofModalTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white w-full max-w-lg rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col">
            
            {/* Modal Header */}
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Camera className="w-5 h-5 text-teal-400" />
                <h3 className="font-bold text-sm">
                  Submit Proof of Work &bull; #{proofModalTicket.ticket_id}
                </h3>
              </div>
              <button
                onClick={() => setProofModalTicket(null)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <form onSubmit={handleSubmitProof} className="p-6 space-y-5">
              
              <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 text-xs text-slate-700 space-y-1">
                <p><strong>Location:</strong> {proofModalTicket.location}</p>
                <p><strong>Description:</strong> {proofModalTicket.description}</p>
              </div>

              {proofError && (
                <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl p-3 flex items-start space-x-2">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <span>{proofError}</span>
                </div>
              )}

              {/* Remark Input */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Work Explanation / Remarks *
                </label>
                <textarea
                  value={proofRemark}
                  onChange={(e) => setProofRemark(e.target.value)}
                  rows={3}
                  required
                  placeholder="Describe the repair performed (e.g. replaced door latch with new brass fitting, tested hinge stability)..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>

              {/* Photo Upload Input */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Proof Photo (Optional, JPG / PNG up to 5MB)
                </label>
                
                <div className="border-2 border-dashed border-slate-200 rounded-2xl p-4 text-center hover:border-teal-400 transition-colors bg-slate-50">
                  {proofPhotoPreview ? (
                    <div className="relative inline-block">
                      <img
                        src={proofPhotoPreview}
                        alt="Preview"
                        className="w-32 h-32 object-cover rounded-xl border border-slate-200 mx-auto shadow-sm"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          setProofPhotoFile(null);
                          setProofPhotoPreview(null);
                        }}
                        className="absolute -top-2 -right-2 bg-rose-600 text-white rounded-full p-1 shadow-md hover:bg-rose-700"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <div>
                      <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                      <p className="text-xs text-slate-600 font-medium">Click to select photo or take picture</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">JPG or PNG (max 5 MB)</p>
                      <input
                        type="file"
                        accept="image/png, image/jpeg"
                        onChange={handlePhotoSelect}
                        className="hidden"
                        id="proof-photo-file-input"
                      />
                      <label
                        htmlFor="proof-photo-file-input"
                        className="inline-block mt-3 bg-white text-slate-700 border border-slate-300 font-semibold px-3 py-1.5 rounded-xl text-xs cursor-pointer hover:bg-slate-50 shadow-sm"
                      >
                        Browse Image
                      </label>
                    </div>
                  )}
                </div>
              </div>

              {/* Buttons */}
              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setProofModalTicket(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingProof}
                  className="inline-flex items-center space-x-1.5 bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-sm transition-all disabled:opacity-50"
                >
                  {submittingProof ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Submitting...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Submit for Confirmation</span>
                    </>
                  )}
                </button>
              </div>

            </form>

          </div>
        </div>
      )}

      {/* Schedule Visit Modal */}
      {scheduleModalTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white w-full max-w-lg rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col">
            
            {/* Modal Header */}
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Clock className="w-5 h-5 text-blue-400" />
                <h3 className="font-bold text-sm">
                  Schedule Field Visit &bull; #{scheduleModalTicket.ticket_id}
                </h3>
              </div>
              <button
                onClick={() => setScheduleModalTicket(null)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <form onSubmit={handleScheduleVisit} className="p-6 space-y-4">
              <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 text-xs text-slate-700 space-y-1">
                <p><strong>Location:</strong> {scheduleModalTicket.location}</p>
                <p><strong>Student:</strong> {scheduleModalTicket.student_name}</p>
                <p><strong>Issue:</strong> {scheduleModalTicket.description}</p>
              </div>

              {scheduleError && (
                <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl p-3 flex items-start space-x-2">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <span>{scheduleError}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Visit Schedule Remark * (Visible to Student)
                </label>
                <input
                  type="text"
                  value={schedulingRemark}
                  onChange={(e) => setSchedulingRemark(e.target.value)}
                  placeholder="e.g. I will come on Monday at 3 PM to inspect and repair"
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-medium"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Setting this will inform the resident student and mark the ticket IN PROGRESS.
                </p>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setScheduleModalTicket(null)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingSchedule}
                  className="inline-flex items-center space-x-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-sm transition-all disabled:opacity-50"
                >
                  {submittingSchedule ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Confirm Schedule</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Ticket Timeline & Detail Modal */}
      {selectedTicketId && (
        <TicketDetailModal
          ticketId={selectedTicketId}
          isOpen={!!selectedTicketId}
          onClose={() => setSelectedTicketId(null)}
          onTicketUpdated={() => setRefreshTrigger(p => p + 1)}
        />
      )}

    </div>
  );
}
