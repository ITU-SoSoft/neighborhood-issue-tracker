import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "./keys";
import * as api from "@/lib/api/client";
import { SavedAddressCreate, SavedAddressUpdate } from "@/lib/api/types";

// ============================================================================
// SAVED ADDRESS QUERIES
// ============================================================================

export function useSavedAddresses(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: queryKeys.addresses.list(),
    queryFn: () => api.getSavedAddresses(),
    enabled: options?.enabled ?? true,
  });
}

export function useSavedAddress(addressId: string) {
  return useQuery({
    queryKey: queryKeys.addresses.detail(addressId),
    queryFn: () => api.getSavedAddressById(addressId),
    enabled: !!addressId,
  });
}

// ============================================================================
// SAVED ADDRESS MUTATIONS
// ============================================================================

export function useCreateSavedAddress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SavedAddressCreate) => api.createSavedAddress(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.addresses.lists() });
    },
  });
}

export function useUpdateSavedAddress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      addressId,
      data,
    }: {
      addressId: string;
      data: SavedAddressUpdate;
    }) => api.updateSavedAddress(addressId, data),
    onSuccess: (_, { addressId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.addresses.detail(addressId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.addresses.lists() });
    },
  });
}

export function useDeleteSavedAddress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (addressId: string) => api.deleteSavedAddress(addressId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.addresses.lists() });
    },
  });
}

