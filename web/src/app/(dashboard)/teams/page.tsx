"use client";

import { useMemo, useState } from "react";
import { useCreateTeam, useDeleteTeam, useTeam, useTeams, useAddTeamMember, useRemoveTeamMember } from "@/lib/queries";
import { useUsers } from "@/lib/queries/users"; // eğer index'ten export ediyorsan "@/lib/queries" da olur
import { UserRole } from "@/lib/api/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/error-state";
import { Plus, Trash2, Users, UserPlus, UserMinus, ChevronDown, ChevronUp } from "lucide-react";

export default function TeamsPage() {
  const teamsQuery = useTeams();
  const createTeamMut = useCreateTeam();
  const deleteTeamMut = useDeleteTeam();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  // hangi team expanded?
  const [expandedTeamId, setExpandedTeamId] = useState<string | null>(null);

  const teams = teamsQuery.data?.items ?? [];

  async function onAddTeam() {
    const n = name.trim();
    if (!n) return;

    await createTeamMut.mutateAsync({
      name: n,
      description: description.trim() ? description.trim() : null,
    });

    setName("");
    setDescription("");
  }

  async function onDeleteTeam(teamId: string) {
    await deleteTeamMut.mutateAsync(teamId);
    if (expandedTeamId === teamId) setExpandedTeamId(null);
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Manage Teams</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* add team form */}
          <div className="grid gap-2 sm:grid-cols-[1fr,1.5fr,auto]">
            <input
              className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
              placeholder="Team name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <input
              className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
              placeholder="Description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <Button
              onClick={onAddTeam}
              disabled={createTeamMut.isPending || !name.trim()}
            >
              <Plus className="mr-2 h-4 w-4" />
              Add
            </Button>
          </div>

          {/* teams list */}
          {teamsQuery.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className="h-12 w-full rounded-lg bg-muted animate-pulse"
                />
              ))}
            </div>
          ) : teamsQuery.isError ? (
            <ErrorState
              title="Failed to load teams"
              message="Please try again."
              onRetry={teamsQuery.refetch}
            />
          ) : teams.length === 0 ? (
            <p className="text-sm text-muted-foreground">No teams yet.</p>
          ) : (
            <div className="space-y-3">
              {teams.map((t) => (
                <TeamRow
                  key={t.id}
                  teamId={t.id}
                  name={t.name}
                  description={t.description}
                  memberCount={t.member_count}
                  activeTicketCount={t.active_ticket_count}
                  isExpanded={expandedTeamId === t.id}
                  onToggle={() =>
                    setExpandedTeamId((prev) => (prev === t.id ? null : t.id))
                  }
                  onDelete={() => onDeleteTeam(t.id)}
                  isDeleting={deleteTeamMut.isPending}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function TeamRow(props: {
  teamId: string;
  name: string;
  description: string | null;
  memberCount: number;
  activeTicketCount: number;
  isExpanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
  isDeleting: boolean;
}) {
  return (
    <div className="rounded-lg border border-border">
      <div className="flex items-center justify-between gap-3 px-3 py-3">
        <div className="min-w-0">
          <div className="font-medium text-foreground truncate">{props.name}</div>
          <div className="text-xs text-muted-foreground truncate">
            {props.description ?? "No description"} • {props.memberCount} members •{" "}
            {props.activeTicketCount} open
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={props.onToggle}>
            <Users className="mr-2 h-4 w-4" />
            Members
            {props.isExpanded ? (
              <ChevronUp className="ml-2 h-4 w-4" />
            ) : (
              <ChevronDown className="ml-2 h-4 w-4" />
            )}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={props.onDelete}
            disabled={props.isDeleting}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      {props.isExpanded && (
        <div className="border-t border-border px-3 py-4">
          <TeamMembersPanel teamId={props.teamId} />
        </div>
      )}
    </div>
  );
}

function TeamMembersPanel({ teamId }: { teamId: string }) {
  // team detail (members)
  const teamQuery = useTeam(teamId);

  // support users list
  const usersQuery = useUsers({ role: UserRole.SUPPORT, page_size: 200 });

  const addMut = useAddTeamMember(teamId);
  const removeMut = useRemoveTeamMember(teamId);

  const [selectedUserId, setSelectedUserId] = useState<string>("");

  const teamMembers = teamQuery.data?.members ?? [];

  const supportUsers = usersQuery.data?.items ?? [];

  // only show users that are not already in this team
  const availableSupportUsers = useMemo(() => {
    const memberIds = new Set(teamMembers.map((m) => m.id));
    return supportUsers.filter((u) => !memberIds.has(u.id));
  }, [supportUsers, teamMembers]);

  async function onAddMember() {
    if (!selectedUserId) return;
    await addMut.mutateAsync(selectedUserId);
    setSelectedUserId("");
  }

  async function onRemoveMember(userId: string) {
    await removeMut.mutateAsync(userId);
  }

  if (teamQuery.isLoading) {
    return <div className="h-16 rounded bg-muted animate-pulse" />;
  }

  if (teamQuery.isError) {
    return (
      <ErrorState
        title="Failed to load team details"
        message="Please try again."
        onRetry={teamQuery.refetch}
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Add member */}
      <div className="grid gap-2 sm:grid-cols-[1fr,auto]">
        <select
          className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
          value={selectedUserId}
          onChange={(e) => setSelectedUserId(e.target.value)}
          disabled={usersQuery.isLoading || addMut.isPending}
        >
          <option value="">
            {usersQuery.isLoading ? "Loading staff..." : "Select staff to add"}
          </option>
          {availableSupportUsers.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name} {u.email ? `(${u.email})` : ""}
            </option>
          ))}
        </select>

        <Button
          onClick={onAddMember}
          disabled={!selectedUserId || addMut.isPending}
        >
          <UserPlus className="mr-2 h-4 w-4" />
          Add Staff
        </Button>
      </div>

      {/* Members list */}
      <div className="space-y-2">
        <div className="text-sm font-medium text-foreground">Team Members</div>

        {teamMembers.length === 0 ? (
          <p className="text-sm text-muted-foreground">No members in this team.</p>
        ) : (
          <div className="space-y-2">
            {teamMembers.map((m) => (
              <div
                key={m.id}
                className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium text-foreground truncate">
                    {m.name}
                  </div>
                  <div className="text-xs text-muted-foreground truncate">
                    {m.email ?? "No email"} • {m.role}
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRemoveMember(m.id)}
                  disabled={removeMut.isPending}
                >
                  <UserMinus className="mr-2 h-4 w-4" />
                  Remove
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}