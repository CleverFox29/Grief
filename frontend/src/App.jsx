import React from 'react';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col justify-between">
      <header className="bg-slate-900 text-white shadow-md">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-teal-500 flex items-center justify-center font-bold text-slate-900 text-lg">
              CG
            </div>
            <div>
              <h1 className="text-base sm:text-lg font-bold leading-tight">CGAS Portal</h1>
              <p className="text-xs text-slate-400">Campus Grievance Addressal System</p>
            </div>
          </div>
          <span className="text-xs bg-slate-800 border border-slate-700 text-slate-300 px-2.5 py-1 rounded-full">
            CS1207 OOP Lab
          </span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 flex-1 w-full">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 sm:p-8 text-center max-w-xl mx-auto">
          <div className="w-14 h-14 bg-teal-50 text-teal-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-semibold">
            ✓
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-800 mb-2">Phase 1 Initialized</h2>
          <p className="text-sm text-slate-600 mb-6">
            Object Oriented Domain Models, SQLite Database Layer, and Responsive Frontend Scaffolding ready.
          </p>
          <div className="inline-flex items-center space-x-2 text-xs font-medium text-slate-500 bg-slate-100 px-3 py-1.5 rounded-md">
            <span>FastAPI Backend + React Frontend</span>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-200 py-4 bg-white text-center text-xs text-slate-500">
        Campus Grievance Addressal System (CGAS) &bull; CS1207 OOP Lab Group II-8
      </footer>
    </div>
  );
}
