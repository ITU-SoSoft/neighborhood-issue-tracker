import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "./keys";
import * as api from "@/lib/api/client";

// ============================================================================
// DISTRICT QUERIES
// ============================================================================

export function useDistricts() {
  return useQuery({
    queryKey: queryKeys.districts.all,
    queryFn: () => api.getDistricts(),
    staleTime: 10 * 60 * 1000, // Districts rarely change, cache for 10 minutes
  });
}

