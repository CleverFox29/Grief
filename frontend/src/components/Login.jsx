import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, GraduationCap, Wrench, Lock, Eye, EyeOff, AlertCircle, AlertTriangle, ArrowRight } from 'lucide-react';
import ForgotPasswordModal from './ForgotPasswordModal';

export default function Login() {
  const { login, loading, sessionWarning, setSessionWarning } = useAuth();
  
  const [role, setRole] = useState('STUDENT'); // 'STUDENT', 'SERVICEMAN', or 'ADMIN'
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const [errorMsg, setErrorMsg] = useState(null);
  const [isLocked, setIsLocked] = useState(false);
  const [isForgotModalOpen, setIsForgotModalOpen] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsLocked(false);
    setSessionWarning(null);

    const res = await login(role, userId.trim(), password);
    if (!res.success) {
      setErrorMsg(res.error);
      if (res.error.toLowerCase().includes('locked')) {
        setIsLocked(true);
      }
    }
  };

  const fillDemoAccount = (demoRole, specificUserId = null) => {
    setRole(demoRole);
    setErrorMsg(null);
    setIsLocked(false);
    if (demoRole === 'STUDENT') {
      setUserId('25CSB0A22');
      setPassword('Student@123');
    } else if (demoRole === 'SERVICEMAN') {
      setUserId(specificUserId || 'service_carpenter');
      setPassword('Serviceman@123');
    } else {
      setUserId('admin01');
      setPassword('Admin@123');
    }
  };

  return (
    <div className="min-h-[calc(100vh-140px)] flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        
        {/* Top Header */}
        <div className="bg-slate-900 text-white p-6 sm:p-8 text-center relative overflow-hidden">
          <div className="absolute -top-12 -right-12 w-32 h-32 bg-teal-500/10 rounded-full blur-2xl"></div>
          <img
            src="/logo.png"
            alt="NIT Warangal Logo"
            className="w-16 h-16 rounded-2xl object-contain bg-white p-1 mx-auto mb-3 shadow-lg border border-slate-700"
          />
          <h2 className="text-xl font-bold tracking-tight">Campus Grievance Addressal</h2>
          <p className="text-xs text-slate-400 mt-1">National Institute of Technology Warangal</p>
        </div>

        {/* Form Container */}
        <div className="p-6 sm:p-8">

          {/* Session timeout alert */}
          {sessionWarning && (
            <div className="mb-5 bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded-xl p-3 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <span>{sessionWarning}</span>
            </div>
          )}

          {/* Error / Lockout alert */}
          {errorMsg && (
            <div className={`mb-5 text-xs rounded-xl p-3 flex items-start space-x-2.5 ${
              isLocked 
                ? 'bg-rose-50 border border-rose-300 text-rose-800 font-medium' 
                : 'bg-rose-50 border border-rose-200 text-rose-700'
            }`}>
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">{isLocked ? 'Account Security Lock' : 'Login Failed'}</p>
                <p className="mt-0.5">{errorMsg}</p>
              </div>
            </div>
          )}

          {/* Role Selection Tabs (F1, U1) */}
          <div className="grid grid-cols-3 gap-1.5 p-1 bg-slate-100 rounded-xl mb-6">
            <button
              type="button"
              onClick={() => {
                setRole('STUDENT');
                setErrorMsg(null);
              }}
              className={`flex items-center justify-center space-x-1.5 py-2.5 rounded-lg text-xs font-semibold transition-all ${
                role === 'STUDENT'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              <GraduationCap className="w-4 h-4 text-teal-600" />
              <span>Student</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setRole('SERVICEMAN');
                setErrorMsg(null);
              }}
              className={`flex items-center justify-center space-x-1.5 py-2.5 rounded-lg text-xs font-semibold transition-all ${
                role === 'SERVICEMAN'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              <Wrench className="w-4 h-4 text-blue-600" />
              <span>Serviceman</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setRole('ADMIN');
                setErrorMsg(null);
              }}
              className={`flex items-center justify-center space-x-1.5 py-2.5 rounded-lg text-xs font-semibold transition-all ${
                role === 'ADMIN'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              <ShieldCheck className="w-4 h-4 text-amber-600" />
              <span>Admin</span>
            </button>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {role === 'STUDENT' 
                  ? 'Student ID / Enrollment Number' 
                  : role === 'SERVICEMAN' 
                  ? 'Serviceman Staff ID' 
                  : 'Administrator ID'}
              </label>
              <input
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder={role === 'STUDENT' ? 'e.g. 25CSB0A22' : role === 'SERVICEMAN' ? 'e.g. service_carpenter' : 'e.g. admin01'}
                required
                className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 text-slate-800 placeholder-slate-400 transition-all"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-slate-700">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => setIsForgotModalOpen(true)}
                  className="text-xs text-teal-600 hover:text-teal-700 font-medium hover:underline"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="w-full text-sm px-3.5 py-2.5 pr-10 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 text-slate-800 placeholder-slate-400 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 inline-flex items-center justify-center space-x-2 py-3 px-4 rounded-xl text-sm font-semibold text-white bg-teal-600 hover:bg-teal-700 active:bg-teal-800 transition-colors shadow-md disabled:opacity-50"
            >
              <span>{loading ? 'Authenticating...' : `Log In as ${role === 'STUDENT' ? 'Student' : role === 'SERVICEMAN' ? 'Serviceman' : 'Admin'}`}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Autofill Helpers */}
          <div className="mt-6 pt-5 border-t border-slate-100">
            <p className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold text-center mb-2.5">
              Lab Evaluation Quick Access
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => fillDemoAccount('STUDENT')}
                className="text-[10px] sm:text-[11px] font-medium py-1.5 px-1 sm:px-2 bg-slate-50 hover:bg-slate-100 text-slate-600 rounded-lg border border-slate-200 transition-colors text-center"
              >
                Student (Roy)
              </button>
              <button
                type="button"
                onClick={() => fillDemoAccount('SERVICEMAN', 'service_carpenter')}
                className="text-[10px] sm:text-[11px] font-medium py-1.5 px-1 sm:px-2 bg-slate-50 hover:bg-slate-100 text-slate-600 rounded-lg border border-slate-200 transition-colors text-center"
              >
                Serviceman (Manoj)
              </button>
              <button
                type="button"
                onClick={() => fillDemoAccount('ADMIN')}
                className="text-[10px] sm:text-[11px] font-medium py-1.5 px-1 sm:px-2 bg-slate-50 hover:bg-slate-100 text-slate-600 rounded-lg border border-slate-200 transition-colors text-center"
              >
                Admin (Admin01)
              </button>
            </div>
            {role === 'SERVICEMAN' && (
              <div className="mt-2.5 flex items-center justify-center space-x-2 text-[10px] text-slate-500">
                <span className="font-semibold text-slate-400">Trade:</span>
                <button
                  type="button"
                  onClick={() => fillDemoAccount('SERVICEMAN', 'service_carpenter')}
                  className="underline hover:text-blue-600 text-slate-600"
                >
                  Manoj (Carpentry)
                </button>
                <span>&bull;</span>
                <button
                  type="button"
                  onClick={() => fillDemoAccount('SERVICEMAN', 'service_admin')}
                  className="underline hover:text-blue-600 text-slate-600"
                >
                  Anita (Admin)
                </button>
                <span>&bull;</span>
                <button
                  type="button"
                  onClick={() => fillDemoAccount('SERVICEMAN', 'service_plumber')}
                  className="underline hover:text-blue-600 text-slate-600"
                >
                  Rajesh (Plumbing)
                </button>
              </div>
            )}
          </div>

        </div>

      </div>

      {/* Forgot Password Modal (F3, U2) */}
      <ForgotPasswordModal
        isOpen={isForgotModalOpen}
        onClose={() => setIsForgotModalOpen(false)}
        onResetSuccess={() => {
          setPassword('');
          setErrorMsg(null);
        }}
      />
    </div>
  );
}
