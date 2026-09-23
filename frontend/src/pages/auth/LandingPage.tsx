import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  CalendarDays,
  ChevronDown,
  Globe2,
  Layers3,
  Play,
  Sparkles,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { WinstaLogo } from '../../components/common/WinstaLogo';
import { useLanguage } from '../../context/LanguageContext';
import type { Language } from '../../i18n/translations';

const copy: Record<Language, {
  navProduct: string;
  navHow: string;
  navSecurity: string;
  signIn: string;
  getStarted: string;
  badge: string;
  title: string;
  titleAccent: string;
  subtitle: string;
  primary: string;
  secondary: string;
  trusted: string;
  featureEyebrow: string;
  featureTitle: string;
  featureSubtitle: string;
  features: { title: string; body: string }[];
  workflowEyebrow: string;
  workflowTitle: string;
  workflowSubtitle: string;
  steps: { title: string; body: string }[];
  ctaTitle: string;
  ctaBody: string;
  ctaButton: string;
  footer: string;
}> = {
  en: {
    navProduct: 'Product', navHow: 'How it works', navSecurity: 'Security', signIn: 'Sign in', getStarted: 'Get started',
    badge: 'Trend intelligence meets creative AI', title: 'Your next great post', titleAccent: 'starts with a signal.',
    subtitle: 'Discover what matters, turn insights into on-brand content, and publish everywhere from one calm, collaborative workspace.',
    primary: 'Start for free', secondary: 'See how it works', trusted: 'Built for teams publishing across',
    featureEyebrow: 'One connected workspace', featureTitle: 'From signal to story in minutes.', featureSubtitle: 'Winsta AI combines trend discovery, creative generation, and omnichannel publishing into one repeatable system.',
    features: [
      { title: 'Trend intelligence', body: 'Monitor conversations across Google Trends, TikTok, Instagram, YouTube, X, and LinkedIn with transparent scoring.' },
      { title: 'Creative AI studio', body: 'Create captions, hooks, and visual directions that respect your brand kit and adapt to every channel.' },
      { title: 'Omnichannel publishing', body: 'Plan, approve, schedule, and measure social content without jumping between six different dashboards.' },
    ],
    workflowEyebrow: 'A better operating rhythm', workflowTitle: 'Less busywork. More momentum.', workflowSubtitle: 'A simple loop your whole team can trust, from the first signal to the final report.',
    steps: [
      { title: 'Find the signal', body: 'Surface high-potential topics with multi-source discovery and human-friendly scoring.' },
      { title: 'Shape the story', body: 'Generate platform-ready copy and creative briefs in English, Indonesian, or Arabic.' },
      { title: 'Ship with confidence', body: 'Approve once, schedule everywhere, and learn from the performance that follows.' },
    ],
    ctaTitle: 'Make every trend useful.', ctaBody: 'Bring your ideas, channels, and team into one focused workspace.', ctaButton: 'Create your workspace', footer: 'Trend intelligence & creative AI for modern teams.',
  },
  id: {
    navProduct: 'Produk', navHow: 'Cara kerja', navSecurity: 'Keamanan', signIn: 'Masuk', getStarted: 'Mulai sekarang',
    badge: 'Trend intelligence bertemu creative AI', title: 'Posting terbaik Anda', titleAccent: 'dimulai dari sebuah sinyal.',
    subtitle: 'Temukan hal yang penting, ubah insight menjadi konten sesuai brand, lalu publikasikan ke semua kanal dari satu workspace yang rapi.',
    primary: 'Mulai gratis', secondary: 'Lihat cara kerja', trusted: 'Dibuat untuk tim yang aktif di',
    featureEyebrow: 'Satu workspace terhubung', featureTitle: 'Dari sinyal menjadi cerita dalam hitungan menit.', featureSubtitle: 'Winsta AI menyatukan penemuan tren, pembuatan kreatif, dan publikasi omnichannel dalam satu sistem yang konsisten.',
    features: [
      { title: 'Trend intelligence', body: 'Pantau percakapan dari Google Trends, TikTok, Instagram, YouTube, X, dan LinkedIn dengan scoring yang transparan.' },
      { title: 'Creative AI studio', body: 'Buat caption, hook, dan arahan visual yang mengikuti brand kit serta menyesuaikan setiap kanal.' },
      { title: 'Publikasi omnichannel', body: 'Rencanakan, setujui, jadwalkan, dan ukur konten tanpa berpindah-pindah dashboard.' },
    ],
    workflowEyebrow: 'Ritme kerja yang lebih baik', workflowTitle: 'Lebih sedikit pekerjaan repetitif. Lebih banyak momentum.', workflowSubtitle: 'Alur sederhana yang bisa dipercaya tim, dari sinyal pertama hingga laporan akhir.',
    steps: [
      { title: 'Temukan sinyal', body: 'Temukan topik potensial melalui discovery multi-sumber dan scoring yang mudah dipahami.' },
      { title: 'Bentuk ceritanya', body: 'Buat copy dan creative brief siap platform dalam bahasa Inggris, Indonesia, atau Arab.' },
      { title: 'Publikasikan dengan yakin', body: 'Setujui sekali, jadwalkan di semua kanal, lalu pelajari performanya.' },
    ],
    ctaTitle: 'Jadikan setiap tren berarti.', ctaBody: 'Satukan ide, kanal, dan tim Anda dalam satu workspace yang fokus.', ctaButton: 'Buat workspace', footer: 'Trend intelligence & creative AI untuk tim modern.',
  },
  ar: {
    navProduct: 'المنتج', navHow: 'كيف يعمل', navSecurity: 'الأمان', signIn: 'تسجيل الدخول', getStarted: 'ابدأ الآن',
    badge: 'ذكاء الاتجاهات يلتقي بالذكاء الإبداعي', title: 'منشورك القادم الرائع', titleAccent: 'يبدأ بإشارة.',
    subtitle: 'اكتشف ما يهم، وحوّل الرؤى إلى محتوى يحافظ على هوية علامتك، وانشر في كل مكان من مساحة عمل واحدة.',
    primary: 'ابدأ مجاناً', secondary: 'شاهد كيف يعمل', trusted: 'مصمم للفرق التي تنشر على',
    featureEyebrow: 'مساحة عمل متصلة', featureTitle: 'من الإشارة إلى القصة خلال دقائق.', featureSubtitle: 'يجمع Winsta AI اكتشاف الاتجاهات، وإنشاء المحتوى، والنشر متعدد القنوات في نظام واحد متكرر.',
    features: [
      { title: 'ذكاء الاتجاهات', body: 'راقب المحادثات عبر Google Trends وTikTok وInstagram وYouTube وX وLinkedIn مع تقييم واضح.' },
      { title: 'استوديو إبداعي بالذكاء الاصطناعي', body: 'أنشئ التعليقات والخطافات والتوجيهات البصرية بما يتوافق مع هوية علامتك لكل قناة.' },
      { title: 'نشر متعدد القنوات', body: 'خطط وراجع وجدول وقِس المحتوى دون التنقل بين ست لوحات مختلفة.' },
    ],
    workflowEyebrow: 'إيقاع عمل أفضل', workflowTitle: 'عمل روتيني أقل. زخم أكبر.', workflowSubtitle: 'حلقة بسيطة يمكن لفريقك الوثوق بها، من الإشارة الأولى إلى التقرير النهائي.',
    steps: [
      { title: 'اعثر على الإشارة', body: 'اكتشف الموضوعات الواعدة من مصادر متعددة مع تقييم سهل الفهم.' },
      { title: 'شكّل القصة', body: 'أنشئ نصوصاً وملخصات إبداعية جاهزة لكل منصة بالعربية أو الإنجليزية أو الإندونيسية.' },
      { title: 'انشر بثقة', body: 'وافق مرة واحدة، وجدول في كل القنوات، وتعلم من الأداء.' },
    ],
    ctaTitle: 'اجعل كل اتجاه مفيداً.', ctaBody: 'اجمع أفكارك وقنواتك وفريقك في مساحة عمل واحدة مركزة.', ctaButton: 'أنشئ مساحة عملك', footer: 'ذكاء الاتجاهات والذكاء الإبداعي للفرق الحديثة.',
  },
};

