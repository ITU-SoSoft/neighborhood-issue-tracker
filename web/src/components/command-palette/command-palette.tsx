"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { Badge } from "@/components/ui/badge";
import { useCommandPalette } from "./command-palette-context";
import { useAuth } from "@/lib/auth/context";
import { useTickets } from "@/lib/queries/tickets";
import { UserRole, TicketStatus } from "@/lib/api/types";

// Icons using SVG (keeping it lightweight)
const Icons = {
  Home: () => (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
      />
    </svg>
  ),
  Tickets: () => (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"
      />
    </svg>
  ),
  Plus: () => (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 4v16m8-8H4"
      />
    </svg>
  ),
  User: () => (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      />
    </svg>
  ),
  Chart: () => (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
      />
    </svg>
  ),
  Alert: () => (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  ),
  Users: () => (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  ),
  Logout: () => (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
      />
    </svg>
  ),
  Search: () => (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
      />
    </svg>
  ),
};

// Status badge variant helper
function getStatusVariant(status: TicketStatus) {
  switch (status) {
    case TicketStatus.NEW:
      return "info";
    case TicketStatus.IN_PROGRESS:
      return "warning";
    case TicketStatus.RESOLVED:
      return "success";
    case TicketStatus.CLOSED:
      return "secondary";
    case TicketStatus.ESCALATED:
      return "danger";
    default:
      return "default";
  }
}

export function CommandPalette() {
  const { isOpen, close } = useCommandPalette();
  const { user, logout, isAuthenticated } = useAuth();
  const router = useRouter();
  const [search, setSearch] = useState("");

  // Only fetch tickets if user is SUPPORT or MANAGER (backend requires these roles)
  const isStaff = user?.role === UserRole.SUPPORT || user?.role === UserRole.MANAGER;
  const { data: ticketsData } = useTickets(
    { page_size: 10 },
    { enabled: isAuthenticated && isStaff }
  );

  // Navigation items based on user role
  const navigationItems = useMemo(() => {
    const items = [
      { name: "Dashboard", href: "/dashboard", icon: Icons.Home },
      { name: "All Tickets", href: "/tickets", icon: Icons.Tickets },
      { name: "Create Ticket", href: "/tickets/new", icon: Icons.Plus },
      { name: "Profile", href: "/profile", icon: Icons.User },
    ];

    // Add staff-only items
    if (user?.role === UserRole.SUPPORT || user?.role === UserRole.MANAGER) {
      items.push({
        name: "Escalations",
        href: "/escalations",
        icon: Icons.Alert,
      });
    }

    // Add manager-only items
    if (user?.role === UserRole.MANAGER) {
      items.push(
        { name: "Analytics", href: "/analytics", icon: Icons.Chart },
        { name: "User Management", href: "/users", icon: Icons.Users }
      );
    }

    return items;
  }, [user?.role]);

  // Quick actions
  const quickActions = useMemo(() => {
    return [
      {
        name: "Create New Ticket",
        action: () => router.push("/tickets/new"),
        icon: Icons.Plus,
      },
      {
        name: "Sign Out",
        action: () => logout(),
        icon: Icons.Logout,
      },
    ];
  }, [router, logout]);

  // Filter tickets based on search
  const filteredTickets = useMemo(() => {
    if (!search || !ticketsData?.items) return [];
    const searchLower = search.toLowerCase();
    return ticketsData.items.filter(
      (ticket) =>
        ticket.title.toLowerCase().includes(searchLower) ||
        ticket.id.toLowerCase().includes(searchLower) ||
        ticket.category_name?.toLowerCase().includes(searchLower)
    );
  }, [search, ticketsData?.items]);

  // Handle selection
  const handleSelect = (callback: () => void) => {
    callback();
    close();
    setSearch("");
  };

  // Reset search when closed
  useEffect(() => {
    if (!isOpen) {
      setSearch("");
    }
  }, [isOpen]);

  return (
    <CommandDialog open={isOpen} onOpenChange={(open) => !open && close()}>
      <CommandInput
        placeholder="Search tickets, navigate, or run commands..."
        value={search}
        onValueChange={setSearch}
      />
      <CommandList>
        <CommandEmpty>
          <div className="py-6 text-center">
            <Icons.Search />
            <p className="mt-2 text-sm text-muted-foreground">
              No results found for &quot;{search}&quot;
            </p>
          </div>
        </CommandEmpty>

        {/* Recent/Searched Tickets */}
        {filteredTickets.length > 0 && (
          <>
            <CommandGroup heading="Tickets">
              {filteredTickets.slice(0, 5).map((ticket) => (
                <CommandItem
                  key={ticket.id}
                  value={`ticket-${ticket.id}-${ticket.title}`}
                  onSelect={() =>
                    handleSelect(() => router.push(`/tickets/${ticket.id}`))
                  }
                >
                  <Icons.Tickets />
                  <span className="flex-1 truncate">{ticket.title}</span>
                  <Badge variant={getStatusVariant(ticket.status)}>
                    {ticket.status.replace("_", " ")}
                  </Badge>
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator />
          </>
        )}

        {/* Navigation */}
        <CommandGroup heading="Navigation">
          {navigationItems.map((item) => (
            <CommandItem
              key={item.href}
              value={`nav-${item.name}`}
              onSelect={() => handleSelect(() => router.push(item.href))}
            >
              <item.icon />
              <span>{item.name}</span>
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        {/* Quick Actions */}
        <CommandGroup heading="Quick Actions">
          {quickActions.map((action) => (
            <CommandItem
              key={action.name}
              value={`action-${action.name}`}
              onSelect={() => handleSelect(action.action)}
            >
              <action.icon />
              <span>{action.name}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>

      {/* Keyboard shortcuts hint */}
      <div className="flex items-center justify-between border-t px-4 py-2 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <kbd className="rounded bg-muted px-1.5 py-0.5 font-mono">
            &uarr;&darr;
          </kbd>
          <span>Navigate</span>
        </div>
        <div className="flex items-center gap-2">
          <kbd className="rounded bg-muted px-1.5 py-0.5 font-mono">Enter</kbd>
          <span>Select</span>
        </div>
        <div className="flex items-center gap-2">
          <kbd className="rounded bg-muted px-1.5 py-0.5 font-mono">Esc</kbd>
          <span>Close</span>
        </div>
      </div>
    </CommandDialog>
  );
}
