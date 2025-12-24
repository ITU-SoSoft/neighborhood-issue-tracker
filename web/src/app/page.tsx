"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Phone } from "lucide-react";

export default function Home() {
  const [showContactModal, setShowContactModal] = useState(false);

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* ARKA PLAN: İstanbul Görseli */}
      <div
        className="fixed inset-0 -z-20 bg-[url('/background.png')] bg-cover bg-center"
        style={{ backgroundAttachment: "fixed" }}
        aria-hidden
      />
      {/* KARARTMA: Yazıların okunması için Dashboard temasıyla uyumlu overlay */}
      <div className="fixed inset-0 -z-10 bg-background/60 backdrop-blur-[2px]" aria-hidden />

      <header className="relative flex w-full items-center justify-between px-6 py-6 sm:px-12">
        <div className="flex items-center gap-3 text-lg font-semibold rounded-full bg-background/95 backdrop-blur-md px-4 py-2 shadow-lg border border-border">
          <span className="grid h-10 w-10 place-content-center rounded-full bg-primary text-primary-foreground">
            NT
          </span>
          <span className="text-foreground">Neighborhood Issue Tracker</span>
        </div>
        <nav className="hidden items-center gap-4 rounded-full bg-background/95 backdrop-blur-md px-6 py-3 text-sm font-medium shadow-lg border border-border md:flex">
          <a href="#features" className="rounded-full px-3 py-1 transition hover:bg-muted text-muted-foreground">
            Features
          </a>
          <a href="#how-it-works" className="rounded-full px-3 py-1 transition hover:bg-muted text-muted-foreground">
            How it works
          </a>
          <button
            onClick={() => setShowContactModal(true)}
            className="rounded-full px-3 py-1 transition hover:bg-muted text-muted-foreground"
          >
            Contact
          </button>
          <a
            href="/sign-in"
            className="rounded-full border border-primary px-4 py-1.5 text-primary transition hover:bg-primary hover:text-primary-foreground"
          >
            Sign in
          </a>
          <a
            href="/sign-up"
            className="rounded-full bg-primary px-4 py-1.5 text-primary-foreground transition hover:bg-primary/90 shadow-md"
          >
            Create account
          </a>
        </nav>
      </header>

      <main className="relative">
        <section className="mx-auto flex min-h-[70vh] max-w-5xl flex-col gap-8 px-6 pb-24 pt-20 sm:px-12">
          <div className="space-y-6 rounded-[2.5rem] border border-border bg-card/95 backdrop-blur-xl p-10 shadow-2xl">
            <span className="inline-flex w-fit items-center rounded-full bg-primary/10 px-4 py-1 text-sm font-medium text-primary border border-primary/20">
              Community-powered reporting
            </span>
            <h1 className="text-4xl font-bold leading-tight text-foreground sm:text-5xl">
              Spot an issue in your neighborhood? <br />
              <span className="text-primary">Report it in seconds</span> and work with your community.
            </h1>
            <p className="text-lg text-muted-foreground">
              Neighborhood Issue Tracker helps residents capture local problems — from flooding to street light outages —
              and share them with the right teams.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row">
              <a
                href="/sign-up"
                className="inline-flex items-center justify-center rounded-full bg-primary px-6 py-3 text-base font-semibold text-primary-foreground transition hover:bg-primary/90"
              >
                Get started
              </a>
              <a
                href="#features"
                className="inline-flex items-center justify-center rounded-full border border-primary px-6 py-3 text-base font-semibold text-primary transition hover:bg-primary hover:text-primary-foreground"
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
            <div
              key={feature.title}
              className="rounded-3xl border border-border bg-card/95 backdrop-blur-md p-6 shadow-xl hover:border-primary/30 transition-all group"
            >
              <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">{feature.title}</h3>
              <p className="mt-3 text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </section>

        <section id="how-it-works" className="mx-auto max-w-5xl px-6 pb-24 sm:px-12">
          <div className="rounded-[2.5rem] border border-border bg-card/95 p-10 shadow-2xl backdrop-blur-md">
            <div className="flex flex-col gap-8 sm:flex-row">
              <div className="sm:w-1/3">
                <h2 className="text-3xl font-bold text-foreground">How it works</h2>
                <p className="mt-3 text-sm text-muted-foreground">
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
                    className="rounded-3xl border border-border bg-muted/50 p-6"
                  >
                    <span className="text-sm font-bold uppercase tracking-widest text-primary">
                      Step {item.step}
                    </span>
                    <h3 className="mt-2 text-lg font-semibold text-foreground">{item.title}</h3>
                    <p className="mt-2 text-sm text-muted-foreground">{item.description}</p>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </section>
      </main>

      <footer id="contact" className="relative border-t border-border bg-background/95 backdrop-blur-md px-6 py-8 text-sm text-muted-foreground sm:px-12">
        <div className="mx-auto flex max-w-5xl items-center justify-center">
          <p>&copy; {new Date().getFullYear()} Neighborhood Issue Tracker.</p>
        </div>
      </footer>

      {/* Contact Modal */}
      <Dialog open={showContactModal} onOpenChange={setShowContactModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold flex items-center gap-2">
              <Phone className="h-6 w-6 text-primary" />
              Contact Us
            </DialogTitle>
            <DialogDescription>
              Get in touch with our support team
            </DialogDescription>
          </DialogHeader>
          <div className="py-6">
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 rounded-lg bg-muted border border-border">
                <Phone className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">Phone Number</p>
                  <p className="text-lg font-semibold text-foreground">+90 555 123 4567</p>
                </div>
              </div>
              <p className="text-sm text-muted-foreground text-center">
                Our support team is available Monday to Friday, 9:00 AM - 6:00 PM
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}