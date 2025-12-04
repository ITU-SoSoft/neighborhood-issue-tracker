import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "./keys";
import * as api from "@/lib/api/client";
import { CategoryCreate, CategoryUpdate } from "@/lib/api/types";

// ============================================================================
// CATEGORY QUERIES
// ============================================================================

export function useCategories(activeOnly = true) {
  return useQuery({
    queryKey: queryKeys.categories.list(activeOnly),
    queryFn: () => api.getCategories(activeOnly),
    staleTime: 5 * 60 * 1000, // Categories rarely change, cache for 5 minutes
  });
}

export function useCategory(categoryId: string) {
  return useQuery({
    queryKey: queryKeys.categories.detail(categoryId),
    queryFn: () => api.getCategoryById(categoryId),
    enabled: !!categoryId,
  });
}

// ============================================================================
// CATEGORY MUTATIONS
// ============================================================================

export function useCreateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CategoryCreate) => api.createCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.categories.all });
    },
  });
}

export function useUpdateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      categoryId,
      data,
    }: {
      categoryId: string;
      data: CategoryUpdate;
    }) => api.updateCategory(categoryId, data),
    onSuccess: (_, { categoryId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.categories.detail(categoryId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.categories.all });
    },
  });
}
