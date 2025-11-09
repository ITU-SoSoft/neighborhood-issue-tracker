"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", ...props }, ref) => {
    return (
      <input
        ref={ref}
        type={type}
        className={cn(
          "block w-full rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-sm transition-colors duration-150 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-200 disabled:cursor-not-allowed disabled:bg-slate-100",
          className,
        )}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";