const platforms = ['Instagram', 'TikTok', 'YouTube', 'Threads', 'X', 'LinkedIn'];

export const LandingPage: React.FC = () => {
  const { language, setLanguage } = useLanguage();
  const text = copy[language];

  return (
    <div className="landing-page min-h-screen overflow-hidden bg-[#fbfcff] text-[#0f172a] selection:bg-[#8b5cf6] selection:text-white">
      <header className="relative z-20 border-b border-slate-200/70 bg-white/75 backdrop-blur-xl">
        <div className="mx-auto flex h-[76px] max-w-7xl items-center justify-between px-5 sm:px-8">
          <Link to="/" aria-label="Winsta AI home" className="group"><WinstaLogo size="md" showText /></Link>
          <nav className="hidden items-center gap-8 text-sm font-semibold text-slate-500 md:flex">
            <a href="#product" className="transition-colors hover:text-slate-900">{text.navProduct}</a>
            <a href="#workflow" className="transition-colors hover:text-slate-900">{text.navHow}</a>
            <a href="#security" className="transition-colors hover:text-slate-900">{text.navSecurity}</a>
          </nav>
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="hidden items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1 sm:flex">
              {(['en', 'id', 'ar'] as Language[]).map((code) => (
                <button key={code} type="button" onClick={() => setLanguage(code)} className={`rounded-lg px-2.5 py-1 text-[11px] font-bold uppercase transition ${language === code ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400 hover:text-slate-700'}`}>{code}</button>
              ))}
            </div>
            <Link to="/login" className="hidden px-3 py-2 text-sm font-bold text-slate-600 transition hover:text-slate-900 sm:block">{text.signIn}</Link>
            <Link to="/login" className="inline-flex items-center gap-2 rounded-xl bg-[#0f172a] px-4 py-2.5 text-sm font-bold text-white shadow-[2px_2px_0px_#8b5cf6] transition hover:-translate-y-0.5 hover:bg-[#1e293b]">{text.getStarted}<ArrowRight className="h-4 w-4" /></Link>
          </div>
        </div>
      </header>

      <main>
        <section className="relative" id="product">
          <div className="pointer-events-none absolute -left-40 top-16 h-96 w-96 rounded-full bg-violet-300/25 blur-3xl" />
          <div className="pointer-events-none absolute right-[-10rem] top-20 h-[34rem] w-[34rem] rounded-full bg-indigo-200/30 blur-3xl" />
          <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-5 pb-20 pt-16 sm:px-8 lg:grid-cols-[1.02fr_.98fr] lg:gap-20 lg:pb-28 lg:pt-24">
            <div className="max-w-2xl">
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-3.5 py-2 text-xs font-extrabold uppercase tracking-[0.12em] text-violet-700"><Sparkles className="h-3.5 w-3.5" />{text.badge}</div>
              <h1 className="font-serif text-5xl font-black leading-[.98] tracking-[-0.045em] text-slate-950 sm:text-6xl lg:text-[5.25rem]">{text.title}<span className="block bg-gradient-to-r from-violet-600 via-indigo-600 to-blue-500 bg-clip-text pb-2 text-transparent">{text.titleAccent}</span></h1>
              <p className="mt-7 max-w-xl text-base leading-8 text-slate-600 sm:text-lg">{text.subtitle}</p>
              <div className="mt-9 flex flex-wrap items-center gap-3">
                <Link to="/login" className="inline-flex items-center gap-2 rounded-2xl bg-[#0f172a] px-5 py-3.5 text-sm font-extrabold text-white shadow-[3px_3px_0px_#8b5cf6] transition hover:-translate-y-0.5 hover:bg-slate-800">{text.primary}<ArrowRight className="h-4 w-4" /></Link>
                <a href="#workflow" className="inline-flex items-center gap-2 rounded-2xl border border-slate-300 bg-white px-5 py-3.5 text-sm font-extrabold text-slate-700 transition hover:border-slate-500"><Play className="h-4 w-4 fill-violet-500 text-violet-500" />{text.secondary}</a>
              </div>
              <div className="mt-12 flex items-center gap-3 text-xs font-bold text-slate-500"><div className="flex -space-x-2"><span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-violet-200 text-violet-800">✦</span><span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-indigo-200 text-indigo-800">◒</span><span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-blue-200 text-blue-800">+</span></div><span>{text.trusted}<br /><span className="text-slate-900">{platforms.slice(0, 4).join(' · ')} + more</span></span></div>
            </div>

            <div className="relative mx-auto w-full max-w-[570px] lg:pt-6">
              <div className="absolute -right-2 -top-2 z-10 hidden rounded-2xl border border-violet-200 bg-white px-3.5 py-3 shadow-xl sm:block"><div className="flex items-center gap-2 text-xs font-extrabold text-slate-700"><span className="h-2 w-2 rounded-full bg-emerald-500" />Live signal detected</div><div className="mt-1 text-[11px] text-slate-400">beauty · jakarta · rising now</div></div>
              <div className="relative overflow-hidden rounded-[28px] border border-slate-200 bg-white p-3 shadow-[0_24px_80px_rgba(79,70,229,.16)] sm:p-4">
                <div className="rounded-[20px] bg-[#0f172a] p-4 text-white sm:p-5">
                  <div className="flex items-center justify-between"><div className="flex items-center gap-2 text-xs font-bold text-slate-300"><span className="h-2 w-2 rounded-full bg-violet-400" />Winsta AI workspace</div><span className="rounded-full bg-white/10 px-2.5 py-1 text-[10px] font-bold text-violet-200">Live</span></div>
                  <div className="mt-7 grid grid-cols-3 gap-2"><div className="rounded-2xl bg-white/10 p-3"><div className="text-[10px] text-slate-400">Signals</div><div className="mt-1 text-2xl font-black">128</div><div className="mt-1 text-[10px] font-bold text-emerald-300">↑ 24% this week</div></div><div className="rounded-2xl bg-white/10 p-3"><div className="text-[10px] text-slate-400">Ready to post</div><div className="mt-1 text-2xl font-black">24</div><div className="mt-1 text-[10px] font-bold text-violet-300">Across 6 channels</div></div><div className="rounded-2xl bg-white/10 p-3"><div className="text-[10px] text-slate-400">Avg. score</div><div className="mt-1 text-2xl font-black">8.7</div><div className="mt-1 text-[10px] font-bold text-blue-300">High potential</div></div></div>
                  <div className="mt-4 rounded-2xl bg-white/[.07] p-4"><div className="flex items-center justify-between"><span className="text-xs font-bold text-slate-300">Trend momentum</span><span className="text-[10px] font-bold text-emerald-300">+42.8%</span></div><div className="mt-4 flex h-20 items-end gap-1.5">{[22, 29, 27, 38, 35, 49, 44, 62, 57, 72, 66, 86, 79, 100].map((height, index) => <div key={index} className={`flex-1 rounded-t-md ${index > 9 ? 'bg-violet-400' : 'bg-slate-600'}`} style={{ height: `${height}%` }} />)}</div></div>
                </div>
                <div className="grid gap-3 p-1 pt-4 sm:grid-cols-[1.1fr_.9fr] sm:p-2 sm:pt-4"><div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><div className="flex items-center justify-between"><span className="text-xs font-extrabold text-slate-700">Content queue</span><span className="text-[10px] font-bold text-violet-600">View all</span></div>{['Instagram carousel · Ready', 'TikTok photo · Scheduled', 'Threads post · In review'].map((item, index) => <div key={item} className="mt-3 flex items-center gap-3 rounded-xl bg-white p-2.5 shadow-sm"><span className={`flex h-7 w-7 items-center justify-center rounded-lg ${index === 0 ? 'bg-pink-100 text-pink-600' : index === 1 ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700'}`}><Layers3 className="h-3.5 w-3.5" /></span><span className="min-w-0 flex-1 truncate text-[11px] font-bold text-slate-700">{item.split(' · ')[0]}</span><span className="text-[9px] font-bold text-slate-400">{item.split(' · ')[1]}</span></div>)}</div><div className="rounded-2xl border border-slate-200 p-4"><span className="text-xs font-extrabold text-slate-700">Best channel</span><div className="mt-4 flex items-center gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 text-violet-700"><TrendingUp className="h-5 w-5" /></div><div><div className="text-lg font-black text-slate-900">Instagram</div><div className="text-[10px] font-bold text-emerald-600">+31% engagement</div></div></div><div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full w-[78%] rounded-full bg-gradient-to-r from-violet-500 to-blue-500" /></div></div></div>
              </div>
              <div className="pointer-events-none absolute -bottom-8 -left-8 h-24 w-24 rounded-full border-[14px] border-violet-100/80" />
            </div>
          </div>
        </section>

        <section className="border-y border-slate-200/70 bg-white/60 py-7" aria-label="Supported platforms"><div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-x-7 gap-y-3 px-5 sm:px-8"><span className="mr-2 text-[11px] font-extrabold uppercase tracking-[.14em] text-slate-400">{text.trusted}</span>{platforms.map((platform) => <span key={platform} className="text-sm font-black tracking-tight text-slate-500/80">{platform}</span>)}</div></section>

        <section className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:py-32" id="security"><div className="max-w-2xl"><div className="mb-4 inline-flex items-center gap-2 text-xs font-extrabold uppercase tracking-[.15em] text-violet-600"><Zap className="h-4 w-4" />{text.featureEyebrow}</div><h2 className="font-serif text-4xl font-black tracking-[-.035em] text-slate-950 sm:text-5xl">{text.featureTitle}</h2><p className="mt-5 text-base leading-7 text-slate-600">{text.featureSubtitle}</p></div><div className="mt-14 grid gap-4 md:grid-cols-3">{text.features.map((feature, index) => { const Icon = [TrendingUp, Sparkles, CalendarDays][index]; return <div key={feature.title} className="group rounded-3xl border border-slate-200 bg-white p-7 shadow-[0_8px_30px_rgba(15,23,42,.03)] transition hover:-translate-y-1 hover:border-violet-200 hover:shadow-[0_18px_40px_rgba(99,102,241,.1)]"><div className={`mb-7 flex h-12 w-12 items-center justify-center rounded-2xl ${index === 0 ? 'bg-violet-100 text-violet-700' : index === 1 ? 'bg-indigo-100 text-indigo-700' : 'bg-blue-100 text-blue-700'}`}><Icon className="h-5 w-5" /></div><h3 className="text-lg font-black text-slate-900">{feature.title}</h3><p className="mt-3 text-sm leading-7 text-slate-600">{feature.body}</p><div className="mt-7 flex items-center gap-2 text-xs font-extrabold text-violet-600">Explore capability <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-1" /></div></div>; })}</div></section>

        <section className="relative overflow-hidden bg-[#0f172a]" id="workflow"><div className="pointer-events-none absolute right-0 top-0 h-full w-1/2 bg-[radial-gradient(circle_at_top_right,rgba(139,92,246,.26),transparent_60%)]" /><div className="relative mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:py-28"><div className="max-w-2xl"><div className="mb-4 inline-flex items-center gap-2 text-xs font-extrabold uppercase tracking-[.15em] text-violet-300"><Globe2 className="h-4 w-4" />{text.workflowEyebrow}</div><h2 className="font-serif text-4xl font-black tracking-[-.035em] text-white sm:text-5xl">{text.workflowTitle}</h2><p className="mt-5 text-base leading-7 text-slate-300">{text.workflowSubtitle}</p></div><div className="mt-16 grid gap-10 md:grid-cols-3">{text.steps.map((step, index) => <div key={step.title} className="relative"><div className="mb-6 flex items-center gap-4"><span className="flex h-11 w-11 items-center justify-center rounded-2xl border border-violet-300/40 bg-violet-400/10 text-sm font-black text-violet-200">0{index + 1}</span>{index < 2 && <div className="hidden h-px flex-1 bg-gradient-to-r from-violet-400/50 to-transparent md:block" />}</div><h3 className="text-lg font-black text-white">{step.title}</h3><p className="mt-3 max-w-xs text-sm leading-7 text-slate-400">{step.body}</p></div>)}</div></div></section>

        <section className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:py-28"><div className="relative overflow-hidden rounded-[30px] bg-gradient-to-br from-violet-600 via-indigo-600 to-blue-600 px-7 py-12 text-white shadow-[0_20px_60px_rgba(79,70,229,.25)] sm:px-12 lg:flex lg:items-center lg:justify-between lg:px-16"><div className="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full border-[32px] border-white/10" /><div className="relative max-w-xl"><h2 className="font-serif text-4xl font-black tracking-[-.035em] sm:text-5xl">{text.ctaTitle}</h2><p className="mt-4 text-base leading-7 text-violet-100">{text.ctaBody}</p></div><Link to="/login" className="relative mt-8 inline-flex shrink-0 items-center justify-center gap-2 rounded-2xl bg-white px-5 py-3.5 text-sm font-extrabold text-indigo-700 shadow-lg transition hover:-translate-y-0.5 hover:bg-violet-50 lg:mt-0">{text.ctaButton}<ArrowRight className="h-4 w-4" /></Link></div></section>
      </main>

      <footer className="border-t border-slate-200 bg-white"><div className="mx-auto flex max-w-7xl flex-col gap-5 px-5 py-8 text-xs text-slate-500 sm:px-8 md:flex-row md:items-center md:justify-between"><div><WinstaLogo size="sm" showText /><p className="mt-3 max-w-xs leading-5">{text.footer}</p></div><div className="flex flex-wrap items-center gap-4 font-semibold"><Link to="/privacy" className="hover:text-slate-900">Privacy</Link><Link to="/terms" className="hover:text-slate-900">Terms</Link><Link to="/data-deletion" className="hover:text-slate-900">Data deletion</Link><Link to="/login" className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-2 text-white hover:bg-slate-800">{text.signIn}<ChevronDown className="h-3 w-3 -rotate-90" /></Link></div></div></footer>
    </div>
  );
};
