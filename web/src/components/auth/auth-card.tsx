"use client";

import * as React from "react";
import Link from "next/link";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface AuthCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  subtitle: string;
  footerHint: string;
  footerActionLabel: string;
  footerActionHref: string;
}

export function AuthCard({
  title,
  subtitle,
  footerHint,
  footerActionLabel,
  footerActionHref,
  className,
  children,
  ...props
}: AuthCardProps) {
  return (
    <Card className={cn("w-full max-w-md space-y-8", className)} {...props}>
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-emerald-600">
          <span className="grid h-8 w-8 place-content-center rounded-full bg-emerald-100 text-emerald-600">
            NT
          </span>
          Neighborhood Issue Tracker
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
          <p className="text-sm text-slate-500">{subtitle}</p>
        </div>
      </div>
      <div className="space-y-6">{children}</div>
      <p className="text-center text-sm text-slate-500">
        {footerHint}{" "}
        <Link href={footerActionHref} className="font-semibold text-emerald-600 hover:text-emerald-700">
          {footerActionLabel}
        </Link>
      </p>
    </Card>
  );
}


