"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export type CardProps = React.HTMLAttributes<HTMLDivElement>;

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-3xl border border-slate-200 bg-white p-8 shadow-lg shadow-emerald-100/40",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  ),
);
Card.displayName = "Card";


