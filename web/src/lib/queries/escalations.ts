import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "./keys";
import * as api from "@/lib/api/client";
import { EscalationStatus, EscalationCreate, EscalationReview } from "@/lib/api/types";

// ============================================================================
// ESCALATION QUERIES
// ============================================================================

interface EscalationListParams {
  status_filter?: EscalationStatus;
  ticket_id?: string;
  page?: number;
  page_size?: number;
}

export function useEscalations(params: EscalationListParams = {}) {
  return useQuery({
    queryKey: queryKeys.escalations.list(params),
    queryFn: () => api.getEscalations(params),
  });
}

export function useEscalation(escalationId: string) {
  return useQuery({
    queryKey: queryKeys.escalations.detail(escalationId),
    queryFn: () => api.getEscalationById(escalationId),
    enabled: !!escalationId,
  });
}

// ============================================================================
// ESCALATION MUTATIONS
// ============================================================================

export function useCreateEscalation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: EscalationCreate) => api.createEscalation(data),
    onSuccess: (_, { ticket_id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.escalations.lists() });
      queryClient.invalidateQueries({
        queryKey: queryKeys.tickets.detail(ticket_id),
      });
      // Escalations affect analytics
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics.dashboard() });
    },
  });
}

export function useApproveEscalation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      escalationId,
      data,
    }: {
      escalationId: string;
      data: EscalationReview;
    }) => api.approveEscalation(escalationId, data),
    onSuccess: (_, { escalationId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.escalations.detail(escalationId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.escalations.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.lists() });
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics.dashboard() });
    },
  });
}

export function useRejectEscalation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      escalationId,
      data,
    }: {
      escalationId: string;
      data: EscalationReview;
    }) => api.rejectEscalation(escalationId, data),
    onSuccess: (_, { escalationId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.escalations.detail(escalationId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.escalations.lists() });
    },
  });
}
