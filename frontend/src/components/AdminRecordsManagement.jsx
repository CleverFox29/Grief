import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Users, 
  HardHat, 
  Layers, 
  Plus, 
  Upload, 
  Trash2, 
  CheckCircle2, 
  AlertTriangle, 
  X, 
  FileText,
  Search,
  Check,
  Download
} from 'lucide-react';

export default function AdminRecordsManagement() {
  const { token } = useAuth();
  const [subTab, setSubTab] = useState('STUDENTS'); // 'STUDENTS', 'STAFF', 'CATEGORIES'

  // Data states
  const [students, setStudents] = useState([]);
  const [staff, setStaff] = useState([]);
  const [servicemen, setServicemen] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // Modals
  const [isAddStudentOpen, setIsAddStudentOpen] = useState(false);
  const [studentModalError, setStudentModalError] = useState(null);
  const [studentSubmitting, setStudentSubmitting] = useState(false);

  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);
  const [isAddStaffOpen, setIsAddStaffOpen] = useState(false);
  const [staffModalError, setStaffModalError] = useState(null);
  const [staffSubmitting, setStaffSubmitting] = useState(false);

  const [isAddServicemanOpen, setIsAddServicemanOpen] = useState(false);
  const [smModalError, setSmModalError] = useState(null);
  const [smSubmitting, setSmSubmitting] = useState(false);

  const [isServicemanCsvModalOpen, setIsServicemanCsvModalOpen] = useState(false);
  const [isAddCategoryOpen, setIsAddCategoryOpen] = useState(false);
  const [categoryModalError, setCategoryModalError] = useState(null);
  const [categorySubmitting, setCategorySubmitting] = useState(false);

  // Helper for parsing backend error details cleanly
  const extractErrorMessage = (data, defaultMsg) => {
    if (!data) return defaultMsg;
    if (typeof data === 'string') return data;
    if (data.detail) {
      if (typeof data.detail === 'string') return data.detail;
      if (Array.isArray(data.detail)) {
        return data.detail.map(d => {
          const field = d.loc && Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : '';
          const msg = d.msg || 'Invalid input';
          return field ? `${field}: ${msg}` : msg;
        }).join('; ');
      }
      if (typeof data.detail === 'object') {
        return JSON.stringify(data.detail);
      }
    }
    if (data.message && typeof data.message === 'string') return data.message;
    return defaultMsg;
  };

  // Form states
  const [studentForm, setStudentForm] = useState({
    user_id: '',
    name: '',
    email: '',
    phone: '',
    password: 'Student@123',
    hostel_room: ''
  });

  const [servicemanForm, setServicemanForm] = useState({
    user_id: '',
    name: '',
    email: '',
    category: '',
    phone: '',
    password: 'Serviceman@123'
  });

  const [staffForm, setStaffForm] = useState({
    name: '',
    contact: '',
    category_id: '',
    notes: ''
  });

  const [categoryForm, setCategoryForm] = useState({
    name: '',
    description: ''
  });

  const [csvFile, setCsvFile] = useState(null);
  const [csvResult, setCsvResult] = useState(null);
  const [smCsvFile, setSmCsvFile] = useState(null);
  const [smCsvResult, setSmCsvResult] = useState(null);

  // Loaders
  const loadStudents = () => {
    setLoading(true);
    fetch('/api/admin/students', { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.json())
      .then(data => setStudents(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const loadServicemen = () => {
    setLoading(true);
    fetch('/api/admin/servicemen', { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : [])
      .then(data => setServicemen(Array.isArray(data) ? data : []))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const loadStaff = () => {
    setLoading(true);
    fetch('/api/staff', { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.json())
      .then(data => setStaff(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const loadCategories = () => {
    setLoading(true);
    fetch('/api/categories', { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.json())
      .then(data => {
        setCategories(data);
        if (data.length > 0 && !servicemanForm.category) {
          setServicemanForm(prev => ({ ...prev, category: data[0].name }));
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (subTab === 'STUDENTS') loadStudents();
    else if (subTab === 'STAFF') {
      loadServicemen();
      loadStaff();
      loadCategories();
    } else if (subTab === 'CATEGORIES') loadCategories();
  }, [subTab]);

  // Handlers
  const handleAddStudent = async (e) => {
    e.preventDefault();
    setStudentModalError(null);
    setStudentSubmitting(true);
    try {
      const resp = await fetch('/api/admin/students', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_id: studentForm.user_id.trim(),
          name: studentForm.name.trim(),
          email: studentForm.email.trim(),
          phone: studentForm.phone?.trim() ? studentForm.phone.trim() : null,
          password: studentForm.password || 'Student@123',
          hostel_room: studentForm.hostel_room?.trim() ? studentForm.hostel_room.trim() : null,
          enrollment_no: studentForm.user_id.trim()
        })
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        throw new Error(extractErrorMessage(data, 'Failed to add student.'));
      }

      setNotification({ type: 'success', message: `Student ${data.name} (${data.user_id}) added successfully.` });
      setIsAddStudentOpen(false);
      setStudentModalError(null);
      setStudentForm({ user_id: '', name: '', email: '', phone: '', password: 'Student@123', hostel_room: '' });
      loadStudents();
    } catch (err) {
      setStudentModalError(err.message || 'An unexpected error occurred while adding student.');
    } finally {
      setStudentSubmitting(false);
    }
  };

  const handleCsvImport = async (e) => {
    e.preventDefault();
    if (!csvFile) return;

    setLoading(true);
    setNotification(null);
    const formData = new FormData();
    formData.append('file', csvFile);

    try {
      const resp = await fetch('/api/admin/students/import-csv', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'CSV Import failed.');

      setCsvResult(data);
      loadStudents();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleAddServiceman = async (e) => {
    e.preventDefault();
    setSmModalError(null);
    setSmSubmitting(true);
    try {
      if (!servicemanForm.category || !servicemanForm.category.trim()) {
        throw new Error('Please select a valid trade / category division.');
      }
      const resp = await fetch('/api/admin/servicemen', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_id: servicemanForm.user_id.trim(),
          name: servicemanForm.name.trim(),
          email: servicemanForm.email.trim(),
          category: servicemanForm.category.trim(),
          phone: servicemanForm.phone?.trim() ? servicemanForm.phone.trim() : null,
          password: servicemanForm.password || 'Serviceman@123'
        })
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        throw new Error(extractErrorMessage(data, 'Failed to add serviceman.'));
      }

      setNotification({ type: 'success', message: `Serviceman ${data.name} (${data.category}) created successfully.` });
      setIsAddServicemanOpen(false);
      setSmModalError(null);
      setServicemanForm({ user_id: '', name: '', email: '', category: categories[0]?.name || '', phone: '', password: 'Serviceman@123' });
      loadServicemen();
      loadStaff();
    } catch (err) {
      setSmModalError(err.message || 'An unexpected error occurred while adding serviceman.');
    } finally {
      setSmSubmitting(false);
    }
  };

  const handleServicemanCsvImport = async (e) => {
    e.preventDefault();
    if (!smCsvFile) return;

    setLoading(true);
    setNotification(null);
    const formData = new FormData();
    formData.append('file', smCsvFile);

    try {
      const resp = await fetch('/api/admin/servicemen/import-csv', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Serviceman CSV import failed.');

      setSmCsvResult(data);
      loadServicemen();
      loadStaff();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleAddStaff = async (e) => {
    e.preventDefault();
    setStaffModalError(null);
    setStaffSubmitting(true);
    try {
      const resp = await fetch('/api/admin/staff', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: staffForm.name.trim(),
          contact: staffForm.contact.trim(),
          category_id: staffForm.category_id ? parseInt(staffForm.category_id) : null,
          notes: staffForm.notes?.trim() || null
        })
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(extractErrorMessage(data, 'Failed to add staff record.'));

      setNotification({ type: 'success', message: `Staff member ${data.name} added.` });
      setIsAddStaffOpen(false);
      setStaffModalError(null);
      setStaffForm({ name: '', contact: '', category_id: '', notes: '' });
      loadStaff();
    } catch (err) {
      setStaffModalError(err.message || 'Failed to add staff record.');
    } finally {
      setStaffSubmitting(false);
    }
  };

  const handleAddCategory = async (e) => {
    e.preventDefault();
    setCategoryModalError(null);
    setCategorySubmitting(true);
    try {
      const resp = await fetch('/api/admin/categories', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: categoryForm.name.trim(),
          description: categoryForm.description.trim()
        })
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(extractErrorMessage(data, 'Failed to add category.'));

      setNotification({ type: 'success', message: `Category '${data.name}' created.` });
      setIsAddCategoryOpen(false);
      setCategoryModalError(null);
      setCategoryForm({ name: '', description: '' });
      loadCategories();
    } catch (err) {
      setCategoryModalError(err.message || 'Failed to add category.');
    } finally {
      setCategorySubmitting(false);
    }
  };

  const handleDeleteCategory = async (id, name) => {
    if (!confirm(`Are you sure you want to delete category '${name}'? (Safeguard: Blocked if open tickets exist)`)) return;
    setNotification(null);
    try {
      const resp = await fetch(`/api/admin/categories/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Failed to delete category.');

      setNotification({ type: 'success', message: data.message });
      loadCategories();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Sub Navigation Bar */}
      <div className="bg-white p-2 rounded-2xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex space-x-1.5">
          <button
            onClick={() => setSubTab('STUDENTS')}
            className={`inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              subTab === 'STUDENTS'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Students (F14)</span>
          </button>

          <button
            onClick={() => setSubTab('STAFF')}
            className={`inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              subTab === 'STAFF'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <HardHat className="w-4 h-4" />
            <span>Servicemen Roster (F14)</span>
          </button>

          <button
            onClick={() => setSubTab('CATEGORIES')}
            className={`inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              subTab === 'CATEGORIES'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Categories (F14)</span>
          </button>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          {subTab === 'STUDENTS' && (
            <>
              <button
                onClick={() => {
                  setCsvResult(null);
                  setCsvFile(null);
                  setIsCsvModalOpen(true);
                }}
                className="inline-flex items-center space-x-1.5 text-xs font-semibold bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 px-3 py-2 rounded-xl shadow-sm transition-colors"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Upload CSV</span>
              </button>

              <button
                onClick={() => {
                  setStudentModalError(null);
                  setIsAddStudentOpen(true);
                }}
                className="inline-flex items-center space-x-1.5 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white px-3.5 py-2 rounded-xl shadow-sm transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Student</span>
              </button>
            </>
          )}

          {subTab === 'STAFF' && (
            <>
              <button
                onClick={() => {
                  setSmCsvResult(null);
                  setSmCsvFile(null);
                  setIsServicemanCsvModalOpen(true);
                }}
                className="inline-flex items-center space-x-1.5 text-xs font-semibold bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 px-3 py-2 rounded-xl shadow-sm transition-colors"
              >
                <Upload className="w-3.5 h-3.5 text-blue-600" />
                <span>Upload Servicemen CSV</span>
              </button>

              <button
                onClick={() => {
                  setSmModalError(null);
                  if (categories.length > 0 && !servicemanForm.category) {
                    setServicemanForm(prev => ({ ...prev, category: categories[0].name }));
                  }
                  setIsAddServicemanOpen(true);
                }}
                className="inline-flex items-center space-x-1.5 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white px-3.5 py-2 rounded-xl shadow-sm transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Serviceman</span>
              </button>
            </>
          )}

          {subTab === 'CATEGORIES' && (
            <button
              onClick={() => {
                setCategoryModalError(null);
                setIsAddCategoryOpen(true);
              }}
              className="inline-flex items-center space-x-1.5 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white px-3.5 py-2 rounded-xl shadow-sm transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Category</span>
            </button>
          )}
        </div>
      </div>

      {/* Notifications */}
      {notification && (
        <div className={`p-4 rounded-xl border text-xs flex items-start space-x-2.5 ${
          notification.type === 'error'
            ? 'bg-rose-50 border-rose-200 text-rose-800'
            : 'bg-teal-50 border-teal-200 text-teal-800'
        }`}>
          {notification.type === 'error' ? (
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
          )}
          <span>{notification.message}</span>
        </div>
      )}

      {/* SUB-TAB 1: STUDENTS */}
      {subTab === 'STUDENTS' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex justify-between items-center text-xs text-slate-600">
            <span>Enrolled Students ({students.length})</span>
            <span className="text-[11px] text-slate-400">Unique Enrollment ID enforced</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Student ID</th>
                  <th className="px-4 py-3">Full Name</th>
                  <th className="px-4 py-3">Campus Email</th>
                  <th className="px-4 py-3">Hostel Room</th>
                  <th className="px-4 py-3">Registered Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {students.map(s => (
                  <tr key={s.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-mono font-bold">{s.user_id}</td>
                    <td className="px-4 py-3 font-semibold">{s.name}</td>
                    <td className="px-4 py-3 text-slate-600">{s.email}</td>
                    <td className="px-4 py-3">{s.hostel_room || 'N/A'}</td>
                    <td className="px-4 py-3 text-slate-400">{new Date(s.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUB-TAB 2: SERVICEMEN & STAFF ROSTER */}
      {subTab === 'STAFF' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex justify-between items-center text-xs text-slate-600">
            <span>Maintenance & Servicemen Personnel ({servicemen.length})</span>
            <span className="text-[11px] text-teal-700 font-semibold">Active accounts with triage & resolution permissions</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Serviceman</th>
                  <th className="px-4 py-3">Trade / Category</th>
                  <th className="px-4 py-3">Contact</th>
                  <th className="px-4 py-3">Campus Email</th>
                  <th className="px-4 py-3">Active Assigned</th>
                  <th className="px-4 py-3">Account Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {servicemen.map(sm => (
                  <tr key={sm.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <div className="font-bold text-slate-900">{sm.name}</div>
                      <div className="font-mono text-[11px] text-slate-400">ID: {sm.user_id}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="bg-teal-50 text-teal-800 border border-teal-200 px-2.5 py-0.5 rounded-full font-semibold text-[10px]">
                        {sm.category}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-700">{sm.phone || 'N/A'}</td>
                    <td className="px-4 py-3 text-slate-600">{sm.email}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] border ${
                        sm.active_tickets_count > 0 
                          ? 'bg-amber-50 text-amber-800 border-amber-200' 
                          : 'bg-slate-50 text-slate-600 border-slate-200'
                      }`}>
                        {sm.active_tickets_count ?? 0} active
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md font-semibold text-[10px]">
                        Active Portal User
                      </span>
                    </td>
                  </tr>
                ))}
                {servicemen.length === 0 && (
                  <tr>
                    <td colSpan="6" className="text-center py-8 text-slate-400">
                      No servicemen found. Click "Add Serviceman" or "Upload Servicemen CSV" to add.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SUB-TAB 3: CATEGORIES */}
      {subTab === 'CATEGORIES' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex justify-between items-center text-xs text-slate-600">
            <span>Grievance Categories ({categories.length})</span>
            <span className="text-[11px] text-amber-700 font-semibold">Protected: Deletion blocked if active tickets exist</span>
          </div>

          <div className="divide-y divide-slate-100">
            {categories.map(cat => (
              <div key={cat.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">{cat.name}</h4>
                  <p className="text-xs text-slate-500 mt-0.5">{cat.description || 'No description provided.'}</p>
                </div>
                <button
                  onClick={() => handleDeleteCategory(cat.id, cat.name)}
                  className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                  title="Delete category (Safeguarded)"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODAL: ADD STUDENT */}
      {isAddStudentOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <h3 className="font-bold text-sm">Add New Student Record</h3>
              <button 
                onClick={() => { setIsAddStudentOpen(false); setStudentModalError(null); }} 
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {studentModalError && (
              <div className="mx-6 mt-4 p-3.5 rounded-xl border border-rose-200 bg-rose-50 text-rose-800 text-xs flex items-start space-x-2.5 animate-fadeIn">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="font-bold text-rose-900 mb-0.5">Failed to add student</div>
                  <div className="text-rose-700 font-medium leading-relaxed">{studentModalError}</div>
                </div>
              </div>
            )}

            <form onSubmit={handleAddStudent} className="p-6 space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Student Enrollment ID *</label>
                <input
                  type="text"
                  required
                  value={studentForm.user_id}
                  onChange={e => setStudentForm({ ...studentForm, user_id: e.target.value })}
                  placeholder="e.g. 25CSB0A99"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  value={studentForm.name}
                  onChange={e => setStudentForm({ ...studentForm, name: e.target.value })}
                  placeholder="Student name"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Campus Email *</label>
                <input
                  type="email"
                  required
                  value={studentForm.email}
                  onChange={e => setStudentForm({ ...studentForm, email: e.target.value })}
                  placeholder="name@campus.edu"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Hostel Room</label>
                <input
                  type="text"
                  value={studentForm.hostel_room}
                  onChange={e => setStudentForm({ ...studentForm, hostel_room: e.target.value })}
                  placeholder="e.g. Hostel 3, Room 101"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Initial Password *</label>
                <input
                  type="password"
                  required
                  value={studentForm.password}
                  onChange={e => setStudentForm({ ...studentForm, password: e.target.value })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-3">
                <button
                  type="button"
                  onClick={() => { setIsAddStudentOpen(false); setStudentModalError(null); }}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={studentSubmitting}
                  className="px-5 py-2 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow disabled:opacity-50 flex items-center space-x-1.5 transition-all"
                >
                  {studentSubmitting ? (
                    <>
                      <span className="inline-block w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Saving Student...</span>
                    </>
                  ) : (
                    <span>Save Student</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: BULK CSV IMPORT */}
      {isCsvModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <h3 className="font-bold text-sm">Bulk Upload Student Records (CSV)</h3>
              <button onClick={() => setIsCsvModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl text-xs space-y-2">
                <p className="font-semibold text-slate-800">CSV Format Specification:</p>
                <p className="text-slate-600 font-mono text-[11px] bg-white p-2 rounded border border-slate-200">
                  user_id,name,email,hostel_room<br />
                  25CSB0A22,Soham Roy,soham@campus.edu,H3-204<br />
                  25CSB0A12,Jibendra Garai,jibendra@campus.edu,H3-205
                </p>
                <p className="text-[11px] text-slate-500">
                  &bull; Duplicate student IDs will be automatically flagged and skipped.
                </p>
              </div>

              {csvResult ? (
                <div className="bg-teal-50 border border-teal-200 rounded-xl p-4 text-xs space-y-2">
                  <h4 className="font-bold text-teal-900 flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-teal-600" />
                    <span>{csvResult.message}</span>
                  </h4>
                  <p className="text-slate-700">Successfully Imported: <strong>{csvResult.successfully_imported}</strong></p>
                  <p className="text-slate-700">Duplicates Skipped: <strong>{csvResult.duplicates_rejected}</strong></p>
                  {csvResult.errors && csvResult.errors.length > 0 && (
                    <div className="mt-2 text-[11px] text-amber-800 bg-amber-50 p-2 rounded border border-amber-200 max-h-24 overflow-y-auto">
                      {csvResult.errors.map((err, i) => <p key={i}>&bull; {err}</p>)}
                    </div>
                  )}
                  <button
                    onClick={() => setIsCsvModalOpen(false)}
                    className="mt-3 w-full py-2 bg-teal-600 text-white rounded-lg font-bold"
                  >
                    Done
                  </button>
                </div>
              ) : (
                <form onSubmit={handleCsvImport} className="space-y-4">
                  <label className="border-2 border-dashed border-slate-300 hover:border-teal-500 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer bg-slate-50 hover:bg-teal-50/20 transition-colors">
                    <Upload className="w-8 h-8 text-slate-400 mb-2" />
                    <span className="text-xs font-semibold text-slate-700">
                      {csvFile ? csvFile.name : 'Select or drop CSV file'}
                    </span>
                    <span className="text-[10px] text-slate-400 mt-0.5">UTF-8 .csv files only</span>
                    <input
                      type="file"
                      accept=".csv, text/csv"
                      onChange={e => setCsvFile(e.target.files[0])}
                      className="hidden"
                    />
                  </label>

                  <div className="flex justify-end space-x-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setIsCsvModalOpen(false)}
                      className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={loading || !csvFile}
                      className="px-5 py-2 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow disabled:opacity-50"
                    >
                      {loading ? 'Processing...' : 'Upload & Process CSV'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MODAL: BULK SERVICEMEN CSV IMPORT */}
      {isServicemanCsvModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <h3 className="font-bold text-sm">Bulk Upload Servicemen Roster (CSV)</h3>
              <button onClick={() => setIsServicemanCsvModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-slate-800">CSV Columns Format:</p>
                  <span className="text-[10px] text-blue-600 font-bold bg-blue-50 px-2 py-0.5 rounded border border-blue-200">sample_servicemen.csv</span>
                </div>
                <p className="text-slate-600 font-mono text-[11px] bg-white p-2 rounded border border-slate-200 overflow-x-auto whitespace-pre">
                  user_id,name,email,category,phone,password{'\n'}
                  service_admin2,Sunita Gupta,sunita.admin@campus.edu,Administrative,+91-9876543214,Serviceman@123{'\n'}
                  service_plumber2,Suresh Jal,suresh.jal@campus.edu,Plumbing,+91-9876543211,Serviceman@123
                </p>
                <p className="text-[11px] text-slate-500">
                  &bull; Categories will match existing departments (Administrative, Plumbing, Carpentry, Electrical, Masonry, Security).
                </p>
              </div>

              {smCsvResult ? (
                <div className="bg-teal-50 border border-teal-200 rounded-xl p-4 text-xs space-y-2">
                  <h4 className="font-bold text-teal-900 flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-teal-600" />
                    <span>{smCsvResult.message}</span>
                  </h4>
                  <p className="text-slate-700">Successfully Imported: <strong>{smCsvResult.successfully_imported}</strong></p>
                  <p className="text-slate-700">Duplicates Skipped: <strong>{smCsvResult.duplicates_rejected}</strong></p>
                  {smCsvResult.errors && smCsvResult.errors.length > 0 && (
                    <div className="mt-2 text-[11px] text-amber-800 bg-amber-50 p-2 rounded border border-amber-200 max-h-24 overflow-y-auto">
                      {smCsvResult.errors.map((err, i) => <p key={i}>&bull; {err}</p>)}
                    </div>
                  )}
                  <button
                    onClick={() => setIsServicemanCsvModalOpen(false)}
                    className="mt-3 w-full py-2 bg-teal-600 text-white rounded-lg font-bold"
                  >
                    Done
                  </button>
                </div>
              ) : (
                <form onSubmit={handleServicemanCsvImport} className="space-y-4">
                  <label className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer bg-slate-50 hover:bg-blue-50/20 transition-colors">
                    <Upload className="w-8 h-8 text-slate-400 mb-2" />
                    <span className="text-xs font-semibold text-slate-700">
                      {smCsvFile ? smCsvFile.name : 'Select or drop Servicemen CSV file'}
                    </span>
                    <span className="text-[10px] text-slate-400 mt-0.5">UTF-8 .csv files only</span>
                    <input
                      type="file"
                      accept=".csv, text/csv"
                      onChange={e => setSmCsvFile(e.target.files[0])}
                      className="hidden"
                    />
                  </label>

                  <div className="flex justify-end space-x-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setIsServicemanCsvModalOpen(false)}
                      className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={loading || !smCsvFile}
                      className="px-5 py-2 text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow disabled:opacity-50"
                    >
                      {loading ? 'Processing...' : 'Upload & Process Servicemen CSV'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MODAL: ADD SERVICEMAN (MANUAL) */}
      {isAddServicemanOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <h3 className="font-bold text-sm">Add New Serviceman Account</h3>
              <button 
                onClick={() => { setIsAddServicemanOpen(false); setSmModalError(null); }} 
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {smModalError && (
              <div className="mx-6 mt-4 p-3.5 rounded-xl border border-rose-200 bg-rose-50 text-rose-800 text-xs flex items-start space-x-2.5 animate-fadeIn">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="font-bold text-rose-900 mb-0.5">Failed to add serviceman</div>
                  <div className="text-rose-700 font-medium leading-relaxed">{smModalError}</div>
                </div>
              </div>
            )}

            <form onSubmit={handleAddServiceman} className="p-6 space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Serviceman User ID *</label>
                <input
                  type="text"
                  required
                  value={servicemanForm.user_id}
                  onChange={e => setServicemanForm({ ...servicemanForm, user_id: e.target.value })}
                  placeholder="e.g. service_admin02"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  value={servicemanForm.name}
                  onChange={e => setServicemanForm({ ...servicemanForm, name: e.target.value })}
                  placeholder="e.g. Sunita Gupta"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Campus Email *</label>
                <input
                  type="email"
                  required
                  value={servicemanForm.email}
                  onChange={e => setServicemanForm({ ...servicemanForm, email: e.target.value })}
                  placeholder="e.g. sunita.admin@campus.edu"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Trade / Category Division *</label>
                <select
                  required
                  value={servicemanForm.category}
                  onChange={e => setServicemanForm({ ...servicemanForm, category: e.target.value })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white"
                >
                  <option value="">Select Division</option>
                  {categories.map(c => (
                    <option key={c.id} value={c.name}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Contact Phone</label>
                <input
                  type="text"
                  value={servicemanForm.phone}
                  onChange={e => setServicemanForm({ ...servicemanForm, phone: e.target.value })}
                  placeholder="e.g. +91-9876543214"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Initial Password</label>
                <input
                  type="password"
                  value={servicemanForm.password}
                  onChange={e => setServicemanForm({ ...servicemanForm, password: e.target.value })}
                  placeholder="Defaults to Serviceman@123"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-3">
                <button
                  type="button"
                  onClick={() => { setIsAddServicemanOpen(false); setSmModalError(null); }}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={smSubmitting}
                  className="px-5 py-2 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow disabled:opacity-50 flex items-center space-x-1.5 transition-all"
                >
                  {smSubmitting ? (
                    <>
                      <span className="inline-block w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Saving Serviceman...</span>
                    </>
                  ) : (
                    <span>Save Serviceman</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: ADD STAFF */}
      {isAddStaffOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <h3 className="font-bold text-sm">Add Maintenance Staff Member</h3>
              <button 
                onClick={() => { setIsAddStaffOpen(false); setStaffModalError(null); }} 
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {staffModalError && (
              <div className="mx-6 mt-4 p-3.5 rounded-xl border border-rose-200 bg-rose-50 text-rose-800 text-xs flex items-start space-x-2.5 animate-fadeIn">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="font-bold text-rose-900 mb-0.5">Failed to add staff member</div>
                  <div className="text-rose-700 font-medium leading-relaxed">{staffModalError}</div>
                </div>
              </div>
            )}

            <form onSubmit={handleAddStaff} className="p-6 space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  value={staffForm.name}
                  onChange={e => setStaffForm({ ...staffForm, name: e.target.value })}
                  placeholder="e.g. Ramesh Kumar"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Contact Phone *</label>
                <input
                  type="text"
                  required
                  value={staffForm.contact}
                  onChange={e => setStaffForm({ ...staffForm, contact: e.target.value })}
                  placeholder="e.g. +91-9876543201"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Primary Trade / Category</label>
                <select
                  value={staffForm.category_id}
                  onChange={e => setStaffForm({ ...staffForm, category_id: e.target.value })}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white"
                >
                  <option value="">General Maintenance (All categories)</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Shift / Assignment Notes</label>
                <input
                  type="text"
                  value={staffForm.notes}
                  onChange={e => setStaffForm({ ...staffForm, notes: e.target.value })}
                  placeholder="e.g. Hostel Block A & B plumber"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-3">
                <button
                  type="button"
                  onClick={() => { setIsAddStaffOpen(false); setStaffModalError(null); }}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={staffSubmitting}
                  className="px-5 py-2 text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white rounded-xl shadow disabled:opacity-50 flex items-center space-x-1.5 transition-all"
                >
                  {staffSubmitting ? (
                    <>
                      <span className="inline-block w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Saving Staff...</span>
                    </>
                  ) : (
                    <span>Save Staff Member</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: ADD CATEGORY */}
      {isAddCategoryOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <h3 className="font-bold text-sm">Add Grievance Category</h3>
              <button 
                onClick={() => { setIsAddCategoryOpen(false); setCategoryModalError(null); }} 
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {categoryModalError && (
              <div className="mx-6 mt-4 p-3.5 rounded-xl border border-rose-200 bg-rose-50 text-rose-800 text-xs flex items-start space-x-2.5 animate-fadeIn">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="font-bold text-rose-900 mb-0.5">Failed to add category</div>
                  <div className="text-rose-700 font-medium leading-relaxed">{categoryModalError}</div>
                </div>
              </div>
            )}

            <form onSubmit={handleAddCategory} className="p-6 space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Category Name *</label>
                <input
                  type="text"
                  required
                  value={categoryForm.name}
                  onChange={e => setCategoryForm({ ...categoryForm, name: e.target.value })}
                  placeholder="e.g. Internet & Wi-Fi"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Description</label>
                <textarea
                  rows={3}
                  value={categoryForm.description}
                  onChange={e => setCategoryForm({ ...categoryForm, description: e.target.value })}
                  placeholder="Describe issues covered by this category..."
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-3">
                <button
                  type="button"
                  onClick={() => { setIsAddCategoryOpen(false); setCategoryModalError(null); }}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={categorySubmitting}
                  className="px-5 py-2 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow disabled:opacity-50 flex items-center space-x-1.5 transition-all"
                >
                  {categorySubmitting ? (
                    <>
                      <span className="inline-block w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Creating...</span>
                    </>
                  ) : (
                    <span>Create Category</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
