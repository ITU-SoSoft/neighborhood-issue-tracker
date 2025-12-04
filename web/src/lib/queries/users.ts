import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "./keys";
import * as api from "@/lib/api/client";
import { UserRole, UserUpdate, UserRoleUpdate } from "@/lib/api/types";

// ============================================================================
// USER QUERIES
// ============================================================================

interface UserListParams {
  role?: UserRole;
  team_id?: string;
  page?: number;
  page_size?: number;
}

export function useUsers(params: UserListParams = {}) {
  return useQuery({
    queryKey: queryKeys.users.list(params),
    queryFn: () => api.getUsers(params),
  });
}

export function useUser(userId: string) {
  return useQuery({
    queryKey: queryKeys.users.detail(userId),
    queryFn: () => api.getUserById(userId),
    enabled: !!userId,
  });
}

export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.users.me(),
    queryFn: () => api.getCurrentUser(),
    retry: false, // Don't retry if not authenticated
  });
}

// ============================================================================
// USER MUTATIONS
// ============================================================================

export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: UserUpdate }) =>
      api.updateUser(userId, data),
    onSuccess: (updatedUser, { userId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.users.detail(userId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.users.me() });
      queryClient.invalidateQueries({ queryKey: queryKeys.users.lists() });
      // Update the cache directly for immediate UI update
      queryClient.setQueryData(queryKeys.users.detail(userId), updatedUser);
    },
  });
}

export function useUpdateUserRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: UserRoleUpdate }) =>
      api.updateUserRole(userId, data),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.users.detail(userId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.users.lists() });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) => api.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.lists() });
    },
  });
}
