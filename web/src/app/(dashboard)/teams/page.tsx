"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import {
  useAddTeamMember,
  useCreateTeam,
  useDeleteTeam,
  useRemoveTeamMember,
  useTeam,
  useTeams,
  useTeamPerformance,
} from "@/lib/queries";
import {
  useUsers,
  useCreateUser,
  useUpdateUserRole,
  useDeleteUser,
} from "@/lib/queries/users";
import { useCategories } from "@/lib/queries/categories";
import { useDistricts } from "@/lib/queries/districts";
import { UserRole } from "@/lib/api/types";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/error-state";
import {
  Plus,
  Trash2,
  Users,
  UserPlus,
  UserMinus,
  ChevronDown,
  ChevronUp,
  Loader2,
} from "lucide-react";

type AnyTeamListResponse =
  | { items: any[]; total?: number }
  | any[];

/** getTeams() response'u bazen {items: []} bazen direkt [] olabiliyor */
function normalizeTeams(data: AnyTeamListResponse | undefined): any[] {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (Array.isArray((data as any).items)) return (data as any).items;
  return [];
}

export default function TeamsPage() {
  const teamsQuery = useTeams();
  const createTeamMut = useCreateTeam();
  const deleteTeamMut = useDeleteTeam();

  // Team performance (workload/open tickets) -> Teams sayfasında göstereceğiz
  // İstersen 7/30/90 gibi yapabilirsin; şimdilik "son 30 gün" mantığında
  const [days] = useState(30);
  const teamPerfQuery = useTeamPerformance(days);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<string[]>([]);
  const [selectedDistrictIds, setSelectedDistrictIds] = useState<string[]>([]);

  // hangi team expanded?
  const [expandedTeamId, setExpandedTeamId] = useState<string | null>(null);

  // Fetch categories and districts
  const categoriesQuery = useCategories(false); // Get all categories
  const districtsQuery = useDistricts();

  // Create user form state
  const [showCreateUserForm, setShowCreateUserForm] = useState(false);

  const teams = normalizeTeams(teamsQuery.data as AnyTeamListResponse);

  // team_id -> open ticket count map (analytics'ten)
  const openByTeamId = useMemo(() => {
    const map = new Map<string, number>();
    const items = (teamPerfQuery.data as any)?.items ?? (teamPerfQuery.data as any)?.teams ?? [];
    for (const t of items) {
      const open = Math.max(0, (t.total_assigned ?? 0) - (t.total_resolved ?? 0));
      if (t.team_id) map.set(t.team_id, open);
    }
    return map;
  }, [teamPerfQuery.data]);

  async function onAddTeam() {
    const n = name.trim();
    if (!n) return;

    await createTeamMut.mutateAsync({
      name: n,
      description: description.trim() ? description.trim() : null,
      category_ids: selectedCategoryIds,
      district_ids: selectedDistrictIds,
    });

    setName("");
    setDescription("");
    setSelectedCategoryIds([]);
    setSelectedDistrictIds([]);
  }

  async function onDeleteTeam(teamId: string) {
    await deleteTeamMut.mutateAsync(teamId);
    if (expandedTeamId === teamId) setExpandedTeamId(null);
  }

  const isLoadingList = teamsQuery.isLoading;
  const isErrorList = teamsQuery.isError;

  return (
    <div className="space-y-6">
      {/* Create User Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Create Support Staff</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCreateUserForm(!showCreateUserForm)}
          >
            {showCreateUserForm ? "Hide Form" : "New Staff"}
          </Button>
        </CardHeader>

        {showCreateUserForm && (
          <CardContent>
            <CreateUserForm onSuccess={() => setShowCreateUserForm(false)} />
          </CardContent>
        )}
      </Card>

      {/* Staff Management Section */}
      <Card>
        <CardHeader>
          <CardTitle>Manage Support Staff</CardTitle>
        </CardHeader>
        <CardContent>
          <StaffManagementPanel teams={teams} />
        </CardContent>
      </Card>

      {/* Teams Section */}
      <Card>
        <CardHeader>
          <CardTitle>Manage Teams</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* add team form */}
          <div className="grid gap-4">
            <div className="grid gap-2 sm:grid-cols-2">
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
            </div>

            {/* Categories Multi-Select */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Categories (Select all that apply)</label>
              <div className="flex flex-wrap gap-2">
                {categoriesQuery.isLoading ? (
                  <span className="text-sm text-muted-foreground">Loading categories...</span>
                ) : categoriesQuery.isError ? (
                  <span className="text-sm text-destructive">Failed to load categories</span>
                ) : (
                  (categoriesQuery.data?.items || []).map((category: any) => (
                    <label
                      key={category.id}
                      className="flex cursor-pointer items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm hover:bg-accent"
                    >
                      <input
                        type="checkbox"
                        checked={selectedCategoryIds.includes(category.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedCategoryIds([...selectedCategoryIds, category.id]);
                          } else {
                            setSelectedCategoryIds(selectedCategoryIds.filter((id) => id !== category.id));
                          }
                        }}
                        className="h-4 w-4"
                      />
                      <span>{category.name}</span>
                    </label>
                  ))
                )}
              </div>
            </div>

            {/* Districts Multi-Select */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Districts (Select all that apply)</label>
              <div className="flex flex-wrap gap-2">
                {districtsQuery.isLoading ? (
                  <span className="text-sm text-muted-foreground">Loading districts...</span>
                ) : districtsQuery.isError ? (
                  <span className="text-sm text-destructive">Failed to load districts</span>
                ) : (
                  (districtsQuery.data?.items || []).map((district: any) => (
                    <label
                      key={district.id}
                      className="flex cursor-pointer items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm hover:bg-accent"
                    >
                      <input
                        type="checkbox"
                        checked={selectedDistrictIds.includes(district.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedDistrictIds([...selectedDistrictIds, district.id]);
                          } else {
                            setSelectedDistrictIds(selectedDistrictIds.filter((id) => id !== district.id));
                          }
                        }}
                        className="h-4 w-4"
                      />
                      <span>{district.name}, {district.city}</span>
                    </label>
                  ))
                )}
              </div>
            </div>

            <Button
              onClick={onAddTeam}
              disabled={createTeamMut.isPending || !name.trim()}
              className="w-full sm:w-auto"
            >
              {createTeamMut.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Plus className="mr-2 h-4 w-4" />
              )}
              Add Team
            </Button>
          </div>

          {/* teams list */}
          {isLoadingList ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className="h-12 w-full rounded-lg bg-muted animate-pulse"
                />
              ))}
            </div>
          ) : isErrorList ? (
            <ErrorState
              title="Failed to load teams"
              message="Please try again."
              onRetry={teamsQuery.refetch}
            />
          ) : teams.length === 0 ? (
            <p className="text-sm text-muted-foreground">No teams yet.</p>
          ) : (
            <div className="space-y-3">
              {teams.map((t: any) => {
                const openTickets = openByTeamId.get(t.id) ?? 0;

                return (
                  <TeamRow
                    key={t.id}
                    teamId={t.id}
                    name={t.name}
                    description={t.description ?? null}
                    memberCount={t.member_count ?? t.memberCount ?? 0}
                    openTicketCount={openTickets}
                    isExpanded={expandedTeamId === t.id}
                    onToggle={() =>
                      setExpandedTeamId((prev) => (prev === t.id ? null : t.id))
                    }
                    onDelete={() => onDeleteTeam(t.id)}
                    isDeleting={deleteTeamMut.isPending}
                    isDeletingThis={
                      deleteTeamMut.isPending &&
                      (deleteTeamMut.variables as any) === t.id
                    }
                    analyticsLoading={teamPerfQuery.isLoading}
                  />
                );
              })}
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
  openTicketCount: number;

  isExpanded: boolean;
  onToggle: () => void;
  onDelete: () => void;

  isDeleting: boolean;
  isDeletingThis: boolean;
  analyticsLoading: boolean;
}) {
  return (
    <div className="rounded-lg border border-border">
      <div className="flex items-center justify-between gap-3 px-3 py-3">
        <div className="min-w-0">
          <div className="font-medium text-foreground truncate">{props.name}</div>
          <div className="text-xs text-muted-foreground truncate">
            {props.description ?? "No description"} • {props.memberCount} members •{" "}
            {props.analyticsLoading ? "…" : `${props.openTicketCount} open`}
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
            {props.isDeletingThis ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="mr-2 h-4 w-4" />
            )}
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

function CreateUserForm({ onSuccess }: { onSuccess: () => void }) {
  const createUserMut = useCreateUser();
  const teamsQuery = useTeams();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("+90");
  const [selectedTeamId, setSelectedTeamId] = useState<string>("");

  const teams = normalizeTeams(teamsQuery.data as AnyTeamListResponse);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!name.trim() || !email.trim() || !password.trim() || phoneNumber.length !== 13) {
      toast.error("Please fill all required fields correctly");
      return;
    }

    try {
      console.log("Creating user with data:", {
        name: name.trim(),
        email: email.trim(),
        phone_number: phoneNumber,
        role: UserRole.SUPPORT,
        team_id: selectedTeamId || undefined,
      });

      await createUserMut.mutateAsync({
        name: name.trim(),
        email: email.trim(),
        password: password.trim(),
        phone_number: phoneNumber,
        role: UserRole.SUPPORT,
        team_id: selectedTeamId || undefined,
      });

      toast.success(`Support staff ${name} created successfully!`);
      
      // Reset form
      setName("");
      setEmail("");
      setPassword("");
      setPhoneNumber("+90");
      setSelectedTeamId("");
      
      onSuccess();
    } catch (error: any) {
      console.error("Failed to create user:", error);
      const errorMessage = error?.message || error?.detail || "Failed to create user";
      toast.error(errorMessage);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Full Name <span className="text-destructive">*</span>
          </label>
          <input
            type="text"
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
            placeholder="Ahmet Yılmaz"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Email <span className="text-destructive">*</span>
          </label>
          <input
            type="email"
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
            placeholder="ahmet@sosoft.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Phone Number <span className="text-destructive">*</span>
          </label>
          <input
            type="tel"
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
            placeholder="+905551234567"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            pattern="^\+90[0-9]{10}$"
            required
          />
          <p className="text-xs text-muted-foreground">Format: +90XXXXXXXXXX</p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Password <span className="text-destructive">*</span>
          </label>
          <input
            type="password"
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
            placeholder="Min 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />
        </div>

        <div className="space-y-2 sm:col-span-2">
          <label className="text-sm font-medium text-foreground">
            Assign to Team (optional)
          </label>
          <select
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
            value={selectedTeamId}
            onChange={(e) => setSelectedTeamId(e.target.value)}
          >
            <option value="">No team (assign later)</option>
            {teams.map((t: any) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex justify-end gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={onSuccess}
          disabled={createUserMut.isPending}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={createUserMut.isPending}>
          {createUserMut.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating...
            </>
          ) : (
            <>
              <UserPlus className="mr-2 h-4 w-4" />
              Create Staff
            </>
          )}
        </Button>
      </div>
    </form>
  );
}

function StaffManagementPanel({ teams }: { teams: any[] }) {
  const supportUsersQuery = useUsers({ role: UserRole.SUPPORT, page_size: 200 });
  const updateRoleMut = useUpdateUserRole();
  const deleteUserMut = useDeleteUser();

  const supportUsers = supportUsersQuery.data?.items ?? [];

  async function handleTeamChange(userId: string, newTeamId: string | null, userName: string) {
    try {
      await updateRoleMut.mutateAsync({
        userId,
        data: {
          role: UserRole.SUPPORT,
          team_id: newTeamId || undefined,
        },
      });
      toast.success(`Updated ${userName}'s team`);
    } catch (error: any) {
      toast.error(error?.message || "Failed to update team");
    }
  }

  async function handleDeleteUser(userId: string, userName: string) {
    if (!confirm(`Are you sure you want to delete ${userName}?`)) {
      return;
    }

    try {
      await deleteUserMut.mutateAsync(userId);
      toast.success(`Deleted ${userName}`);
    } catch (error: any) {
      toast.error(error?.message || "Failed to delete user");
    }
  }

  if (supportUsersQuery.isLoading) {
    return <div className="space-y-2">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="h-16 w-full rounded-lg bg-muted animate-pulse" />
      ))}
    </div>;
  }

  if (supportUsersQuery.isError) {
    return (
      <ErrorState
        title="Failed to load staff"
        message="Please try again."
        onRetry={supportUsersQuery.refetch}
      />
    );
  }

  if (supportUsers.length === 0) {
    return <p className="text-sm text-muted-foreground">No support staff yet.</p>;
  }

  return (
    <div className="space-y-3">
      {supportUsers.map((user: any) => {
        const currentTeam = teams.find((t) => t.id === user.team_id);
        
        return (
          <div
            key={user.id}
            className="flex items-center justify-between gap-3 rounded-lg border border-border px-4 py-3"
          >
            <div className="flex-1 min-w-0">
              <div className="font-medium text-foreground truncate">{user.name}</div>
              <div className="text-xs text-muted-foreground truncate">
                {user.email} • {user.phone_number}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <select
                className="rounded-lg border border-border bg-background px-3 py-2 text-sm min-w-[200px]"
                value={user.team_id || ""}
                onChange={(e) => handleTeamChange(user.id, e.target.value || null, user.name)}
                disabled={updateRoleMut.isPending}
              >
                <option value="">No team</option>
                {teams.map((t: any) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>

              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDeleteUser(user.id, user.name)}
                disabled={deleteUserMut.isPending}
              >
                {deleteUserMut.isPending && deleteUserMut.variables === user.id ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="mr-2 h-4 w-4" />
                )}
                Delete
              </Button>
            </div>
          </div>
        );
      })}
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
    const memberIds = new Set(teamMembers.map((m: any) => m.id));
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
          {addMut.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <UserPlus className="mr-2 h-4 w-4" />
          )}
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
            {teamMembers.map((m: any) => (
              <div
                key={m.id}
                className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium text-foreground truncate">
                    {m.name}
                  </div>
                  <div className="text-xs text-muted-foreground truncate">
                    {/* TeamMemberResponse backend'de email değil phone_number var */}
                    {(m.phone_number as string | undefined) ?? "No phone"} • {m.role}
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRemoveMember(m.id)}
                  disabled={removeMut.isPending}
                >
                  {removeMut.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <UserMinus className="mr-2 h-4 w-4" />
                  )}
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
