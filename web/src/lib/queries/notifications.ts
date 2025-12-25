import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "./keys";
import * as api from "@/lib/api/client";

// ============================================================================
// NOTIFICATION QUERIES
// ============================================================================

interface NotificationListParams {
  unread_only?: boolean;
  page?: number;
  page_size?: number;
}

interface QueryOptions {
  enabled?: boolean;
}

export function useNotifications(
  params?: NotificationListParams,
  options?: QueryOptions
) {
  return useQuery({
    queryKey: queryKeys.notifications.list(params),
    queryFn: () => api.getNotifications(params),
    enabled: options?.enabled ?? true,
    refetchInterval: 10000,
    staleTime: 5000,
  });
}

export function useUnreadNotificationCount(options?: QueryOptions) {
  return useQuery({
    queryKey: queryKeys.notifications.unreadCount(),
    queryFn: () => api.getUnreadNotificationCount(),
    enabled: options?.enabled ?? true,
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

// ============================================================================
// NOTIFICATION MUTATIONS
// ============================================================================

export function useMarkNotificationAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) =>
      api.markNotificationAsRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.lists(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.unreadCount(),
      });
    },
  });
}

export function useMarkAllNotificationsAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.markAllNotificationsAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.lists(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.unreadCount(),
      });
    },
  });
}

export function useDeleteNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) => api.deleteNotification(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.lists(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.unreadCount(),
      });
    },
  });
}

