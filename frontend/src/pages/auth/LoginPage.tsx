import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ShieldCheck, UserPlus, LogIn } from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { WinstaLogo } from '../../components/common/WinstaLogo';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { authApi } from '../../api/auth';

interface LoginPageProps {
  onSuccess: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onSuccess }) => {
  const { login, isLoading } = useAuth();
  const { addToast } = useToast();
  
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      if (mode === 'register') {
        await authApi.register({
          email,
          password,
          full_name: fullName,
        });
        addToast('success', 'Account Created', 'Signing in with your new credentials...');
      }

      await login(email, password);
      addToast('success', 'Welcome to Winsta AI', `Signed in as ${email}`);
      onSuccess();
    } catch (err: any) {
      addToast('error', mode === 'login' ? 'Sign In Failed' : 'Registration Failed', err.message || 'Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-[#f8fafc] text-slate-900 relative overflow-hidden">
      {/* Background Decorative Winsta Gradient Rings */}
      <div className="absolute top-1/4 -left-20 w-96 h-96 bg-[#8b5cf6]/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-[#6366f1]/12 rounded-full blur-3xl pointer-events-none" />

      <Card className="max-w-md w-full p-8 md:p-10 relative z-10 border border-slate-200 bg-white shadow-xl rounded-3xl">
        {/* Brand Header */}
        <div className="text-center mb-8 flex flex-col items-center">
          <div className="mb-3">
            <WinstaLogo size="lg" />
          </div>
          <h1 className="text-2xl font-serif font-extrabold text-slate-900 tracking-tight">
            Winsta AI Studio
          </h1>
          <p className="text-xs font-sans font-semibold text-slate-500 uppercase tracking-wider mt-1">
            Prompt Trends & Social Media Workspace
          </p>
        </div>

        {/* Tab Selector: Sign In vs Register */}
        <div className="flex rounded-2xl bg-slate-100 p-1 mb-6 border border-slate-200">
          <button
            type="button"
            onClick={() => setMode('login')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              mode === 'login'
                ? 'bg-[#0f172a] text-[#ffffff] shadow-xs'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            <LogIn className="w-3.5 h-3.5" />
            Sign In
          </button>
          <button
            type="button"
            onClick={() => setMode('register')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              mode === 'register'
                ? 'bg-[#0f172a] text-[#ffffff] shadow-xs'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            <UserPlus className="w-3.5 h-3.5" />
            Create Account
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <Input
              label="Full Name"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              placeholder="Your Full Name"
            />
          )}

          <div>
            <Input
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="name@winsta.ai"
            />
          </div>

          <div>
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full mt-4"
            isLoading={isLoading || isSubmitting}
            rightIcon={<ArrowRight className="w-4 h-4 text-[#a78bfa]" />}
          >
            {mode === 'login' ? 'Sign In to Studio' : 'Create Studio Account'}
          </Button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-200 text-center text-[11px] text-slate-500 flex items-center justify-center gap-2 font-medium">
          <ShieldCheck className="w-4 h-4 text-[#8b5cf6]" />
          <span>Secured by JWT Token & RBAC Authorization</span>
        </div>
      </Card>

      {/* Public Legal Links for App Reviewers & Verification */}
      <footer className="mt-6 relative z-10 flex flex-wrap items-center justify-center gap-3 text-xs text-slate-500">
        <span>© {new Date().getFullYear()} Bookmind</span>
        <span>•</span>
        <Link to="/privacy" className="hover:text-purple-600 font-semibold underline-offset-4 hover:underline">
          Privacy Policy
        </Link>
        <span>•</span>
        <Link to="/terms" className="hover:text-purple-600 font-semibold underline-offset-4 hover:underline">
          Terms of Service
        </Link>
        <span>•</span>
        <Link to="/data-deletion" className="hover:text-purple-600 font-semibold underline-offset-4 hover:underline">
          Data Deletion
        </Link>
      </footer>
    </div>
  );
};
