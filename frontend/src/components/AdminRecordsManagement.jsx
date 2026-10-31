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
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // Modals
  const [isAddStudentOpen, setIsAddStudentOpen] = useState(false);
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);
  const [isAddStaffOpen, setIsAddStaffOpen] = useState(false);
  const [isAddCategoryOpen, setIsAddCategoryOpen] = useState(false);

  // Form states
  const [studentForm, setStudentForm] = useState({
    user_id: '',
    name: '',
    email: '',
    phone: '',
    password: 'Student@123',
    hostel_room: ''
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

  // Loaders
  const loadStudents = () => {
    setLoading(true);
    fetch('/api/admin/students', { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.json())
      .then(data => setStudents(data))
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
      .then(data => setCategories(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (subTab === 'STUDENTS') loadStudents();
    else if (subTab === 'STAFF') {
      loadStaff();
      loadCategories();
    } else if (subTab === 'CATEGORIES') loadCategories();
  }, [subTab]);

  // Handlers
  const handleAddStudent = async (e) => {
    e.preventDefault();
    setNotification(null);
    try {
      const resp = await fetch('/api/admin/students', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(studentForm)
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Failed to add student.');

      setNotification({ type: 'success', message: `Student ${data.name} (${data.user_id}) added successfully.` });
      setIsAddStudentOpen(false);
      setStudentForm({ user_id: '', name: '', email: '', phone: '', password: 'Student@123', hostel_room: '' });
      loadStudents();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
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

  const handleAddStaff = async (e) => {
    e.preventDefault();
    setNotification(null);
    try {
      const resp = await fetch('/api/admin/staff', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: staffForm.name,
          contact: staffForm.contact,
          category_id: staffForm.category_id ? parseInt(staffForm.category_id) : null,
          notes: staffForm.notes
        })
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Failed to add staff record.');

      setNotification({ type: 'success', message: `Staff member ${data.name} added.` });
      setIsAddStaffOpen(false);
      setStaffForm({ name: '', contact: '', category_id: '', notes: '' });
      loadStaff();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    }
  };

  const handleAddCategory = async (e) => {
    e.preventDefault();
    setNotification(null);
    try {
      const resp = await fetch('/api/admin/categories', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(categoryForm)
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Failed to add category.');

      setNotification({ type: 'success', message: `Category '${data.name}' created.` });
      setIsAddCategoryOpen(false);
      setCategoryForm({ name: '', description: '' });
      loadCategories();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
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
            <span>Staff Roster (F14)</span>
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
                onClick={() => setIsAddStudentOpen(true)}
                className="inline-flex items-center space-x-1.5 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white px-3.5 py-2 rounded-xl shadow-sm transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Student</span>
              </button>
            </>
          )}

          {subTab === 'STAFF' && (
            <button
              onClick={() => setIsAddStaffOpen(true)}
              className="inline-flex items-center space-x-1.5 text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white px-3.5 py-2 rounded-xl shadow-sm transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Staff Record</span>
            </button>
          )}

          {subTab === 'CATEGORIES' && (
            <button
              onClick={() => setIsAddCategoryOpen(true)}
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

      {/* SUB-TAB 2: STAFF ROSTER */}
      {subTab === 'STAFF' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex justify-between items-center text-xs text-slate-600">
            <span>Maintenance & Admin Personnel ({staff.length})</span>
            <span className="text-[11px] text-slate-400">Held as database records (do not log in)</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Contact Number</th>
                  <th className="px-4 py-3">Trade / Category</th>
                  <th className="px-4 py-3">Notes</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                {staff.map(w => (
                  <tr key={w.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-bold text-slate-900">{w.name}</td>
                    <td className="px-4 py-3 font-mono text-slate-700">{w.contact}</td>
                    <td className="px-4 py-3">
                      <span className="bg-teal-50 text-teal-800 border border-teal-200 px-2.5 py-0.5 rounded-full font-semibold text-[10px]">
                        {w.category_name || 'General Maintenance'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500">{w.notes || '-'}</td>
                    <td className="px-4 py-3">
                      <span className="text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md font-semibold text-[10px]">
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
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
              <button onClick={() => setIsAddStudentOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAddStudent} className="p-6 space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Student Enrollment ID *</label>
                <input
                  type="text"
                  required
                  value={studentForm.user_id}
                  onChange={e => setStudentForm({ ...studentForm, user_id: e.target.value })}
                  placeholder="e.g. 25CSB0A99"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300"
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
                  onClick={() => setIsAddStudentOpen(false)}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow"
                >
                  Save Student
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

      {/* MODAL: ADD STAFF */}
      {isAddStaffOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <h3 className="font-bold text-sm">Add Maintenance Staff Member</h3>
              <button onClick={() => setIsAddStaffOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
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
                  onClick={() => setIsAddStaffOpen(false)}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white rounded-xl shadow"
                >
                  Save Staff Member
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
              <button onClick={() => setIsAddCategoryOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
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
                  onClick={() => setIsAddCategoryOpen(false)}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow"
                >
                  Create Category
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
