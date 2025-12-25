import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "./keys";
import * as api from "@/lib/api/client";
import {
  TicketStatus,
  TicketCreate,
  TicketStatusUpdate,
  TicketAssignUpdate,
  PhotoType,
  CommentCreate,
  FeedbackCreate,
  FeedbackUpdate,
} from "@/lib/api/types";

// ============================================================================
// TYPES
// ============================================================================

export interface TicketListParams {
  status_filter?: TicketStatus;
  category_id?: string;
  team_id?: string;
  page?: number;
  page_size?: number;
}

export interface QueryOptions {
  enabled?: boolean;
}

// ============================================================================
// TICKET QUERIES
// ============================================================================

export function useTickets(
  params: TicketListParams = {},
  options?: QueryOptions,
) {
  return useQuery({
    queryKey: queryKeys.tickets.list(params),
    queryFn: () => api.getTickets(params),
    enabled: options?.enabled ?? true,
  });
}

export function useTicket(ticketId: string) {
  return useQuery({
    queryKey: queryKeys.tickets.detail(ticketId),
    queryFn: () => api.getTicketById(ticketId),
    enabled: !!ticketId,
  });
}

export function useMyTickets(
  params?: {
    status_filter?: TicketStatus;
    category_id?: string;
    page?: number;
    page_size?: number;
  },
  options?: QueryOptions,
) {
  return useQuery({
    queryKey: queryKeys.tickets.my(params),
    queryFn: () => api.getMyTickets(params),
    enabled: options?.enabled ?? true,
  });
}

export function useAssignedTickets(
  params?: {
    status_filter?: TicketStatus;
    category_id?: string;
    page?: number;
    page_size?: number;
  },
  options?: QueryOptions,
) {
  return useQuery({
    queryKey: queryKeys.tickets.assigned(params),
    queryFn: () => api.getAssignedTickets(params),
    enabled: options?.enabled ?? true,
  });
}

export function useFollowedTickets(
  params?: {
    status_filter?: TicketStatus;
    category_id?: string;
    page?: number;
    page_size?: number;
  },
  options?: QueryOptions,
) {
  return useQuery({
    queryKey: queryKeys.tickets.followed(params),
    queryFn: () => api.getFollowedTickets(params),
    enabled: options?.enabled ?? true,
  });
}

export function useAllUserTickets(
  params?: {
    status_filter?: TicketStatus;
    category_id?: string;
    page?: number;
    page_size?: number;
  },
  options?: QueryOptions,
) {
  return useQuery({
    queryKey: queryKeys.tickets.allUser(params),
    queryFn: () => api.getAllUserTickets(params),
    enabled: options?.enabled ?? true,
  });
}

export function useNearbyTickets(params: {
  latitude: number;
  longitude: number;
  radius_meters?: number;
  category_id?: string;
}) {
  return useQuery({
    queryKey: queryKeys.tickets.nearby(params),
    queryFn: () => api.getNearbyTickets(params),
    enabled: !!params.latitude && !!params.longitude,
  });
}

/**
 * Helper: fetch tickets for a specific team (nice for manager UI filters).
 * Example usage:
 *   useTicketsByTeam(teamId, { status_filter: TicketStatus.IN_PROGRESS })
 */
export function useTicketsByTeam(
  teamId: string | null | undefined,
  params?: Omit<TicketListParams, "team_id">,
  options?: QueryOptions,
) {
  return useTickets(
    {
      ...(params ?? {}),
      team_id: teamId ?? undefined,
    },
    {
      enabled: (options?.enabled ?? true) && !!teamId,
    },
  );
}

// ============================================================================
// TICKET MUTATIONS
// ============================================================================

export function useCreateTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TicketCreate) => api.createTicket(data),
    onSuccess: () => {
      // Tickets
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.my() });

      // Analytics (KPIs/heatmap/etc can change)
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics.all });

      // Notifications
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.lists() });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.unreadCount(),
      });
    },
  });
}

export function useUpdateTicketStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      ticketId,
      data,
    }: {
      ticketId: string;
      data: TicketStatusUpdate;
    }) => api.updateTicketStatus(ticketId, data),
    onSuccess: (_, { ticketId }) => {
      // Ticket detail + lists
      queryClient.invalidateQueries({
        queryKey: queryKeys.tickets.detail(ticketId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.my() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.assigned() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.followed() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.allUser() });

      // Analytics
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics.all });

      // Notifications
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.lists() });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.unreadCount(),
      });
    },
  });
}

export function useAssignTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      ticketId,
      data,
    }: {
      ticketId: string;
      data: TicketAssignUpdate;
    }) => api.assignTicket(ticketId, data),
    onSuccess: (_, { ticketId }) => {
      // Ticket detail + lists
      queryClient.invalidateQueries({
        queryKey: queryKeys.tickets.detail(ticketId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.assigned() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.my() });

      // Analytics (team workload changes)
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics.all });

      // Notifications (assignment generally creates notifications)
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.lists() });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.unreadCount(),
      });
    },
  });
}

export function useUploadTicketPhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      ticketId,
      file,
      photoType,
    }: {
      ticketId: string;
      file: File;
      photoType: PhotoType;
    }) => api.uploadTicketPhoto(ticketId, file, photoType),
    onSuccess: (_, { ticketId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tickets.detail(ticketId),
      });
    },
  });
}

export function useFollowTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ticketId: string) => api.followTicket(ticketId),
    onSuccess: (_, ticketId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tickets.detail(ticketId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.followed() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.allUser() });

      // Notifications
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.lists() });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.unreadCount(),
      });
    },
  });
}

export function useUnfollowTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ticketId: string) => api.unfollowTicket(ticketId),
    onSuccess: (_, ticketId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.tickets.detail(ticketId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.followed() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.allUser() });
    },
  });
}

// ============================================================================
// COMMENTS
// ============================================================================

export function useTicketComments(ticketId: string) {
  return useQuery({
    queryKey: queryKeys.comments.byTicket(ticketId),
    queryFn: () => api.getTicketComments(ticketId),
    enabled: !!ticketId,
  });
}

export function useCreateComment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      ticketId,
      data,
    }: {
      ticketId: string;
      data: CommentCreate;
    }) => api.createComment(ticketId, data),
    onSuccess: (_, { ticketId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.comments.byTicket(ticketId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tickets.detail(ticketId),
      });

      // Notifications
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.lists() });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.unreadCount(),
      });
    },
  });
}

// ============================================================================
// FEEDBACK
// ============================================================================

export function useTicketFeedback(ticketId: string) {
  return useQuery({
    queryKey: queryKeys.feedback.byTicket(ticketId),
    queryFn: () => api.getTicketFeedback(ticketId),
    enabled: !!ticketId,
    retry: false,
  });
}

export function useSubmitFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      ticketId,
      data,
    }: {
      ticketId: string;
      data: FeedbackCreate;
    }) => api.submitFeedback(ticketId, data),
    onSuccess: (_, { ticketId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.feedback.byTicket(ticketId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tickets.detail(ticketId),
      });

      // Analytics (ratings change)
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.analytics.feedbackTrends(),
      });
    },
  });
}

export function useUpdateFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      ticketId,
      data,
    }: {
      ticketId: string;
      data: FeedbackUpdate;
    }) => api.updateFeedback(ticketId, data),
    onSuccess: (_, { ticketId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.feedback.byTicket(ticketId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tickets.detail(ticketId),
      });

      // Analytics (ratings change)
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.analytics.feedbackTrends(),
      });
    },
  });
}
