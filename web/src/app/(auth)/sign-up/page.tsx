"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { AuthCard } from "@/components/auth/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { signUpRequest } from "@/lib/api/auth";
import { SignUpInput, signUpSchema } from "@/lib/validators/auth";

export default function SignUpPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const form = useForm<SignUpInput>({
    resolver: zodResolver(signUpSchema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  const onSubmit = async (values: SignUpInput) => {
    try {
      setIsSubmitting(true);
      setErrorMessage(null);
      setSuccessMessage(null);

      const response = await signUpRequest(values);
      setSuccessMessage("Account created successfully.");
      router.push(response.redirectTo ?? "/sign-in");
    } catch (error) {
      if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Unable to create account. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const authBaseUrl =
    process.env.NEXT_PUBLIC_AUTH_BASE_URL?.replace(/\/$/, "") ?? "/api/auth";

  const handleGoogleSignUp = () => {
    window.location.href = `${authBaseUrl}/google`;
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
      <AuthCard
        title="Create an account"
        subtitle="Join the platform and start reporting issues with your community."
        footerHint="Already have an account?"
        footerActionLabel="Sign in"
        footerActionHref="/sign-in"
        className="relative mx-auto bg-white/90 backdrop-blur"
      >
        <div className="space-y-3">
          <button
            type="button"
            onClick={handleGoogleSignUp}
            className="flex w-full items-center justify-center gap-3 rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-emerald-300 hover:text-emerald-600 focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500"
          >
            <span className="inline-flex h-5 w-5 items-center justify-center">
              <svg viewBox="0 0 24 24" aria-hidden="true" className="h-5 w-5">
                <path
                  d="M23.04 12.2615C23.04 11.4459 22.9669 10.661 22.8304 9.90771H12V14.3568H18.1896C17.9225 15.7957 17.1578 17.0003 15.9532 17.8084V20.713H19.764C21.9304 18.711 23.04 15.7638 23.04 12.2615Z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23.5C15.1056 23.5 17.7088 22.4634 19.764 20.713L15.9532 17.8084C14.8425 18.5551 13.4891 18.9945 12 18.9945C9.01144 18.9945 6.46972 16.9726 5.56744 14.2471H1.63248V17.2453C3.67656 21.0215 7.53464 23.5 12 23.5Z"
                  fill="#34A853"
                />
                <path
                  d="M5.56746 14.2471C5.33335 13.5004 5.19981 12.7051 5.19981 11.8841C5.19981 11.063 5.33335 10.2678 5.56746 9.52106V6.52289H1.6325C0.775625 8.07484 0.319824 9.92271 0.319824 11.8841C0.319824 13.8455 0.775625 15.6933 1.6325 17.2452L5.56746 14.2471Z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 4.77342C13.6359 4.77342 15.0966 5.33827 16.26 6.44268L19.845 2.85776C17.7056 0.880518 15.1024 -0.15625 12 -0.15625C7.53464 -0.15625 3.67656 2.32222 1.63248 6.09841L5.56744 9.09658C6.46972 6.37114 9.01144 4.34924 12 4.34924V4.77342Z"
                  fill="#EA4335"
                />
              </svg>
            </span>
            Continue with Google
          </button>
          <div className="flex items-center gap-4 text-xs uppercase tracking-[0.2em] text-slate-400">
            <span className="h-px flex-1 bg-slate-200" />
            or
            <span className="h-px flex-1 bg-slate-200" />
          </div>
        </div>
        <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
          <div className="space-y-1.5">
            <label htmlFor="name" className="text-sm font-medium text-slate-700">
              Full name
            </label>
            <Input id="name" autoComplete="name" placeholder="Ada Lovelace" {...form.register("name")} />
            {form.formState.errors.name && (
              <p className="text-sm text-red-600">{form.formState.errors.name.message}</p>
            )}
          </div>
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
              autoComplete="new-password"
              placeholder="Create a strong password"
              {...form.register("password")}
            />
            {form.formState.errors.password && (
              <p className="text-sm text-red-600">{form.formState.errors.password.message}</p>
            )}
          </div>
          <div className="space-y-1.5">
            <label htmlFor="confirmPassword" className="text-sm font-medium text-slate-700">
              Confirm password
            </label>
            <Input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              placeholder="Re-enter your password"
              {...form.register("confirmPassword")}
            />
            {form.formState.errors.confirmPassword && (
              <p className="text-sm text-red-600">{form.formState.errors.confirmPassword.message}</p>
            )}
          </div>
          <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-500">
            <p>
              By creating an account you agree to our{" "}
              <Link href="/terms" className="font-semibold text-emerald-600 hover:text-emerald-700">
                terms of service
              </Link>{" "}
              and{" "}
              <Link href="/privacy" className="font-semibold text-emerald-600 hover:text-emerald-700">
                privacy policy
              </Link>
              .
            </p>
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
            Create account
          </Button>
        </form>
      </AuthCard>
    </div>
  );
}


