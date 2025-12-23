"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Ticket,
  Plus,
  User,
  LogOut,
  BarChart3,
  Users,
  AlertTriangle,
  Menu,
  X,
} from "lucide-react";
import { useState } from "react";

import { useAuth } from "@/lib/auth/context";
import { UserRole } from "@/lib/api/types";
import { cn, getRoleLabel } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  roles?: UserRole[];
}

const navItems: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: <Home className="h-5 w-5" />,
  },
  {
    label: "My Tickets",
    href: "/tickets?view=my",
    icon: <Ticket className="h-5 w-5" />,
    roles: [UserRole.CITIZEN],
  },
  {
    label: "All Tickets",
    href: "/tickets",
    icon: <Ticket className="h-5 w-5" />,
    roles: [UserRole.SUPPORT, UserRole.MANAGER],
  },
  {
    label: "Assigned to Me",
    href: "/tickets?view=assigned",
    icon: <Ticket className="h-5 w-5" />,
    roles: [UserRole.SUPPORT],
  },
  {
    label: "Report Issue",
    href: "/tickets/new",
    icon: <Plus className="h-5 w-5" />,
    roles: [UserRole.CITIZEN],
  },
  {
    label: "Escalations",
    href: "/escalations",
    icon: <AlertTriangle className="h-5 w-5" />,
    roles: [UserRole.SUPPORT, UserRole.MANAGER],
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: <BarChart3 className="h-5 w-5" />,
    roles: [UserRole.MANAGER],
  },
  {
    label: "Management",
    href: "/teams",
    icon: <Users className="h-5 w-5" />,
    roles: [UserRole.MANAGER],
  },
];

interface SidebarProps {
  isStaff?: boolean;
}

export function Sidebar({ isStaff = false }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const filteredNavItems = navItems.filter((item) => {
    if (!item.roles) return true;
    return user && item.roles.includes(user.role);
  });

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div
        className={cn(
          "flex h-16 items-center gap-2 border-b px-6",
          isStaff ? "bg-slate-800 border-slate-700" : "border-border",
        )}
      >
        <span
          className={cn(
            "grid h-8 w-8 place-content-center rounded-full text-sm font-bold",
            isStaff
              ? "bg-primary/20 text-primary"
              : "bg-primary/10 text-primary",
          )}
        >
          NT
        </span>
        <span
          className={cn(
            "text-sm font-semibold",
            isStaff ? "text-white" : "text-foreground",
          )}
        >
          {isStaff ? "Staff Portal" : "Neighborhood Tracker"}
        </span>
      </div>

      {/* Navigation */}
      <nav
        className={cn("flex-1 space-y-1 p-4", isStaff ? "bg-slate-800" : "")}
      >
        {filteredNavItems.map((item) => {
          // Handle query params for active state
          const itemPath = item.href.split("?")[0];
          const isActive =
            pathname === itemPath ||
            (pathname.startsWith(`${itemPath}/`) && itemPath !== "/tickets") ||
            (item.href.includes("?") && pathname === itemPath);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setIsMobileOpen(false)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? isStaff
                    ? "bg-slate-700 text-white"
                    : "bg-primary/10 text-primary"
                  : isStaff
                    ? "text-slate-300 hover:bg-slate-700 hover:text-white"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              {item.icon}
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      {user && (
        <div
          className={cn(
            "border-t p-4",
            isStaff ? "bg-slate-800 border-slate-700" : "border-border",
          )}
        >
          <div
            className={cn(
              "flex items-center gap-3 rounded-lg p-3",
              isStaff ? "bg-slate-700" : "bg-muted/50",
            )}
          >
            <div
              className={cn(
                "flex h-10 w-10 items-center justify-center rounded-full",
                isStaff
                  ? "bg-primary/20 text-primary"
                  : "bg-primary/10 text-primary",
              )}
            >
              <User className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <p
                className={cn(
                  "truncate text-sm font-medium",
                  isStaff ? "text-white" : "text-foreground",
                )}
              >
                {user.name}
              </p>
              <p
                className={cn(
                  "truncate text-xs",
                  isStaff ? "text-slate-400" : "text-muted-foreground",
                )}
              >
                {getRoleLabel(user.role)}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={logout}
              className={cn(
                isStaff
                  ? "text-slate-400 hover:text-white hover:bg-slate-600"
                  : "text-muted-foreground hover:text-foreground",
              )}
              aria-label="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </>
  );

  return (
    <>
      {/* Mobile toggle button */}
      <Button
        variant="outline"
        size="icon"
        className="fixed left-4 top-4 z-50 lg:hidden"
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        aria-label={isMobileOpen ? "Close menu" : "Open menu"}
      >
        {isMobileOpen ? (
          <X className="h-5 w-5" />
        ) : (
          <Menu className="h-5 w-5" />
        )}
      </Button>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col shadow-lg transition-transform lg:translate-x-0 lg:shadow-none lg:border-r",
          isStaff
            ? "bg-slate-800 lg:border-slate-700"
            : "bg-background lg:border-border",
          isMobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
        aria-label="Main navigation"
      >
        <SidebarContent />
      </aside>
    </>
  );
}
