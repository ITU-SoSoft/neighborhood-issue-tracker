"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { AuthCard } from "@/components/auth/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/ui/form-field";
import { Skeleton } from "@/components/ui/skeleton";
import { staffLogin } from "@/lib/api/client";
import { useAuth } from "@/lib/auth/context";
import { StaffLoginInput, staffLoginSchema } from "@/lib/validators";

function StaffSignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login: authLogin } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<StaffLoginInput>({
    resolver: zodResolver(staffLoginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values: StaffLoginInput) => {
    try {
      setIsSubmitting(true);

      const response = await staffLogin(values);
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
        backgroundImage: 'url("/auth-bg.png")',
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <div className="absolute inset-0 bg-slate-950/70" aria-hidden />
      <div className="relative w-full max-w-md">
        <AuthCard
          title="Staff Sign In"
          subtitle="Enter your credentials to access the staff dashboard. This portal is exclusively for support and manager roles."
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
                placeholder="staff@example.com"
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
            <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-xs text-red-700">
              <p className="font-medium">Staff Only Access</p>
              <p className="mt-1">
                This login is restricted to support and manager accounts. If you are a citizen,
                please use the{" "}
                <a href="/sign-in" className="font-semibold text-red-800 hover:text-red-600 underline">
                  citizen portal
                </a>.
              </p>
            </div>
            <Button type="submit" className="w-full" isLoading={isSubmitting}>
              Sign in as Staff
            </Button>
          </form>
        </AuthCard>
      </div>
    </div>
  );
}

function StaffSignInFormFallback() {
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
      <div className="relative w-full max-w-md">
        <AuthCard
          title="Staff Sign In"
          subtitle="Enter your credentials to access the staff dashboard. This portal is exclusively for support and manager roles."
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
            <Skeleton className="h-20 w-full rounded-2xl" />
            <Skeleton className="h-10 w-full" />
          </div>
        </AuthCard>
      </div>
    </div>
  );
}

export default function StaffSignInPage() {
  return (
    <Suspense fallback={<StaffSignInFormFallback />}>
      <StaffSignInForm />
    </Suspense>
  );
}
