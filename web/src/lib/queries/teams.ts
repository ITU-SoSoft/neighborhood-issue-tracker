import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createTeam,
  deleteTeam,
  getTeamById,
  getTeams,
  updateTeam,
  addTeamMember,
  removeTeamMember,
} from "@/lib/api/client";
import type {
  TeamCreate,
  TeamDetailResponse,
  TeamListResponse,
  TeamUpdate,
} from "@/lib/api/types";

// ------------------------------------------------------------
// Query Keys
// ------------------------------------------------------------
const TEAM_KEYS = {
  all: ["teams"] as const,
  list: () => ["teams"] as const,
  detail: (teamId: string) => ["teams", teamId] as const,
};

type QueryOptions = { enabled?: boolean };

// ------------------------------------------------------------
// Queries
// ------------------------------------------------------------

// List
export function useTeams(options?: QueryOptions) {
  return useQuery<TeamListResponse>({
    queryKey: TEAM_KEYS.list(),
    queryFn: () => getTeams(),
    enabled: options?.enabled ?? true,
  });
}

// Detail
export function useTeam(teamId: string, options?: QueryOptions) {
  return useQuery<TeamDetailResponse>({
    queryKey: TEAM_KEYS.detail(teamId),
    queryFn: () => getTeamById(teamId),
    enabled: (options?.enabled ?? true) && !!teamId,
  });
}

// ------------------------------------------------------------
// Mutations
// ------------------------------------------------------------

/**
 * After team changes, these parts may change:
 * - teams list/detail
 * - analytics (workload/team performance)
 * - users list (team_id / team_name display)
 */
async function invalidateAfterTeamChange(
  qc: ReturnType<typeof useQueryClient>,
  teamId?: string,
) {
  await qc.invalidateQueries({ queryKey: TEAM_KEYS.all });
  if (teamId) {
    await qc.invalidateQueries({ queryKey: TEAM_KEYS.detail(teamId) });
  }
  // Your project already uses queryKeys for analytics/users in other files,
  // but here we keep it generic to avoid circular imports.
  await qc.invalidateQueries({ queryKey: ["analytics"] });
  await qc.invalidateQueries({ queryKey: ["users"] });
}

// Create
export function useCreateTeam() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (data: TeamCreate) => createTeam(data),

    onMutate: async (newTeam) => {
      await qc.cancelQueries({ queryKey: TEAM_KEYS.list() });

      const previous = qc.getQueryData<TeamListResponse>(TEAM_KEYS.list());

      // Optimistic: push a temporary item to list if list exists
      if (previous) {
        qc.setQueryData<TeamListResponse>(TEAM_KEYS.list(), {
          ...previous,
          items: [
            {
              // temporary id (backend will overwrite on refetch)
              id: `temp-${Date.now()}`,
              name: newTeam.name,
              description: newTeam.description ?? null,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              member_count: 0,
            },
            ...previous.items,
          ],
          total: previous.total + 1,
        });
      }

      return { previous };
    },

    onError: (_err, _newTeam, ctx) => {
      if (ctx?.previous) {
        qc.setQueryData(TEAM_KEYS.list(), ctx.previous);
      }
    },

    onSuccess: async () => {
      await invalidateAfterTeamChange(qc);
    },
  });
}

// Update
export function useUpdateTeam(teamId: string) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (data: TeamUpdate) => updateTeam(teamId, data),

    onMutate: async (patch) => {
      await qc.cancelQueries({ queryKey: TEAM_KEYS.detail(teamId) });
      await qc.cancelQueries({ queryKey: TEAM_KEYS.list() });

      const prevDetail = qc.getQueryData<TeamDetailResponse>(
        TEAM_KEYS.detail(teamId),
      );
      const prevList = qc.getQueryData<TeamListResponse>(TEAM_KEYS.list());

      // Optimistic detail
      if (prevDetail) {
        qc.setQueryData<TeamDetailResponse>(TEAM_KEYS.detail(teamId), {
          ...prevDetail,
          name: patch.name ?? prevDetail.name,
          description: patch.description ?? prevDetail.description,
        });
      }

      // Optimistic list
      if (prevList) {
        qc.setQueryData<TeamListResponse>(TEAM_KEYS.list(), {
          ...prevList,
          items: prevList.items.map((t) =>
            t.id === teamId
              ? {
                  ...t,
                  name: patch.name ?? t.name,
                  description: patch.description ?? t.description,
                }
              : t,
          ),
        });
      }

      return { prevDetail, prevList };
    },

    onError: (_err, _patch, ctx) => {
      if (ctx?.prevDetail)
        qc.setQueryData(TEAM_KEYS.detail(teamId), ctx.prevDetail);
      if (ctx?.prevList) qc.setQueryData(TEAM_KEYS.list(), ctx.prevList);
    },

    onSuccess: async () => {
      await invalidateAfterTeamChange(qc, teamId);
    },
  });
}

// Delete
export function useDeleteTeam() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (teamId: string) => deleteTeam(teamId),

    onMutate: async (teamId) => {
      await qc.cancelQueries({ queryKey: TEAM_KEYS.list() });

      const prevList = qc.getQueryData<TeamListResponse>(TEAM_KEYS.list());

      if (prevList) {
        qc.setQueryData<TeamListResponse>(TEAM_KEYS.list(), {
          ...prevList,
          items: prevList.items.filter((t) => t.id !== teamId),
          total: prevList.total - 1,
        });
      }

      return { prevList };
    },

    onError: (_err, _teamId, ctx) => {
      if (ctx?.prevList) qc.setQueryData(TEAM_KEYS.list(), ctx.prevList);
    },

    onSuccess: async (_data, teamId) => {
      // Also remove detail cache
      qc.removeQueries({ queryKey: TEAM_KEYS.detail(teamId) });
      await invalidateAfterTeamChange(qc);
    },
  });
}

// Add member
export function useAddTeamMember(teamId: string) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) => addTeamMember(teamId, userId),

    onSuccess: async () => {
      await invalidateAfterTeamChange(qc, teamId);
    },
  });
}

// Remove member
export function useRemoveTeamMember(teamId: string) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) => removeTeamMember(teamId, userId),

    onSuccess: async () => {
      await invalidateAfterTeamChange(qc, teamId);
    },
  });
}
