import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Scale,
  Globe,
  Mail,
  ArrowLeft,
  Calendar,
} from 'lucide-react';
import { WinstaLogo } from '../../components/common/WinstaLogo';

export const TermsPage: React.FC = () => {
  const [lang, setLang] = useState<'en' | 'id'>('en');

  const lastUpdated = 'August 27, 2026';

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
              to="/privacy"
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 hidden md:inline-flex items-center gap-1"
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
          <div className="flex items-center gap-2 text-xs font-bold text-purple-600 uppercase tracking-widest mb-3">
            <Scale className="w-4 h-4" />
            <span>Bookmind & Winsta AI Platform</span>
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-serif font-black text-slate-900 tracking-tight">
            {lang === 'en' ? 'Terms of Service' : 'Ketentuan Layanan'}
          </h1>
          <p className="mt-3 text-sm sm:text-base text-slate-600 max-w-3xl leading-relaxed">
            {lang === 'en'
              ? 'Please review these Terms of Service before using the Bookmind platform (https://bookmind.my.id). By creating an account or connecting your social media channels, you agree to be bound by these terms.'
              : 'Harap membaca Ketentuan Layanan ini sebelum menggunakan platform Bookmind (https://bookmind.my.id). Dengan mendaftar atau menghubungkan akun media sosial Anda, Anda menyetujui ketentuan ini.'}
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-4 text-xs font-medium text-slate-500">
            <span className="flex items-center gap-1.5 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
              <Calendar className="w-3.5 h-3.5 text-purple-600" />
              <strong>{lang === 'en' ? 'Last Updated:' : 'Terakhir Diperbarui:'}</strong> {lastUpdated}
            </span>
            <span className="flex items-center gap-1.5 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
              <Globe className="w-3.5 h-3.5 text-blue-600" />
              <strong>Domain:</strong> bookmind.my.id
            </span>
            <span className="flex items-center gap-1.5 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
              <Mail className="w-3.5 h-3.5 text-emerald-600" />
              <strong>Legal Inquiries:</strong> legal@bookmind.my.id
            </span>
          </div>
        </div>
      </div>

      {/* Main Body */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Important Notice */}
        <div className="mb-10 p-6 rounded-3xl bg-linear-to-r from-purple-50 via-indigo-50 to-blue-50 border border-purple-200 shadow-xs">
          <div className="flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-purple-700 shrink-0 mt-0.5" />
            <div>
              <h2 className="text-sm font-black uppercase tracking-wider text-purple-900 mb-1">
                {lang === 'en' ? 'Platform Agreement Summary' : 'Ringkasan Perjanjian Layanan'}
              </h2>
              <p className="text-xs text-slate-700 leading-relaxed">
                {lang === 'en'
                  ? 'Bookmind provides automated trend curation and social media automation. You retain full intellectual property ownership of your creative prompts and content. By connecting third-party networks (Meta, TikTok, YouTube, LinkedIn, X), you agree to comply with each platform’s terms of service and developer policies.'
                  : 'Bookmind menyediakan kurasi trend otomatis dan otomasi media sosial. Anda memegang kepemilikan penuh hak cipta atas konten dan prompt Anda. Dengan menghubungkan platform pihak ketiga (Meta, TikTok, YouTube, LinkedIn, X), Anda juga setuju untuk mematuhi kebijakan masing-masing platform tersebut.'}
              </p>
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
                1. Acceptance of Terms & Eligibility
              </h2>
              <p className="mb-3">
                These Terms of Service ("Terms") constitute a legally binding agreement between you and <strong>Bookmind</strong> (accessible at <a href="https://bookmind.my.id" className="text-purple-600 hover:underline font-semibold">https://bookmind.my.id</a>, powered by Winsta AI technology).
              </p>
              <p className="mb-3">
                By registering an account, accessing our dashboard, or connecting any social media profile, you affirm that:
              </p>
              <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-700">
                <li>You are at least 18 years old (or the legal age of majority in your jurisdiction).</li>
                <li>You have the legal authority to bind yourself or the legal entity on whose behalf you are acting.</li>
                <li>You will provide accurate, current, and complete registration information.</li>
                <li>You will maintain the security of your credentials and notify us immediately of any unauthorized access.</li>
              </ul>
            </section>

            {/* Section 2 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">2</span>
                2. Description of Services
              </h2>
              <p className="mb-3">
                Bookmind provides digital creators and marketing teams with:
              </p>
              <ul className="list-disc pl-5 space-y-2 mb-4">
                <li>
                  <strong>Automated Trend Discovery:</strong> Aggregating viral trend patterns from public signals (Google Trends, Instagram, TikTok, YouTube Shorts, X).
                </li>
                <li>
                  <strong>6-Modality AI Prompt Synthesis:</strong> Generating structured prompt packages for Text-to-Image, Text-to-Video, Text-to-Voice, Image-to-Image, and Motion workflows.
                </li>
                <li>
                  <strong>Multi-Channel Publishing & Scheduling:</strong> Direct publishing to user-authorized Facebook Pages, Instagram Professional Accounts, TikTok Creator Accounts, YouTube Channels, LinkedIn Profiles/Pages, and X accounts.
                </li>
                <li>
                  <strong>Analytics & Campaign Tracking:</strong> Monitoring cross-platform performance and engagement statistics.
                </li>
              </ul>
            </section>

            {/* Section 3 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">3</span>
                3. Third-Party Platform Policies & Compliance
              </h2>
              <p className="mb-3">
                When using Bookmind to schedule or publish to third-party platforms, you agree to comply strictly with their respective policies and community guidelines:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs mb-4">
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200">
                  <p className="font-bold text-slate-900 mb-1">Meta (Facebook & Instagram)</p>
                  <p className="text-slate-600">
                    Must comply with <a href="https://www.facebook.com/terms.php" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Meta Terms of Service</a> and <a href="https://transparency.fb.com/policies/community-standards/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Community Standards</a>.
                  </p>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200">
                  <p className="font-bold text-slate-900 mb-1">YouTube & Google</p>
                  <p className="text-slate-600">
                    Must comply with <a href="https://www.youtube.com/t/terms" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">YouTube Terms of Service</a> and <a href="https://policies.google.com/terms" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Google Terms of Service</a>.
                  </p>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200">
                  <p className="font-bold text-slate-900 mb-1">TikTok</p>
                  <p className="text-slate-600">
                    Must comply with <a href="https://www.tiktok.com/legal/terms-of-service" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">TikTok Terms of Service</a> and <a href="https://www.tiktok.com/community-guidelines" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Community Guidelines</a>.
                  </p>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200">
                  <p className="font-bold text-slate-900 mb-1">LinkedIn & X</p>
                  <p className="text-slate-600">
                    Must comply with <a href="https://www.linkedin.com/legal/user-agreement" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">LinkedIn User Agreement</a> and <a href="https://twitter.com/tos" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">X Rules & Terms</a>.
                  </p>
                </div>
              </div>
              <p className="text-xs text-slate-500 italic">
                Bookmind is an independent third-party software solution and is not endorsed, sponsored, or directly affiliated with Meta Platforms, Google LLC, ByteDance / TikTok, LinkedIn Corporation, or X Corp.
              </p>
            </section>

            {/* Section 4 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">4</span>
                4. User Content & Intellectual Property Rights
              </h2>
              <ul className="list-disc pl-5 space-y-2 mb-4">
                <li>
                  <strong>Your Ownership:</strong> You retain 100% intellectual property ownership of your media, text, brief inputs, and custom prompt variations.
                </li>
                <li>
                  <strong>Limited Operational License:</strong> You grant Bookmind a worldwide, non-exclusive, royalty-free license solely to host, process, format, and transmit your content to the social platforms you explicitly choose to publish to.
                </li>
                <li>
                  <strong>AI Generated Outputs:</strong> Outputs generated by integrated AI models (such as prompts, hashtags, and suggested captions) are provided for your creative use. You are solely responsible for reviewing and approving AI-assisted content before live broadcast.
                </li>
              </ul>
            </section>

            {/* Section 5 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">5</span>
                5. Prohibited Conduct & Acceptable Use
              </h2>
              <p className="mb-3">You agree NOT to use the Bookmind platform to:</p>
              <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-700 mb-4">
                <li>Publish abusive, defamatory, hateful, sexually explicit, or illegal content.</li>
                <li>Infringe upon the copyright, trademark, or patent of any third party.</li>
                <li>Engage in automated spamming, deceptive marketing, or deceptive traffic generation.</li>
                <li>Attempt to bypass rate limits, reverse engineer backend endpoints, or execute unauthorized automated scraping.</li>
                <li>Distribute malware, trojans, or attempt unauthorized access to platform servers.</li>
              </ul>
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 text-xs font-medium">
                Violation of acceptable use guidelines may result in immediate suspension or termination of your account without prior notice.
              </div>
            </section>

            {/* Section 6 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">6</span>
                6. Disclaimer of Warranties & Limitation of Liability
              </h2>
              <p className="mb-3 text-xs">
                THE PLATFORM IS PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS. TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, BOOKMIND DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
              </p>
              <p className="text-xs text-slate-600 mb-3">
                Bookmind shall not be liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of profits, data, or audience engagement resulting from third-party social media API downtime, policy changes, or algorithmic shifts.
              </p>
            </section>

            {/* Section 7 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">7</span>
                7. Governing Law & Dispute Resolution
              </h2>
              <p className="mb-3 text-xs">
                These Terms shall be governed by and construed in accordance with the laws of the Republic of Indonesia, without regard to conflict of law principles. Any dispute arising out of or related to these Terms shall be resolved through friendly consultation or submitted to the competent courts of Indonesia.
              </p>
            </section>

            {/* Section 8 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">8</span>
                8. Contact Information
              </h2>
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
                <p className="font-bold text-slate-900 text-sm">Bookmind Legal Department</p>
                <p><strong>Platform:</strong> Bookmind / Winsta AI Automation</p>
                <p><strong>Website:</strong> <a href="https://bookmind.my.id" className="text-purple-600 hover:underline">https://bookmind.my.id</a></p>
                <p><strong>Legal Email:</strong> <a href="mailto:legal@bookmind.my.id" className="text-purple-600 hover:underline">legal@bookmind.my.id</a></p>
                <p><strong>General Support:</strong> <a href="mailto:support@bookmind.my.id" className="text-purple-600 hover:underline">support@bookmind.my.id</a></p>
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
                1. Penerimaan Ketentuan & Kelayakan
              </h2>
              <p className="mb-3">
                Ketentuan Layanan ini ("Ketentuan") merupakan perjanjian hukum antara Anda dan <strong>Bookmind</strong> (dapat diakses di <a href="https://bookmind.my.id" className="text-purple-600 hover:underline font-semibold">https://bookmind.my.id</a>).
              </p>
              <p className="mb-3">
                Dengan mendaftarkan akun atau menghubungkan media sosial Anda, Anda menyatakan bahwa:
              </p>
              <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-700">
                <li>Anda telah berusia minimal 18 tahun atau memiliki wewenang hukum yang sah.</li>
                <li>Anda memiliki hak untuk mewakili entitas bisnis jika mendaftar atas nama organisasi.</li>
                <li>Informasi akun yang Anda berikan adalah benar, akurat, dan terkini.</li>
                <li>Anda bertanggung jawab menjaga kerahasiaan kata sandi dan sesi login Anda.</li>
              </ul>
            </section>

            {/* Seksi 2 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">2</span>
                2. Deskripsi Layanan
              </h2>
              <p className="mb-3">
                Bookmind menyediakan layanan otomasi cerdas bagi kreator dan bisnis:
              </p>
              <ul className="list-disc pl-5 space-y-2 mb-4">
                <li>
                  <strong>Eksplorasi & Kurasi Trend:</strong> Pengumpulan sinyal trend viral secara otomatis dari berbagai platform (Google Trends, Instagram, TikTok, YouTube Shorts, X).
                </li>
                <li>
                  <strong>Sintesis Prompt AI 6-Modalitas:</strong> Pembuatan formula prompt teks-ke-gambar, video, naskah audio, dan animasi visual.
                </li>
                <li>
                  <strong>Penjadwalan & Penerbitan Multi-Platform:</strong> Integrasi langsung ke Facebook Page, Instagram Creator/Business, TikTok, YouTube, LinkedIn, dan X.
                </li>
                <li>
                  <strong>Analitik Konten:</strong> Pemantauan metrik engagement dan efektivitas kampanye.
                </li>
              </ul>
            </section>

            {/* Seksi 3 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">3</span>
                3. Kepatuhan Terhadap Ketentuan Platform Pihak Ketiga
              </h2>
              <p className="mb-3">
                Saat mempublikasikan konten melalui Bookmind, Anda wajib mematuhi ketentuan dan pedoman komunitas masing-masing penyedia:
              </p>
              <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-700 mb-3">
                <li>Meta: Facebook Terms of Service & Instagram Community Guidelines.</li>
                <li>Google & YouTube: YouTube Terms of Service & Google Terms.</li>
                <li>TikTok: TikTok Terms of Service & Community Guidelines.</li>
                <li>LinkedIn: LinkedIn User Agreement.</li>
                <li>X: X Rules and Policies.</li>
              </ul>
            </section>

            {/* Seksi 4 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">4</span>
                4. Hak Kekayaan Intelektual & Kepemilikan Konten
              </h2>
              <p className="mb-3">
                Anda memegang hak kepemilikan penuh 100% atas materi media, teks, dan karya yang Anda buat. Bookmind hanya menerima lisensi teknis untuk memproses dan mengirimkan materi ke platform tujuan yang Anda tentukan.
              </p>
            </section>

            {/* Seksi 5 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">5</span>
                5. Batasan Tanggung Jawab
              </h2>
              <p className="mb-3 text-xs">
                Layanan disediakan sebagaimana adanya ("AS IS"). Bookmind tidak bertanggung jawab atas gangguan teknis di luar kendali wajar kami, termasuk pemeliharaan sistem atau perubahan kebijakan API dari penyedia platform pihak ketiga.
              </p>
            </section>

            {/* Seksi 6 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">6</span>
                6. Hukum yang Berlaku
              </h2>
              <p className="mb-3 text-xs">
                Ketentuan ini diatur dan ditafsirkan sesuai dengan hukum Republik Indonesia.
              </p>
            </section>

            {/* Seksi 7 */}
            <section className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center text-xs font-black">7</span>
                7. Kontak Resmi
              </h2>
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
                <p className="font-bold text-slate-900 text-sm">Departemen Legal Bookmind</p>
                <p><strong>Platform:</strong> Bookmind / Winsta AI Automation</p>
                <p><strong>Website:</strong> <a href="https://bookmind.my.id" className="text-purple-600 hover:underline">https://bookmind.my.id</a></p>
                <p><strong>Email Legal:</strong> <a href="mailto:legal@bookmind.my.id" className="text-purple-600 hover:underline">legal@bookmind.my.id</a></p>
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
            <Link to="/privacy" className="hover:text-purple-600 font-semibold">Privacy Policy</Link>
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
