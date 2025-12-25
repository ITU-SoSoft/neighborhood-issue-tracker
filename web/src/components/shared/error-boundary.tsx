"use client";

import { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorDetails {
  message: string;
  stack?: string;
  componentStack?: string;
  timestamp: string;
  url: string;
  userAgent: string;
  storageAvailable: boolean;
  cookiesEnabled: boolean;
  isEmbeddedBrowser: boolean;
  errorType: string;
}

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorDetails: ErrorDetails | null;
}

/**
 * Check if localStorage is available and accessible
 */
function isStorageAvailable(): boolean {
  try {
    const testKey = "__storage_test__";
    window.localStorage.setItem(testKey, testKey);
    window.localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if cookies are enabled
 */
function areCookiesEnabled(): boolean {
  try {
    document.cookie = "cookietest=1";
    const result = document.cookie.indexOf("cookietest=") !== -1;
    document.cookie = "cookietest=1; expires=Thu, 01-Jan-1970 00:00:01 GMT";
    return result;
  } catch {
    return false;
  }
}

/**
 * Detect if running in an embedded browser (Gmail, Facebook, etc.)
 */
function isEmbeddedBrowser(): boolean {
  if (typeof window === "undefined") return false;
  const ua = navigator.userAgent.toLowerCase();

  // Common embedded browser signatures
  const embeddedSignatures = [
    "fban", // Facebook App
    "fbav", // Facebook App Version
    "instagram", // Instagram
    "twitter", // Twitter
    "line", // Line
    "wv", // WebView
    "gsa", // Google Search App
    "webview", // Generic WebView
  ];

  return embeddedSignatures.some((sig) => ua.includes(sig));
}

/**
 * Log error details to console and potentially to external service
 */
function logError(errorDetails: ErrorDetails): void {
  // Console logging with structured data
  console.group("🚨 Application Error Caught by Error Boundary");
  console.error("Error:", errorDetails.message);
  console.error("Type:", errorDetails.errorType);
  console.error("URL:", errorDetails.url);
  console.error("Timestamp:", errorDetails.timestamp);
  console.log("Environment Details:");
  console.table({
    storageAvailable: errorDetails.storageAvailable,
    cookiesEnabled: errorDetails.cookiesEnabled,
    isEmbeddedBrowser: errorDetails.isEmbeddedBrowser,
    userAgent: errorDetails.userAgent,
  });
  if (errorDetails.stack) {
    console.error("Stack Trace:", errorDetails.stack);
  }
  if (errorDetails.componentStack) {
    console.error("Component Stack:", errorDetails.componentStack);
  }
  console.groupEnd();

  // TODO: Send to external logging service (e.g., Sentry, LogRocket)
  // This is where you'd integrate with your preferred error tracking service
  // Example:
  // if (typeof window !== 'undefined' && window.Sentry) {
  //   window.Sentry.captureException(new Error(errorDetails.message), {
  //     extra: errorDetails,
  //   });
  // }
}

/**
 * Classify error type for better user messaging
 */
function classifyError(error: Error): string {
  const message = error.message.toLowerCase();
  const name = error.name.toLowerCase();

  if (
    message.includes("operation is insecure") ||
    message.includes("access is denied") ||
    message.includes("securityerror")
  ) {
    return "STORAGE_ACCESS_BLOCKED";
  }

  if (message.includes("quota") || message.includes("storage")) {
    return "STORAGE_QUOTA_EXCEEDED";
  }

  if (message.includes("network") || message.includes("fetch")) {
    return "NETWORK_ERROR";
  }

  if (name === "chunkloaderror" || message.includes("loading chunk")) {
    return "CHUNK_LOAD_ERROR";
  }

  return "UNKNOWN_ERROR";
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorDetails: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    const errorDetails: ErrorDetails = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack || undefined,
      timestamp: new Date().toISOString(),
      url: typeof window !== "undefined" ? window.location.href : "unknown",
      userAgent:
        typeof navigator !== "undefined" ? navigator.userAgent : "unknown",
      storageAvailable:
        typeof window !== "undefined" ? isStorageAvailable() : false,
      cookiesEnabled:
        typeof document !== "undefined" ? areCookiesEnabled() : false,
      isEmbeddedBrowser: isEmbeddedBrowser(),
      errorType: classifyError(error),
    };

    this.setState({ errorInfo, errorDetails });
    logError(errorDetails);
  }

  handleRetry = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorDetails: null,
    });
  };

  handleOpenInBrowser = (): void => {
    // Attempt to open the current URL in the system browser
    const currentUrl = window.location.href;
    window.open(currentUrl, "_system");
  };

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    const { hasError, errorDetails } = this.state;
    const { children, fallback } = this.props;

    if (hasError) {
      // Custom fallback provided
      if (fallback) {
        return fallback;
      }

      // Determine if it's a storage-related error
      const isStorageError =
        errorDetails?.errorType === "STORAGE_ACCESS_BLOCKED";
      const isEmbedded = errorDetails?.isEmbeddedBrowser;

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
              <AlertTriangle className="mx-auto h-16 w-16 text-amber-500" />
              <h1 className="mt-6 text-2xl font-semibold text-foreground">
                {isStorageError
                  ? "Browser Compatibility Issue"
                  : "Something went wrong"}
              </h1>

              {isStorageError || isEmbedded ? (
                <>
                  <p className="mt-4 text-muted-foreground">
                    It looks like you&apos;re opening this link from an email
                    app or embedded browser that restricts certain features.
                  </p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    For the best experience, please open this link in your
                    regular browser (Safari, Chrome, Firefox, etc.).
                  </p>
                  <div className="mt-6 space-y-3">
                    <Button
                      className="w-full"
                      onClick={this.handleOpenInBrowser}
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      Open in Browser
                    </Button>
                    <Button
                      className="w-full"
                      variant="outline"
                      onClick={this.handleReload}
                    >
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Try Again
                    </Button>
                  </div>
                  <p className="mt-4 text-xs text-muted-foreground">
                    Copy this link and paste it in your browser:
                  </p>
                  <code className="mt-1 block break-all rounded bg-muted p-2 text-xs">
                    {typeof window !== "undefined" ? window.location.href : ""}
                  </code>
                </>
              ) : (
                <>
                  <p className="mt-4 text-muted-foreground">
                    An unexpected error occurred. Please try again.
                  </p>
                  {errorDetails && (
                    <details className="mt-4 text-left">
                      <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
                        Technical Details
                      </summary>
                      <pre className="mt-2 max-h-32 overflow-auto rounded bg-muted p-2 text-xs">
                        {errorDetails.message}
                      </pre>
                    </details>
                  )}
                  <div className="mt-6 space-y-3">
                    <Button className="w-full" onClick={this.handleRetry}>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Try Again
                    </Button>
                    <Button
                      className="w-full"
                      variant="outline"
                      onClick={this.handleReload}
                    >
                      Reload Page
                    </Button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      );
    }

    return children;
  }
}
