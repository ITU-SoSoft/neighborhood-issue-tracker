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
} from "lucide-react";

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
            <th className="pb-3 font-medium text-right">Avg Rating</th>
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
              <td className="py-3 text-right">
                {category.average_rating !== null ? (
                  <span className="flex items-center justify-end gap-1">
                    <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
                    {category.average_rating.toFixed(1)}
                  </span>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
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

  const kpis = kpisQuery.data;

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
          value={kpis ? formatPercentage(kpis.resolution_rate, 0) : "-"}
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

        {/* Feedback Trends */}
        <motion.div variants={staggerItem}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Feedback by Category
              </CardTitle>
            </CardHeader>
            <CardContent>
              {feedbackTrendsQuery.isError ? (
                <ErrorState
                  title="Failed to load"
                  message="Could not load feedback trends."
                  onRetry={feedbackTrendsQuery.refetch}
                />
              ) : (
                <FeedbackTrendsSection
                  data={feedbackTrendsQuery.data?.items}
                  isLoading={feedbackTrendsQuery.isLoading}
                />
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  );
}
