"use client";

import { useState } from "react";
import { useTeamTickets, useReassignTicket } from "@/lib/queries/team-tickets";
import { useTeams } from "@/lib/queries/teams";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Loader2, ArrowRightCircle } from "lucide-react";
import Link from "next/link";
import type { Ticket } from "@/lib/api/types";

interface TeamTicketsPanelProps {
  teamId: string;
  isExpanded?: boolean;
}

export function TeamTicketsPanel({
  teamId,
  isExpanded = true,
}: TeamTicketsPanelProps) {
  const ticketsQuery = useTeamTickets(teamId, isExpanded);
  const allTeamsQuery = useTeams();
  const reassignMut = useReassignTicket();
  const [reassigningTicketId, setReassingTicketId] = useState<string | null>(
    null,
  );

  const allTickets = ticketsQuery.data?.items ?? [];
  // Filter out RESOLVED tickets
  const tickets = allTickets.filter(
    (ticket: Ticket) => ticket.status !== "RESOLVED",
  );
  const allTeams = Array.isArray(allTeamsQuery.data)
    ? allTeamsQuery.data
    : ((allTeamsQuery.data as any)?.items ?? []);
  const otherTeams = allTeams.filter((t: any) => t.id !== teamId);

  async function handleReassign(ticketId: string, newTeamId: string) {
    setReassingTicketId(ticketId);
    try {
      await reassignMut.mutateAsync({ ticketId, teamId: newTeamId });
    } finally {
      setReassingTicketId(null);
    }
  }

  if (ticketsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (ticketsQuery.isError) {
    return (
      <div className="text-sm text-destructive">
        Failed to load tickets. Please try again.
      </div>
    );
  }

  if (tickets.length === 0) {
    return (
      <div className="text-sm text-muted-foreground py-4">
        No tickets assigned to this team.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium mb-3">
        Assigned Tickets ({tickets.length})
      </h4>
      {tickets.map((ticket: Ticket) => (
        <div
          key={ticket.id}
          className="flex items-center justify-between gap-3 p-3 rounded-lg border border-border bg-card"
        >
          <div className="flex-1 min-w-0">
            <Link
              href={`/tickets/${ticket.id}`}
              className="text-sm font-medium hover:underline truncate block"
            >
              {ticket.title}
            </Link>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline" className="text-xs">
                {ticket.status}
              </Badge>
              {ticket.category_name && (
                <span className="text-xs text-muted-foreground">
                  {ticket.category_name}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Select
              disabled={
                reassigningTicketId === ticket.id || otherTeams.length === 0
              }
              onValueChange={(newTeamId) =>
                handleReassign(ticket.id, newTeamId)
              }
            >
              <SelectTrigger className="w-[180px] h-9">
                <SelectValue placeholder="Reassign to..." />
              </SelectTrigger>
              <SelectContent>
                {otherTeams.map((team: any) => (
                  <SelectItem key={team.id} value={team.id}>
                    {team.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {reassigningTicketId === ticket.id && (
              <Loader2 className="h-4 w-4 animate-spin" />
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
