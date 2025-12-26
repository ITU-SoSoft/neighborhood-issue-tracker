"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { CheckCircle, ArrowLeft, Loader2 } from "lucide-react";

import { AuthCard } from "@/components/auth/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/ui/form-field";
import { Skeleton } from "@/components/ui/skeleton";
import { setPassword } from "@/lib/api/client";

const setPasswordSchema = z
  .object({
    phone_number: z
      .string()
      .min(1, "Phone number is required")
      .regex(
        /^(\+90|0)?[0-9\s-]{10,}$/,
        "Please enter a valid Turkish phone number",
      ),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Za-z]/, "Password must contain at least one letter")
      .regex(/\d/, "Password must contain at least one number")
      .regex(
        /[!@#$%^&*(),.?":{}|<>]/,
        "Password must contain at least one special character",
      ),
    confirmPassword: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type SetPasswordInput = z.infer<typeof setPasswordSchema>;

function SetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [hasToken, setHasToken] = useState(false);
  const [countdown, setCountdown] = useState(5);

  const form = useForm<SetPasswordInput>({
    resolver: zodResolver(setPasswordSchema),
    defaultValues: {
      phone_number: "",
      password: "",
      confirmPassword: "",
    },
  });

  // Check for token after mount to avoid hydration race condition
  // when clicking links from email clients like Gmail
  useEffect(() => {
    if (token) {
      setHasToken(true);
    }
    setIsLoading(false);
  }, [token]);

  useEffect(() => {
    if (isSuccess && countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else if (isSuccess && countdown === 0) {
      router.push("/staff");
    }
  }, [isSuccess, countdown, router]);

  // Show loading while checking for token
  if (isLoading) {
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

  if (!hasToken) {
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
            <h1 className="text-2xl font-semibold text-red-600">
              Invalid Link
            </h1>
            <p className="mt-2 text-muted-foreground">
              This invite link is invalid or has expired. Please contact your
              manager for a new invite.
            </p>
            <Button className="mt-6 w-full" onClick={() => router.push("/")}>
              Go to Home
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (isSuccess) {
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
            <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
            <h1 className="mt-6 text-2xl font-semibold text-green-600">
              Password Set Successfully!
            </h1>
            <p className="mt-2 text-muted-foreground">
              Your account is now active. You can log in with your email and
              password.
            </p>
            <p className="mt-4 text-sm text-muted-foreground">
              Redirecting to login in {countdown} seconds...
            </p>
            <Button
              className="mt-6 w-full"
              onClick={() => router.push("/staff")}
            >
              Go to Staff Login Now
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const onSubmit = async (values: SetPasswordInput) => {
    if (!token) return;

    try {
      setIsSubmitting(true);

      // Normalize phone number to +90 format
      let phoneNumber = values.phone_number.replace(/[\s-]/g, "");
      if (phoneNumber.startsWith("0")) {
        phoneNumber = "+90" + phoneNumber.slice(1);
      } else if (!phoneNumber.startsWith("+")) {
        phoneNumber = "+90" + phoneNumber;
      }

      await setPassword({
        token,
        phone_number: phoneNumber,
        password: values.password,
      });

      toast.success("Password set successfully!");
      setIsSuccess(true);
    } catch (error) {
      if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error("Failed to set password. Please try again.");
      }
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
      <div className="relative grid w-full max-w-6xl items-center gap-12 lg:grid-cols-[1.1fr_1fr]">
        <div className="space-y-8 rounded-4xl border border-border bg-card/95 p-10 text-foreground shadow-xl backdrop-blur">
          <p className="text-sm font-semibold uppercase tracking-wide text-primary">
            Welcome to the team
          </p>
          <h1 className="text-4xl font-semibold leading-snug lg:text-5xl">
            Set up your account to get started.
          </h1>
          <p className="text-base text-foreground/80">
            You&apos;ve been invited to join Sosoft as a staff member. Complete
            your account setup by verifying your phone number and creating a
            password.
          </p>
          <ul className="space-y-3 text-sm text-foreground/75">
            <li>Enter the phone number your manager registered for you.</li>
            <li>Create a secure password for your account.</li>
            <li>Start helping your community right away.</li>
          </ul>
        </div>

        <AuthCard
          title="Set Your Password"
          subtitle="Enter your phone number and create a password to activate your account."
          className="bg-background/90 backdrop-blur"
        >
          <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
            <FormField
              id="phone_number"
              label="Phone Number"
              error={form.formState.errors.phone_number?.message}
              required
            >
              <Input
                id="phone_number"
                type="tel"
                autoComplete="tel"
                placeholder="+90 555 123 4567"
                {...form.register("phone_number")}
              />
            </FormField>
            <FormField
              id="password"
              label="Password"
              error={form.formState.errors.password?.message}
              required
            >
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                placeholder="Create a strong password"
                {...form.register("password")}
              />
            </FormField>
            <FormField
              id="confirmPassword"
              label="Confirm Password"
              error={form.formState.errors.confirmPassword?.message}
              required
            >
              <Input
                id="confirmPassword"
                type="password"
                autoComplete="new-password"
                placeholder="Confirm your password"
                {...form.register("confirmPassword")}
              />
            </FormField>
            <p className="text-xs text-muted-foreground">
              Password must be at least 8 characters and include a letter,
              number, and special character.
            </p>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Setting Password...
                </>
              ) : (
                "Set Password & Activate Account"
              )}
            </Button>
          </form>
        </AuthCard>
      </div>
    </div>
  );
}

function SetPasswordFormFallback() {
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
      <div className="relative grid w-full max-w-6xl items-center gap-12 lg:grid-cols-[1.1fr_1fr]">
        <div className="space-y-8 rounded-4xl border border-primary/20 bg-primary/10 p-10 backdrop-blur">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
        <AuthCard
          title="Set Your Password"
          subtitle="Enter your phone number and create a password to activate your account."
          className="bg-background/90 backdrop-blur"
        >
          <div className="space-y-4">
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-10 w-full" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-10 w-full" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-10 w-full" />
            </div>
            <Skeleton className="h-10 w-full" />
          </div>
        </AuthCard>
      </div>
    </div>
  );
}

export default function SetPasswordPage() {
  return (
    <Suspense fallback={<SetPasswordFormFallback />}>
      <SetPasswordForm />
    </Suspense>
  );
}
