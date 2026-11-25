import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Database,
  Shield,
  Bell,
  DollarSign,
  CheckCircle2,
  RefreshCw,
  Users,
  UserPlus,
  Key,
  ShieldCheck,
  Check,
  X,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

const AVAILABLE_ROLES = ['Super Admin', 'Admin', 'Analyst', 'Viewer'];

export default function Settings() {
  const { user: currentUser, hasPermission } = useAuth();
  const [currency, setCurrency] = useState(() => {
    return localStorage.getItem('rg_setting_currency') || 'USD';
  });
  const [fiscalYearStart, setFiscalYearStart] = useState(() => {
    return localStorage.getItem('rg_setting_fiscalYearStart') || '01';
  });
  const [marginAlertThreshold, setMarginAlertThreshold] = useState(() => {
    return localStorage.getItem('rg_setting_marginAlertThreshold') || '25.0';
  });
  const [dbStatus, setDbStatus] = useState({
    status: 'Connected',
    latency: '1.2ms',
    rows: '5,200 Records',
    engine: 'FastAPI / SQLite Engine',
  });
  const [saved, setSaved] = useState(false);

  // User Management State
  const [usersList, setUsersList] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [userActionError, setUserActionError] = useState('');
  const [userActionSuccess, setUserActionSuccess] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // New User Form State
  const [newEmail, setNewEmail] = useState('');
  const [newName, setNewName] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('Analyst');
  const [isCreatingUser, setIsCreatingUser] = useState(false);

  const canManageUsers = hasPermission('manage:users') || currentUser?.role === 'Super Admin';

  const loadUsers = async () => {
    if (!canManageUsers) return;
    setLoadingUsers(true);
    try {
      const data = await api.getUsers();
      setUsersList(data);
    } catch (err) {
      console.warn('Failed to load users list:', err.message);
    } finally {
      setLoadingUsers(false);
    }
  };

  useEffect(() => {
    const t0 = performance.now();
    api
      .healthCheck()
      .then((res) => {
        const roundtrip = Math.round(performance.now() - t0);
        setDbStatus({
          status: res.status === 'healthy' ? 'Operational' : 'Degraded',
          latency: `${roundtrip}ms Latency`,
          rows: '5,200 Orders (24,079 Rows)',
          engine: 'FastAPI / SQLite Live Engine',
        });
      })
      .catch(() => {
        setDbStatus({
          status: 'Disconnected',
          latency: 'Timeout',
          rows: 'Unknown',
          engine: 'Connection Error',
        });
      });

    if (canManageUsers) {
      loadUsers();
    }
  }, [canManageUsers]);

  const handleSave = (e) => {
    e.preventDefault();
    try {
      localStorage.setItem('rg_setting_currency', currency);
      localStorage.setItem('rg_setting_fiscalYearStart', fiscalYearStart);
      localStorage.setItem('rg_setting_marginAlertThreshold', marginAlertThreshold);
    } catch (err) {
      console.warn('LocalStorage save failed:', err);
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleToggleStatus = async (user) => {
    setUserActionError('');
    setUserActionSuccess('');
    try {
      await api.updateUserStatus(user.id, !user.is_active);
      setUserActionSuccess(`User ${user.email} status updated.`);
      await loadUsers();
      setTimeout(() => setUserActionSuccess(''), 3000);
    } catch (err) {
      setUserActionError(err.message || 'Failed to update user status.');
      setTimeout(() => setUserActionError(''), 4000);
    }
  };

  const handleChangeRole = async (user, newRoleValue) => {
    setUserActionError('');
    setUserActionSuccess('');
    try {
      await api.updateUserRole(user.id, newRoleValue);
      setUserActionSuccess(`Role updated to ${newRoleValue} for ${user.email}.`);
      await loadUsers();
      setTimeout(() => setUserActionSuccess(''), 3000);
    } catch (err) {
      setUserActionError(err.message || 'Failed to update user role.');
      setTimeout(() => setUserActionError(''), 4000);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setUserActionError('');
    setIsCreatingUser(true);
    try {
      await api.createUser({
        email: newEmail.trim(),
        full_name: newName.trim(),
        password: newPassword,
        role: newRole,
      });
      setUserActionSuccess(`User ${newEmail} created successfully.`);
      setShowCreateModal(false);
      setNewEmail('');
      setNewName('');
      setNewPassword('');
      setNewRole('Analyst');
      await loadUsers();
      setTimeout(() => setUserActionSuccess(''), 3000);
    } catch (err) {
      setUserActionError(err.message || 'Failed to create user. Verify password complexity.');
    } finally {
      setIsCreatingUser(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-brand-dark">
          Platform Configuration & Parameters
        </h1>
        <p className="text-xs text-brand-gray mt-0.5">
          Manage currency display, fiscal thresholds, profit margin alert gates, and database settings.
        </p>
      </div>

      {saved && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 size={16} className="text-emerald-600" />
          <span>Platform settings updated successfully.</span>
        </div>
      )}

      {userActionSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 size={16} className="text-emerald-600" />
          <span>{userActionSuccess}</span>
        </div>
      )}

      {userActionError && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-center gap-2">
          <AlertCircle size={16} className="text-rose-600 shrink-0" />
          <span>{userActionError}</span>
        </div>
      )}

      {/* Database Diagnostic Status */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-subtle">
        <div className="flex items-center justify-between pb-3 border-b border-border mb-4">
          <div className="flex items-center gap-2">
            <Database size={18} className="text-bronze" />
            <h3 className="text-sm font-bold text-brand-dark">Database Connection & Diagnostic Status</h3>
          </div>
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
            Operational
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded-lg bg-background border border-border">
            <span className="text-brand-gray text-[10px] uppercase font-semibold">Engine / Dialect</span>
            <div className="text-brand-dark font-mono font-bold mt-1">{dbStatus.engine}</div>
          </div>
          <div className="p-3 rounded-lg bg-background border border-border">
            <span className="text-brand-gray text-[10px] uppercase font-semibold">Indexed Orders Pool</span>
            <div className="text-brand-dark font-mono font-bold mt-1">{dbStatus.rows}</div>
          </div>
          <div className="p-3 rounded-lg bg-background border border-border">
            <span className="text-brand-gray text-[10px] uppercase font-semibold">Query Latency</span>
            <div className="text-emerald-700 font-mono font-bold mt-1">{dbStatus.latency}</div>
          </div>
        </div>
      </div>

      {/* RBAC User Management (Visible to Super Admin) */}
      {canManageUsers && (
        <div className="bg-card border border-border rounded-xl p-6 shadow-subtle space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Users size={18} className="text-bronze" />
              <div>
                <h3 className="text-sm font-bold text-brand-dark">
                  Platform Users & Role-Based Access Control (RBAC)
                </h3>
                <p className="text-xs text-brand-gray mt-0.5">
                  Manage enterprise users, roles (Super Admin, Admin, Analyst, Viewer), and account states.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-dark text-white text-xs font-semibold rounded-lg hover:bg-black transition-colors cursor-pointer"
            >
              <UserPlus size={14} />
              <span>Provision User</span>
            </button>
          </div>

          {loadingUsers ? (
            <div className="p-8 text-center text-xs text-brand-gray">Loading user directory...</div>
          ) : usersList.length === 0 ? (
            <div className="p-6 text-center text-xs text-brand-gray bg-background rounded-lg border border-border">
              No additional platform users provisioned. Use the "Provision User" button to onboard analysts and reviewers.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border/80 text-[11px] text-brand-gray uppercase font-semibold">
                    <th className="py-2.5 px-3">User</th>
                    <th className="py-2.5 px-3">Assigned Role</th>
                    <th className="py-2.5 px-3">Account Status</th>
                    <th className="py-2.5 px-3">Last Active</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {usersList.map((u) => {
                    const isSelf = currentUser?.id === u.id;
                    const roleColor =
                      u.role === 'Super Admin'
                        ? 'bg-amber-100 text-amber-800 border-amber-300'
                        : u.role === 'Admin'
                        ? 'bg-purple-100 text-purple-800 border-purple-300'
                        : u.role === 'Analyst'
                        ? 'bg-blue-100 text-blue-800 border-blue-300'
                        : 'bg-emerald-100 text-emerald-800 border-emerald-300';

                    return (
                      <tr key={u.id} className="hover:bg-background/60 transition-colors">
                        <td className="py-3 px-3">
                          <div className="font-semibold text-brand-dark flex items-center gap-1.5">
                            <span>{u.full_name}</span>
                            {isSelf && (
                              <span className="text-[9px] px-1.5 py-0.2 rounded bg-bronze/10 text-bronze-dark font-mono font-medium">
                                you
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-brand-gray">{u.email}</div>
                        </td>
                        <td className="py-3 px-3">
                          <select
                            value={u.role}
                            disabled={isSelf && u.role === 'Super Admin'}
                            onChange={(e) => handleChangeRole(u, e.target.value)}
                            className={`text-[11px] font-semibold px-2 py-1 rounded border ${roleColor} focus:outline-none cursor-pointer`}
                          >
                            {AVAILABLE_ROLES.map((r) => (
                              <option key={r} value={r}>
                                {r}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="py-3 px-3">
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              u.is_active
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : 'bg-rose-50 text-rose-700 border border-rose-200'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                u.is_active ? 'bg-emerald-600' : 'bg-rose-500'
                              }`}
                            />
                            {u.is_active ? 'Active' : 'Deactivated'}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-[11px] text-brand-gray">
                          {u.last_login ? new Date(u.last_login).toLocaleString() : 'Never logged in'}
                        </td>
                        <td className="py-3 px-3 text-right">
                          <button
                            type="button"
                            disabled={isSelf}
                            onClick={() => handleToggleStatus(u)}
                            className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
                              isSelf
                                ? 'opacity-40 cursor-not-allowed text-brand-gray'
                                : u.is_active
                                ? 'text-rose-700 hover:bg-rose-50 border border-rose-200 cursor-pointer'
                                : 'text-emerald-700 hover:bg-emerald-50 border border-emerald-200 cursor-pointer'
                            }`}
                          >
                            {u.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Form Settings */}
      <form onSubmit={handleSave} className="bg-card border border-border rounded-xl p-6 shadow-subtle space-y-5">
        <div>
          <h3 className="text-sm font-bold text-brand-dark mb-1">Financial Parameters</h3>
          <p className="text-xs text-brand-gray mb-4">
            Configure financial display conventions across all analytics modules.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-medium text-brand-dark mb-1">Base Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze"
              >
                <option value="USD">USD ($) - United States Dollar</option>
                <option value="EUR">EUR (€) - Euro</option>
                <option value="GBP">GBP (£) - British Pound</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-brand-dark mb-1">Fiscal Year Starting Month</label>
              <select
                value={fiscalYearStart}
                onChange={(e) => setFiscalYearStart(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze"
              >
                <option value="01">January (Calendar Year)</option>
                <option value="04">April (Q2 Start)</option>
                <option value="10">October (Federal Fiscal)</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-brand-dark mb-1">Profit Margin Alert Floor (%)</label>
              <input
                type="number"
                step="0.5"
                value={marginAlertThreshold}
                onChange={(e) => setMarginAlertThreshold(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze font-mono"
              />
              <span className="text-[10px] text-brand-gray mt-1 block">
                Products yielding below this threshold trigger an automated thin-margin alert.
              </span>
            </div>

            <div>
              <label className="block font-medium text-brand-dark mb-1">Data Model Cache Invalidation</label>
              <select className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze">
                <option>Real-Time SQL Execution (Immediate)</option>
                <option>5-Minute Aggregate Cache</option>
              </select>
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-border flex justify-end">
          <button
            type="submit"
            className="px-5 py-2 bg-brand-dark text-white text-xs font-semibold rounded-lg hover:bg-black transition-colors"
          >
            Save Configuration
          </button>
        </div>
      </form>

      {/* Provision User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="bg-card border border-border rounded-xl shadow-elevated w-full max-w-md p-6 relative">
            <button
              onClick={() => setShowCreateModal(false)}
              className="absolute top-4 right-4 text-brand-gray hover:text-brand-dark p-1 rounded-lg"
            >
              <X size={16} />
            </button>

            <div className="flex items-center gap-2 pb-3 border-b border-border mb-4">
              <div className="w-8 h-8 rounded-lg bg-bronze/10 border border-bronze/30 flex items-center justify-center text-bronze">
                <UserPlus size={16} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-brand-dark">Provision Enterprise User</h3>
                <p className="text-[11px] text-brand-gray">Create an account with role-based access.</p>
              </div>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-medium text-brand-dark mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sarah Jenkins"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze"
                />
              </div>

              <div>
                <label className="block font-medium text-brand-dark mb-1">Corporate Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="s.jenkins@revenueguard.io"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze"
                />
              </div>

              <div>
                <label className="block font-medium text-brand-dark mb-1">Initial Password</label>
                <input
                  type="password"
                  required
                  placeholder="Minimum 8 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze"
                />
                <span className="text-[10px] text-brand-gray mt-1 block">
                  Must contain uppercase, lowercase, number, and special character.
                </span>
              </div>

              <div>
                <label className="block font-medium text-brand-dark mb-1">Assigned Role</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-brand-dark focus:outline-none focus:border-bronze"
                >
                  {AVAILABLE_ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-3 border-t border-border flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-border rounded-lg text-brand-dark hover:bg-background transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreatingUser}
                  className="px-4 py-2 bg-brand-dark text-white rounded-lg hover:bg-black font-semibold transition-colors disabled:opacity-50"
                >
                  {isCreatingUser ? 'Provisioning...' : 'Provision Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
