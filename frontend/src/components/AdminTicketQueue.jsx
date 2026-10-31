import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Search, 
  Filter, 
  MapPin, 
  Calendar, 
  Clock, 
  HardHat, 
  Shield, 
  Layers, 
  CopyCheck, 
  ChevronDown, 
  ChevronUp, 
  Edit3, 
  Eye, 
  RotateCcw,
  AlertTriangle
} from 'lucide-react';
import TicketDetailModal from './TicketDetailModal';
import AdminUpdateTicketModal from './AdminUpdateTicketModal';

export default function AdminTicketQueue() {
  const { token } = useAuth();

  const [tickets, setTickets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filter & Search states
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [sortBy, setSortBy] = useState('oldest_unresolved');

  // Modal states
  const [selectedTicketId, setSelectedTicketId] = useState(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [ticketToUpdate, setTicketToUpdate] = useState(null);
  const [isUpdateOpen, setIsUpdateOpen] = useState(false);

  // Expanded duplicate children map { [parentId]: boolean }
  const [expandedParents, setExpandedParents] = useState({});

  const toggleDuplicateExpand = (id) => {
    setExpandedParents(prev => ({ ...prev, [id]: !prev[id] }));
  };

  // Load categories
  useEffect(() => {
    fetch('/api/categories')
      .then(r => r.json())
      .then(cats => setCategories(cats))
      .catch(console.error);
  }, []);

  const fetchQueue = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (searchTerm.trim()) params.append('search', searchTerm.trim());
    if (selectedCategory) params.append('category_id', selectedCategory);
    if (selectedStatus && selectedStatus !== 'ALL') params.append('status', selectedStatus);
    if (selectedLocation.trim()) params.append('location', selectedLocation.trim());
    params.append('sort', sortBy);

    fetch(`/api/tickets/admin-queue?${params.toString()}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => setTickets(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchQueue();
  }, [searchTerm, selectedCategory, selectedStatus, selectedLocation, sortBy]);

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedCategory('');
    setSelectedStatus('');
    setSelectedLocation('');
    setSortBy('oldest_unresolved');
  };

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
    <div className="space-y-6">
      
      {/* Search and Filters Bar (F9, F10) */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        
        {/* Top: Search and Quick Clear */}
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by Ticket ID (e.g. 0001), description or location..."
              className="w-full text-sm pl-9 pr-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full sm:w-auto text-xs px-3 py-2.5 rounded-xl border border-slate-300 bg-white font-medium text-slate-700"
            >
              <option value="oldest_unresolved">Sort: Oldest Unresolved First</option>
              <option value="newest">Sort: Newest First</option>
              <option value="oldest">Sort: Oldest First</option>
            </select>

            <button
              onClick={clearFilters}
              className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 px-3 py-2.5 rounded-xl font-medium transition-colors"
              title="Reset all filters"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden xs:inline">Reset</span>
            </button>
          </div>
        </div>

        {/* Filter Dropdowns Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-100">
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 bg-white"
            >
              <option value="">All Categories</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Status
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300 bg-white"
            >
              <option value="">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="IN PROGRESS">IN PROGRESS</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="CLOSED">CLOSED</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Location Filter
            </label>
            <input
              type="text"
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              placeholder="e.g. Hostel 3 or Lab"
              className="w-full text-xs px-3 py-2 rounded-lg border border-slate-300"
            />
          </div>
        </div>

      </div>

      {/* Ticket Queue List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h3 className="font-bold text-sm">Unified Ticket Queue (F9)</h3>
            <span className="text-xs bg-slate-800 text-amber-300 px-2 py-0.5 rounded-full font-semibold border border-amber-500/30">
              {tickets.length} Primary Tickets
            </span>
          </div>
          <span className="text-xs text-slate-400 hidden sm:inline">
            Duplicates grouped under parent tickets
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            Filtering and sorting queue...
          </div>
        ) : tickets.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <p className="text-sm font-semibold text-slate-700">No tickets match your filters</p>
            <p className="text-xs text-slate-400">Try modifying your search or resetting filters.</p>
            <button
              onClick={clearFilters}
              className="px-4 py-2 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {tickets.map((t) => {
              const isExpanded = !!expandedParents[t.id];
              return (
                <div key={t.id} className="p-5 hover:bg-slate-50/70 transition-colors">
                  
                  {/* Top Row: ID, Badges & Actions */}
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-2.5">
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
                      {t.is_confidential && (
                        <span className="inline-flex items-center space-x-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-300">
                          <Shield className="w-3 h-3 text-amber-600" />
                          <span>Confidential</span>
                        </span>
                      )}
                      {t.is_flagged_duplicate && (
                        <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                          Flagged Duplicate
                        </span>
                      )}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          setSelectedTicketId(t.id);
                          setIsDetailOpen(true);
                        }}
                        className="inline-flex items-center space-x-1.5 text-xs font-semibold bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 px-3 py-1.5 rounded-lg transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5 text-slate-500" />
                        <span>View</span>
                      </button>

                      <button
                        onClick={() => {
                          setTicketToUpdate(t);
                          setIsUpdateOpen(true);
                        }}
                        className="inline-flex items-center space-x-1.5 text-xs font-semibold bg-amber-500 hover:bg-amber-600 text-slate-950 px-3 py-1.5 rounded-lg shadow-sm transition-colors"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>Triage</span>
                      </button>
                    </div>
                  </div>

                  {/* Grievance Summary & Location */}
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-slate-800 line-clamp-2">
                      {t.description}
                    </p>
                    <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-slate-500 pt-1">
                      <span className="flex items-center space-x-1 font-medium text-slate-700">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        <span>{t.location}</span>
                      </span>
                      <span>Filed by: <strong>{t.student_name}</strong></span>
                      {t.assigned_staff_name && (
                        <span className="flex items-center space-x-1 text-teal-800 font-medium">
                          <HardHat className="w-3.5 h-3.5 text-teal-600" />
                          <span>Staff: {t.assigned_staff_name}</span>
                        </span>
                      )}
                      <span className="text-slate-400">
                        {new Date(t.created_at).toLocaleDateString()} at {new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>

                  {/* Grouped Duplicate Children Toggle (U5) */}
                  {t.duplicate_count > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-100">
                      <button
                        onClick={() => toggleDuplicateExpand(t.id)}
                        className="inline-flex items-center space-x-1.5 text-xs font-semibold text-purple-700 hover:text-purple-900 bg-purple-50 hover:bg-purple-100 px-3 py-1.5 rounded-lg transition-colors border border-purple-200"
                      >
                        <CopyCheck className="w-3.5 h-3.5 text-purple-600" />
                        <span>{t.duplicate_count} Linked Duplicate Ticket(s)</span>
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>

                      {isExpanded && (
                        <div className="mt-2 pl-4 border-l-2 border-purple-300 space-y-2 animate-fadeIn">
                          {t.duplicate_children.map(child => (
                            <div key={child.id} className="p-3 bg-purple-50/40 border border-purple-200 rounded-xl text-xs flex items-center justify-between">
                              <div>
                                <span className="font-mono font-bold text-slate-900">#{child.ticket_id}</span>
                                <span className="text-slate-500 ml-2">Filed by {child.student_name} ({new Date(child.created_at).toLocaleDateString()})</span>
                                <p className="text-slate-700 italic mt-0.5">"{child.description}"</p>
                              </div>
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getStatusBadge(child.status)}`}>
                                {child.status}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      <TicketDetailModal
        ticketId={selectedTicketId}
        isOpen={isDetailOpen}
        onClose={() => {
          setIsDetailOpen(false);
          setSelectedTicketId(null);
        }}
        onTicketUpdated={fetchQueue}
      />

      {/* Update/Triage Modal */}
      <AdminUpdateTicketModal
        ticket={ticketToUpdate}
        isOpen={isUpdateOpen}
        onClose={() => {
          setIsUpdateOpen(false);
          setTicketToUpdate(null);
        }}
        onUpdated={() => {
          fetchQueue();
        }}
      />

    </div>
  );
}
