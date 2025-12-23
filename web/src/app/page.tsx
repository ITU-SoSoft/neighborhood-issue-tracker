"use client";

export default function Home() {
  return (
    <div className="relative min-h-screen overflow-hidden text-slate-100">
      {/* ARKA PLAN: İstanbul Görseli */}
      <div
        className="fixed inset-0 -z-20 bg-[url('https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&q=80&w=2000')] bg-cover bg-center"
        style={{ backgroundAttachment: "fixed" }}
        aria-hidden
      />
      {/* KARARTMA: Yazıların okunması için Dashboard temasıyla uyumlu overlay */}
      <div className="fixed inset-0 -z-10 bg-slate-950/70 backdrop-blur-[2px]" aria-hidden />

      <header className="relative flex w-full items-center justify-between px-6 py-6 sm:px-12">
        <div className="flex items-center gap-3 text-lg font-semibold rounded-full bg-slate-900/60 px-4 py-2 shadow-lg backdrop-blur-md border border-white/10">
          {/* BUTON YEŞİLİ KORUNDU */}
          <span className="grid h-10 w-10 place-content-center rounded-full bg-emerald-500 text-white">
            NT
          </span>
          <span className="text-white">Neighborhood Issue Tracker</span>
        </div>
        <nav className="hidden items-center gap-4 rounded-full bg-slate-900/60 px-6 py-3 text-sm font-medium shadow-lg backdrop-blur-md border border-white/10 md:flex">
          <a href="#features" className="rounded-full px-3 py-1 transition hover:bg-white/10 text-slate-300">
            Features
          </a>
          <a href="#how-it-works" className="rounded-full px-3 py-1 transition hover:bg-white/10 text-slate-300">
            How it works
          </a>
          <a href="#contact" className="rounded-full px-3 py-1 transition hover:bg-white/10 text-slate-300">
            Contact
          </a>
          {/* BUTON YEŞİLİ KORUNDU */}
          <a
            href="/sign-in"
            className="rounded-full border border-emerald-500 px-4 py-1.5 text-emerald-400 transition hover:bg-emerald-500 hover:text-white"
          >
            Sign in
          </a>
          <a
            href="/sign-up"
            className="rounded-full bg-emerald-600 px-4 py-1.5 text-white transition hover:bg-emerald-700 shadow-md"
          >
            Create account
          </a>
        </nav>
      </header>

      <main className="relative">
        <section className="mx-auto flex min-h-[70vh] max-w-5xl flex-col gap-8 px-6 pb-24 pt-20 sm:px-12">
          {/* YEŞİL YERİNE LACİVERT (image_352fec'teki gibi) */}
          <div className="space-y-6 rounded-[2.5rem] border border-white/10 bg-slate-900/80 p-10 shadow-2xl backdrop-blur-xl">
            <span className="inline-flex w-fit items-center rounded-full bg-emerald-500/10 px-4 py-1 text-sm font-medium text-emerald-400 border border-emerald-500/20">
              Community-powered reporting
            </span>
            <h1 className="text-4xl font-bold leading-tight text-white sm:text-5xl">
              Spot an issue in your neighborhood? <br />
              <span className="text-emerald-400">Report it in seconds</span> and work with your community.
            </h1>
            <p className="text-lg text-slate-300">
              Neighborhood Issue Tracker helps residents capture local problems — from flooding to street light outages —
              and share them with the right teams.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row">
              <a
                href="/sign-up"
                className="inline-flex items-center justify-center rounded-full bg-emerald-600 px-6 py-3 text-base font-semibold text-white transition hover:bg-emerald-700"
              >
                Get started
              </a>
              <a
                href="#features"
                className="inline-flex items-center justify-center rounded-full border border-emerald-400 px-6 py-3 text-base font-semibold text-emerald-400 transition hover:bg-emerald-500 hover:text-white"
              >
                Explore features
              </a>
            </div>
          </div>
        </section>

        <section
          id="features"
          className="mx-auto grid max-w-5xl gap-6 px-6 pb-24 sm:grid-cols-3 sm:px-12"
        >
          {[
            {
              title: "Map-based reporting",
              description: "Pin the exact location, add photos, and describe the issue so teams can respond faster.",
            },
            {
              title: "Real-time status",
              description: "Follow updates from municipal teams and stay informed about every action taken.",
            },
            {
              title: "Community collaboration",
              description: "Upvote issues, share feedback, and help prioritize what needs attention first.",
            },
          ].map((feature) => (
            /* KARTLARDA LACİVERT TEMA UYGULANDI */
            <div
              key={feature.title}
              className="rounded-3xl border border-white/10 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md hover:border-emerald-500/30 transition-all group"
            >
              <h3 className="text-lg font-semibold text-white group-hover:text-emerald-400 transition-colors">{feature.title}</h3>
              <p className="mt-3 text-sm text-slate-400 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </section>

        <section id="how-it-works" className="mx-auto max-w-5xl px-6 pb-24 sm:px-12">
          {/* LACİVERT/BLUE-950 TEMA */}
          <div className="rounded-[2.5rem] border border-white/10 bg-slate-900/60 p-10 shadow-2xl backdrop-blur-md">
            <div className="flex flex-col gap-8 sm:flex-row">
              <div className="sm:w-1/3">
                <h2 className="text-3xl font-bold text-white">How it works</h2>
                <p className="mt-3 text-sm text-slate-400">
                  Three simple steps to make your neighborhood safer and more livable.
                </p>
              </div>
              <ol className="flex flex-1 flex-col gap-6">
                {[
                  { step: "01", title: "Report the issue", description: "Locate the problem, add a note, and submit in under a minute." },
                  { step: "02", title: "Internal Processing", description: "Municipal support teams receive, analyze, and assign your ticket." },
                  { step: "03", title: "Track & Review", description: "See when it's resolved, check before/after photos, and rate the service." },
                ].map((item) => (
                  <li
                    key={item.step}
                    className="rounded-3xl border border-white/5 bg-slate-800/40 p-6 backdrop-blur-sm"
                  >
                    <span className="text-sm font-bold uppercase tracking-widest text-emerald-400">
                      Step {item.step}
                    </span>
                    <h3 className="mt-2 text-lg font-semibold text-white">{item.title}</h3>
                    <p className="mt-2 text-sm text-slate-400">{item.description}</p>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </section>
      </main>

      <footer id="contact" className="relative border-t border-white/10 bg-slate-950/90 px-6 py-8 text-sm text-slate-500 backdrop-blur-md sm:px-12">
        <div className="mx-auto flex max-w-5xl flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <p>&copy; {new Date().getFullYear()} Neighborhood Issue Tracker.</p>
          <div className="flex gap-6">
            <a href="/privacy" className="transition hover:text-emerald-400 text-slate-400">Privacy</a>
            <a href="/terms" className="transition hover:text-emerald-400 text-slate-400">Terms</a>
            <a href="/contact" className="transition hover:text-emerald-400 text-emerald-500 font-medium">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}