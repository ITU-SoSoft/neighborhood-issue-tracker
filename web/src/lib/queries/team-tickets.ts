import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "./keys";
import * as api from "@/lib/api/client";

export function useTeamTickets(teamId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.tickets.byTeam(teamId),
    queryFn: () => api.getTicketsByTeam(teamId),
    enabled,
  });
}

export function useReassignTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ticketId, teamId }: { ticketId: string; teamId: string }) =>
      api.assignTicket(ticketId, { team_id: teamId }),
    onSuccess: (_, variables) => {
      // Invalidate all team tickets queries
      queryClient.invalidateQueries({ queryKey: queryKeys.tickets.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.teams.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics.all });
    },
  });
}
