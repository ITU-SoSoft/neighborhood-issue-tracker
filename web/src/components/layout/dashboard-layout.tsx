"use client";

import { Sidebar } from "./sidebar";
import { Navbar } from "./navbar";
import { useRequireAuth, useAuth } from "@/lib/auth/context";
import { Skeleton } from "@/components/ui/skeleton";
import { UserRole } from "@/lib/api/types";

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
}

export function DashboardLayout({ children, title }: DashboardLayoutProps) {
  const { isLoading, isAuthenticated } = useRequireAuth();
  const { user } = useAuth();

  const isStaff =
    user?.role === UserRole.SUPPORT || user?.role === UserRole.MANAGER;

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="grid h-12 w-12 place-content-center rounded-full bg-primary/10 text-primary">
            <span className="text-lg font-bold">NT</span>
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-24 mx-auto" />
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect via useRequireAuth
  }

  return (
    <div className="min-h-screen bg-muted/30">
      <Sidebar isStaff={isStaff} />
      <div className="lg:pl-64">
        <Navbar title={title} isStaff={isStaff} />
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
