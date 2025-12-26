"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { ArrowLeft, CheckCircle, XCircle, Loader2, Lock } from "lucide-react";

import { AuthCard } from "@/components/auth/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/ui/form-field";
import { resetPassword } from "@/lib/api/client";
import { resetPasswordSchema, ResetPasswordInput } from "@/lib/validators";

type PageStatus = "loading" | "form" | "success" | "error";

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState<PageStatus>("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const [countdown, setCountdown] = useState(5);

  // Check for token after mount to avoid hydration race condition
  // when clicking links from email clients like Gmail
  useEffect(() => {
    if (token) {
      setStatus("form");
    } else {
      setStatus("error");
      setErrorMessage("Invalid password reset link. No token provided.");
    }
  }, [token]);

  const form = useForm<ResetPasswordInput>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: "",
      confirmPassword: "",
    },
  });

  const onSubmit = async (values: ResetPasswordInput) => {
    if (!token) return;

    try {
      setIsSubmitting(true);
      await resetPassword({
        token,
        password: values.password,
      });
      setStatus("success");
      toast.success("Password reset successfully");

      // Start countdown for redirect
      let count = 5;
      const interval = setInterval(() => {
        count--;
        setCountdown(count);
        if (count === 0) {
          clearInterval(interval);
          router.push("/sign-in");
        }
      }, 1000);
    } catch (error) {
      setStatus("error");
      if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Failed to reset password. The link may have expired.");
      }
      toast.error("Failed to reset password");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="relative flex min-h-screen items-center justify-center px-4 py-16"
      style={{
        backgroundImage: 'url("/background.png")',
        backgroundAttachment: "fixed",
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <div
        className="absolute inset-0 bg-background/60 backdrop-blur-[2px]"
        aria-hidden
      />
      <Link href="/" className="absolute left-6 top-6 z-10">
        <Button
          variant="ghost"
          size="sm"
          className="bg-background/90 backdrop-blur-sm"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Home
        </Button>
      </Link>

      <div className="relative w-full max-w-md">
        {status === "loading" && (
          <div className="rounded-2xl border border-border bg-card/95 p-8 text-center shadow-xl backdrop-blur">
            <Loader2 className="mx-auto h-16 w-16 animate-spin text-primary" />
            <h1 className="mt-6 text-2xl font-semibold">Loading...</h1>
          </div>
        )}

        {status === "success" && (
          <div className="rounded-2xl border border-border bg-card/95 p-8 text-center shadow-xl backdrop-blur">
            <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
            <h1 className="mt-6 text-2xl font-semibold text-green-600">
              Password Reset!
            </h1>
            <p className="mt-2 text-muted-foreground">
              Your password has been reset successfully. You can now log in with
              your new password.
            </p>
            <p className="mt-4 text-sm text-muted-foreground">
              Redirecting to login in {countdown} seconds...
            </p>
            <Button
              className="mt-6 w-full"
              onClick={() => router.push("/sign-in")}
            >
              Go to Login Now
            </Button>
          </div>
        )}

        {status === "error" && (
          <div className="rounded-2xl border border-border bg-card/95 p-8 text-center shadow-xl backdrop-blur">
            <XCircle className="mx-auto h-16 w-16 text-red-500" />
            <h1 className="mt-6 text-2xl font-semibold text-red-600">
              Reset Failed
            </h1>
            <p className="mt-2 text-muted-foreground">{errorMessage}</p>
            <div className="mt-6 space-y-3">
              <Link href="/forgot-password">
                <Button className="w-full" variant="outline">
                  Request New Reset Link
                </Button>
              </Link>
              <Link href="/sign-in">
                <Button className="w-full">Go to Login</Button>
              </Link>
            </div>
          </div>
        )}

        {status === "form" && (
          <AuthCard
            title="Reset your password"
            subtitle="Enter your new password below."
            footerHint="Remember your password?"
            footerActionLabel="Sign in"
            footerActionHref="/sign-in"
            className="bg-background/90 backdrop-blur"
          >
            <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
              <FormField
                id="password"
                label="New password"
                error={form.formState.errors.password?.message}
                required
              >
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    placeholder="Enter new password"
                    className="pl-10"
                    {...form.register("password")}
                  />
                </div>
              </FormField>
              <FormField
                id="confirmPassword"
                label="Confirm password"
                error={form.formState.errors.confirmPassword?.message}
                required
              >
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="confirmPassword"
                    type="password"
                    autoComplete="new-password"
                    placeholder="Confirm new password"
                    className="pl-10"
                    {...form.register("confirmPassword")}
                  />
                </div>
              </FormField>
              <p className="text-xs text-muted-foreground">
                Password must be at least 8 characters and include a letter,
                number, and special character.
              </p>
              <Button type="submit" className="w-full" isLoading={isSubmitting}>
                Reset Password
              </Button>
            </form>
          </AuthCard>
        )}
      </div>
    </div>
  );
}

function ResetPasswordFallback() {
  return (
    <div
      className="relative flex min-h-screen items-center justify-center px-4 py-16"
      style={{
        backgroundImage: 'url("/background.png")',
        backgroundAttachment: "fixed",
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <div
        className="absolute inset-0 bg-background/60 backdrop-blur-[2px]"
        aria-hidden
      />
      <div className="relative w-full max-w-md">
        <div className="rounded-2xl border border-border bg-card/95 p-8 text-center shadow-xl backdrop-blur">
          <Loader2 className="mx-auto h-16 w-16 animate-spin text-primary" />
          <h1 className="mt-6 text-2xl font-semibold">Loading...</h1>
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<ResetPasswordFallback />}>
      <ResetPasswordContent />
    </Suspense>
  );
}
