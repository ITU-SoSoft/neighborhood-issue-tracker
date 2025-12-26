"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle, XCircle, Loader2, ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { verifyEmail } from "@/lib/api/client";

type VerificationStatus = "loading" | "success" | "error";

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<VerificationStatus>("loading");
  const [message, setMessage] = useState("");
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("Invalid verification link. No token provided.");
      return;
    }

    const verify = async () => {
      try {
        const response = await verifyEmail(token);
        setStatus("success");
        setMessage(response.message);
      } catch (error) {
        setStatus("error");
        if (error instanceof Error) {
          setMessage(error.message);
        } else {
          setMessage(
            "Failed to verify email. Please try again or request a new verification link.",
          );
        }
      }
    };

    verify();
  }, [token]);

  useEffect(() => {
    if (status === "success" && countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else if (status === "success" && countdown === 0) {
      router.push("/sign-in");
    }
  }, [status, countdown, router]);

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
        <div className="rounded-2xl border border-border bg-card/95 p-8 text-center shadow-xl backdrop-blur">
          {status === "loading" && (
            <>
              <Loader2 className="mx-auto h-16 w-16 animate-spin text-primary" />
              <h1 className="mt-6 text-2xl font-semibold">
                Verifying your email...
              </h1>
              <p className="mt-2 text-muted-foreground">
                Please wait while we verify your email address.
              </p>
            </>
          )}

          {status === "success" && (
            <>
              <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
              <h1 className="mt-6 text-2xl font-semibold text-green-600">
                Email Verified!
              </h1>
              <p className="mt-2 text-muted-foreground">{message}</p>
              <p className="mt-4 text-sm text-muted-foreground">
                Redirecting to login in {countdown} seconds...
              </p>
              <Button
                className="mt-6 w-full"
                onClick={() => router.push("/sign-in")}
              >
                Go to Login Now
              </Button>
            </>
          )}

          {status === "error" && (
            <>
              <XCircle className="mx-auto h-16 w-16 text-red-500" />
              <h1 className="mt-6 text-2xl font-semibold text-red-600">
                Verification Failed
              </h1>
              <p className="mt-2 text-muted-foreground">{message}</p>
              <div className="mt-6 space-y-3">
                <Button
                  className="w-full"
                  variant="outline"
                  onClick={() => router.push("/sign-up")}
                >
                  Create New Account
                </Button>
                <Button
                  className="w-full"
                  onClick={() => router.push("/sign-in")}
                >
                  Go to Login
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function VerifyEmailFallback() {
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
          <h1 className="mt-6 text-2xl font-semibold">
            Verifying your email...
          </h1>
          <p className="mt-2 text-muted-foreground">
            Please wait while we verify your email address.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<VerifyEmailFallback />}>
      <VerifyEmailContent />
    </Suspense>
  );
}
