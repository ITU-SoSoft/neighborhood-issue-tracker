import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  action?: React.ReactNode;
  className?: string;
}

// Error icon
const ErrorIcon = () => (
  <svg
    aria-hidden="true"
    className="h-16 w-16 text-destructive/50"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
    strokeWidth={1}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
    />
  </svg>
);

const OfflineIcon = () => (
  <svg
    aria-hidden="true"
    className="h-16 w-16 text-muted-foreground/50"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
    strokeWidth={1}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
    />
  </svg>
);

const NotFoundIcon = () => (
  <svg
    aria-hidden="true"
    className="h-16 w-16 text-muted-foreground/50"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
    strokeWidth={1}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
    />
  </svg>
);

export function ErrorState({
  title = "Something went wrong",
  message = "An unexpected error occurred. Please try again.",
  onRetry,
  action,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 text-center",
        className
      )}
    >
      <ErrorIcon />
      <h3 className="mt-4 text-lg font-semibold text-foreground">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground max-w-sm">{message}</p>
      {onRetry && (
        <Button onClick={onRetry} variant="outline" className="mt-6">
          Try Again
        </Button>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

// Pre-configured error states
export function NetworkError({ onRetry }: { onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <OfflineIcon />
      <h3 className="mt-4 text-lg font-semibold text-foreground">
        Connection Error
      </h3>
      <p className="mt-1 text-sm text-muted-foreground max-w-sm">
        Unable to connect to the server. Please check your internet connection
        and try again.
      </p>
      {onRetry && (
        <Button onClick={onRetry} variant="outline" className="mt-6">
          Try Again
        </Button>
      )}
    </div>
  );
}

export function NotFoundError({
  resource = "resource",
  onGoBack,
}: {
  resource?: string;
  onGoBack?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <NotFoundIcon />
      <h3 className="mt-4 text-lg font-semibold text-foreground">Not Found</h3>
      <p className="mt-1 text-sm text-muted-foreground max-w-sm">
        The {resource} you&apos;re looking for doesn&apos;t exist or has been
        removed.
      </p>
      {onGoBack && (
        <Button onClick={onGoBack} variant="outline" className="mt-6">
          Go Back
        </Button>
      )}
    </div>
  );
}

export function PermissionError({ onGoBack }: { onGoBack?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <svg
        aria-hidden="true"
        className="h-16 w-16 text-muted-foreground/50"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
      </svg>
      <h3 className="mt-4 text-lg font-semibold text-foreground">
        Access Denied
      </h3>
      <p className="mt-1 text-sm text-muted-foreground max-w-sm">
        You don&apos;t have permission to access this resource.
      </p>
      {onGoBack && (
        <Button onClick={onGoBack} variant="outline" className="mt-6">
          Go Back
        </Button>
      )}
    </div>
  );
}
