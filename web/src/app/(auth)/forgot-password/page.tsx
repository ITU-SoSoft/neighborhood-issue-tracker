"use client";

import { useState } from "react";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { ArrowLeft, Mail, CheckCircle } from "lucide-react";

import { AuthCard } from "@/components/auth/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/ui/form-field";
import { forgotPassword } from "@/lib/api/client";
import { forgotPasswordSchema, ForgotPasswordInput } from "@/lib/validators";

export default function ForgotPasswordPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const form = useForm<ForgotPasswordInput>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: "",
    },
  });

  const onSubmit = async (values: ForgotPasswordInput) => {
    try {
      setIsSubmitting(true);
      await forgotPassword(values);
      setIsSubmitted(true);
      toast.success("Password reset email sent");
    } catch (error) {
      // Always show success for security (don't reveal if email exists)
      setIsSubmitted(true);
      toast.success("Password reset email sent");
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
        {isSubmitted ? (
          <div className="rounded-2xl border border-border bg-card/95 p-8 text-center shadow-xl backdrop-blur">
            <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
            <h1 className="mt-6 text-2xl font-semibold">Check your email</h1>
            <p className="mt-2 text-muted-foreground">
              If an account with that email exists, we&apos;ve sent you a
              password reset link. The link will expire in 1 hour.
            </p>
            <div className="mt-6 space-y-3">
              <Button
                className="w-full"
                variant="outline"
                onClick={() => {
                  setIsSubmitted(false);
                  form.reset();
                }}
              >
                Send another email
              </Button>
              <Link href="/sign-in">
                <Button className="w-full">Back to Sign in</Button>
              </Link>
            </div>
          </div>
        ) : (
          <AuthCard
            title="Forgot password?"
            subtitle="Enter your email address and we'll send you a link to reset your password."
            footerHint="Remember your password?"
            footerActionLabel="Sign in"
            footerActionHref="/sign-in"
            className="bg-background/90 backdrop-blur"
          >
            <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
              <FormField
                id="email"
                label="Email address"
                error={form.formState.errors.email?.message}
                required
              >
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="you@example.com"
                    className="pl-10"
                    {...form.register("email")}
                  />
                </div>
              </FormField>
              <Button type="submit" className="w-full" isLoading={isSubmitting}>
                Send reset link
              </Button>
            </form>
          </AuthCard>
        )}
      </div>
    </div>
  );
}
