"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { CheckCircle } from "lucide-react";

import { AuthCard } from "@/components/auth/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/ui/form-field";
import { ArrowLeft } from "lucide-react";
import { register } from "@/lib/api/client";
import { RegisterInput, registerSchema } from "@/lib/validators";

export default function SignUpPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState("");

  const form = useForm<RegisterInput>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      phone_number: "+90",
      full_name: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  const handleRegister = async (values: RegisterInput) => {
    try {
      setIsSubmitting(true);

      await register({
        phone_number: values.phone_number,
        full_name: values.full_name,
        email: values.email,
        password: values.password,
      });

      setRegisteredEmail(values.email);
      setIsSuccess(true);
      toast.success("Registration successful! Please check your email.");
    } catch (error) {
      if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error("Failed to create account. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div
        className="relative flex min-h-screen items-center justify-center px-4 py-16"
        style={{
          backgroundImage: 'url("/background.png")',
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundAttachment: "fixed",
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
          <div className="rounded-2xl border border-border bg-card/95 p-8 text-center shadow-xl backdrop-blur">
            <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
            <h1 className="mt-6 text-2xl font-semibold">Check Your Email</h1>
            <p className="mt-2 text-muted-foreground">
              We&apos;ve sent a verification link to{" "}
              <strong>{registeredEmail}</strong>.
            </p>
            <p className="mt-4 text-sm text-muted-foreground">
              Click the link in the email to verify your account and start using
              Sosoft.
            </p>
            <div className="mt-6 space-y-3">
              <Button
                className="w-full"
                variant="outline"
                onClick={() => setIsSuccess(false)}
              >
                Use a Different Email
              </Button>
              <Button
                className="w-full"
                onClick={() => router.push("/sign-in")}
              >
                Go to Login
              </Button>
            </div>
            <p className="mt-4 text-xs text-muted-foreground">
              Didn&apos;t receive the email? Check your spam folder or try
              again.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="relative flex min-h-screen items-center justify-center px-4 py-16"
      style={{
        backgroundImage: 'url("/background.png")',
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundAttachment: "fixed",
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
      <AuthCard
        title="Create an account"
        subtitle="Join the platform and start reporting issues in your community."
        footerHint="Already have an account?"
        footerActionLabel="Sign in"
        footerActionHref="/sign-in"
        className="relative mx-auto bg-background/90 backdrop-blur"
      >
        <form
          className="space-y-4"
          onSubmit={form.handleSubmit(handleRegister)}
        >
          <FormField
            id="full_name"
            label="Full name"
            error={form.formState.errors.full_name?.message}
            required
          >
            <Input
              id="full_name"
              autoComplete="name"
              placeholder="Ada Lovelace"
              {...form.register("full_name")}
            />
          </FormField>
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
            id="phone_number"
            label="Phone number"
            error={form.formState.errors.phone_number?.message}
            description="Enter your Turkish phone number starting with +90"
            required
          >
            <Input
              id="phone_number"
              type="tel"
              autoComplete="tel"
              placeholder="+905XXXXXXXXX"
              {...form.register("phone_number")}
            />
          </FormField>
          <FormField
            id="password"
            label="Password"
            error={form.formState.errors.password?.message}
            description="At least 8 characters with a letter, number, and special character"
            required
          >
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              placeholder="Enter your password"
              {...form.register("password")}
            />
          </FormField>
          <FormField
            id="confirmPassword"
            label="Confirm password"
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
          <div className="space-y-3 rounded-2xl border border-border bg-muted/50 p-4 text-xs text-muted-foreground">
            <p>
              By creating an account you agree to our{" "}
              <Link
                href="/terms"
                className="font-semibold text-primary hover:text-primary/80"
              >
                terms of service
              </Link>{" "}
              and{" "}
              <Link
                href="/privacy"
                className="font-semibold text-primary hover:text-primary/80"
              >
                privacy policy
              </Link>
              .
            </p>
          </div>
          <Button type="submit" className="w-full" isLoading={isSubmitting}>
            Create account
          </Button>
        </form>
      </AuthCard>
    </div>
  );
}
