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
} from "@/lib/api/types";

// ============================================================================
// TICKET QUERIES
// ============================================================================

interface TicketListParams {
  status_filter?: TicketStatus;
  category_id?: string;
  assignee_id?: string;
  page?: number;
  page_size?: number;
}

interface QueryOptions {
  enabled?: boolean;
}

export function useTickets(params: TicketListParams = {}, options?: QueryOptions) {
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

export function useMyTickets(params?: { page?: number; page_size?: number }, options?: QueryOptions) {
  return useQuery({
    queryKey: queryKeys.tickets.my(params),
    queryFn: () => api.getMyTickets(params),
    enabled: options?.enabled ?? true,
  });
}

export function useAssignedTickets(params?: {
  page?: number;
  page_size?: number;
}, options?: QueryOptions) {
  return useQuery({
    queryKey: queryKeys.tickets.assigned(params),
    queryFn: () => api.getAssignedTickets(params),
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

// ============================================================================
// TICKET MUTATIONS
// ============================================================================

export function useCreateTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TicketCreate) => api.createTicket(data),
    onSuccess: () => {
      // Invalidate all ticket lists
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.my() });
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
      // Invalidate the specific ticket and all lists
      queryClient.invalidateQueries({
        queryKey: queryKeys.tickets.detail(ticketId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.my() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.assigned() });
      // Also invalidate analytics as status changes affect KPIs
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics.all });
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
      queryClient.invalidateQueries({
        queryKey: queryKeys.tickets.detail(ticketId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.assigned() });
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
    },
  });
}

// ============================================================================
// COMMENT MUTATIONS
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
    },
  });
}

// ============================================================================
// FEEDBACK MUTATIONS
// ============================================================================

export function useTicketFeedback(ticketId: string) {
  return useQuery({
    queryKey: queryKeys.feedback.byTicket(ticketId),
    queryFn: () => api.getTicketFeedback(ticketId),
    enabled: !!ticketId,
    retry: false, // Don't retry on 404 (no feedback yet)
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
      // Feedback affects analytics
      queryClient.invalidateQueries({
        queryKey: queryKeys.analytics.feedbackTrends(),
      });
    },
  });
}
