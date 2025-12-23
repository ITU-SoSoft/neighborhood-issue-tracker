"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth/context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ErrorState } from "@/components/shared/error-state";
import {
  useDashboardKPIs,
  useCategoryStats,
  useFeedbackTrends,
  useTeamPerformance,
  useNeighborhoodStats,
} from "@/lib/queries/analytics";
import { UserRole } from "@/lib/api/types";
import { formatPercentage, formatRating, formatDuration } from "@/lib/utils";
import {
  fadeInUp,
  staggerContainer,
  staggerItem,
  cardHover,
  cardTap,
} from "@/lib/animations";
import {
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Star,
  Ticket,
  MessageSquare,
  Loader2,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";

const timeRangeOptions = [
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" },
  { value: "90", label: "Last 90 days" },
];

interface KPICardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  iconBgClass: string;
  isLoading?: boolean;
}

function KPICard({ title, value, icon, iconBgClass, isLoading }: KPICardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <Skeleton className="h-11 w-11 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-6 w-16" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

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

function CategoryStatsTable({
  data,
  isLoading,
}: {
  data:
  | {
    category_id: string;
    category_name: string;
    total_tickets: number;
    open_tickets: number;
    resolved_tickets: number;
    average_rating: number | null;
  }[]
  | undefined;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center justify-between py-2">
            <Skeleton className="h-4 w-32" />
            <div className="flex gap-4">
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-4 w-12" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <p className="text-muted-foreground text-center py-4">
        No category data available
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b text-left text-sm text-muted-foreground">
            <th className="pb-3 font-medium">Category</th>
            <th className="pb-3 font-medium text-right">Total</th>
            <th className="pb-3 font-medium text-right">Open</th>
            <th className="pb-3 font-medium text-right">Resolved</th>
          </tr>
        </thead>
        <tbody>
          {data.map((category) => (
            <tr key={category.category_id} className="border-b last:border-0">
              <td className="py-3 font-medium">{category.category_name}</td>
              <td className="py-3 text-right">{category.total_tickets}</td>
              <td className="py-3 text-right">
                <Badge variant="secondary">{category.open_tickets}</Badge>
              </td>
              <td className="py-3 text-right">
                <Badge variant="success">{category.resolved_tickets}</Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FeedbackTrendsSection({
  data,
  isLoading,
}: {
  data:
  | {
    category_id: string;
    category_name: string;
    total_feedbacks: number;
    average_rating: number;
    rating_distribution: Record<number, number>;
  }[]
  | undefined;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="p-4 border rounded-lg">
            <Skeleton className="h-5 w-32 mb-2" />
            <Skeleton className="h-4 w-full" />
          </div>
        ))}
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <p className="text-muted-foreground text-center py-4">
        No feedback data available
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {data.map((trend) => (
        <div key={trend.category_id} className="p-4 border rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium">{trend.category_name}</h4>
            <div className="flex items-center gap-2">
              <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
              <span className="font-semibold">
                {trend.average_rating.toFixed(1)}
              </span>
              <span className="text-sm text-muted-foreground">
                ({trend.total_feedbacks} reviews)
              </span>
            </div>
          </div>
          {/* Rating distribution bar */}
          <div className="flex gap-1 h-2">
            {[5, 4, 3, 2, 1].map((rating) => {
              const count = trend.rating_distribution[rating] || 0;
              const percentage =
                trend.total_feedbacks > 0
                  ? (count / trend.total_feedbacks) * 100
                  : 0;
              const colors: Record<number, string> = {
                5: "bg-green-500",
                4: "bg-green-400",
                3: "bg-yellow-400",
                2: "bg-orange-400",
                1: "bg-red-500",
              };
              return (
                <div
                  key={rating}
                  className={`${colors[rating]} rounded-sm`}
                  style={{ width: `${Math.max(percentage, 2)}%` }}
                  title={`${rating} stars: ${count} (${percentage.toFixed(0)}%)`}
                />
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AnalyticsPage() {
  const { user } = useAuth();
  const [days, setDays] = useState(30);

  const kpisQuery = useDashboardKPIs(days);
  const categoryStatsQuery = useCategoryStats(days);
  const feedbackTrendsQuery = useFeedbackTrends(days);
  const teamPerformanceQuery = useTeamPerformance(days);
  const neighborhoodStatsQuery = useNeighborhoodStats(days, 5);

  const kpis = kpisQuery.data;
  const teamData = teamPerformanceQuery.data?.items ?? [];
  const neighborhoodData = neighborhoodStatsQuery.data?.items ?? [];

  // Access check - Manager only
  if (user && user.role !== UserRole.MANAGER) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold text-foreground">Access Denied</h2>
        <p className="text-muted-foreground mt-2">
          Analytics is only available to managers.
        </p>
        <Link href="/dashboard">
          <Button className="mt-4">Go to Dashboard</Button>
        </Link>
      </div>
    );
  }

  return (
    <motion.div
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {/* Header */}
      <motion.div
        className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        variants={fadeInUp}
      >
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Analytics</h1>
          <p className="text-muted-foreground">
            Performance metrics and insights
          </p>
        </div>
        <Select
          value={days.toString()}
          onValueChange={(value) => setDays(parseInt(value, 10))}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {timeRangeOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </motion.div>

      {/* KPI Cards */}
      <motion.div
        className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        <KPICard
          title="Total Tickets"
          value={kpis?.total_tickets ?? 0}
          icon={<Ticket className="h-5 w-5 text-blue-600" />}
          iconBgClass="bg-blue-100"
          isLoading={kpisQuery.isLoading}
        />
        <KPICard
          title="Open Tickets"
          value={kpis?.open_tickets ?? 0}
          icon={<Clock className="h-5 w-5 text-amber-600" />}
          iconBgClass="bg-amber-100"
          isLoading={kpisQuery.isLoading}
        />
        <KPICard
          title="Resolution Rate"
          value={kpis ? formatPercentage(kpis.resolution_rate, 2) : "-"}
          icon={<TrendingUp className="h-5 w-5 text-green-600" />}
          iconBgClass="bg-green-100"
          isLoading={kpisQuery.isLoading}
        />
        <KPICard
          title="Avg Rating"
          value={formatRating(kpis?.average_rating ?? null)}
          icon={<Star className="h-5 w-5 text-purple-600" />}
          iconBgClass="bg-purple-100"
          isLoading={kpisQuery.isLoading}
        />
      </motion.div>

      {/* Secondary KPIs */}
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
          isLoading={kpisQuery.isLoading}
        />
        <KPICard
          title="Resolved"
          value={kpis?.resolved_tickets ?? 0}
          icon={<CheckCircle2 className="h-5 w-5 text-primary" />}
          iconBgClass="bg-primary/10"
          isLoading={kpisQuery.isLoading}
        />
        <KPICard
          title="Avg Resolution Time"
          value={formatDuration(kpis?.average_resolution_hours ?? null)}
          icon={<Clock className="h-5 w-5 text-muted-foreground" />}
          iconBgClass="bg-muted"
          isLoading={kpisQuery.isLoading}
        />
      </motion.div>

      {/* Category Stats and Feedback */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Category Stats */}
        <motion.div variants={staggerItem}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Tickets by Category
              </CardTitle>
            </CardHeader>
            <CardContent>
              {categoryStatsQuery.isError ? (
                <ErrorState
                  title="Failed to load"
                  message="Could not load category stats."
                  onRetry={categoryStatsQuery.refetch}
                />
              ) : (
                <CategoryStatsTable
                  data={categoryStatsQuery.data?.items}
                  isLoading={categoryStatsQuery.isLoading}
                />
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Feedback Trends (Moved from bottom) */}
        <motion.div variants={staggerItem}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Feedback Trends
              </CardTitle>
            </CardHeader>
            <CardContent>
              {feedbackTrendsQuery.isError ? (
                <ErrorState
                  title="Failed to Load"
                  message="Could not load feedback trends."
                  onRetry={feedbackTrendsQuery.refetch}
                />
              ) : !feedbackTrendsQuery.data?.items ? (
                <div className="h-[300px] flex items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : (
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={feedbackTrendsQuery.data.items} margin={{ top: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis
                        dataKey="category_name"
                        stroke="#888888"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis
                        stroke="#888888"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                        domain={[0, 5]}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          borderColor: 'hsl(var(--border))',
                        }}
                        formatter={(value: number | string | undefined) => [`${(Number(value) || 0).toFixed(1)} / 5.0`, 'Rating']}
                      />
                      <Bar
                        dataKey="average_rating"
                        fill="hsl(var(--primary))"
                        radius={[4, 4, 0, 0]}
                        name="Average Rating"
                        label={{
                          position: 'top',
                          fill: 'hsl(var(--foreground))',
                          fontSize: 12,
                          formatter: (value: any) => Number(value).toFixed(1)
                        }}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Pie Charts - Category Distribution */}
        <motion.div className="grid gap-6 lg:grid-cols-2" variants={fadeInUp}>
          {/* Total Tickets by Category */}
          <Card>
            <CardHeader>
              <CardTitle>Total Tickets (By Category)</CardTitle>
              <p className="text-sm text-muted-foreground">
                Distribution of tickets by category
              </p>
            </CardHeader>
            <CardContent>
              {categoryStatsQuery.isLoading ? (
                <div className="h-[300px] flex items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : categoryStatsQuery.isError ? (
                <ErrorState
                  title="Failed to Load"
                  message="Could not load category statistics."
                  onRetry={categoryStatsQuery.refetch}
                />
              ) : !categoryStatsQuery.data?.items || categoryStatsQuery.data.items.length === 0 ? (
                <div className="h-[300px] flex items-center justify-center">
                  <p className="text-sm text-muted-foreground">No data</p>
                </div>
              ) : (
                <div className="h-[300px] relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categoryStatsQuery.data.items as any}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={5}
                        dataKey="total_tickets"
                        nameKey="category_name"
                        label={({ name }: { name?: string }) => name ?? ''}
                      >
                        {categoryStatsQuery.data.items.map((entry: any, index: number) => {
                          const colorMap: Record<string, string> = {
                            'Infrastructure': '#0088FE',
                            'Traffic': '#00C49F',
                            'Lighting': '#FFBB28',
                            'Waste Management': '#FF8042',
                            'Parks': '#8884d8',
                            'Other': '#82ca9d',
                          };
                          return (
                            <Cell
                              key={`cell-${index}`}
                              fill={colorMap[entry.category_name] || '#999999'}
                            />
                          );
                        })}
                      </Pie>
                      <Tooltip />
                      <Legend formatter={(_value: any, entry: any) => entry.payload?.category_name} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="text-center">
                      <div className="text-2xl font-normal text-foreground">
                        {categoryStatsQuery.data.items.reduce((sum: number, cat: any) => sum + cat.total_tickets, 0)}
                      </div>
                      <div className="text-xs text-muted-foreground">Total</div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Open Tickets by Category */}
          <Card>
            <CardHeader>
              <CardTitle>Open Tickets (By Category)</CardTitle>
              <p className="text-sm text-muted-foreground">
                Open tickets requiring attention
              </p>
            </CardHeader>
            <CardContent>
              {categoryStatsQuery.isLoading ? (
                <div className="h-[300px] flex items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : categoryStatsQuery.isError ? (
                <ErrorState
                  title="Failed to Load"
                  message="Could not load category statistics."
                  onRetry={categoryStatsQuery.refetch}
                />
              ) : !categoryStatsQuery.data?.items || categoryStatsQuery.data.items.length === 0 ? (
                <div className="h-[300px] flex items-center justify-center">
                  <p className="text-sm text-muted-foreground">No data</p>
                </div>
              ) : (
                <div className="h-[300px] relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categoryStatsQuery.data.items as any}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={5}
                        dataKey="open_tickets"
                        nameKey="category_name"
                        label={({ name }: { name?: string }) => name ?? ''}
                      >
                        {categoryStatsQuery.data.items.map((entry: any, index: number) => {
                          const colorMap: Record<string, string> = {
                            'Infrastructure': '#0088FE',
                            'Traffic': '#00C49F',
                            'Lighting': '#FFBB28',
                            'Waste Management': '#FF8042',
                            'Parks': '#8884d8',
                            'Other': '#82ca9d',
                          };
                          return (
                            <Cell
                              key={`cell-${index}`}
                              fill={colorMap[entry.category_name] || '#999999'}
                            />
                          );
                        })}
                      </Pie>
                      <Tooltip />
                      <Legend formatter={(_value: any, entry: any) => entry.payload?.category_name} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="text-center">
                      <div className="text-2xl font-normal text-foreground">
                        {categoryStatsQuery.data.items.reduce((sum: number, cat: any) => sum + cat.open_tickets, 0)}
                      </div>
                      <div className="text-xs text-muted-foreground">Open</div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>



        {/* Top 5 Problematic Neighborhoods */}
        <motion.div variants={staggerItem}>
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
                  <p className="text-sm text-muted-foreground">No district data found</p>
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
                          <div className={`flex items-center justify-center w-8 h-8 rounded-full font-bold
                            ${index === 0 ? 'bg-red-100 text-red-700' :
                              index === 1 ? 'bg-orange-100 text-orange-700' :
                                'bg-muted text-muted-foreground'
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

        {/* Team Performance */}
        <motion.div variants={staggerItem}>
          <div className="grid gap-6">
            <div>
              <h2 className="text-lg font-semibold tracking-tight">Team Performance</h2>
              <p className="text-sm text-muted-foreground">
                Resolution rates and citizen satisfaction
              </p>
            </div>

            {teamPerformanceQuery.isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            ) : teamPerformanceQuery.isError ? (
              <ErrorState
                title="Failed to Load"
                message="Could not load team performance data."
                onRetry={teamPerformanceQuery.refetch}
              />
            ) : !teamData || teamData.length === 0 ? (
              <div className="flex items-center justify-center py-12 border rounded-lg bg-muted/10">
                <p className="text-sm text-muted-foreground">No team data found</p>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {teamData.map((team: any) => {
                  const resolutionRate = team.resolution_rate || 0;
                  const rating = team.average_rating || 0;

                  return (
                    <motion.div
                      key={team.team_id}
                      variants={staggerItem}
                      whileHover={cardHover}
                      whileTap={cardTap}
                    >
                      <Card className="h-full">
                        <CardContent className="p-6">
                          <div className="space-y-4">
                            <div className="flex items-start justify-between">
                              <h3 className="font-semibold text-foreground line-clamp-2">
                                {((name) => {
                                  const map: Record<string, string> = {
                                    'Bakırköy Elektrik Takımı': 'Bakırköy Electricity Team',
                                    'Kadıköy Trafik Takımı': 'Kadıköy Traffic Team',
                                    'Beşiktaş Temizlik Takımı': 'Beşiktaş Waste Management Team',
                                    'Şişli Park Takımı': 'Şişli Parks Team',
                                    'İstanbul Genel Altyapı': 'Istanbul General Infrastructure',
                                    'Avrupa Yakası Trafik': 'European Side Traffic'
                                  };
                                  return map[name] || name;
                                })(team.team_name)}
                              </h3>
                            </div>

                            <div className="text-center py-4 bg-muted/50 rounded-lg">
                              <div className="text-4xl font-bold text-foreground">
                                {resolutionRate.toFixed(1)}%
                              </div>
                              <div className="text-xs text-muted-foreground mt-1">
                                Resolution Rate
                              </div>
                            </div>

                            <div className="flex items-center justify-between text-sm">
                              <span className="text-muted-foreground">Citizen Rating</span>
                              <div className="flex items-center gap-1 font-medium">
                                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                                {rating > 0 ? rating.toFixed(1) : 'N/A'}
                              </div>
                            </div>

                            <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t">
                              <div>
                                <p className="text-muted-foreground">Assigned</p>
                                <p className="font-medium text-lg">{team.assigned_tickets}</p>
                              </div>
                              <div>
                                <p className="text-muted-foreground">Resolved</p>
                                <p className="font-medium text-lg text-green-600">{team.resolved_tickets}</p>
                              </div>
                              <div>
                                <p className="text-muted-foreground">Avg. Time</p>
                                <p className="font-medium">
                                  {team.average_resolution_time
                                    ? `${Math.round(team.average_resolution_time)}h`
                                    : 'N/A'}
                                </p>
                              </div>
                              <div>
                                <p className="text-muted-foreground">Members</p>
                                <p className="font-medium">{team.member_count}</p>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
