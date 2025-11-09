"use client";

import * as React from "react";
import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";

const buttonVariants = {
  primary:
    "bg-emerald-600 text-white hover:bg-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500",
  secondary:
    "bg-white text-slate-900 ring-1 ring-inset ring-slate-200 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500",
  ghost:
    "text-slate-900 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500",
};

type ButtonVariant = keyof typeof buttonVariants;

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { className, variant = "primary", isLoading, disabled, children, ...props },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-full px-5 py-2.5 text-sm font-semibold transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-60",
          buttonVariants[variant],
          className,
        )}
        disabled={disabled ?? isLoading}
        {...props}
      >
        {isLoading ? (
          <span className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Processing...</span>
          </span>
        ) : (
          children
        )}
      </button>
    );
  },
);
Button.displayName = "Button";


