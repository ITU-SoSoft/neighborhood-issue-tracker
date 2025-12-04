"use client";

import { Bell, Search, Shield } from "lucide-react";
import { useAuth } from "@/lib/auth/context";
import { useCommandPalette } from "@/components/command-palette";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface NavbarProps {
  title?: string;
  isStaff?: boolean;
}

export function Navbar({ title, isStaff = false }: NavbarProps) {
  const { user } = useAuth();
  const { open: openCommandPalette } = useCommandPalette();

  return (
    <header
      className={cn(
        "sticky top-0 z-30 flex h-16 items-center justify-between border-b px-6 lg:pl-72",
        isStaff
          ? "border-slate-200 bg-slate-50"
          : "border-border bg-background",
      )}
    >
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-foreground lg:text-xl">
          {title || "Dashboard"}
        </h1>
        {isStaff && (
          <Badge
            variant="secondary"
            className="hidden sm:inline-flex gap-1 bg-slate-200 text-slate-700"
          >
            <Shield className="h-3 w-3" />
            Staff
          </Badge>
        )}
      </div>

      <div className="flex items-center gap-2">
        {/* Search button - opens command palette */}
        <Button
          variant="ghost"
          size="sm"
          onClick={openCommandPalette}
          className="gap-2 text-muted-foreground"
          aria-label="Search (Cmd+K)"
        >
          <Search className="h-4 w-4" />
          <span className="hidden sm:inline-flex">Search</span>
          <kbd className="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:inline-flex">
            <span className="text-xs">&#8984;</span>K
          </kbd>
        </Button>

        {/* Notifications */}
        <Button
          variant="ghost"
          size="icon"
          className="relative text-muted-foreground"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" aria-hidden="true" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-destructive">
            <span className="sr-only">You have new notifications</span>
          </span>
        </Button>

        {/* User avatar (mobile) */}
        <div
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium lg:hidden",
            isStaff ? "bg-slate-700 text-white" : "bg-primary/10 text-primary",
          )}
          role="img"
          aria-label={`User: ${user?.name || "Unknown"}`}
        >
          {user?.name?.charAt(0).toUpperCase() || "U"}
        </div>
      </div>
    </header>
  );
}
