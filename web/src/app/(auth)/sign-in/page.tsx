"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { AuthCard } from "@/components/auth/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/ui/form-field";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft } from "lucide-react";
import { login } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/context";
import { LoginInput, loginSchema } from "@/lib/validators";

function SignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login: authLogin } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values: LoginInput) => {
    try {
      setIsSubmitting(true);

      const response = await login(values);
      await authLogin(response.access_token, response.refresh_token);
      
      toast.success("Signed in successfully");

      const callbackUrl = searchParams.get("callbackUrl");
      router.push(callbackUrl ?? "/dashboard");
    } catch (error) {
      if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error("Unable to sign in. Please try again.");
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
      <div className="absolute inset-0 bg-background/60 backdrop-blur-[2px]" aria-hidden />
      <Link
        href="/"
        className="absolute left-6 top-6 z-10"
      >
        <Button variant="ghost" size="sm" className="bg-background/90 backdrop-blur-sm">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Home
        </Button>
      </Link>
      <div className="relative grid w-full max-w-6xl items-center gap-12 lg:grid-cols-[1.1fr_1fr]">
        <div className="space-y-8 rounded-4xl border border-border bg-card/95 p-10 text-foreground shadow-xl backdrop-blur">
          <p className="text-sm font-semibold uppercase tracking-wide text-primary">
            Welcome back
          </p>
          <h1 className="text-4xl font-semibold leading-snug lg:text-5xl">
            Stay in sync with what matters in your neighborhood.
          </h1>
          <p className="text-base text-foreground/80">
            Track the issues you care about, receive real-time updates from municipal teams, and work with neighbors to
            resolve problems faster.
          </p>
          <ul className="space-y-3 text-sm text-foreground/75">
            <li>Report new issues in seconds.</li>
            <li>Keep track of issues you care about.</li>
            <li>Coordinate volunteer efforts and community responses seamlessly.</li>
          </ul>
          <div className="rounded-3xl border border-border bg-muted/50 p-6">
            <p className="text-sm font-medium text-primary">New to the platform?</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Create an account to access collaborative reporting tools and invite your neighbors to join you.
            </p>
            <Link
              href="/sign-up"
              className="mt-4 inline-flex items-center justify-center rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              Create a free account
            </Link>
          </div>
        </div>

        <AuthCard
          title="Sign in"
          subtitle="Enter your email and password to access your dashboard."
          footerHint="Do not have an account yet?"
          footerActionLabel="Create one now"
          footerActionHref="/sign-up"
          className="bg-background/90 backdrop-blur"
        >
          <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
            <FormField
              id="email"
              label="Email address"
              error={form.formState.errors.email?.message}
              required
            >
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                {...form.register("email")}
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
                autoComplete="current-password"
                placeholder="Enter your password"
                {...form.register("password")}
              />
            </FormField>
            <Button type="submit" className="w-full" isLoading={isSubmitting}>
              Sign in
            </Button>
          </form>
        </AuthCard>
      </div>
    </div>
  );
}

function SignInFormFallback() {
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
      <div className="absolute inset-0 bg-background/60 backdrop-blur-[2px]" aria-hidden />
      <Link
        href="/"
        className="absolute left-6 top-6 z-10"
      >
        <Button variant="ghost" size="sm" className="bg-background/90 backdrop-blur-sm">
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
          title="Sign in"
          subtitle="Enter your email and password to access your dashboard."
          footerHint="Do not have an account yet?"
          footerActionLabel="Create one now"
          footerActionHref="/sign-up"
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
            <Skeleton className="h-10 w-full" />
          </div>
        </AuthCard>
      </div>
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={<SignInFormFallback />}>
      <SignInForm />
    </Suspense>
  );
}
