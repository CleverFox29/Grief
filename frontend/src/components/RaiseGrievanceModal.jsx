import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  X, 
  Upload, 
  AlertTriangle, 
  Shield, 
  CheckCircle2, 
  ArrowRight, 
  Image as ImageIcon, 
  Layers, 
  MapPin, 
  FileText,
  CopyCheck,
  Sparkles
} from 'lucide-react';

export default function RaiseGrievanceModal({ isOpen, onClose, onTicketCreated }) {
  const { token } = useAuth();
  
  // Step state: 1 = Form Details, 2 = Duplicate Warning Review, 3 = Success confirmation
  const [step, setStep] = useState(1);
  const [categories, setCategories] = useState([]);
  
  // Form fields
  const [categoryId, setCategoryId] = useState('');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [isConfidential, setIsConfidential] = useState(false);
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  
  // Duplicate check state
  const [duplicateMatches, setDuplicateMatches] = useState([]);
  const [selectedParentId, setSelectedParentId] = useState(null);
  const [createdTicket, setCreatedTicket] = useState(null);

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Fetch active categories on mount
  useEffect(() => {
    if (isOpen) {
      fetch('/api/categories')
        .then(res => res.json())
        .then(data => {
          setCategories(data);
          if (data.length > 0 && !categoryId) {
            setCategoryId(data[0].id.toString());
          }
        })
        .catch(() => setErrorMsg('Failed to load categories.'));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Client-side 5 MB check (F4, NFR 4.2)
    if (file.size > 5 * 1024 * 1024) {
      setErrorMsg('Selected photo exceeds the 5 MB maximum limit.');
      return;
    }

    // MIME type check
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      setErrorMsg('Only JPG and PNG images are allowed.');
      return;
    }

    setErrorMsg(null);
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
  };

  const removePhoto = () => {
    setPhotoFile(null);
    if (photoPreview) URL.revokeObjectURL(photoPreview);
    setPhotoPreview(null);
  };

  // Submit flow step 1: Check for duplicates before creation (F6)
  const handleProceed = async (e) => {
    e.preventDefault();
    if (!location.trim() || !description.trim()) {
      setErrorMsg('Please fill in both location and description.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    try {
      // Real-time duplicate check (NFR 4.1: < 2s)
      const resp = await fetch('/api/tickets/check-duplicates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          category_id: parseInt(categoryId),
          location: location.trim(),
          description: description.trim()
        })
      });

      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Duplicate check failed');

      if (data.has_duplicates && data.matches.length > 0) {
        setDuplicateMatches(data.matches);
        setSelectedParentId(data.matches[0].id); // Default to top match
        setStep(2); // Move to duplicate review screen (F7)
      } else {
        // No duplicate found: Proceed directly to ticket creation
        await submitTicket('CREATE', null);
      }
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Final ticket submission
  const submitTicket = async (action, parentId) => {
    setLoading(true);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append('category_id', categoryId);
    formData.append('location', location.trim());
    formData.append('description', description.trim());
    formData.append('is_confidential', isConfidential);
    formData.append('action', action);
    if (parentId) {
      formData.append('parent_ticket_id', parentId);
    }
    if (photoFile) {
      formData.append('photo', photoFile);
    }

    try {
      const resp = await fetch('/api/tickets', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Failed to submit ticket');

      setCreatedTicket(data);
      setStep(3); // Move to Success Screen
      onTicketCreated && onTicketCreated(data);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetAndClose = () => {
    setStep(1);
    setLocation('');
    setDescription('');
    setIsConfidential(false);
    removePhoto();
    setDuplicateMatches([]);
    setCreatedTicket(null);
    setErrorMsg(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl border border-slate-200 overflow-hidden max-h-[92vh] flex flex-col">
        
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-500/20 text-teal-400 flex items-center justify-center font-bold">
              +
            </div>
            <div>
              <h3 className="font-bold text-base leading-tight">Raise Campus Grievance</h3>
              <p className="text-xs text-slate-400">Step {step} of {step === 2 ? '3 (Duplicate Review)' : '3'}</p>
            </div>
          </div>
          <button 
            onClick={handleResetAndClose} 
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto flex-1">
          {errorMsg && (
            <div className="mb-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl p-3 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* STEP 1: Main Grievance Form */}
          {step === 1 && (
            <form onSubmit={handleProceed} className="space-y-5">
              
              {/* Category & Location Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center space-x-1.5">
                    <Layers className="w-3.5 h-3.5 text-teal-600" />
                    <span>Grievance Category *</span>
                  </label>
                  <select
                    value={categoryId}
                    onChange={(e) => setCategoryId(e.target.value)}
                    required
                    className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center space-x-1.5">
                    <MapPin className="w-3.5 h-3.5 text-teal-600" />
                    <span>Campus Location / Room *</span>
                  </label>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="e.g. Hostel 3, Room 204 or Block A Washroom"
                    required
                    className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                  {/* Quick suggestion tags */}
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {['Hostel 1', 'Hostel 2', 'Hostel 3', 'Library', 'Mess Hall', 'Academic Block'].map(loc => (
                      <button
                        type="button"
                        key={loc}
                        onClick={() => setLocation(loc)}
                        className="text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-600 px-2 py-0.5 rounded-md"
                      >
                        {loc}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center space-x-1.5">
                  <FileText className="w-3.5 h-3.5 text-teal-600" />
                  <span>Issue Description *</span>
                </label>
                <textarea
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the fault clearly. What is damaged or malfunctioning?"
                  required
                  className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              {/* Photo Upload & Confidential Toggle */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                {/* Photo Upload */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Photo Attachment (Optional, max 5 MB JPG/PNG)
                  </label>
                  {!photoPreview ? (
                    <label className="border-2 border-dashed border-slate-300 hover:border-teal-500 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer transition-colors bg-slate-50 hover:bg-teal-50/30">
                      <Upload className="w-6 h-6 text-slate-400 mb-1" />
                      <span className="text-xs font-medium text-slate-600">Click or tap to upload photo</span>
                      <span className="text-[10px] text-slate-400">JPG or PNG &bull; Max 5 MB</span>
                      <input
                        type="file"
                        accept="image/png, image/jpeg"
                        onChange={handlePhotoChange}
                        className="hidden"
                      />
                    </label>
                  ) : (
                    <div className="relative rounded-xl overflow-hidden border border-slate-200 max-h-36 flex items-center justify-center bg-slate-100">
                      <img src={photoPreview} alt="Preview" className="max-h-36 object-contain" />
                      <button
                        type="button"
                        onClick={removePhoto}
                        className="absolute top-2 right-2 bg-slate-900/80 hover:bg-rose-600 text-white p-1 rounded-full text-xs transition-colors"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>

                {/* Confidential Marking Box */}
                <div className="flex flex-col justify-between">
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5">
                    <label className="flex items-start space-x-2.5 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isConfidential}
                        onChange={(e) => setIsConfidential(e.target.checked)}
                        className="mt-0.5 rounded text-teal-600 focus:ring-teal-500 w-4 h-4"
                      />
                      <div>
                        <span className="text-xs font-semibold text-slate-800 flex items-center space-x-1">
                          <Shield className="w-3.5 h-3.5 text-amber-600" />
                          <span>Confidential Grievance</span>
                        </span>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Restricts visibility strictly to Administrators. Recommended for sensitive security or personal safety reports (F4).
                        </p>
                      </div>
                    </label>
                  </div>

                  <div className="text-[11px] text-slate-400 mt-2">
                    &bull; Real-time duplicate detection will compare against open campus tickets.
                  </div>
                </div>
              </div>

              {/* Submit Buttons */}
              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={handleResetAndClose}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex items-center space-x-1.5 px-6 py-2.5 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow-md transition-colors disabled:opacity-50"
                >
                  <span>{loading ? 'Analyzing...' : 'Check & Submit Ticket'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

            </form>
          )}

          {/* STEP 2: Duplicate Warning & Resolution (F6, F7) */}
          {step === 2 && (
            <div className="space-y-5 animate-fadeIn">
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-xs text-amber-900">
                <div className="flex items-start space-x-2.5">
                  <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-bold text-sm text-amber-900">Possible Duplicate Grievance Detected</h4>
                    <p className="mt-1 text-slate-700">
                      We found <strong>{duplicateMatches.length}</strong> existing open ticket(s) matching your location and description.
                      To avoid duplicated campus maintenance work, you can <strong>support</strong> the existing issue or submit as a new ticket anyway.
                    </p>
                  </div>
                </div>
              </div>

              {/* Duplicate List Selection */}
              <div className="space-y-3">
                <p className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Similar Existing Tickets:
                </p>
                {duplicateMatches.map((m) => (
                  <label
                    key={m.id}
                    className={`block p-4 rounded-xl border cursor-pointer transition-all ${
                      selectedParentId === m.id
                        ? 'border-teal-500 bg-teal-50/50 ring-2 ring-teal-500/20'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        <input
                          type="radio"
                          name="selected_parent"
                          checked={selectedParentId === m.id}
                          onChange={() => setSelectedParentId(m.id)}
                          className="mt-1 text-teal-600 focus:ring-teal-500"
                        />
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-mono text-xs font-bold text-slate-900">#{m.ticket_id}</span>
                            <span className="text-[10px] font-semibold bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                              {m.category_name}
                            </span>
                            <span className="text-[10px] font-semibold bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                              {m.status}
                            </span>
                          </div>
                          <p className="text-xs font-medium text-slate-800 mt-1 flex items-center space-x-1">
                            <MapPin className="w-3 h-3 text-slate-400" />
                            <span>{m.location}</span>
                          </p>
                          <p className="text-xs text-slate-600 mt-1 italic line-clamp-2">
                            "{m.description}"
                          </p>
                        </div>
                      </div>

                      <div className="text-right shrink-0 ml-2">
                        <span className="inline-block text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                          {m.similarity_score}% match
                        </span>
                      </div>
                    </div>
                  </label>
                ))}
              </div>

              {/* Action Buttons as per F7 */}
              <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="text-xs font-semibold text-slate-500 hover:text-slate-800"
                >
                  &larr; Edit Details
                </button>

                <div className="flex items-center space-x-2 w-full sm:w-auto">
                  {/* Option B: Submit Anyway */}
                  <button
                    type="button"
                    disabled={loading}
                    onClick={() => submitTicket('SUBMIT_ANYWAY', null)}
                    className="flex-1 sm:flex-none px-4 py-2.5 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors border border-slate-300"
                  >
                    Submit as New Anyway (Flagged)
                  </button>

                  {/* Option A: Support Existing (F7 Recommended) */}
                  <button
                    type="button"
                    disabled={loading || !selectedParentId}
                    onClick={() => submitTicket('SUPPORT', selectedParentId)}
                    className="flex-1 sm:flex-none inline-flex items-center justify-center space-x-1.5 px-5 py-2.5 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow-md transition-colors"
                  >
                    <CopyCheck className="w-4 h-4" />
                    <span>Support Existing Issue</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Submission Success Confirmation (F5, U3) */}
          {step === 3 && createdTicket && (
            <div className="text-center py-6 animate-fadeIn">
              <div className="w-16 h-16 bg-teal-50 text-teal-600 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl">
                <CheckCircle2 className="w-10 h-10 text-teal-600" />
              </div>

              <h4 className="text-xl font-bold text-slate-800 mb-1">
                Grievance Successfully Registered!
              </h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mb-6">
                Your ticket has been logged into the central campus maintenance database.
              </p>

              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 max-w-md mx-auto text-left space-y-2 mb-6">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-500">Ticket ID:</span>
                  <span className="font-mono font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200">
                    #{createdTicket.ticket_id}
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-500">Category:</span>
                  <span className="font-medium text-slate-800">{createdTicket.category_name}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-500">Status:</span>
                  <span className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                    createdTicket.status === 'DUPLICATE'
                      ? 'bg-purple-100 text-purple-800'
                      : 'bg-emerald-100 text-emerald-800'
                  }`}>
                    {createdTicket.status}
                  </span>
                </div>
                {createdTicket.is_flagged_duplicate && (
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-500">Duplicate Flag:</span>
                    <span className="text-amber-700 font-semibold">Flagged for Admin Review</span>
                  </div>
                )}
                {createdTicket.parent_ticket_id && (
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-500">Linked Parent Ticket:</span>
                    <span className="font-mono font-semibold text-slate-700">#{createdTicket.parent_ticket_id}</span>
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={handleResetAndClose}
                className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl shadow transition-colors"
              >
                Close & View My Dashboard
              </button>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
