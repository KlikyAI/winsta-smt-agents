import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Trash2,
  ArrowLeft,
  ExternalLink,
} from 'lucide-react';
import { WinstaLogo } from '../../components/common/WinstaLogo';

export const DataDeletionPage: React.FC = () => {
  const [lang, setLang] = useState<'en' | 'id'>('en');

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 font-sans antialiased selection:bg-purple-500 selection:text-white">
      {/* Top Header */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2 group">
              <WinstaLogo size="sm" showText={true} />
            </Link>
            <span className="hidden sm:inline-block px-2 py-0.5 text-[11px] font-bold bg-rose-100 text-rose-800 rounded-full border border-rose-200">
              User Data Protection
            </span>
          </div>

          <div className="flex items-center gap-3">
            {/* Language Toggle */}
            <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
              <button
                type="button"
                onClick={() => setLang('en')}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                  lang === 'en'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                🇺🇸 English
              </button>
              <button
                type="button"
                onClick={() => setLang('id')}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                  lang === 'id'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                🇮🇩 Bahasa Indonesia
              </button>
            </div>

            <Link
              to="/privacy"
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 hidden md:inline-flex"
            >
              Privacy Policy
            </Link>

            <Link
              to="/"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-slate-900 text-white hover:bg-slate-800 text-xs font-bold shadow-xs transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to App</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <div className="flex items-center gap-2 text-xs font-bold text-rose-600 uppercase tracking-widest mb-3">
            <Trash2 className="w-4 h-4" />
            <span>Meta & Social Platform Compliance</span>
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-serif font-black text-slate-900 tracking-tight">
            {lang === 'en' ? 'User Data Deletion Instructions' : 'Petunjuk Penghapusan Data Pengguna'}
          </h1>
          <p className="mt-3 text-sm sm:text-base text-slate-600 max-w-3xl leading-relaxed">
            {lang === 'en'
              ? 'Bookmind (https://bookmind.my.id) provides simple, transparent, and direct methods for users to request deletion of all personal data, OAuth tokens, and connected social media assets.'
              : 'Bookmind (https://bookmind.my.id) menyediakan metode transparan dan langsung bagi pengguna untuk meminta penghapusan seluruh data pribadi, token OAuth, dan aset media sosial terhubung.'}
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="space-y-8">
          {/* Method 1 */}
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
            <div className="flex items-center gap-3 mb-3">
              <span className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-black text-sm">1</span>
              <h2 className="text-lg font-bold text-slate-900">
                {lang === 'en' ? 'Method 1: In-App Account Disconnection (Instant)' : 'Metode 1: Pemutusan Akun dari Dashboard (Instan)'}
              </h2>
            </div>
            <p className="text-sm text-slate-600 mb-4 leading-relaxed">
              {lang === 'en'
                ? 'You can instantly purge all stored OAuth tokens and platform associations at any time:'
                : 'Anda dapat segera menghapus seluruh token OAuth dan izin akun kapan saja:'}
            </p>
            <ol className="list-decimal pl-5 space-y-2 text-xs text-slate-700 leading-relaxed">
              <li>Log in to your account at <a href="https://bookmind.my.id" className="text-purple-600 font-semibold hover:underline">https://bookmind.my.id</a>.</li>
              <li>Navigate to <strong>Social Accounts</strong> (<code className="bg-slate-100 px-1 py-0.5 rounded text-slate-800">/social/accounts</code>).</li>
              <li>Locate the connected provider card (Meta / Facebook, Instagram, TikTok, YouTube, LinkedIn, or X).</li>
              <li>Click the red <strong>"Disconnect"</strong> button.</li>
              <li>Our backend immediately erases the encrypted access tokens, refresh tokens, and linked identifiers from our database.</li>
            </ol>
          </div>

          {/* Method 2 */}
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
            <div className="flex items-center gap-3 mb-3">
              <span className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-black text-sm">2</span>
              <h2 className="text-lg font-bold text-slate-900">
                {lang === 'en' ? 'Method 2: Email Data Deletion Request' : 'Metode 2: Permohonan Hapus Data via Email'}
              </h2>
            </div>
            <p className="text-sm text-slate-600 mb-4 leading-relaxed">
              {lang === 'en'
                ? 'If you wish to delete your entire account including past prompt packages, brief histories, and logs, submit a deletion request:'
                : 'Jika Anda ingin menghapus seluruh data akun termasuk riwayat prompt, brief, dan log secara total:'}
            </p>
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-2">
              <p><strong>Email Address:</strong> <a href="mailto:privacy@bookmind.my.id" className="text-purple-600 font-bold hover:underline">privacy@bookmind.my.id</a></p>
              <p><strong>Subject Line:</strong> Data Deletion Request - [Your Registered Email]</p>
              <p><strong>Processing Time:</strong> Requests are processed within 48 business hours, and a confirmation email with deletion ID will be sent upon completion.</p>
            </div>
          </div>

          {/* Method 3 */}
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
            <div className="flex items-center gap-3 mb-3">
              <span className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-black text-sm">3</span>
              <h2 className="text-lg font-bold text-slate-900">
                {lang === 'en' ? 'Method 3: Remove Access via Third-Party Portals' : 'Metode 3: Cabut Izin Melalui Portal Penyedia'}
              </h2>
            </div>
            <p className="text-sm text-slate-600 mb-4 leading-relaxed">
              {lang === 'en'
                ? 'You can also revoke Bookmind access permissions directly from each social network:'
                : 'Anda juga dapat mencabut izin Bookmind langsung dari masing-masing jejaring sosial:'}
            </p>
            <ul className="list-disc pl-5 space-y-2 text-xs text-slate-700">
              <li>
                <strong>Facebook / Instagram:</strong> Go to <a href="https://www.facebook.com/settings?tab=applications" target="_blank" rel="noopener noreferrer" className="text-blue-600 font-semibold hover:underline inline-flex items-center gap-0.5">Facebook Settings &gt; Apps and Websites <ExternalLink className="w-3 h-3" /></a>, find Bookmind, and click <strong>Remove</strong>.
              </li>
              <li>
                <strong>Google & YouTube:</strong> Go to <a href="https://myaccount.google.com/permissions" target="_blank" rel="noopener noreferrer" className="text-blue-600 font-semibold hover:underline inline-flex items-center gap-0.5">Google Security &gt; Third-Party Apps with Account Access <ExternalLink className="w-3 h-3" /></a>, click Bookmind, and select <strong>Remove Access</strong>.
              </li>
              <li>
                <strong>TikTok:</strong> Go to TikTok app &gt; Profile &gt; Settings & Privacy &gt; Security & Permissions &gt; Apps & Services &gt; Remove Bookmind.
              </li>
              <li>
                <strong>LinkedIn:</strong> Go to <a href="https://www.linkedin.com/psettings/permitted-services" target="_blank" rel="noopener noreferrer" className="text-blue-600 font-semibold hover:underline inline-flex items-center gap-0.5">LinkedIn Settings &gt; Data Privacy &gt; Permitted Services <ExternalLink className="w-3 h-3" /></a> and remove Bookmind.
              </li>
            </ul>
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="mt-12 pt-8 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <div>
            © {new Date().getFullYear()} Bookmind (bookmind.my.id). All rights reserved.
          </div>
          <div className="flex items-center gap-4">
            <Link to="/privacy" className="hover:text-purple-600 font-semibold">Privacy Policy</Link>
            <span>•</span>
            <Link to="/terms" className="hover:text-purple-600 font-semibold">Terms of Service</Link>
            <span>•</span>
            <Link to="/" className="hover:text-purple-600 font-semibold">Dashboard</Link>
          </div>
        </div>
      </div>
    </div>
  );
};
