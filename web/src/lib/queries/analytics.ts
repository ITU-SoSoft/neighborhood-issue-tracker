import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "./keys";
import * as api from "@/lib/api/client";
import { TicketStatus } from "@/lib/api/types";

// ============================================================================
// ANALYTICS QUERIES
// ============================================================================

export function useDashboardKPIs(days = 30) {
  return useQuery({
    queryKey: queryKeys.analytics.dashboard(days),
    queryFn: () => api.getDashboardKPIs(days),
    staleTime: 2 * 60 * 1000, // KPIs can be cached for 2 minutes
  });
}

export function useHeatmap(params?: {
  days?: number;
  category_id?: string;
  status?: TicketStatus;
}) {
  return useQuery({
    queryKey: queryKeys.analytics.heatmap(params),
    queryFn: () => api.getHeatmap(params),
    staleTime: 5 * 60 * 1000, // Heatmap data can be cached longer
  });
}

export function useTeamPerformance(days = 30) {
  return useQuery({
    queryKey: queryKeys.analytics.teamPerformance(days),
    queryFn: () => api.getTeamPerformance(days),
    staleTime: 5 * 60 * 1000,
  });
}

export function useMemberPerformance(teamId: string, days = 30) {
  return useQuery({
    queryKey: queryKeys.analytics.memberPerformance(teamId, days),
    queryFn: () => api.getMemberPerformance(teamId, days),
    enabled: !!teamId,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCategoryStats(days = 30) {
  return useQuery({
    queryKey: queryKeys.analytics.categoryStats(days),
    queryFn: () => api.getCategoryStats(days),
    staleTime: 5 * 60 * 1000,
  });
}

export function useNeighborhoodStats(days = 30, limit = 5) {
  return useQuery({
    queryKey: ['neighborhood-stats', days, limit],
    queryFn: () => api.getNeighborhoodStats(days, limit),
    staleTime: 5 * 60 * 1000,
  });
}

export function useFeedbackTrends(days = 30) {
  return useQuery({
    queryKey: queryKeys.analytics.feedbackTrends(days),
    queryFn: () => api.getFeedbackTrends(days),
    staleTime: 5 * 60 * 1000,
  });
}

export function useQuarterlyReport(year: number, quarter: number) {
  return useQuery({
    queryKey: queryKeys.analytics.quarterlyReport(year, quarter),
    queryFn: () => api.getQuarterlyReport(year, quarter),
    enabled: !!year && !!quarter && quarter >= 1 && quarter <= 4,
    staleTime: 10 * 60 * 1000, // Reports can be cached for 10 minutes
  });
}
