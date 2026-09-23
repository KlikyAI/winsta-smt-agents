import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Lock,
  Eye,
  Trash2,
  CheckCircle2,
  ExternalLink,
  Globe,
  Mail,
  Server,
  Key,
  Share2,
  ArrowLeft,
  Calendar,
} from 'lucide-react';
import { WinstaLogo } from '../../components/common/WinstaLogo';

export const PrivacyPage: React.FC = () => {
  const [lang, setLang] = useState<'en' | 'id'>('en');

  const effectiveDate = 'August 27, 2026';

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 font-sans antialiased selection:bg-purple-500 selection:text-white">
      {/* Top Navigation */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2 group">
              <WinstaLogo size="sm" showText={true} />
            </Link>
            <span className="hidden sm:inline-block px-2 py-0.5 text-[11px] font-bold bg-purple-100 text-purple-800 rounded-full border border-purple-200">
              Legal Center
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
              to="/terms"
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 hidden md:inline-flex items-center gap-1"
            >
              Terms of Service
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

      {/* Main Content Hero */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <div className="flex items-center gap-2 text-xs font-bold text-purple-600 uppercase tracking-widest mb-3">
            <ShieldCheck className="w-4 h-4" />
            <span>Bookmind & Winsta AI Platform</span>
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-serif font-black text-slate-900 tracking-tight">
            {lang === 'en' ? 'Privacy Policy' : 'Kebijakan Privasi'}
          </h1>
          <p className="mt-3 text-sm sm:text-base text-slate-600 max-w-3xl leading-relaxed">
            {lang === 'en'
              ? 'This Privacy Policy describes how Bookmind (https://bookmind.my.id) collects, uses, protects, and discloses personal data and social media API data when you use our platform.'
              : 'Kebijakan Privasi ini menjelaskan bagaimana Bookmind (https://bookmind.my.id) mengumpulkan, menggunakan, melindungi, dan mengungkapkan data pribadi serta data API media sosial saat Anda menggunakan platform kami.'}
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-4 text-xs font-medium text-slate-500">
            <span className="flex items-center gap-1.5 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
              <Calendar className="w-3.5 h-3.5 text-purple-600" />
              <strong>{lang === 'en' ? 'Effective Date:' : 'Berlaku Sejak:'}</strong> {effectiveDate}
            </span>
            <span className="flex items-center gap-1.5 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
              <Globe className="w-3.5 h-3.5 text-blue-600" />
              <strong>Domain:</strong> bookmind.my.id
            </span>
            <span className="flex items-center gap-1.5 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
              <Mail className="w-3.5 h-3.5 text-emerald-600" />
              <strong>Contact:</strong> privacy@bookmind.my.id
            </span>
          </div>
        </div>
      </div>

      {/* Quick Jump & Document Body */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Compliance Highlights Card */}
        <div className="mb-10 p-6 rounded-3xl bg-linear-to-r from-purple-50 via-indigo-50 to-blue-50 border border-purple-200/80 shadow-xs">
          <h2 className="text-sm font-black uppercase tracking-wider text-purple-900 mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-purple-600" />
            {lang === 'en' ? 'Key Privacy Commitments' : 'Komitmen Privasi Utama Kami'}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-slate-700">
            <div className="flex items-start gap-2 bg-white/80 p-3 rounded-2xl border border-purple-100">
              <Lock className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
              <span>
                <strong>{lang === 'en' ? 'Encrypted Credentials:' : 'Kredensial Terenkripsi:'}</strong>{' '}
                {lang === 'en'
                  ? 'All OAuth access tokens and secrets are encrypted at rest using AES-256 encryption.'
                  : 'Semua token akses OAuth dan secret dienkripsi saat disimpan menggunakan enkripsi AES-256.'}
              </span>
            </div>
            <div className="flex items-start gap-2 bg-white/80 p-3 rounded-2xl border border-purple-100">
              <Eye className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <span>
                <strong>{lang === 'en' ? 'No Data Selling:' : 'Tidak Menjual Data:'}</strong>{' '}
                {lang === 'en'
                  ? 'We never sell, rent, or trade your personal or social media data to third parties.'
                  : 'Kami tidak pernah menjual, menyewakan, atau memperdagangkan data pribadi atau data media sosial Anda ke pihak ketiga.'}
              </span>
            </div>
            <div className="flex items-start gap-2 bg-white/80 p-3 rounded-2xl border border-purple-100">
              <Trash2 className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>
                <strong>{lang === 'en' ? 'Full User Control:' : 'Kontrol Penuh Pengguna:'}</strong>{' '}
                {lang === 'en'
                  ? 'Disconnect social channels anytime to instantly revoke tokens and purge cached data.'
                  : 'Putuskan koneksi akun media sosial kapan saja untuk mencabut token dan menghapus data.'}
              </span>
            </div>
            <div className="flex items-start gap-2 bg-white/80 p-3 rounded-2xl border border-purple-100">
              <Server className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <span>
                <strong>{lang === 'en' ? 'Limited Use Adherence:' : 'Kepatuhan Limited Use:'}</strong>{' '}
                {lang === 'en'
                  ? 'Fully compliant with Google API Services User Data Policy and Meta Platform Terms.'
                  : 'Sepenuhnya mematuhi Google API Services User Data Policy dan Ketentuan Platform Meta.'}
              </span>
            </div>
          </div>
        </div>

        {/* English Content */}
        {lang === 'en' && (
          <div className="space-y-10 text-slate-800 leading-relaxed text-sm">
            {/* Section 1 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">1</span>
                1. Overview & Service Description
              </h2>
              <p className="mb-3">
                <strong>Bookmind</strong> (accessible at <a href="https://bookmind.my.id" className="text-purple-600 hover:underline font-semibold">https://bookmind.my.id</a>, powered by Winsta AI technology) provides automated trend discovery, AI prompt creation, creative asset planning, and multi-channel social media publishing tools.
              </p>
              <p>
              To provide these automated curation and scheduling services, Bookmind integrates with third-party social media platform APIs including Meta (Facebook & Instagram), Threads, TikTok, YouTube (Google Cloud), LinkedIn, and X (Twitter). This Privacy Policy explains what data we access, how it is processed, and your rights regarding data control and deletion.
              </p>
            </section>

            {/* Section 2 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">2</span>
                2. Information We Collect
              </h2>
              <p className="mb-3">We collect information to operate, improve, and secure our services:</p>
              <ul className="list-disc pl-5 space-y-2 mb-4">
                <li>
                  <strong>Account Registration Data:</strong> Name, email address, password hash, role, and authentication tokens when you register or sign in.
                </li>
                <li>
                  <strong>OAuth Authentication Data:</strong> Scoped OAuth tokens, user IDs, channel IDs, Page IDs, and profile details provided by authorized third-party platforms when you link your social accounts.
                </li>
                <li>
                  <strong>Content & Scheduling Data:</strong> Creative briefs, prompts, generated captions, hashtags, images, and video media uploaded or generated for publishing.
                </li>
                <li>
                  <strong>Technical & Log Data:</strong> IP address, browser user-agent, API request timestamps, error logs, and session activity for security and rate-limiting purposes.
                </li>
              </ul>
            </section>

            {/* Section 3 - Third-Party Social API Integrations */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">3</span>
                3. Third-Party Platform Integrations & OAuth Scopes
              </h2>
              <p className="mb-4">
                When you connect your social media accounts via OAuth 2.0, Bookmind requests only the minimum permissions necessary to discover trends and publish approved content:
              </p>

              {/* Meta Box */}
              <div className="mb-4 p-5 rounded-2xl bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-2 font-bold text-slate-900 mb-2">
                  <Share2 className="w-4 h-4 text-blue-600" />
                  <span>Meta for Developers (Facebook & Instagram Graph API)</span>
                </div>
                <p className="text-xs text-slate-600 mb-2">
                  <strong>Scopes Requested:</strong> <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">pages_show_list</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">pages_read_engagement</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">pages_manage_posts</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">instagram_basic</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">instagram_content_publish</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">instagram_manage_insights</code>.
                </p>
                <p className="text-xs text-slate-600">
                  <strong>Usage:</strong> Authenticating connected Facebook Pages and Instagram Professional/Creator accounts, publishing scheduled posts/reels, and retrieving post analytics. We do not access private messages, personal timelines, or personal friend lists.
                </p>
              </div>

              {/* Google / YouTube Box */}
              <div className="mb-4 p-5 rounded-2xl bg-slate-50 border border-amber-200/80">
                <div className="flex items-center gap-2 font-bold text-slate-900 mb-2">
                  <Key className="w-4 h-4 text-rose-600" />
                  <span>Google APIs & YouTube Data API v3</span>
                </div>
                <p className="text-xs text-slate-600 mb-2">
                  <strong>Scopes Requested:</strong> <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">https://www.googleapis.com/auth/youtube.readonly</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">https://www.googleapis.com/auth/youtube.upload</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">userinfo.profile</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">userinfo.email</code>.
                </p>
                <p className="text-xs text-slate-600 mb-3">
                  <strong>Usage:</strong> Connecting your authorized YouTube channel, reading channel metadata and video upload statuses, and publishing user-approved video content / Shorts directly to your channel.
                </p>
                
                {/* Google Limited Use Notice */}
                <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-300 text-xs text-amber-950 font-medium leading-relaxed">
                  <strong>Google API Limited Use Disclosure:</strong> Bookmind's use and transfer of information received from Google APIs to any other app will adhere to the <a href="https://developers.google.com/terms/api-services-user-data-policy" target="_blank" rel="noopener noreferrer" className="underline font-bold text-amber-900 inline-flex items-center gap-0.5">Google API Services User Data Policy <ExternalLink className="w-3 h-3" /></a>, including the Limited Use requirements. Google user data is not shared with third parties, not sold, and not used for personalized advertising or training generalized AI models.
                </div>
              </div>

              {/* TikTok Box */}
              <div className="mb-4 p-5 rounded-2xl bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-2 font-bold text-slate-900 mb-2">
                  <Share2 className="w-4 h-4 text-black" />
                  <span>TikTok for Developers (Login Kit & Content Posting API)</span>
                </div>
                <p className="text-xs text-slate-600 mb-2">
                  <strong>Scopes Requested:</strong> <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">user.info.basic</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">video.publish</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">video.upload</code>.
                </p>
                <p className="text-xs text-slate-600">
                  <strong>Usage:</strong> Connecting creator profiles, generating video draft payloads, and publishing user-approved videos to TikTok accounts.
                </p>
              </div>

              {/* LinkedIn Box */}
              <div className="mb-4 p-5 rounded-2xl bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-2 font-bold text-slate-900 mb-2">
                  <Share2 className="w-4 h-4 text-blue-700" />
                  <span>LinkedIn Developer Platform</span>
                </div>
                <p className="text-xs text-slate-600 mb-2">
                  <strong>Scopes Requested:</strong> <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">openid</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">profile</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">email</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">w_member_social</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">w_organization_social</code>.
                </p>
                <p className="text-xs text-slate-600">
                  <strong>Usage:</strong> Authenticating profile identity and sharing professional articles, media, and campaign updates to personal profiles or managed organization pages.
                </p>
              </div>

              {/* X Platform Box */}
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-2 font-bold text-slate-900 mb-2">
                  <Share2 className="w-4 h-4 text-slate-900" />
                  <span>X (Twitter) Developer API v2</span>
                </div>
                <p className="text-xs text-slate-600 mb-2">
                  <strong>Scopes Requested:</strong> <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">tweet.read</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">tweet.write</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">users.read</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">offline.access</code>.
                </p>
                <p className="text-xs text-slate-600">
                  <strong>Usage:</strong> Authenticating profile identity, scheduling tweets and thread updates, and verifying post publication status.
                </p>
              </div>
            </section>

            {/* Section 4 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">4</span>
                4. How We Use and Protect Data
              </h2>
              <p className="mb-3">We process data solely for the following business and operational purposes:</p>
              <ul className="list-disc pl-5 space-y-2 mb-4">
                <li>Providing automated trend discovery and multi-signal scoring algorithms.</li>
                <li>Synthesizing 6-modality AI prompt packages (Text-to-Image, Text-to-Video, Voice scripts).</li>
                <li>Executing user-approved publishing schedules across connected social networks.</li>
                <li>Maintaining authenticated sessions with secure JWT tokens and role-based permissions.</li>
                <li>Monitoring system health, diagnostics, and preventing malicious API abuse.</li>
              </ul>
              <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-950 text-xs">
                <strong>Strict Human-Access Policy:</strong> Our engineers and staff do not view or access your private social media content or OAuth tokens unless you explicitly request customer support assistance or diagnostics.
              </div>
            </section>

            {/* Section 5 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">5</span>
                5. Data Storage, Retention & Security
              </h2>
              <p className="mb-3">
                Security is fundamental to our architecture:
              </p>
              <ul className="list-disc pl-5 space-y-2 mb-4">
                <li>
                  <strong>Encryption at Rest:</strong> All OAuth tokens (access tokens, refresh tokens, and client secrets) are encrypted using authenticated cryptography (AES-256 / Fernet encryption) before storage in PostgreSQL.
                </li>
                <li>
                  <strong>Encryption in Transit:</strong> All HTTP communications require TLS 1.3 / SSL encryption with strict HTTPS enforcement on <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-800">bookmind.my.id</code>.
                </li>
                <li>
                  <strong>Data Retention:</strong> OAuth tokens and user preferences are retained only as long as your account remains active and connected. If you disconnect an account or delete your profile, tokens are permanently purged within 24 hours.
                </li>
              </ul>
            </section>

            {/* Section 6 - User Rights & Data Deletion */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">6</span>
                6. User Data Deletion Instructions (Meta, Google, TikTok, LinkedIn)
              </h2>
              <p className="mb-3">
                In compliance with Meta Platform Policy, Google Data Guidelines, TikTok Developer Terms, and Indonesian Personal Data Protection (UU PDP), you have the right to request deletion of all personal data and connected social tokens:
              </p>
              <div className="space-y-3 mb-4">
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                  <h3 className="font-bold text-slate-900 text-xs mb-1">Option 1: Instant In-App Disconnect</h3>
                  <p className="text-xs text-slate-600">
                    Log in to your Bookmind dashboard, navigate to <strong>/social/accounts</strong>, and click <strong>"Disconnect"</strong> on any social platform. All OAuth tokens and linked references are immediately erased.
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                  <h3 className="font-bold text-slate-900 text-xs mb-1">Option 2: Dedicated Data Deletion Request</h3>
                  <p className="text-xs text-slate-600">
                    Visit our dedicated instructions page at <Link to="/data-deletion" className="text-purple-600 font-semibold hover:underline">https://bookmind.my.id/data-deletion</Link> or email our privacy team at <a href="mailto:privacy@bookmind.my.id" className="text-purple-600 font-semibold hover:underline">privacy@bookmind.my.id</a> with the subject <em>"Data Deletion Request"</em>.
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                  <h3 className="font-bold text-slate-900 text-xs mb-1">Option 3: Revoke Access via Provider Security Portals</h3>
                  <p className="text-xs text-slate-600">
                    You can also revoke Bookmind's authorization directly at any time:
                  </p>
                  <ul className="list-disc pl-5 mt-1 text-xs text-slate-600 space-y-1">
                    <li><a href="https://www.facebook.com/settings?tab=applications" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Meta / Facebook App Settings</a></li>
                    <li><a href="https://myaccount.google.com/permissions" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Google Account Permissions (YouTube)</a></li>
                    <li><a href="https://www.tiktok.com/setting" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">TikTok Manage Apps & Permissions</a></li>
                    <li><a href="https://www.linkedin.com/psettings/permitted-services" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">LinkedIn Permitted Services</a></li>
                    <li><a href="https://twitter.com/settings/connected_apps" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">X Connected Apps</a></li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Section 7 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">7</span>
                7. International & Regional Privacy Rights (UU PDP, GDPR, CCPA)
              </h2>
              <p className="mb-3">
                Depending on your location, you may have statutory rights regarding your personal information under Indonesian UU No. 27/2022 (UU PDP), EU GDPR, or California CCPA:
              </p>
              <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-700 mb-3">
                <li>Right to access personal data collected about you.</li>
                <li>Right to rectify inaccurate or incomplete data.</li>
                <li>Right to erasure (the "right to be forgotten").</li>
                <li>Right to restrict or object to certain processing activities.</li>
                <li>Right to data portability in a structured, machine-readable format.</li>
              </ul>
              <p className="text-xs text-slate-600">
                To exercise any of these rights, contact our Data Protection Officer at <a href="mailto:privacy@bookmind.my.id" className="text-purple-600 font-semibold hover:underline">privacy@bookmind.my.id</a>.
              </p>
            </section>

            {/* Section 8 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">8</span>
                8. Contact Information
              </h2>
              <p className="mb-3">
                If you have questions, feedback, or concerns regarding this Privacy Policy or our security practices, please reach out to:
              </p>
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
                <p className="font-bold text-slate-900 text-sm">Bookmind Data Protection Office</p>
                <p><strong>Platform:</strong> Bookmind / Winsta AI Automation</p>
                <p><strong>Official Website:</strong> <a href="https://bookmind.my.id" className="text-purple-600 hover:underline">https://bookmind.my.id</a></p>
                <p><strong>Privacy Email:</strong> <a href="mailto:privacy@bookmind.my.id" className="text-purple-600 hover:underline">privacy@bookmind.my.id</a></p>
                <p><strong>Support Email:</strong> <a href="mailto:support@bookmind.my.id" className="text-purple-600 hover:underline">support@bookmind.my.id</a></p>
              </div>
            </section>
          </div>
        )}

        {/* Indonesian Content */}
        {lang === 'id' && (
          <div className="space-y-10 text-slate-800 leading-relaxed text-sm">
            {/* Seksi 1 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">1</span>
                1. Gambaran Umum & Deskripsi Layanan
              </h2>
              <p className="mb-3">
                <strong>Bookmind</strong> (dapat diakses di <a href="https://bookmind.my.id" className="text-purple-600 hover:underline font-semibold">https://bookmind.my.id</a>, didukung oleh teknologi Winsta AI) menyediakan platform kurasi trend otomatis, perancangan prompt AI kreatif, manajemen aset, dan penerbitan konten media sosial multi-platform.
              </p>
              <p>
                Untuk menyediakan layanan ini, Bookmind terintegrasi dengan API resmi dari platform media sosial pihak ketiga, termasuk Meta (Facebook & Instagram), TikTok, YouTube (Google Cloud), LinkedIn, dan X (Twitter). Kebijakan Privasi ini menjelaskan data apa saja yang kami akses, bagaimana data tersebut diproses, dan hak-hak Anda atas privasi data.
              </p>
            </section>

            {/* Seksi 2 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">2</span>
                2. Data yang Kami Kumpulkan
              </h2>
              <p className="mb-3">Kami mengumpulkan data yang diperlukan untuk mengoperasikan layanan:</p>
              <ul className="list-disc pl-5 space-y-2 mb-4">
                <li>
                  <strong>Data Pendaftaran Akun:</strong> Nama lengkap, alamat email, hash kata sandi, peran pengguna, dan token autentikasi saat masuk.
                </li>
                <li>
                  <strong>Data Autentikasi OAuth:</strong> Token akses terenkripsi, ID pengguna, ID channel/halaman, dan nama pengguna dari platform media sosial yang Anda hubungkan.
                </li>
                <li>
                  <strong>Data Konten & Penjadwalan:</strong> Brief konten, prompt AI, caption, hashtag, dan media gambar/video yang Anda jadwalkan untuk dipublikasikan.
                </li>
                <li>
                  <strong>Data Teknis & Log:</strong> Alamat IP, user-agent browser, timestamp permintaan API, dan log diagnostik keamanan sistem.
                </li>
              </ul>
            </section>

            {/* Seksi 3 - Integrasi API Media Sosial */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">3</span>
                3. Integrasi Platform Pihak Ketiga & Izin OAuth
              </h2>
              <p className="mb-4">
                Saat Anda menghubungkan akun media sosial melalui OAuth 2.0, Bookmind hanya meminta izin minimum yang diperlukan:
              </p>

              {/* Meta Box */}
              <div className="mb-4 p-5 rounded-2xl bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-2 font-bold text-slate-900 mb-2">
                  <Share2 className="w-4 h-4 text-blue-600" />
                  <span>Meta for Developers (Facebook & Instagram Graph API)</span>
                </div>
                <p className="text-xs text-slate-600 mb-2">
                  <strong>Izin (Scopes):</strong> <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">pages_show_list</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">pages_read_engagement</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">pages_manage_posts</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">instagram_basic</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">instagram_content_publish</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">instagram_manage_insights</code>.
                </p>
                <p className="text-xs text-slate-600">
                  <strong>Penggunaan:</strong> Menghubungkan Facebook Page dan Akun Instagram Profesional/Kreator untuk menjadwalkan dan menerbitkan postingan/Reels serta memantau performa konten. Kami tidak mengakses pesan pribadi atau linimasa pribadi.
                </p>
              </div>

              {/* Google / YouTube Box */}
              <div className="mb-4 p-5 rounded-2xl bg-slate-50 border border-amber-200/80">
                <div className="flex items-center gap-2 font-bold text-slate-900 mb-2">
                  <Key className="w-4 h-4 text-rose-600" />
                  <span>Google APIs & YouTube Data API v3</span>
                </div>
                <p className="text-xs text-slate-600 mb-2">
                  <strong>Izin (Scopes):</strong> <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">youtube.readonly</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">youtube.upload</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">userinfo.profile</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">userinfo.email</code>.
                </p>
                <p className="text-xs text-slate-600 mb-3">
                  <strong>Penggunaan:</strong> Mengidentifikasi akun YouTube Anda, memeriksa status channel, dan mengunggah video/Shorts yang telah Anda setujui ke channel YouTube Anda.
                </p>
                <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-300 text-xs text-amber-950 font-medium leading-relaxed">
                  <strong>Pernyataan Google Limited Use:</strong> Penggunaan dan transfer informasi yang diterima dari Google API oleh Bookmind tunduk pada <a href="https://developers.google.com/terms/api-services-user-data-policy" target="_blank" rel="noopener noreferrer" className="underline font-bold text-amber-900 inline-flex items-center gap-0.5">Google API Services User Data Policy <ExternalLink className="w-3 h-3" /></a>, termasuk ketentuan Limited Use. Data pengguna Google tidak dijual, tidak dibagikan ke pihak ketiga, dan tidak digunakan untuk iklan tertarget atau pelatihan model AI umum.
                </div>
              </div>

              {/* TikTok Box */}
              <div className="mb-4 p-5 rounded-2xl bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-2 font-bold text-slate-900 mb-2">
                  <Share2 className="w-4 h-4 text-black" />
                  <span>TikTok for Developers (Login Kit & Content Posting API)</span>
                </div>
                <p className="text-xs text-slate-600 mb-2">
                  <strong>Izin (Scopes):</strong> <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">user.info.basic</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">video.publish</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">video.upload</code>.
                </p>
                <p className="text-xs text-slate-600">
                  <strong>Penggunaan:</strong> Mengotentikasi profil kreator TikTok dan menerbitkan video yang dijadwalkan langsung ke akun TikTok Anda.
                </p>
              </div>

              {/* LinkedIn Box */}
              <div className="mb-4 p-5 rounded-2xl bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-2 font-bold text-slate-900 mb-2">
                  <Share2 className="w-4 h-4 text-blue-700" />
                  <span>LinkedIn Developer Platform</span>
                </div>
                <p className="text-xs text-slate-600 mb-2">
                  <strong>Izin (Scopes):</strong> <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">openid</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">profile</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">email</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">w_member_social</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">w_organization_social</code>.
                </p>
                <p className="text-xs text-slate-600">
                  <strong>Penggunaan:</strong> Autentikasi dan penerbitan postingan artikel atau media ke profil profesional LinkedIn atau halaman perusahaan resmi.
                </p>
              </div>

              {/* X Platform Box */}
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-2 font-bold text-slate-900 mb-2">
                  <Share2 className="w-4 h-4 text-slate-900" />
                  <span>X (Twitter) Developer API v2</span>
                </div>
                <p className="text-xs text-slate-600 mb-2">
                  <strong>Izin (Scopes):</strong> <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">tweet.read</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">tweet.write</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">users.read</code>, <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-800">offline.access</code>.
                </p>
                <p className="text-xs text-slate-600">
                  <strong>Penggunaan:</strong> Menjadwalkan dan menerbitkan postingan tweet atau thread serta memverifikasi status publikasi.
                </p>
              </div>
            </section>

            {/* Seksi 4 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">4</span>
                4. Penyimpanan, Keamanan & Enkripsi Data
              </h2>
              <ul className="list-disc pl-5 space-y-2 mb-4">
                <li>
                  <strong>Enkripsi Saat Disimpan (Encryption at Rest):</strong> Semua token OAuth dan kredensial sensitif dienkripsi dengan standar industri AES-256 sebelum disimpan ke dalam database PostgreSQL.
                </li>
                <li>
                  <strong>Enkripsi Saat Pengiriman (Encryption in Transit):</strong> Seluruh lalu lintas data diwajibkan menggunakan protokol HTTPS dengan sertifikat SSL/TLS 1.3 terkini.
                </li>
                <li>
                  <strong>Kebijakan Akses Ketat:</strong> Karyawan kami tidak memiliki akses membaca data pribadi media sosial Anda kecuali atas izin eksplisit Anda untuk kebutuhan bantuan teknis.
                </li>
              </ul>
            </section>

            {/* Seksi 5 - Petunjuk Penghapusan Data */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">5</span>
                5. Petunjuk Penghapusan Data Pengguna (User Data Deletion)
              </h2>
              <p className="mb-3">
                Sesuai dengan Undang-Undang Pelindungan Data Pribadi (UU PDP No. 27/2022) serta Kebijakan Platform Meta, Google, TikTok, dan LinkedIn, Anda berhak meminta penghapusan seluruh data Anda:
              </p>
              <div className="space-y-3 mb-4">
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                  <h3 className="font-bold text-slate-900 text-xs mb-1">Opsi 1: Pemutusan Akun Langsung di Dashboard</h3>
                  <p className="text-xs text-slate-600">
                    Buka menu <strong>/social/accounts</strong> pada dashboard Bookmind, lalu klik tombol <strong>"Disconnect"</strong>. Token akses dan kredensial terhubung akan segera dihapus permanen.
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200">
                  <h3 className="font-bold text-slate-900 text-xs mb-1">Opsi 2: Permohonan Penghapusan via Email</h3>
                  <p className="text-xs text-slate-600">
                    Kunjungi panduan resmi di <Link to="/data-deletion" className="text-purple-600 font-semibold hover:underline">https://bookmind.my.id/data-deletion</Link> atau kirimkan email ke <a href="mailto:privacy@bookmind.my.id" className="text-purple-600 font-semibold hover:underline">privacy@bookmind.my.id</a> dengan subjek <em>"Permohonan Hapus Data"</em>.
                  </p>
                </div>
              </div>
            </section>

            {/* Seksi 6 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">6</span>
                6. Hubungi Kami
              </h2>
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
                <p className="font-bold text-slate-900 text-sm">Tim Privasi & Keamanan Bookmind</p>
                <p><strong>Platform:</strong> Bookmind / Winsta AI Automation</p>
                <p><strong>Website:</strong> <a href="https://bookmind.my.id" className="text-purple-600 hover:underline">https://bookmind.my.id</a></p>
                <p><strong>Email Privasi:</strong> <a href="mailto:privacy@bookmind.my.id" className="text-purple-600 hover:underline">privacy@bookmind.my.id</a></p>
                <p><strong>Email Bantuan:</strong> <a href="mailto:support@bookmind.my.id" className="text-purple-600 hover:underline">support@bookmind.my.id</a></p>
              </div>
            </section>
          </div>
        )}

        {/* Footer Navigation */}
        <div className="mt-12 pt-8 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <div>
            © {new Date().getFullYear()} Bookmind (bookmind.my.id). All rights reserved.
          </div>
          <div className="flex items-center gap-4">
            <Link to="/terms" className="hover:text-purple-600 font-semibold">Terms of Service</Link>
            <span>•</span>
            <Link to="/data-deletion" className="hover:text-purple-600 font-semibold">Data Deletion</Link>
            <span>•</span>
            <Link to="/" className="hover:text-purple-600 font-semibold">Dashboard</Link>
          </div>
        </div>
      </div>
    </div>
  );
};
