"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth/context";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/shared/error-state";
import { useEscalations } from "@/lib/queries/escalations";
import { EscalationStatus, UserRole } from "@/lib/api/types";
import { formatRelativeTime, cn } from "@/lib/utils";
import {
  fadeInUp,
  staggerContainer,
  staggerItem,
  cardHover,
  cardTap,
} from "@/lib/animations";
import {
  AlertTriangle,
  Clock,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Filter,
} from "lucide-react";

const statusTabs = [
  { value: "", label: "All", icon: Filter },
  { value: EscalationStatus.PENDING, label: "Pending", icon: Clock },
  { value: EscalationStatus.APPROVED, label: "Approved", icon: CheckCircle2 },
  { value: EscalationStatus.REJECTED, label: "Rejected", icon: XCircle },
] as const;

function getStatusVariant(
  status: EscalationStatus,
): "warning" | "success" | "danger" {
  switch (status) {
    case EscalationStatus.PENDING:
      return "warning";
    case EscalationStatus.APPROVED:
      return "success";
    case EscalationStatus.REJECTED:
      return "danger";
    default:
      return "warning";
  }
}

function EscalationCardSkeleton() {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-3">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-full" />
        </div>
        <Skeleton className="h-6 w-20" />
      </div>
    </Card>
  );
}

export default function EscalationsPage() {
  const { user } = useAuth();
  const [statusFilter, setStatusFilter] = useState<EscalationStatus | "">("");

  const { data, isLoading, isError, refetch } = useEscalations({
    status_filter: statusFilter || undefined,
    page_size: 50,
  });

  const escalations = data?.items ?? [];
  const isManager = user?.role === UserRole.MANAGER;

  // Redirect check for non-staff users
  if (user && user.role === UserRole.CITIZEN) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold text-foreground">Access Denied</h2>
        <p className="text-muted-foreground mt-2">
          You do not have permission to view this page.
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
      <motion.div variants={fadeInUp}>
        <h1 className="text-2xl font-semibold text-foreground">Escalations</h1>
        <p className="text-muted-foreground">
          {isManager
            ? "Review and manage escalated tickets"
            : "View escalation requests"}
        </p>
      </motion.div>

      {/* Status Tabs */}
      <motion.div variants={fadeInUp}>
        <div className="flex flex-wrap gap-2">
          {statusTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = statusFilter === tab.value;
            return (
              <Button
                key={tab.value}
                variant={isActive ? "default" : "outline"}
                size="sm"
                onClick={() => setStatusFilter(tab.value)}
                className={cn("gap-2", isActive && "shadow-sm")}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </Button>
            );
          })}
        </div>
      </motion.div>

      {/* Escalations List */}
      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <EscalationCardSkeleton key={i} />
          ))}
        </div>
      ) : isError ? (
        <ErrorState
          title="Failed to load escalations"
          message="There was a problem loading the escalations. Please try again."
          onRetry={refetch}
        />
      ) : escalations.length === 0 ? (
        <motion.div variants={fadeInUp}>
          <Card>
            <CardContent className="py-12 text-center">
              <AlertTriangle className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-semibold text-foreground">
                No escalations found
              </h3>
              <p className="mt-2 text-muted-foreground">
                {statusFilter
                  ? `No ${statusFilter.toLowerCase()} escalations at this time.`
                  : "There are no escalation requests at this time."}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      ) : (
        <motion.div
          className="space-y-4"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {escalations.map((escalation) => (
            <motion.div key={escalation.id} variants={staggerItem}>
              <Link href={`/escalations/${escalation.id}`}>
                <motion.div whileHover={cardHover} whileTap={cardTap}>
                  <Card className="p-5 transition hover:border-primary/30 hover:shadow-md">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1 space-y-2">
                        <div className="flex items-center gap-3">
                          <h3 className="font-semibold text-foreground line-clamp-1">
                            {escalation.ticket_title || "Untitled Ticket"}
                          </h3>
                          <Badge variant={getStatusVariant(escalation.status)}>
                            {escalation.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {escalation.reason}
                        </p>
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                          <span>
                            Requested by{" "}
                            <span className="font-medium text-foreground">
                              {escalation.requester_name || "Unknown"}
                            </span>
                          </span>
                          <span>
                            {formatRelativeTime(escalation.created_at)}
                          </span>
                          {escalation.reviewer_name && (
                            <span>
                              Reviewed by{" "}
                              <span className="font-medium text-foreground">
                                {escalation.reviewer_name}
                              </span>
                            </span>
                          )}
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 shrink-0 text-muted-foreground" />
                    </div>
                  </Card>
                </motion.div>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
}
