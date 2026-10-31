import React, { useState } from 'react';
import { X, KeyRound, ShieldAlert, CheckCircle2, ArrowRight } from 'lucide-react';

export default function ForgotPasswordModal({ isOpen, onClose, onResetSuccess }) {
  const [step, setStep] = useState(1); // 1 = Request OTP, 2 = Verify & Set Password
  const [userId, setUserId] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [otpPreview, setOtpPreview] = useState(null);

  if (!isOpen) return null;

  const handleRequestOTP = async (e) => {
    e.preventDefault();
    if (!userId.trim()) {
      setError('Please enter your User ID.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const resp = await fetch('/api/auth/request-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId.trim() })
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Failed to request OTP');

      setOtpPreview(data.otp_preview);
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      setError('New password must be at least 6 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const resp = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId.trim(),
          otp_code: otpCode.trim(),
          new_password: newPassword
        })
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Password reset failed');

      setSuccessMsg('Password successfully changed! You can now log in.');
      setTimeout(() => {
        onResetSuccess && onResetSuccess();
        onClose();
      }, 1800);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
        
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <KeyRound className="w-5 h-5 text-teal-400" />
            <h3 className="font-semibold text-base">Reset Account Password</h3>
          </div>
          <button 
            onClick={onClose} 
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-4 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl p-3 flex items-start space-x-2">
              <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="mb-4 bg-teal-50 border border-teal-200 text-teal-800 text-xs rounded-xl p-3 flex items-start space-x-2">
              <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
              <span>{successMsg}</span>
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={handleRequestOTP} className="space-y-4">
              <p className="text-xs text-slate-600">
                Enter your registered ID (Student or Admin ID). An OTP valid for <strong>5 minutes</strong> will be issued.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  User ID / Enrollment No
                </label>
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="e.g. 25CSB0A22 or admin01"
                  required
                  className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
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
                  className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow-sm transition-colors disabled:opacity-50"
                >
                  <span>{loading ? 'Sending...' : 'Send OTP'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleResetPassword} className="space-y-4">
              {otpPreview && (
                <div className="bg-amber-50 border border-amber-200 text-amber-900 rounded-xl p-3 text-xs">
                  <p className="font-semibold text-amber-800">Demo/Lab OTP Simulation:</p>
                  <p className="mt-0.5">Use OTP code: <strong className="font-mono text-sm tracking-wider bg-white px-2 py-0.5 rounded border border-amber-300">{otpPreview}</strong> (valid 5 mins)</p>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  6-Digit OTP Code
                </label>
                <input
                  type="text"
                  maxLength={6}
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                  placeholder="Enter 6-digit OTP"
                  required
                  className="w-full text-sm font-mono tracking-widest text-center px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  New Password
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  required
                  className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
                  required
                  className="w-full text-sm px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex justify-between items-center pt-2">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="text-xs font-medium text-slate-500 hover:text-slate-800"
                >
                  &larr; Back
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-5 py-2 text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow-sm transition-colors disabled:opacity-50"
                >
                  {loading ? 'Updating...' : 'Set New Password'}
                </button>
              </div>
            </form>
          )}

        </div>

      </div>
    </div>
  );
}
