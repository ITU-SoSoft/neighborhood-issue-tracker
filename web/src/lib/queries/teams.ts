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
import type { TeamCreate, TeamDetailResponse, TeamListResponse, TeamUpdate } from "@/lib/api/types";

// Liste
export function useTeams() {
  return useQuery<TeamListResponse>({
    queryKey: ["teams"],
    queryFn: () => getTeams(),
  });
}

// Detay
export function useTeam(teamId: string) {
  return useQuery<TeamDetailResponse>({
    queryKey: ["teams", teamId],
    queryFn: () => getTeamById(teamId),
    enabled: !!teamId,
  });
}

// Create
export function useCreateTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TeamCreate) => createTeam(data),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["teams"] });
    },
  });
}

// Update
export function useUpdateTeam(teamId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TeamUpdate) => updateTeam(teamId, data),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["teams"] });
      await qc.invalidateQueries({ queryKey: ["teams", teamId] });
    },
  });
}

// Delete
export function useDeleteTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (teamId: string) => deleteTeam(teamId),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["teams"] });
    },
  });
}

// Add member
export function useAddTeamMember(teamId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => addTeamMember(teamId, userId),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["teams"] });
      await qc.invalidateQueries({ queryKey: ["teams", teamId] });
    },
  });
}

// Remove member
export function useRemoveTeamMember(teamId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => removeTeamMember(teamId, userId),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["teams"] });
      await qc.invalidateQueries({ queryKey: ["teams", teamId] });
    },
  });
}
