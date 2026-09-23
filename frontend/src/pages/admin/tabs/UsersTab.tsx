import React, { useState, useEffect } from 'react';
import { Users, UserPlus, RefreshCw } from 'lucide-react';
import { Card } from '../../../components/common/Card';
import { Button } from '../../../components/common/Button';
import { authApi } from '../../../api/auth';
import type { User, UserRole } from '../../../types/auth';
import { useToast } from '../../../context/ToastContext';

export const UsersTab: React.FC = () => {
  const { addToast } = useToast();

  const [usersList, setUsersList] = useState<User[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [inviteForm, setInviteForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'viewer' as UserRole,
  });
  const [isSavingUser, setIsSavingUser] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setIsLoadingUsers(true);
    try {
      const response = await authApi.listUsers();
      setUsersList(response.data || []);
    } catch (error: any) {
      addToast('error', 'Unable to load users', error?.message || 'Please try again.');
    } finally {
      setIsLoadingUsers(false);
    }
  };

  const handleInviteUser = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsSavingUser(true);
    try {
      await authApi.createUser(inviteForm);
      setInviteForm({ full_name: '', email: '', password: '', role: 'viewer' });
      setIsInviteOpen(false);
      await fetchUsers();
      addToast('success', 'User created', 'The new team member can now sign in.');
    } catch (error: any) {
      addToast('error', 'Unable to create user', error?.message || 'Please check the form.');
    } finally {
      setIsSavingUser(false);
    }
  };

  const handleUserUpdate = async (user: User, changes: { role?: UserRole; is_active?: boolean }) => {
    try {
      const response = await authApi.updateUser(user.id, changes);
      setUsersList((current) => current.map((item) => item.id === user.id ? response.data : item));
      addToast('success', 'User updated', `${user.email} permissions are now active.`);
    } catch (error: any) {
      addToast('error', 'Unable to update user', error?.message || 'Please try again.');
      await fetchUsers();
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Users className="w-4 h-4" />
            </span>
            <h3 className="text-lg font-bold tracking-tight text-slate-900">
              Users & Role-Based Access Control (RBAC)
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage team members, permissions, and administrative access for Winsta AI Studio.
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => setIsInviteOpen((open) => !open)}
          leftIcon={<UserPlus className="w-3.5 h-3.5" />}
        >
          Invite Member
        </Button>
      </div>

      {isInviteOpen && (
        <Card className="p-5 border border-blue-200 bg-blue-50/40">
          <form onSubmit={handleInviteUser} className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
            <label className="text-xs font-semibold text-slate-700">
              Full name
              <input required value={inviteForm.full_name} onChange={(event) => setInviteForm({ ...inviteForm, full_name: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" />
            </label>
            <label className="text-xs font-semibold text-slate-700">
              Email
              <input required type="email" value={inviteForm.email} onChange={(event) => setInviteForm({ ...inviteForm, email: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" />
            </label>
            <label className="text-xs font-semibold text-slate-700">
              Temporary password
              <input required minLength={8} type="password" value={inviteForm.password} onChange={(event) => setInviteForm({ ...inviteForm, password: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" />
            </label>
            <div className="flex gap-2">
              <label className="text-xs font-semibold text-slate-700 flex-1">
                Role
                <select value={inviteForm.role} onChange={(event) => setInviteForm({ ...inviteForm, role: event.target.value as UserRole })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                  <option value="viewer">Viewer</option>
                  <option value="reviewer">Reviewer</option>
                  <option value="trend_manager">Trend Manager</option>
                  <option value="admin">Admin</option>
                </select>
              </label>
              <Button type="submit" variant="primary" size="sm" isLoading={isSavingUser}>Create</Button>
            </div>
          </form>
        </Card>
      )}

      {/* User Directory Table */}
      <Card className="overflow-hidden border border-slate-200 bg-white">
        <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Team Directory ({usersList.filter((user) => user.is_active).length} Active Accounts)</h4>
          <Button variant="light" size="sm" onClick={fetchUsers} isLoading={isLoadingUsers} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>Refresh</Button>
        </div>
        <div className="divide-y divide-slate-100">
          {isLoadingUsers && <div className="p-8 text-center text-sm text-slate-500">Loading users…</div>}
          {!isLoadingUsers && usersList.length === 0 && <div className="p-8 text-center text-sm text-slate-500">No users found.</div>}
          {!isLoadingUsers && usersList.map((u) => (
            <div key={u.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#0f172a] text-[#a78bfa] font-bold text-xs flex items-center justify-center">
                  {u.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-slate-900">{u.full_name}</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border bg-purple-100 text-purple-800 border-purple-200">{u.role.replace('_', ' ')}</span>
                  </div>
                  <span className="text-xs text-slate-500">{u.email}</span>
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs text-slate-500">
                <select value={u.role} onChange={(event) => handleUserUpdate(u, { role: event.target.value as UserRole })} className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs font-semibold text-slate-700">
                  <option value="viewer">Viewer</option>
                  <option value="reviewer">Reviewer</option>
                  <option value="trend_manager">Trend Manager</option>
                  <option value="admin">Admin</option>
                </select>
                <button type="button" onClick={() => handleUserUpdate(u, { is_active: !u.is_active })} className={`inline-flex items-center gap-1 font-bold ${u.is_active ? 'text-emerald-600' : 'text-slate-400'}`}>
                  <span className={`w-2 h-2 rounded-full ${u.is_active ? 'bg-emerald-500' : 'bg-slate-300'}`}></span> {u.is_active ? 'Active' : 'Inactive'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Permissions Matrix Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-5 bg-white border border-slate-200 space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-xs">A</span>
            <h4 className="font-bold text-sm text-slate-900">Admin Role</h4>
          </div>
          <p className="text-xs text-slate-500">Full platform control: Discovery runs, dynamic LLM model switches, API key management, social publishing approvals.</p>
        </Card>
        <Card className="p-5 bg-white border border-slate-200 space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs">E</span>
            <h4 className="font-bold text-sm text-slate-900">Trend Manager Role</h4>
          </div>
          <p className="text-xs text-slate-500">Content management: trigger discoveries, manage sources and scoring, and edit social media copy and schedules.</p>
        </Card>
        <Card className="p-5 bg-white border border-slate-200 space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs">R</span>
            <h4 className="font-bold text-sm text-slate-900">Reviewer / Viewer</h4>
          </div>
          <p className="text-xs text-slate-500">Reviewer can approve content; Viewer remains read-only for trends, analytics, and the social calendar.</p>
        </Card>
      </div>
    </div>
  );
};

