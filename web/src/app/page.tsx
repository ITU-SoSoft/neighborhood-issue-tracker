export default function Home() {
  return (
    <div className="relative min-h-screen overflow-hidden text-slate-900">
      <div
        className="fixed inset-0 -z-20 bg-[url('/auth-bg.png')] bg-cover bg-center"
        style={{ backgroundAttachment: "fixed" }}
        aria-hidden
      />
      <div className="fixed inset-0 -z-10 bg-white/60 backdrop-blur-[2px]" aria-hidden />

      <header className="relative flex w-full items-center justify-between px-6 py-6 sm:px-12">
        <div className="flex items-center gap-3 text-lg font-semibold rounded-full bg-slate-50/80 px-4 py-2 shadow-lg shadow-emerald-100/40 backdrop-blur-sm">
          <span className="grid h-10 w-10 place-content-center rounded-full bg-emerald-500 text-white">
            NT
          </span>
          Neighborhood Issue Tracker
        </div>
        <nav className="hidden items-center gap-4 rounded-full bg-slate-50/80 px-6 py-3 text-sm font-medium text-slate-700 shadow-lg shadow-emerald-100/40 backdrop-blur-sm md:flex">
          <a href="#features" className="rounded-full px-3 py-1 transition hover:bg-emerald-100 hover:text-emerald-600">
            Features
          </a>
          <a href="#how-it-works" className="rounded-full px-3 py-1 transition hover:bg-emerald-100 hover:text-emerald-600">
            How it works
          </a>
          <a href="#contact" className="rounded-full px-3 py-1 transition hover:bg-emerald-100 hover:text-emerald-600">
            Contact
          </a>
          <a
            href="/sign-in"
            className="rounded-full border border-emerald-500 px-4 py-1.5 text-emerald-600 transition hover:bg-emerald-500 hover:text-white"
          >
            Sign in
          </a>
          <a
            href="/sign-up"
            className="rounded-full bg-emerald-600 px-4 py-1.5 text-white transition hover:bg-emerald-700"
          >
            Create account
          </a>
        </nav>
      </header>

      <main className="relative">
        <section className="mx-auto flex min-h-[70vh] max-w-5xl flex-col gap-8 px-6 pb-24 pt-20 sm:px-12">
          <div className="space-y-6 rounded-[2.5rem] border border-emerald-200/80 bg-emerald-100/85 p-10 shadow-xl shadow-emerald-100/50 backdrop-blur-sm">
            <span className="inline-flex w-fit items-center rounded-full bg-emerald-200/90 px-4 py-1 text-sm font-medium text-emerald-800 shadow">
              Community-powered reporting
            </span>
            <h1 className="text-4xl font-semibold leading-tight text-slate-900 sm:text-5xl">
              Spot an issue in your neighborhood? Report it in seconds and work with your community to get it fixed.
            </h1>
            <p className="text-lg text-slate-700">
              Neighborhood Issue Tracker helps residents capture local problems — from flooding to street light outages —
              and share them with the right teams. Track progress, collaborate with neighbors, and celebrate resolutions
              together.
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
                className="inline-flex items-center justify-center rounded-full border border-emerald-400 px-6 py-3 text-base font-semibold text-emerald-600 transition hover:bg-emerald-500 hover:text-white"
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
              description:
                "Pin the exact location, add photos, and describe the issue so teams can respond faster.",
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
            <div
              key={feature.title}
              className="rounded-3xl border border-emerald-200/80 bg-emerald-100/75 p-6 shadow-lg shadow-emerald-100/45 backdrop-blur-sm"
            >
              <h3 className="text-lg font-semibold text-slate-900">{feature.title}</h3>
              <p className="mt-3 text-sm text-slate-600">{feature.description}</p>
            </div>
          ))}
        </section>

        <section
          id="how-it-works"
          className="mx-auto max-w-5xl px-6 pb-24 sm:px-12"
        >
          <div className="rounded-[2.5rem] border border-emerald-200/80 bg-emerald-100/75 p-10 shadow-xl shadow-emerald-100/50 backdrop-blur-sm">
            <div className="flex flex-col gap-8 sm:flex-row">
              <div className="sm:w-1/3">
                <h2 className="text-3xl font-semibold text-slate-900">How it works</h2>
                <p className="mt-3 text-sm text-slate-600">
                  Three simple steps to make your neighborhood safer and more livable.
                </p>
              </div>
              <ol className="flex flex-1 flex-col gap-6">
                {[
                  {
                    step: "01",
                    title: "Report the issue",
                    description:
                      "Locate the problem, add a quick note, and submit your report in under a minute.",
                  },
                  {
                    step: "02",
                    title: "Share with your community",
                    description:
                      "Neighbors can upvote and comment, helping municipal teams understand urgency and context.",
                  },
                  {
                    step: "03",
                    title: "Track the resolution",
                    description:
                      "Receive updates as the issue progresses from acknowledgment to resolution and closure.",
                  },
                ].map((item) => (
                  <li
                    key={item.step}
                    className="rounded-3xl border border-emerald-100 bg-emerald-50/80 p-6 shadow-lg shadow-emerald-100/35 backdrop-blur-sm"
                  >
                    <span className="text-sm font-semibold uppercase tracking-wide text-emerald-700">
                      {item.step}
                    </span>
                    <h3 className="mt-2 text-lg font-semibold text-slate-900">{item.title}</h3>
                    <p className="mt-2 text-sm text-slate-600">{item.description}</p>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </section>
      </main>

      <footer
        id="contact"
        className="relative border-t border-white/40 bg-slate-50/85 px-6 py-6 text-sm text-slate-600 backdrop-blur-sm sm:px-12"
      >
        <div className="mx-auto flex max-w-5xl flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <p>
            &copy; {new Date().getFullYear()} Neighborhood Issue Tracker. All rights reserved.
          </p>
          <div className="flex gap-4">
            <a href="/privacy" className="transition hover:text-emerald-600">
              Privacy
            </a>
            <a href="/terms" className="transition hover:text-emerald-600">
              Terms
            </a>
            <a href="/contact" className="transition hover:text-emerald-600">
              Contact
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
