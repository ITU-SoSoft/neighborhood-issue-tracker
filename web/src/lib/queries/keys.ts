// Query key factory for type-safe, consistent query keys
// Based on TanStack Query best practices

import { TicketStatus, EscalationStatus, UserRole } from "@/lib/api/types";

export const queryKeys = {
  // Tickets
  tickets: {
    all: ["tickets"] as const,
    lists: () => [...queryKeys.tickets.all, "list"] as const,
    list: (filters: {
      status_filter?: TicketStatus;
      category_id?: string;
      assignee_id?: string;
      page?: number;
      page_size?: number;
    }) => [...queryKeys.tickets.lists(), filters] as const,
    details: () => [...queryKeys.tickets.all, "detail"] as const,
    detail: (id: string) => [...queryKeys.tickets.details(), id] as const,
    my: (params?: {
      status_filter?: TicketStatus;
      category_id?: string;
      page?: number;
      page_size?: number;
    }) => [...queryKeys.tickets.all, "my", params ?? {}] as const,
    assigned: (params?: {
      status_filter?: TicketStatus;
      category_id?: string;
      page?: number;
      page_size?: number;
    }) => [...queryKeys.tickets.all, "assigned", params ?? {}] as const,
    followed: (params?: {
      status_filter?: TicketStatus;
      category_id?: string;
      page?: number;
      page_size?: number;
    }) => [...queryKeys.tickets.all, "followed", params ?? {}] as const,
    allUser: (params?: {
      status_filter?: TicketStatus;
      category_id?: string;
      page?: number;
      page_size?: number;
    }) => [...queryKeys.tickets.all, "allUser", params ?? {}] as const,
    nearby: (params: {
      latitude: number;
      longitude: number;
      radius_meters?: number;
      category_id?: string;
    }) => [...queryKeys.tickets.all, "nearby", params] as const,
  },

  // Categories
  categories: {
    all: ["categories"] as const,
    list: (activeOnly?: boolean) =>
      [...queryKeys.categories.all, "list", { activeOnly }] as const,
    detail: (id: string) =>
      [...queryKeys.categories.all, "detail", id] as const,
  },

  // Users
  users: {
    all: ["users"] as const,
    lists: () => [...queryKeys.users.all, "list"] as const,
    list: (filters?: {
      role?: UserRole;
      team_id?: string;
      page?: number;
      page_size?: number;
    }) => [...queryKeys.users.lists(), filters ?? {}] as const,
    detail: (id: string) => [...queryKeys.users.all, "detail", id] as const,
    me: () => [...queryKeys.users.all, "me"] as const,
  },

  // Comments
  comments: {
    all: ["comments"] as const,
    byTicket: (ticketId: string) =>
      [...queryKeys.comments.all, "ticket", ticketId] as const,
  },

  // Feedback
  feedback: {
    all: ["feedback"] as const,
    byTicket: (ticketId: string) =>
      [...queryKeys.feedback.all, "ticket", ticketId] as const,
  },

  // Escalations
  escalations: {
    all: ["escalations"] as const,
    lists: () => [...queryKeys.escalations.all, "list"] as const,
    list: (filters?: {
      status_filter?: EscalationStatus;
      page?: number;
      page_size?: number;
    }) => [...queryKeys.escalations.lists(), filters ?? {}] as const,
    detail: (id: string) =>
      [...queryKeys.escalations.all, "detail", id] as const,
  },

  // Analytics
  analytics: {
    all: ["analytics"] as const,
    dashboard: (days?: number) =>
      [...queryKeys.analytics.all, "dashboard", { days }] as const,
    heatmap: (params?: {
      days?: number;
      category_id?: string;
      status?: TicketStatus;
    }) => [...queryKeys.analytics.all, "heatmap", params ?? {}] as const,
    teamPerformance: (days?: number) =>
      [...queryKeys.analytics.all, "teamPerformance", { days }] as const,
    memberPerformance: (teamId: string, days?: number) =>
      [
        ...queryKeys.analytics.all,
        "memberPerformance",
        teamId,
        { days },
      ] as const,
    categoryStats: (days?: number) =>
      [...queryKeys.analytics.all, "categoryStats", { days }] as const,
    feedbackTrends: (days?: number) =>
      [...queryKeys.analytics.all, "feedbackTrends", { days }] as const,
    quarterlyReport: (year: number, quarter: number) =>
      [...queryKeys.analytics.all, "quarterlyReport", { year, quarter }] as const,
  },

  // Saved Addresses
  addresses: {
    all: ["addresses"] as const,
    lists: () => [...queryKeys.addresses.all, "list"] as const,
    list: () => [...queryKeys.addresses.lists()] as const,
    detail: (id: string) => [...queryKeys.addresses.all, "detail", id] as const,
  },

  // Notifications
  notifications: {
    all: ["notifications"] as const,
    lists: () => [...queryKeys.notifications.all, "list"] as const,
    list: (params?: {
      unread_only?: boolean;
      page?: number;
      page_size?: number;
    }) => [...queryKeys.notifications.lists(), params ?? {}] as const,
    unreadCount: () => [...queryKeys.notifications.all, "unreadCount"] as const,
  },

  // Districts
  districts: {
    all: ["districts"] as const,
  },

  // Teams
  teams: {
    all: ["teams"] as const,
    lists: () => [...queryKeys.teams.all, "list"] as const,
    list: (filters?: {
      page?: number;
      page_size?: number;
    }) => [...queryKeys.teams.lists(), filters ?? {}] as const,
    detail: (id: string) => [...queryKeys.teams.all, "detail", id] as const,
    unassignedMembers: () => [...queryKeys.teams.all, "unassignedMembers"] as const,
  },
} as const;
