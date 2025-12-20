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
  FileDown,
  Users,
  Lightbulb,
} from "lucide-react";

// Custom Progress Bar to avoid module resolution errors
function CustomProgressBar({ value, colorClass = "bg-primary" }: { value: number; colorClass?: string }) {
  return (
    <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
      <div 
        className={`h-full ${colorClass} transition-all duration-500`} 
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  );
}

function KPICard({ title, value, icon, iconBgClass, isLoading }: { 
  title: string; value: string | number; icon: React.ReactNode; iconBgClass: string; isLoading: boolean 
}) {
  if (isLoading) return (
    <Card><CardContent className="p-6"><div className="flex items-center gap-4"><Skeleton className="h-11 w-11 rounded-full" /><div className="space-y-2"><Skeleton className="h-4 w-24" /><Skeleton className="h-6 w-16" /></div></div></CardContent></Card>
  );
  return (
    <motion.div variants={staggerItem} whileHover={cardHover} whileTap={cardTap}>
      <Card><CardContent className="p-6"><div className="flex items-center gap-4">
        <div className={`rounded-full p-3 ${iconBgClass}`}>{icon}</div>
        <div><p className="text-sm text-muted-foreground">{title}</p><p className="text-2xl font-semibold">{value}</p></div>
      </div></CardContent></Card>
    </motion.div>
  );
}

export default function AnalyticsPage() {
  const { user } = useAuth();
  const [days, setDays] = useState(30);

  const kpisQuery = useDashboardKPIs(days);
  const categoryStatsQuery = useCategoryStats(days);
  const feedbackTrendsQuery = useFeedbackTrends(days);
  const teamPerformanceQuery = useTeamPerformance(days);

  const kpis = kpisQuery.data;

  if (user && user.role !== UserRole.MANAGER) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <AlertTriangle className="h-16 w-16 text-amber-500 mb-4" />
        <h2 className="text-2xl font-bold">Access Denied</h2>
        <p className="text-muted-foreground mt-2">Manager privileges are required to view analytics.</p>
        <Link href="/dashboard" className="mt-6"><Button>Go Back</Button></Link>
      </div>
    );
  }

  return (
    <motion.div className="space-y-8 pb-12" initial="hidden" animate="visible" variants={staggerContainer}>
      {/* Header */}
      <motion.div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between" variants={fadeInUp}>
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Quarterly Performance</h1>
          <p className="text-muted-foreground">Strategic overview of municipality service efficiency.</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={days.toString()} onValueChange={(v) => setDays(parseInt(v, 10))}>
            <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 Days</SelectItem>
              <SelectItem value="30">Last 30 Days</SelectItem>
              <SelectItem value="90">Last 90 Days</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={() => window.print()} className="gap-2"><FileDown className="h-4 w-4" /> Export PDF</Button>
        </div>
      </motion.div>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard title="Total Tickets" value={kpis?.total_tickets ?? "0"} icon={<Ticket className="text-blue-600" />} iconBgClass="bg-blue-100" isLoading={kpisQuery.isLoading} />
        <KPICard title="Resolution Rate" value={kpis ? formatPercentage(kpis.resolution_rate, 0) : "0%"} icon={<CheckCircle2 className="text-green-600" />} iconBgClass="bg-green-100" isLoading={kpisQuery.isLoading} />
        <KPICard title="Avg Resolution Time" value={formatDuration(kpis?.average_resolution_hours ?? 0)} icon={<Clock className="text-amber-600" />} iconBgClass="bg-amber-100" isLoading={kpisQuery.isLoading} />
        <KPICard title="Avg Citizen Rating" value={formatRating(kpis?.average_rating ?? null)} icon={<Star className="text-purple-600" />} iconBgClass="bg-purple-100" isLoading={kpisQuery.isLoading} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Team Efficiency */}
        <Card className="lg:col-span-1 shadow-md">
          <CardHeader><CardTitle className="flex items-center gap-2 text-lg"><Users className="h-5 w-5" /> Team Efficiency</CardTitle></CardHeader>
          <CardContent className="space-y-6">
            {teamPerformanceQuery.isLoading ? <Skeleton className="h-40 w-full" /> : 
              teamPerformanceQuery.data?.items?.map((team: any) => (
                <div key={team.team_id} className="space-y-2">
                  <div className="flex justify-between text-sm font-medium"><span>{team.team_name}</span><span>%{team.resolution_rate}</span></div>
                  <CustomProgressBar value={team.resolution_rate} colorClass={team.resolution_rate > 80 ? "bg-green-500" : "bg-blue-500"} />
                </div>
              ))
            }
            <div className="mt-4 p-3 bg-primary/5 rounded-lg border border-primary/10 text-xs text-muted-foreground italic">
              "Note: Evaluate high-performing teams for mentorship roles."
            </div>
          </CardContent>
        </Card>

        {/* Category Stats */}
        <Card className="lg:col-span-2 shadow-md">
          <CardHeader><CardTitle className="text-lg">Issues by Category</CardTitle></CardHeader>
          <CardContent>
            {categoryStatsQuery.isLoading ? <Skeleton className="h-48 w-full" /> : (
              <table className="w-full text-sm">
                <thead><tr className="border-b text-muted-foreground text-left font-medium"><th className="pb-2">Category</th><th className="pb-2 text-right">Total</th><th className="pb-2 text-right">Avg Rating</th></tr></thead>
                <tbody>
                  {categoryStatsQuery.data?.items?.map((cat: any) => (
                    <tr key={cat.category_id} className="border-b last:border-0 hover:bg-muted/50 transition-colors">
                      <td className="py-3 font-medium">{cat.category_name}</td>
                      <td className="py-3 text-right">{cat.total_tickets}</td>
                      <td className="py-3 text-right font-bold text-primary">{cat.average_rating?.toFixed(1) ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Trends & Insights */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="shadow-md">
          <CardHeader><CardTitle className="flex items-center gap-2 text-lg"><MessageSquare className="h-5 w-5" /> Feedback Trends</CardTitle></CardHeader>
          <CardContent>
            {feedbackTrendsQuery.isLoading ? <Skeleton className="h-40 w-full" /> : 
              feedbackTrendsQuery.data?.items?.map((trend: any) => (
                <div key={trend.category_id} className="mb-4 last:mb-0 p-3 border rounded-lg bg-card/50">
                  <div className="flex justify-between items-center mb-1"><span className="font-medium">{trend.category_name}</span><span className="flex items-center text-yellow-500 font-bold"><Star className="h-4 w-4 fill-current mr-1"/>{trend.average_rating.toFixed(1)}</span></div>
                  <p className="text-[11px] text-muted-foreground">Total of {trend.total_feedbacks} reviews collected.</p>
                </div>
              ))
            }
          </CardContent>
        </Card>

        <Card className="border-amber-200 bg-amber-50 shadow-md">
          <CardHeader><CardTitle className="text-amber-800 text-lg flex items-center gap-2"><AlertTriangle className="h-5 w-5" /> Operational Insight</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-white rounded-lg border border-amber-200">
              <p className="text-sm font-bold text-amber-900">Low Rating Alert: Lighting Repairs</p>
              <p className="text-xs text-amber-800 mt-1 italic">Consistently mentions "slow response time."</p>
              <div className="mt-3 px-2 py-1 bg-amber-100 text-[10px] font-bold text-amber-700 w-fit rounded uppercase">
                PROPOSAL: Night-shift Implementation
              </div>
            </div>
            <p className="text-xs text-muted-foreground px-1">
              Data suggests re-balancing workloads between teams to reduce latency.
            </p>
          </CardContent>
        </Card>
      </div>
    </motion.div>
  );
}