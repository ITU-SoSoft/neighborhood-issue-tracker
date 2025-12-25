"use client";

import { useState } from "react";
import Link from "next/link";
import { Bell, Search, Shield, UserCircle } from "lucide-react";
import { useAuth } from "@/lib/auth/context";
import { useCommandPalette } from "@/components/command-palette";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { NotificationPanel } from "@/components/notifications/notification-panel";
import { useUnreadNotificationCount } from "@/lib/queries/notifications";

interface NavbarProps {
  title?: string;
  isStaff?: boolean;
}

export function Navbar({ title, isStaff = false }: NavbarProps) {
  const { user } = useAuth();
  const { open: openCommandPalette } = useCommandPalette();
  const [isNotificationPanelOpen, setIsNotificationPanelOpen] = useState(false);
  const { data: unreadData } = useUnreadNotificationCount();
  const unreadCount = unreadData?.count ?? 0;

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
          onClick={() => setIsNotificationPanelOpen(true)}
        >
          <Bell className="h-5 w-5" aria-hidden="true" />
          {unreadCount > 0 && (
            <>
              {/* Animated pulse ring */}
              <span className="absolute right-0 top-0 flex h-5 w-5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-5 w-5 bg-red-500 items-center justify-center text-[10px] font-bold text-white shadow-lg">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              </span>
              <span className="sr-only">You have {unreadCount} new notifications</span>
            </>
          )}
        </Button>

        {/* Notification Panel */}
        <NotificationPanel
          isOpen={isNotificationPanelOpen}
          onClose={() => setIsNotificationPanelOpen(false)}
        />

        {/* Profile button - icon on desktop */}
        <Link href="/profile" className="hidden lg:block">
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "relative",
              isStaff ? "text-slate-600 hover:text-slate-900" : "text-muted-foreground hover:text-foreground",
            )}
            aria-label="Go to profile"
          >
            <UserCircle className="h-5 w-5" aria-hidden="true" />
          </Button>
        </Link>

        {/* User avatar - on mobile with profile link */}
        <Link href="/profile" className="lg:hidden">
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors cursor-pointer",
              isStaff 
                ? "bg-slate-700 text-white hover:bg-slate-600" 
                : "bg-primary/10 text-primary hover:bg-primary/20",
            )}
            role="button"
            aria-label={`Go to profile (${user?.name || "User"})`}
          >
            {user?.name?.charAt(0).toUpperCase() || "U"}
          </div>
        </Link>
      </div>
    </header>
  );
}
