"use client";

import { useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth/context";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  DashboardKPISkeleton,
  TicketCardSkeleton,
} from "@/components/shared/skeletons";
import { EmptyTickets } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";

import {
  useMyTickets,
  useAssignedTickets,
  useDashboardKPIs,
  useEscalations,
  useTickets,
} from "@/lib/queries";
import {
  useHeatmap,
  useCategoryStats,
  useTeamPerformance,
  useNeighborhoodStats,
} from "@/lib/queries/analytics";

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
  getCategoryColor,
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

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

// Dynamically import the heatmap component to avoid SSR issues with Leaflet
const HeatmapVisualization = dynamic(
  () =>
    import("@/components/map/heatmap-visualization").then((mod) => ({
      default: mod.HeatmapVisualization,
    })),
  {
    ssr: false,
    loading: () => (
      <div className="h-[400px] rounded-xl bg-muted flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    ),
  },
);

// ============================================================================
// SHARED HELPERS / COMPONENTS
// ============================================================================

function getTimeRangeLabel(days: number): string {
  switch (days) {
    case 7:
      return "last 7 days";
    case 30:
      return "last 30 days";
    case 90:
      return "last 90 days";
    case 365:
      return "last year";
    default:
      return `last ${days} days`;
  }
}

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
            <div className={`rounded-full p-3 ${iconBgClass}`}>{icon}</div>
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

function TicketListItem({
  ticket,
  showCategory = false,
  showMeta = true,
}: TicketListItemProps) {
  return (
    <motion.div variants={staggerItem}>
      <Link
        href={`/tickets/${ticket.id}`}
        className="block rounded-xl border border-border p-4 transition hover:border-primary/30 hover:bg-primary/5"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <h3 className="font-medium text-foreground truncate">
              {ticket.title}
            </h3>
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
    <motion.div initial="hidden" animate="visible" variants={fadeInUp}>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-4">
          <CardTitle className="text-lg">{title}</CardTitle>
          <Link
            href={viewAllHref}
            className="text-sm text-primary hover:text-primary/80"
          >
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
                <TicketListItem
                  key={ticket.id}
                  ticket={ticket}
                  showCategory={showCategory}
                />
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
  // Get all tickets for stats (use max page size to get accurate counts)
  // Backend limit is 100, so we use that
  const { data, isLoading, isError, refetch } = useMyTickets({ page_size: 100 });
  const tickets = data?.items ?? [];
  
  // Use API total for accurate total count - if not available, use items length
  // But note: items length might be limited by page_size, so prefer API total
  const totalTickets = data?.total !== undefined && data.total > 0 
    ? data.total 
    : tickets.length > 0 
      ? tickets.length 
      : 0;
  
  const stats = {
    total: totalTickets,
    inProgress: tickets.filter((t) => t.status === TicketStatus.IN_PROGRESS)
      .length,
    resolved: tickets.filter(
      (t) =>
        t.status === TicketStatus.RESOLVED || t.status === TicketStatus.CLOSED,
    ).length,
    pending: tickets.filter((t) => t.status === TicketStatus.NEW).length,
  };

  // Show only first 5 tickets for display
  const recentTickets = tickets.slice(0, 5);

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
          <h1 className="text-2xl font-semibold text-foreground">
            Welcome back!
          </h1>
          <p className="text-muted-foreground">
            Track and manage your neighborhood issues
          </p>
        </div>
        <Link href="/tickets/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Report Issue
          </Button>
        </Link>
      </motion.div>

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

      <TicketListCard
        title="Recent Reports"
        viewAllHref="/tickets"
        tickets={recentTickets}
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
  const [days, setDays] = useState(30);
  const { user } = useAuth();

  const ticketsQuery = useAssignedTickets({ page_size: 5 });
  const escalationsQuery = useEscalations({
    status_filter: EscalationStatus.PENDING,
    page_size: 5,
  });
  const kpisQuery = useDashboardKPIs(days);

  const assignedTickets = ticketsQuery.data?.items ?? [];
  const assignedTicketsTotal = ticketsQuery.data?.total ?? 0;
  const escalations = escalationsQuery.data?.items ?? [];
  const kpis = kpisQuery.data;
  const teamName = user?.team_name;

  const isLoading =
    ticketsQuery.isLoading || escalationsQuery.isLoading || kpisQuery.isLoading;

  return (
    <motion.div
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      <motion.div variants={fadeInUp}>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">
              Support Dashboard
            </h1>
            <p className="text-muted-foreground">
              {teamName ? (
                <>
                  Manage assigned tickets and escalations • Team:{" "}
                  <span className="font-medium text-foreground">{teamName}</span>
                </>
              ) : (
                "Manage assigned tickets and escalations"
              )}
            </p>
          </div>

          <Select
            value={days.toString()}
            onValueChange={(v) => setDays(parseInt(v, 10))}
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="90">Last 90 days</SelectItem>
              <SelectItem value="365">Last year</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </motion.div>

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
            value={assignedTicketsTotal}
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
            value={kpis ? formatPercentage(kpis.resolution_rate, 2) : "-"}
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

      <div className="grid gap-6 lg:grid-cols-2">
        <TicketListCard
          title="Assigned Tickets"
          viewAllHref="/tickets?assigned=me"
          tickets={assignedTickets}
          isLoading={ticketsQuery.isLoading}
          isError={ticketsQuery.isError}
          refetch={ticketsQuery.refetch}
        />

        <motion.div initial="hidden" animate="visible" variants={fadeInUp}>
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
    </motion.div>
  );
}

// ============================================================================
// MANAGER DASHBOARD  (Workload Snapshot REAL TEAM DATA)
// ============================================================================

function ManagerDashboard() {
  const [days, setDays] = useState(30);
  const [heatmapFilter, setHeatmapFilter] = useState<
    "all" | TicketStatus
  >("all");

  const kpisQuery = useDashboardKPIs(days);
  const ticketsQuery = useTickets({ page: 1, page_size: 3 });
  const escalationsQuery = useEscalations({
    status_filter: EscalationStatus.PENDING,
    page_size: 5,
  });

  const heatmapQuery = useHeatmap({
    days,
    status: heatmapFilter === "all" ? undefined : heatmapFilter,
  });

  const categoryStatsQuery = useCategoryStats(days);
  const teamPerformanceQuery = useTeamPerformance(days);
  const neighborhoodStatsQuery = useNeighborhoodStats(days, 5);

  const kpis = kpisQuery.data;
  const recentTickets = ticketsQuery.data?.items ?? [];
  const pendingEscalations = escalationsQuery.data?.items ?? [];
  const heatmapData = heatmapQuery.data;

  const categoryItems = categoryStatsQuery.data?.items ?? [];
  const teamData = teamPerformanceQuery.data?.items ?? [];
  const neighborhoodData = neighborhoodStatsQuery.data?.items ?? [];

  const isKPILoading = kpisQuery.isLoading;

  // -----------------------------
  // Robust field getters (in case API uses slightly different names)
  // -----------------------------
  const getTeamName = (t: any) =>
    (t?.team_name ?? t?.name ?? t?.teamName ?? "Unnamed Team") as string;

  const getOpenCount = (t: any) =>
    Number(t?.open_tickets ?? t?.openTickets ?? t?.open_count ?? t?.open ?? 0);

  const sortedTeams = [...teamData].sort(
    (a: any, b: any) => getOpenCount(b) - getOpenCount(a),
  );
  const totalOpenAcrossTeams = sortedTeams.reduce(
    (sum: number, t: any) => sum + getOpenCount(t),
    0,
  );

  // Generate consistent colors for all categories
  const categoryColorMap: Record<string, string> = categoryItems.reduce(
    (acc, item) => {
      acc[item.category_name] = getCategoryColor(item.category_name);
      return acc;
    },
    {} as Record<string, string>,
  );

  const totalCategoryTickets = categoryItems.reduce(
    (sum: number, c: any) => sum + Number(c?.total_tickets ?? 0),
    0,
  );
  const totalCategoryOpen = categoryItems.reduce(
    (sum: number, c: any) => sum + Number(c?.open_tickets ?? 0),
    0,
  );

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
          <h1 className="text-2xl font-semibold text-foreground">
            Manager Dashboard
          </h1>
          <p className="text-muted-foreground">
            High-level overview of city-wide performance and workloads
          </p>
        </div>

        <div className="flex gap-2">
          <Select
            value={days.toString()}
            onValueChange={(v) => setDays(parseInt(v, 10))}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="90">Last 90 days</SelectItem>
              <SelectItem value="365">Last year</SelectItem>
            </SelectContent>
          </Select>

          <Link href="/analytics">
            <Button variant="outline">
              <TrendingUp className="mr-2 h-4 w-4" />
              View Analytics
            </Button>
          </Link>
        </div>
      </motion.div>

      {/* KPI Cards */}
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
            value={kpis ? formatPercentage(kpis.resolution_rate, 2) : "-"}
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

      {/* Additional Stats */}
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

      {/* Pending Escalations */}
      <motion.div initial="hidden" animate="visible" variants={fadeInUp}>
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

      <div className="grid gap-6 lg:grid-cols-2">
        <TicketListCard
          title="Recent Tickets"
          viewAllHref="/tickets"
          tickets={recentTickets}
          isLoading={ticketsQuery.isLoading}
          isError={ticketsQuery.isError}
          refetch={ticketsQuery.refetch}
          showCategory
        />

        <div className="grid gap-4 sm:grid-cols-2">
          {/* Total Tickets */}
          <motion.div initial="hidden" animate="visible" variants={fadeInUp}>
            <Card className="h-full">
              <CardHeader className="p-4">
                <CardTitle className="text-base flex items-center gap-2">
                  <TicketIcon className="h-4 w-4" />
                  Total Tickets
                </CardTitle>
                <p className="text-xs text-muted-foreground">By Category</p>
              </CardHeader>
              <CardContent className="p-4">
                {categoryStatsQuery.isLoading ? (
                  <div className="h-[350px] flex items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                ) : categoryStatsQuery.isError ? (
                  <ErrorState
                    title="Error"
                    message="Failed"
                    onRetry={categoryStatsQuery.refetch}
                  />
                ) : categoryItems.length === 0 ? (
                  <div className="h-[350px] flex items-center justify-center">
                    <p className="text-xs text-muted-foreground">No data</p>
                  </div>
                ) : (
                  <div className="h-[350px] relative">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={categoryItems as any[]}
                          cx="50%"
                          cy="42%"
                          innerRadius={65}
                          outerRadius={95}
                          paddingAngle={2}
                          dataKey="total_tickets"
                          nameKey="category_name"
                          label={false}
                          minAngle={5}
                        >
                          {categoryItems.map((entry: any, index: number) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={
                                categoryColorMap[entry.category_name] ||
                                "#999999"
                              }
                            />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend
                          verticalAlign="bottom"
                          height={50}
                          iconType="circle"
                          wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
                        />
                      </PieChart>
                    </ResponsiveContainer>

                    <div className="absolute top-[33%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none">
                      <div className="text-center">
                        <div className="text-2xl font-semibold text-foreground">
                          {totalCategoryTickets}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Total
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Open Tickets */}
          <motion.div initial="hidden" animate="visible" variants={fadeInUp}>
            <Card className="h-full">
              <CardHeader className="p-4">
                <CardTitle className="text-base flex items-center gap-2">
                  <TicketIcon className="h-4 w-4" />
                  Open Tickets
                </CardTitle>
                <p className="text-xs text-muted-foreground">By Category</p>
              </CardHeader>
              <CardContent className="p-4">
                {categoryStatsQuery.isLoading ? (
                  <div className="h-[350px] flex items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                ) : categoryStatsQuery.isError ? (
                  <ErrorState
                    title="Error"
                    message="Failed"
                    onRetry={categoryStatsQuery.refetch}
                  />
                ) : categoryItems.length === 0 ? (
                  <div className="h-[350px] flex items-center justify-center">
                    <p className="text-xs text-muted-foreground">No data</p>
                  </div>
                ) : (
                  <div className="h-[350px] relative">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={categoryItems as any[]}
                          cx="50%"
                          cy="42%"
                          innerRadius={65}
                          outerRadius={95}
                          paddingAngle={2}
                          dataKey="open_tickets"
                          nameKey="category_name"
                          label={false}
                          minAngle={5}
                        >
                          {categoryItems.map((entry: any, index: number) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={
                                categoryColorMap[entry.category_name] ||
                                "#999999"
                              }
                            />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend
                          verticalAlign="bottom"
                          height={50}
                          iconType="circle"
                          wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
                        />
                      </PieChart>
                    </ResponsiveContainer>

                    <div className="absolute top-[33%] left-1/2 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none">
                      <div className="text-center">
                        <div className="text-2xl font-semibold text-foreground">
                          {totalCategoryOpen}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Open
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* Workload Snapshot & Quick Actions */}
      <motion.div
        className="grid gap-6 lg:grid-cols-[1.4fr,1fr]"
        variants={fadeInUp}
      >
        {/* Workload Snapshot (TEAM API DATA) */}
        <Card>
          <CardContent className="p-6">
            <h2 className="mb-4 text-lg font-semibold text-foreground">
              Workload Snapshot
            </h2>
            <p className="mb-4 text-sm text-muted-foreground">
              High-level distribution of open tickets across support teams. This
              helps managers balance workloads and identify overloaded teams.
            </p>

            {teamPerformanceQuery.isLoading ? (
              <div className="py-10 flex items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            ) : teamPerformanceQuery.isError ? (
              <ErrorState
                title="Failed to load team workload"
                message="Could not load workload data. Please try again."
                onRetry={teamPerformanceQuery.refetch}
              />
            ) : sortedTeams.length === 0 ? (
              <div className="py-10 text-center text-sm text-muted-foreground">
                No team workload data found.
              </div>
            ) : (
              <div className="space-y-3 text-xs text-muted-foreground">
                {sortedTeams.map((t: any) => {
                  const open = getOpenCount(t);
                  const percent =
                    totalOpenAcrossTeams > 0
                      ? Math.round((open / totalOpenAcrossTeams) * 100)
                      : 0;

                  const teamName = getTeamName(t);
                  const key = (t?.team_id ?? t?.id ?? teamName) as string;

                  return (
                    <div key={key}>
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-foreground">
                          {teamName}
                        </span>
                        <span>{open} open</span>
                      </div>
                      <div className="mt-1 h-2 rounded-full bg-muted">
                        <div
                          className="h-2 rounded-full bg-primary"
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
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
                  Manage Teams and Categories
                </Button>
              </Link>
              <Link href="/escalations">
                <Button variant="outline">
                  <AlertTriangle className="mr-2 h-4 w-4" />
                  Review Escalations
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Issue Density Heatmap */}
      <motion.div variants={fadeInUp}>
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>Issue Density Heatmap</CardTitle>
                <p className="text-sm text-muted-foreground">
                  Geographic visualization of reported issues (
                  {getTimeRangeLabel(days)})
                </p>
              </div>
              <Select
                value={heatmapFilter}
                onValueChange={(v) =>
                  setHeatmapFilter(v as "all" | TicketStatus)
                }
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="z-[1000]">
                  <SelectItem value="all">All Created</SelectItem>
                  <SelectItem value={TicketStatus.NEW}>New</SelectItem>
                  <SelectItem value={TicketStatus.IN_PROGRESS}>
                    In Progress
                  </SelectItem>
                  <SelectItem value={TicketStatus.RESOLVED}>Resolved</SelectItem>
                  <SelectItem value={TicketStatus.CLOSED}>Closed</SelectItem>
                  <SelectItem value={TicketStatus.ESCALATED}>
                    Escalated
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            {heatmapQuery.isLoading ? (
              <div className="h-[400px] rounded-xl bg-muted flex items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            ) : heatmapQuery.isError ? (
              <ErrorState
                title="Failed to load heatmap"
                message="Could not load heatmap data. Please try again."
                onRetry={heatmapQuery.refetch}
              />
            ) : !heatmapData || heatmapData.points.length === 0 ? (
              <div className="h-[400px] rounded-xl border border-dashed border-border bg-muted/40 flex flex-col items-center justify-center p-8 text-center">
                <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-sm text-muted-foreground">
                  No{" "}
                  {heatmapFilter !== "all"
                    ? `${getStatusLabel(heatmapFilter as TicketStatus).toLowerCase()} `
                    : ""}
                  tickets found in the {getTimeRangeLabel(days)}.
                  <br />
                  The heatmap will appear once issues are reported.
                </p>
              </div>
            ) : (
              <>
                <HeatmapVisualization
                  points={heatmapData.points}
                  height="450px"
                />

                <div className="grid gap-4 md:grid-cols-3 text-xs">
                  <div>
                    <p className="font-medium text-foreground text-sm mb-2">
                      Legend
                    </p>
                    <ul className="space-y-1 text-muted-foreground">
                      <li className="flex items-center gap-2">
                        <span className="h-3 w-3 rounded-sm bg-blue-500" />
                        Low density
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="h-3 w-3 rounded-sm bg-yellow-500" />
                        Medium density
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="h-3 w-3 rounded-sm bg-red-500" />
                        High density
                      </li>
                    </ul>
                  </div>

                  <div>
                    <p className="font-medium text-foreground text-sm mb-2">
                      Statistics
                    </p>
                    <ul className="space-y-1 text-muted-foreground">
                      <li>Unique locations: {heatmapData.points.length}</li>
                      <li>Total tickets: {heatmapData.total_tickets}</li>
                      <li>Max at one location: {heatmapData.max_count}</li>
                    </ul>
                  </div>

                  <div>
                    <p className="font-medium text-foreground text-sm mb-2">
                      Use Cases
                    </p>
                    <p className="text-muted-foreground">
                      Identify problem areas requiring additional resources.
                      Zoom and pan to explore specific neighborhoods and
                      coordinate field team deployment.
                    </p>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Top 5 Problematic Districts */}
      <motion.div variants={fadeInUp}>
        <Card>
          <CardHeader>
            <CardTitle>Top 5 Problematic Districts</CardTitle>
            <p className="text-sm text-muted-foreground">
              Districts with most tickets and category breakdown
            </p>
          </CardHeader>

          <CardContent>
            {neighborhoodStatsQuery.isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            ) : neighborhoodStatsQuery.isError ? (
              <ErrorState
                title="Failed to Load"
                message="Could not load district statistics."
                onRetry={neighborhoodStatsQuery.refetch}
              />
            ) : neighborhoodData.length === 0 ? (
              <div className="flex items-center justify-center py-12">
                <p className="text-sm text-muted-foreground">
                  No district data found
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {neighborhoodData.map((neighborhood: any, index: number) => (
                  <div
                    key={neighborhood.district}
                    className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div
                          className={`flex items-center justify-center w-8 h-8 rounded-full font-bold
                            ${
                              index === 0
                                ? "bg-red-100 text-red-700"
                                : index === 1
                                  ? "bg-orange-100 text-orange-700"
                                  : "bg-muted text-muted-foreground"
                            }`}
                        >
                          {index + 1}
                        </div>
                        <div>
                          <h3 className="font-medium text-foreground text-lg">
                            {neighborhood.district}
                          </h3>
                          <p className="text-sm text-muted-foreground">
                            {neighborhood.total_tickets} total tickets
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {neighborhood.category_breakdown.map((cat: any) => (
                        <div
                          key={cat.category_name}
                          className="flex items-center gap-1.5 px-2 py-1 bg-muted/50 rounded-md text-xs"
                        >
                          <span className="font-medium text-foreground">
                            {cat.category_name}:
                          </span>
                          <span className="text-muted-foreground">
                            {cat.ticket_count}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}

// ============================================================================
// MAIN PAGE
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
