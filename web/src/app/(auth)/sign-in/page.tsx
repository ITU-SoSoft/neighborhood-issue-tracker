"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { AuthCard } from "@/components/auth/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { signInRequest } from "@/lib/api/auth";
import { SignInInput, signInSchema } from "@/lib/validators/auth";

export default function SignInPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const form = useForm<SignInInput>({
    resolver: zodResolver(signInSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values: SignInInput) => {
    try {
      setIsSubmitting(true);
      setErrorMessage(null);
      setSuccessMessage(null);

      const response = await signInRequest(values);
      setSuccessMessage("Signed in successfully.");

      const callbackUrl = searchParams.get("callbackUrl");
      router.push(response.redirectTo ?? callbackUrl ?? "/issues");
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Unable to sign in. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="relative flex min-h-screen items-center justify-center px-4 py-16"
      style={{
        backgroundImage: 'url("/auth-bg.png")',
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <div className="absolute inset-0 bg-slate-950/70" aria-hidden />
      <div className="relative grid w-full max-w-6xl items-center gap-12 lg:grid-cols-[1.1fr_1fr]">
        <div className="space-y-8 rounded-4xl border border-emerald-200/80 bg-emerald-100/75 p-10 text-slate-900 shadow-xl shadow-emerald-100/45 backdrop-blur">
          <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">
            Welcome back
          </p>
          <h1 className="text-4xl font-semibold leading-snug text-emerald-900 lg:text-5xl">
            Stay in sync with what matters in your neighborhood.
          </h1>
          <p className="text-base text-emerald-900/80">
            Track the issues you care about, receive real-time updates from municipal teams, and work with neighbors to
            resolve problems faster.
          </p>
          <ul className="space-y-3 text-sm text-emerald-900/75">
            <li>• Report new issues in seconds.</li>
            <li>• Keep track of issues you care about.</li>
            <li>• Coordinate volunteer efforts and community responses seamlessly.</li>
          </ul>
          <div className="rounded-3xl border border-emerald-200/70 bg-emerald-50/85 p-6">
            <p className="text-sm font-medium text-emerald-700">New to the platform?</p>
            <p className="mt-2 text-sm text-emerald-900/75">
              Create an account to access collaborative reporting tools and invite your neighbors to join you.
            </p>
            <Link
              href="/sign-up"
              className="mt-4 inline-flex items-center justify-center rounded-full bg-emerald-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
            >
              Create a free account
            </Link>
          </div>
        </div>

        <AuthCard
          title="Sign in"
          subtitle="Enter your credentials to access your dashboard."
          footerHint="Do not have an account yet?"
          footerActionLabel="Create one now"
          footerActionHref="/sign-up"
          className="bg-white/90 backdrop-blur"
        >
          <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
            <div className="space-y-1.5">
              <label htmlFor="email" className="text-sm font-medium text-slate-700">
                Email address
              </label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                {...form.register("email")}
              />
              {form.formState.errors.email && (
                <p className="text-sm text-red-600">{form.formState.errors.email.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <label htmlFor="password" className="text-sm font-medium text-slate-700">
                Password
              </label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="Enter your password"
                {...form.register("password")}
              />
              {form.formState.errors.password && (
                <p className="text-sm text-red-600">{form.formState.errors.password.message}</p>
              )}
            </div>
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 text-slate-600">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border border-slate-300 text-emerald-600 focus:ring-emerald-400"
                />
                Remember me
              </label>
              <Link href="/forgot-password" className="font-semibold text-emerald-600 hover:text-emerald-700">
                Forgot password?
              </Link>
            </div>
            {errorMessage ? (
              <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-600">
                {errorMessage}
              </div>
            ) : null}
            {successMessage ? (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
                {successMessage}
              </div>
            ) : null}
            <Button type="submit" className="w-full" isLoading={isSubmitting}>
              Sign in
            </Button>
          </form>
        </AuthCard>
      </div>
    </div>
  );
}


