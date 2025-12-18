"use client";

import { useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth/context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DashboardKPISkeleton, TicketCardSkeleton } from "@/components/shared/skeletons";
import { EmptyTickets } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import {
  useMyTickets,
  useAssignedTickets,
  useDashboardKPIs,
  useEscalations,
} from "@/lib/queries";
import { useHeatmap } from "@/lib/queries/analytics";
import {
  Ticket,
  TicketStatus,
  UserRole,
  EscalationStatus,
} from "@/lib/api/types";
import {
  formatDate,
  formatRelativeTime,
  getStatusVariant,
  getStatusLabel,
  formatPercentage,
  formatDuration,
  formatRating,
} from "@/lib/utils";
import {
  fadeInUp,
  staggerContainer,
  staggerItem,
  cardHover,
  cardTap,
} from "@/lib/animations";
import {
  Plus,
  Ticket as TicketIcon,
  Clock,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Star,
  Users,
  Loader2,
} from "lucide-react";

// Dynamically import the heatmap component to avoid SSR issues with Leaflet
const HeatmapVisualization = dynamic(
  () => import("@/components/map/heatmap-visualization").then((mod) => ({ default: mod.HeatmapVisualization })),
  {
    ssr: false,
    loading: () => (
      <div className="h-[400px] rounded-xl bg-muted flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    ),
  }
);

// ============================================================================
// SHARED COMPONENTS
// ============================================================================

interface KPICardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  iconBgClass: string;
}

