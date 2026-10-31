import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  BarChart3, 
  FileText, 
  Download, 
  Calendar, 
  ShieldCheck, 
  Clock, 
  Filter, 
  ArrowRight,
  TrendingUp,
  RefreshCw
} from 'lucide-react';

export default function AdminReports() {
  const { token } = useAuth();
  
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [report, setReport] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const fetchReportsAndLogs = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    // Fetch report summary
    fetch(`/api/admin/reports?${params.toString()}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => setReport(data))
      .catch(console.error);

    // Fetch audit logs
    fetch('/api/admin/audit-logs?limit=50', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => setAuditLogs(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchReportsAndLogs();
  }, [startDate, endDate]);

  const handleExportCSV = async () => {
    setExporting(true);
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    try {
      const resp = await fetch(`/api/admin/reports/export?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cgas_summary_report_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed', err);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-8">
      
      {/* Date Range Picker & Export Bar (F15, U9) */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h3 className="font-bold text-sm text-slate-800 flex items-center space-x-1.5">
            <BarChart3 className="w-4 h-4 text-teal-600" />
            <span>Grievance Metrics & Reports (U9)</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">Filter category counts and export reports</p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl text-xs">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="date"
              value={startDate}
              onChange={e => setStartDate(e.target.value)}
              className="bg-transparent focus:outline-none text-slate-700 font-medium"
            />
            <span className="text-slate-400">to</span>
            <input
              type="date"
              value={endDate}
              onChange={e => setEndDate(e.target.value)}
              className="bg-transparent focus:outline-none text-slate-700 font-medium"
            />
          </div>

          <button
            onClick={fetchReportsAndLogs}
            className="p-2 text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
            title="Refresh metrics"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleExportCSV}
            disabled={exporting}
            className="inline-flex items-center space-x-1.5 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-xl shadow-sm transition-colors disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{exporting ? 'Exporting...' : 'Export CSV (F15)'}</span>
          </button>
        </div>
      </div>

      {/* Summary Table by Category and Status */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-teal-400" />
            <h4 className="font-bold text-sm">Grievance Breakdown by Category & Status</h4>
          </div>
          <span className="text-xs text-slate-300 font-semibold">
            Total Tickets: {report?.total_tickets || 0}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-700 uppercase font-bold border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3 text-blue-700">OPEN</th>
                <th className="px-4 py-3 text-amber-700">IN PROGRESS</th>
                <th className="px-4 py-3 text-emerald-700">RESOLVED</th>
                <th className="px-4 py-3 text-slate-700">CLOSED</th>
                <th className="px-4 py-3 text-purple-700">DUPLICATE</th>
                <th className="px-4 py-3 font-extrabold text-slate-900">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-800">
              {report?.summary?.map(item => (
                <tr key={item.category_id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-bold text-slate-900">{item.category_name}</td>
                  <td className="px-4 py-3 font-semibold text-blue-700">{item.open_count}</td>
                  <td className="px-4 py-3 font-semibold text-amber-700">{item.in_progress_count}</td>
                  <td className="px-4 py-3 font-semibold text-emerald-700">{item.resolved_count}</td>
                  <td className="px-4 py-3 font-semibold text-slate-600">{item.closed_count}</td>
                  <td className="px-4 py-3 font-semibold text-purple-700">{item.duplicate_count}</td>
                  <td className="px-4 py-3 font-bold text-slate-900 bg-slate-50">{item.total_count}</td>
                </tr>
              ))}
            </tbody>
            {report && (
              <tfoot className="bg-slate-100 font-extrabold text-slate-900 border-t-2 border-slate-300">
                <tr>
                  <td className="px-4 py-3">TOTAL</td>
                  <td className="px-4 py-3 text-blue-800">{report.total_open}</td>
                  <td className="px-4 py-3 text-amber-800">{report.total_in_progress}</td>
                  <td className="px-4 py-3 text-emerald-800">{report.total_resolved}</td>
                  <td className="px-4 py-3 text-slate-800">{report.total_closed}</td>
                  <td className="px-4 py-3 text-purple-800">{report.total_duplicate}</td>
                  <td className="px-4 py-3 bg-teal-50 text-teal-900 font-black">{report.total_tickets}</td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </div>

      {/* Immutable System Audit Trail (F15, NFR 4.2) */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h4 className="font-bold text-sm">System Security & Action Audit Trail</h4>
          </div>
          <span className="text-[11px] text-slate-400">
            Immutable log (F15, NFR 4.2)
          </span>
        </div>

        <div className="overflow-x-auto max-h-96 overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-600 uppercase font-semibold border-b border-slate-200 sticky top-0">
              <tr>
                <th className="px-4 py-2.5">Timestamp</th>
                <th className="px-4 py-2.5">Action</th>
                <th className="px-4 py-2.5">Actor</th>
                <th className="px-4 py-2.5">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-800">
              {auditLogs.map(log => (
                <tr key={log.id} className="hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="bg-slate-100 text-slate-800 px-2 py-0.5 rounded font-mono text-[10px] font-bold">
                      {log.action}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 font-medium text-slate-700">
                    {log.user_name} ({log.user_role})
                  </td>
                  <td className="px-4 py-2.5 text-slate-600">
                    {log.details || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
