import React, { useState } from 'react';
import { X, Lock, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function ChangePasswordModal({ isOpen, onClose }) {
  const { changePassword } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match.');
      return;
    }

    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters long.');
      return;
    }

    setIsSubmitting(true);
    try {
      await changePassword(currentPassword, newPassword);
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        onClose();
      }, 1500);
    } catch (err) {
      setError(err.message || 'Failed to update password. Verify your current password.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="bg-card border border-border rounded-xl shadow-elevated w-full max-w-md p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-brand-gray hover:text-brand-dark p-1 rounded-lg"
        >
          <X size={16} />
        </button>

        <div className="flex items-center gap-2 pb-3 border-b border-border mb-4">
          <div className="w-8 h-8 rounded-lg bg-bronze/10 border border-bronze/30 flex items-center justify-center text-bronze">
            <Lock size={16} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-brand-dark">Change Account Password</h3>
            <p className="text-[11px] text-brand-gray">Update your corporate login credentials.</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-2.5 rounded-lg bg-rose-50 border border-rose-200 flex items-start gap-2 text-rose-800 text-xs">
            <AlertCircle size={15} className="shrink-0 mt-0.5 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-4 p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center gap-2 text-emerald-800 text-xs">
            <CheckCircle2 size={15} className="shrink-0 text-emerald-600" />
            <span>Password updated successfully!</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5 text-xs">
          <div>
            <label className="block font-medium text-brand-dark mb-1">Current Password</label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Enter current password"
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze"
            />
          </div>

          <div>
            <label className="block font-medium text-brand-dark mb-1">New Password</label>
            <input
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Must include upper, lower, digit, special"
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze"
            />
            <span className="text-[10px] text-brand-gray mt-1 block">
              Minimum 8 characters with at least 1 uppercase, 1 lowercase, 1 number, and 1 symbol.
            </span>
          </div>

          <div>
            <label className="block font-medium text-brand-dark mb-1">Confirm New Password</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter new password"
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze"
            />
          </div>

          <div className="pt-3 border-t border-border flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-border rounded-lg text-brand-dark hover:bg-background transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-brand-dark text-white rounded-lg hover:bg-black font-semibold transition-colors disabled:opacity-50"
            >
              {isSubmitting ? 'Updating...' : 'Update Password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