function KPICard({ title, value, icon, iconBgClass }: KPICardProps) {
  return (
    <motion.div
      variants={staggerItem}
      whileHover={cardHover}
      whileTap={cardTap}
    >
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className={`rounded-full p-3 ${iconBgClass}`}>
              {icon}
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{title}</p>
              <p className="text-2xl font-semibold text-foreground">{value}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

interface TicketListItemProps {
  ticket: Ticket;
  showCategory?: boolean;
  showMeta?: boolean;
}

function TicketListItem({ ticket, showCategory = false, showMeta = true }: TicketListItemProps) {
  return (
    <motion.div variants={staggerItem}>
      <Link
        href={`/tickets/${ticket.id}`}
        className="block rounded-xl border border-border p-4 transition hover:border-primary/30 hover:bg-primary/5"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <h3 className="font-medium text-foreground truncate">{ticket.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground truncate">
              {showCategory && `${ticket.category_name} • `}
              {ticket.location.address || ticket.location.city}
            </p>
          </div>
          <Badge variant={getStatusVariant(ticket.status)}>
            {getStatusLabel(ticket.status)}
          </Badge>
        </div>
        {showMeta && (
          <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
            <span>{formatRelativeTime(ticket.created_at)}</span>
            <span>{ticket.comment_count} comments</span>
            <span>{ticket.follower_count} followers</span>
          </div>
        )}
      </Link>
    </motion.div>
  );
}

interface TicketListCardProps {
  title: string;
  viewAllHref: string;
  tickets: Ticket[];
  isLoading: boolean;
  isError: boolean;
  refetch: () => void;
  emptyAction?: () => void;
  showCategory?: boolean;
}

function TicketListCard({
  title,
  viewAllHref,
  tickets,
  isLoading,
  isError,
  refetch,
  emptyAction,
  showCategory = false,
}: TicketListCardProps) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeInUp}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-4">
          <CardTitle className="text-lg">{title}</CardTitle>
          <Link href={viewAllHref} className="text-sm text-primary hover:text-primary/80">
            View all
          </Link>
        </CardHeader>
        <CardContent className="pt-0">
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <TicketCardSkeleton key={i} />
              ))}
            </div>
          ) : isError ? (
            <ErrorState
              title="Failed to load"
              message="Could not load tickets. Please try again."
              onRetry={refetch}
            />
          ) : tickets.length === 0 ? (
            <EmptyTickets onCreateTicket={emptyAction} />
          ) : (
            <motion.div
              className="space-y-3"
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
            >
              {tickets.map((ticket) => (
                <TicketListItem key={ticket.id} ticket={ticket} showCategory={showCategory} />
              ))}
            </motion.div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ============================================================================
// CITIZEN DASHBOARD
// ============================================================================

function CitizenDashboard() {
  const { data, isLoading, isError, refetch } = useMyTickets({ page_size: 5 });
  const tickets = data?.items ?? [];

  const stats = {
    total: tickets.length,
    inProgress: tickets.filter((t) => t.status === TicketStatus.IN_PROGRESS).length,
    resolved: tickets.filter((t) => t.status === TicketStatus.RESOLVED || t.status === TicketStatus.CLOSED).length,
    pending: tickets.filter((t) => t.status === TicketStatus.NEW).length,
  };

  return (
    <motion.div
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {/* Welcome section */}
      <motion.div
        className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        variants={fadeInUp}
      >
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Welcome back!</h1>
          <p className="text-muted-foreground">Track and manage your neighborhood issues</p>
        </div>
        <Link href="/tickets/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Report Issue
          </Button>
        </Link>
      </motion.div>

      {/* Quick stats */}
      {isLoading ? (
        <DashboardKPISkeleton />
      ) : (
        <motion.div
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <KPICard
            title="Total Reports"
            value={stats.total}
            icon={<TicketIcon className="h-5 w-5 text-blue-600" />}
            iconBgClass="bg-blue-100"
          />
          <KPICard
            title="In Progress"
            value={stats.inProgress}
            icon={<Clock className="h-5 w-5 text-amber-600" />}
            iconBgClass="bg-amber-100"
          />
          <KPICard
            title="Resolved"
            value={stats.resolved}
            icon={<CheckCircle2 className="h-5 w-5 text-green-600" />}
            iconBgClass="bg-green-100"
          />
          <KPICard
            title="Pending"
            value={stats.pending}
            icon={<AlertTriangle className="h-5 w-5 text-muted-foreground" />}
            iconBgClass="bg-muted"
          />
        </motion.div>
      )}

      {/* Recent tickets */}
      <TicketListCard
        title="Recent Reports"
        viewAllHref="/tickets"
        tickets={tickets}
        isLoading={isLoading}
        isError={isError}
        refetch={refetch}
        showCategory
      />
    </motion.div>
  );
}

// ============================================================================
// SUPPORT DASHBOARD
// ============================================================================

function SupportDashboard() {
  const [activeTab, setActiveTab] = useState<"overview" | "heatmap">("overview");

  const ticketsQuery = useAssignedTickets({ page_size: 5 });
  const escalationsQuery = useEscalations({
    status_filter: EscalationStatus.PENDING,
    page_size: 5,
  });
  const kpisQuery = useDashboardKPIs(30);

  const assignedTickets = ticketsQuery.data?.items ?? [];
  const escalations = escalationsQuery.data?.items ?? [];
  const kpis = kpisQuery.data;

  const isLoading =
    ticketsQuery.isLoading || escalationsQuery.isLoading || kpisQuery.isLoading;

  return (
    <motion.div
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {/* Header + Tabs */}
      <motion.div variants={fadeInUp}>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Support Dashboard</h1>
            <p className="text-muted-foreground">
              Manage assigned tickets, escalations and neighborhood issues
            </p>
          </div>

          {/* Overview / Heatmap toggle */}
          <div className="inline-flex items-center rounded-full border bg-background p-1 text-xs">
            <button
              type="button"
              onClick={() => setActiveTab("overview")}
              className={`rounded-full px-4 py-1 transition ${
                activeTab === "overview"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              Overview
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("heatmap")}
              className={`rounded-full px-4 py-1 transition ${
                activeTab === "heatmap"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              Heatmap
            </button>
          </div>
        </div>
      </motion.div>

      {activeTab === "overview" ? (
        <>
          {/* KPI Cards */}
          {isLoading ? (
            <DashboardKPISkeleton />
          ) : (
            <motion.div
              className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
            >
              <KPICard
                title="Assigned"
                value={assignedTickets.length}
                icon={<TicketIcon className="h-5 w-5 text-blue-600" />}
                iconBgClass="bg-blue-100"
              />
              <KPICard
                title="Pending Escalations"
                value={escalations.length}
                icon={<AlertTriangle className="h-5 w-5 text-amber-600" />}
                iconBgClass="bg-amber-100"
              />
              <KPICard
                title="Resolution Rate"
                value={kpis ? formatPercentage(kpis.resolution_rate, 0) : "-"}
                icon={<TrendingUp className="h-5 w-5 text-green-600" />}
                iconBgClass="bg-green-100"
              />
              <KPICard
                title="Avg Rating"
                value={formatRating(kpis?.average_rating ?? null)}
                icon={<Star className="h-5 w-5 text-purple-600" />}
                iconBgClass="bg-purple-100"
              />
            </motion.div>
          )}

          {/* Assigned tickets + escalations */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Assigned Tickets */}
            <TicketListCard
              title="Assigned Tickets"
              viewAllHref="/tickets?assigned=me"
              tickets={assignedTickets}
              isLoading={ticketsQuery.isLoading}
              isError={ticketsQuery.isError}
              refetch={ticketsQuery.refetch}
            />

            {/* Pending Escalations */}
            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeInUp}
            >
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-4">
                  <CardTitle className="text-lg">Pending Escalations</CardTitle>
                  <Link
                    href="/escalations"
                    className="text-sm text-primary hover:text-primary/80"
                  >
                    View all
                  </Link>
                </CardHeader>
                <CardContent className="pt-0">
                  {escalationsQuery.isLoading ? (
                    <div className="space-y-3">
                      {Array.from({ length: 3 }).map((_, i) => (
                        <TicketCardSkeleton key={i} />
                      ))}
                    </div>
                  ) : escalations.length === 0 ? (
                    <p className="py-4 text-center text-muted-foreground">
                      No pending escalations
                    </p>
                  ) : (
                    <motion.div
                      className="space-y-3"
                      variants={staggerContainer}
                      initial="hidden"
                      animate="visible"
                    >
                      {escalations.map((escalation) => (
                        <motion.div key={escalation.id} variants={staggerItem}>
                          <Link
                            href={`/escalations/${escalation.id}`}
                            className="block rounded-lg border border-border p-3 transition hover:border-amber-300 hover:bg-amber-50"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <span className="font-medium text-foreground truncate">
                                {escalation.ticket_title}
                              </span>
                              <Badge variant="warning">Pending</Badge>
                            </div>
                            <p className="mt-1 text-xs text-muted-foreground">
                              By {escalation.requester_name} •{" "}
                              {formatDate(escalation.created_at)}
                            </p>
                          </Link>
                        </motion.div>
                      ))}
                    </motion.div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </>
      ) : (
        // Heatmap tab content – pure UI placeholder, analytics eklenebilir
        <motion.div variants={fadeInUp}>
          <Card>
            <CardHeader>
              <CardTitle>Issue Density Heatmap</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="rounded-xl border border-dashed border-border bg-muted/40 p-8 text-center text-sm text-muted-foreground">
                A map-based visualization of issue density by neighborhood will be
                displayed here. Support staff can use this view to identify hotspots
                and prioritize field teams.
              </div>

              <div className="grid gap-4 md:grid-cols-3 text-xs text-muted-foreground">
                <div>
                  <p className="font-medium text-foreground text-sm mb-2">
                    Legend
                  </p>
                  <ul className="space-y-1">
                    <li className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-sm bg-emerald-300" />
                      Low issue density
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-sm bg-amber-300" />
                      Medium issue density
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-sm bg-red-400" />
                      High issue density
                    </li>
                  </ul>
                </div>
                <div>
                  <p className="font-medium text-foreground text-sm mb-2">
                    Example districts
                  </p>
                  <ul className="space-y-1">
                    <li>Pine Avenue – 12 open tickets</li>
                    <li>Central Park – 8 open tickets</li>
                    <li>Harbor Road – 5 open tickets</li>
                  </ul>
                </div>
                <div>
                  <p className="font-medium text-foreground text-sm mb-2">
                    Next steps
                  </p>
                  <p>
                    This view will later be connected to the analytics service and
                    map component to render real-time ticket density.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}

// ============================================================================
// MANAGER DASHBOARD
// ============================================================================

function ManagerDashboard() {
  const kpisQuery = useDashboardKPIs(30);
  const ticketsQuery = useMyTickets({ page_size: 5 });
  const escalationsQuery = useEscalations({
    status_filter: EscalationStatus.PENDING,
    page_size: 5,
  });

  const kpis = kpisQuery.data;
  const recentTickets = ticketsQuery.data?.items ?? [];
  const pendingEscalations = escalationsQuery.data?.items ?? [];

  const isKPILoading = kpisQuery.isLoading;

  return (
    <motion.div
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      <motion.div
        className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        variants={fadeInUp}
      >
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Manager Dashboard</h1>
          <p className="text-muted-foreground">
            High-level overview of city-wide performance and workloads
          </p>
        </div>
        <Link href="/analytics">
          <Button variant="outline">
            <TrendingUp className="mr-2 h-4 w-4" />
            View Analytics
          </Button>
        </Link>
      </motion.div>

      {/* KPI Cards – overall system metrics */}
      {isKPILoading ? (
        <DashboardKPISkeleton />
      ) : (
        <motion.div
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <KPICard
            title="Total Tickets"
            value={kpis?.total_tickets ?? 0}
            icon={<TicketIcon className="h-5 w-5 text-blue-600" />}
            iconBgClass="bg-blue-100"
          />
          <KPICard
            title="Open Tickets"
            value={kpis?.open_tickets ?? 0}
            icon={<Clock className="h-5 w-5 text-amber-600" />}
            iconBgClass="bg-amber-100"
          />
          <KPICard
            title="Resolution Rate"
            value={kpis ? formatPercentage(kpis.resolution_rate, 0) : "-"}
            icon={<TrendingUp className="h-5 w-5 text-green-600" />}
            iconBgClass="bg-green-100"
          />
          <KPICard
            title="Avg Rating"
            value={formatRating(kpis?.average_rating ?? null)}
            icon={<Star className="h-5 w-5 text-purple-600" />}
            iconBgClass="bg-purple-100"
          />
        </motion.div>
      )}

      {/* Additional Stats – escalations, resolved, avg time */}
      {isKPILoading ? (
        <div className="grid gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="h-11 w-11 rounded-full bg-muted animate-pulse" />
                  <div className="space-y-2">
                    <div className="h-4 w-24 bg-muted rounded animate-pulse" />
                    <div className="h-6 w-12 bg-muted rounded animate-pulse" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <motion.div
          className="grid gap-4 sm:grid-cols-3"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <KPICard
            title="Escalated"
            value={kpis?.escalated_tickets ?? 0}
            icon={<AlertTriangle className="h-5 w-5 text-red-600" />}
            iconBgClass="bg-red-100"
          />
          <KPICard
            title="Resolved"
            value={kpis?.resolved_tickets ?? 0}
            icon={<CheckCircle2 className="h-5 w-5 text-primary" />}
            iconBgClass="bg-primary/10"
          />
          <KPICard
            title="Avg Resolution Time"
            value={formatDuration(kpis?.average_resolution_hours ?? null)}
            icon={<Clock className="h-5 w-5 text-muted-foreground" />}
            iconBgClass="bg-muted"
          />
        </motion.div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Tickets */}
        <TicketListCard
          title="Recent Tickets"
          viewAllHref="/tickets"
          tickets={recentTickets}
          isLoading={ticketsQuery.isLoading}
          isError={ticketsQuery.isError}
          refetch={ticketsQuery.refetch}
          showCategory
        />

        {/* Pending Escalations */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={fadeInUp}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <CardTitle className="text-lg">Pending Escalations</CardTitle>
              <Link
                href="/escalations"
                className="text-sm text-primary hover:text-primary/80"
              >
                View all
              </Link>
            </CardHeader>
            <CardContent className="pt-0">
              {escalationsQuery.isLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <TicketCardSkeleton key={i} />
                  ))}
                </div>
              ) : pendingEscalations.length === 0 ? (
                <p className="py-4 text-center text-muted-foreground">
                  No pending escalations
                </p>
              ) : (
                <motion.div
                  className="space-y-3"
                  variants={staggerContainer}
                  initial="hidden"
                  animate="visible"
                >
                  {pendingEscalations.map((escalation) => (
                    <motion.div key={escalation.id} variants={staggerItem}>
                      <Link
                        href={`/escalations/${escalation.id}`}
                        className="block rounded-lg border border-border p-3 transition hover:border-amber-300 hover:bg-amber-50"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium text-foreground truncate">
                            {escalation.ticket_title}
                          </span>
                          <Badge variant="warning">Pending</Badge>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground line-clamp-1">
                          {escalation.reason}
                        </p>
                      </Link>
                    </motion.div>
                  ))}
                </motion.div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Workload Snapshot & Quick Actions */}
      <motion.div
        className="grid gap-6 lg:grid-cols-[1.4fr,1fr]"
        variants={fadeInUp}
      >
        {/* Workload Snapshot */}
        <Card>
          <CardContent className="p-6">
            <h2 className="mb-4 text-lg font-semibold text-foreground">
              Workload Snapshot
            </h2>
            <p className="mb-4 text-sm text-muted-foreground">
              High-level distribution of open tickets across support teams. This
              helps managers balance workloads and identify overloaded teams.
            </p>
            <div className="space-y-3 text-xs text-muted-foreground">
              {[
                { team: "Central Support Team", percent: 60, tickets: 42 },
                { team: "North District Team", percent: 25, tickets: 18 },
                { team: "South District Team", percent: 15, tickets: 11 },
              ].map((row) => (
                <div key={row.team}>
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-foreground">{row.team}</span>
                    <span>{row.tickets} open</span>
                  </div>
                  <div className="mt-1 h-2 rounded-full bg-muted">
                    <div
                      className="h-2 rounded-full bg-primary"
                      style={{ width: `${row.percent}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardContent className="p-6">
            <h2 className="mb-4 text-lg font-semibold text-foreground">
              Quick Actions
            </h2>
            <div className="flex flex-wrap gap-3">
              <Link href="/analytics">
                <Button variant="outline">
                  <TrendingUp className="mr-2 h-4 w-4" />
                  View Analytics
                </Button>
              </Link>
              <Link href="/teams">
                <Button variant="outline">
                  <Users className="mr-2 h-4 w-4" />
                  Manage Teams
                </Button>
              </Link>
              <Link href="/escalations">
                <Button variant="outline">
                  <AlertTriangle className="mr-2 h-4 w-4" />
                  Review Escalations
                </Button>
              </Link>
              <Link href="/categories">
                <Button variant="outline">
                  <TicketIcon className="mr-2 h-4 w-4" />
                  Manage Categories
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}

// ============================================================================
// MAIN DASHBOARD PAGE
// ============================================================================

export default function DashboardPage() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <div className="h-8 w-48 bg-muted rounded animate-pulse" />
          <div className="h-4 w-64 bg-muted rounded animate-pulse" />
        </div>
        <DashboardKPISkeleton />
      </div>
    );
  }

  // Render role-specific dashboard
  switch (user?.role) {
    case UserRole.MANAGER:
      return <ManagerDashboard />;
    case UserRole.SUPPORT:
      return <SupportDashboard />;
    case UserRole.CITIZEN:
    default:
      return <CitizenDashboard />;
  }
}
