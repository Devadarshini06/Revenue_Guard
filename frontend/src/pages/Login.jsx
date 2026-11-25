import React, { useState } from 'react';
import { ShieldCheck, Lock, Mail, Eye, EyeOff, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    if (!email.trim() || !password) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email.trim(), password);
    } catch (err) {
      setErrorMessage(err.message || 'Invalid email or password.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickFill = (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setErrorMessage('');
  };

  return (
    <div className="min-h-screen bg-[#231F1D] flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 relative overflow-hidden select-none">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-[#C5A880]/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-[#8C6E46]/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md space-y-8 relative z-10">
        {/* Brand Header */}
        <div className="text-center">
          <div className="mx-auto w-14 h-14 rounded-2xl bg-gradient-to-br from-[#C5A880] to-[#8C6E46] flex items-center justify-center text-[#231F1D] shadow-xl mb-4 border border-[#E5E1DD]/20">
            <ShieldCheck size={32} strokeWidth={2.2} />
          </div>
          <div className="flex items-center justify-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white font-sans">
              RevenueGuard
            </h1>
            <span className="text-[10px] font-mono font-semibold uppercase px-2 py-0.5 rounded bg-[#C5A880]/20 text-[#C5A880] border border-[#C5A880]/30">
              PRO
            </span>
          </div>
          <p className="mt-2 text-xs text-[#A09891]">
            Enterprise Financial Intelligence & Revenue Integrity Platform
          </p>
        </div>

        {/* Card Form */}
        <div className="bg-[#2B2624] border border-[#3D3633] rounded-2xl p-7 shadow-2xl backdrop-blur-md">
          <div className="mb-6 pb-4 border-b border-[#3D3633]">
            <h2 className="text-sm font-semibold text-white">Sign In to RevenueGuard</h2>
            <p className="text-xs text-[#A09891] mt-0.5">
              Enter your corporate credentials to access financial dashboards.
            </p>
          </div>

          {errorMessage && (
            <div className="mb-5 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-start gap-2.5 text-rose-300 text-xs animate-shake">
              <AlertCircle size={16} className="shrink-0 mt-0.5 text-rose-400" />
              <div className="leading-relaxed">{errorMessage}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#E5E1DD] mb-1.5">
                Corporate Email Address
              </label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-2.5 text-[#A09891]" />
                <input
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@revenueguard.io"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-[#1F1B19] border border-[#3D3633] rounded-lg text-white focus:outline-none focus:border-[#C5A880] focus:ring-1 focus:ring-[#C5A880] transition-all placeholder:text-[#A09891]/60"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[#E5E1DD] mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-2.5 text-[#A09891]" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-10 py-2 text-xs bg-[#1F1B19] border border-[#3D3633] rounded-lg text-white focus:outline-none focus:border-[#C5A880] focus:ring-1 focus:ring-[#C5A880] transition-all placeholder:text-[#A09891]/60"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-[#A09891] hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 py-2.5 px-4 bg-gradient-to-r from-[#C5A880] to-[#A0825B] hover:from-[#D4B991] hover:to-[#B2936C] text-[#231F1D] text-xs font-bold rounded-lg shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-[#231F1D] border-t-transparent rounded-full animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight size={14} />
                </>
              )}
            </button>
          </form>

          {/* Demonstration Quick Fill Bar */}
          <div className="mt-6 pt-5 border-t border-[#3D3633]">
            <div className="text-[11px] font-semibold text-[#A09891] uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Quick Login Credentials</span>
              <span className="text-[10px] text-[#C5A880] lowercase">click to fill</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickFill('superadmin@revenueguard.io', 'SuperAdmin2026!')}
                className="px-2 py-1.5 rounded bg-[#1F1B19] hover:bg-[#3A3431] border border-[#3D3633] text-[11px] text-[#E5E1DD] text-center transition-colors cursor-pointer"
              >
                <div className="font-semibold text-[#C5A880]">Super Admin</div>
                <div className="text-[9px] text-[#A09891] truncate">All Modules</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('analyst@revenueguard.io', 'Analyst2026!')}
                className="px-2 py-1.5 rounded bg-[#1F1B19] hover:bg-[#3A3431] border border-[#3D3633] text-[11px] text-[#E5E1DD] text-center transition-colors cursor-pointer"
              >
                <div className="font-semibold text-blue-300">Analyst</div>
                <div className="text-[9px] text-[#A09891] truncate">Analytics & SQL</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('viewer@revenueguard.io', 'Viewer2026!')}
                className="px-2 py-1.5 rounded bg-[#1F1B19] hover:bg-[#3A3431] border border-[#3D3633] text-[11px] text-[#E5E1DD] text-center transition-colors cursor-pointer"
              >
                <div className="font-semibold text-emerald-300">Viewer</div>
                <div className="text-[9px] text-[#A09891] truncate">Read Only</div>
              </button>
            </div>
          </div>
        </div>

        {/* Security Compliance Footer */}
        <div className="text-center text-[11px] text-[#A09891]/80 space-y-1">
          <p>
            Secured by Argon2id password hashing, rotating JWT access tokens & rate limiting.
          </p>
          <p className="text-[10px] text-[#A09891]/60">
            RevenueGuard Enterprise © 2026 • Confidential Financial Intelligence
          </p>
        </div>
      </div>
    </div>
  );
}
