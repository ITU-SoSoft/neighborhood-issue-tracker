"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth/context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ErrorState } from "@/components/shared/error-state";
import {
  useEscalation,
  useApproveEscalation,
  useRejectEscalation,
} from "@/lib/queries/escalations";
import { EscalationStatus, UserRole } from "@/lib/api/types";
import { formatDate } from "@/lib/utils";
import { fadeInUp, staggerContainer, staggerItem } from "@/lib/animations";
import {
  AlertTriangle,
  ArrowLeft,
  Clock,
  CheckCircle2,
  XCircle,
  User,
  FileText,
  Loader2,
  ExternalLink,
} from "lucide-react";

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

function getStatusIcon(status: EscalationStatus) {
  switch (status) {
    case EscalationStatus.PENDING:
      return <Clock className="h-5 w-5" />;
    case EscalationStatus.APPROVED:
      return <CheckCircle2 className="h-5 w-5" />;
    case EscalationStatus.REJECTED:
      return <XCircle className="h-5 w-5" />;
    default:
      return <AlertTriangle className="h-5 w-5" />;
  }
}

function EscalationDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-10" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-64" />
          <Skeleton className="h-4 w-40" />
        </div>
      </div>
      <Card>
        <CardContent className="p-6 space-y-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </CardContent>
      </Card>
    </div>
  );
}

export default function EscalationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const escalationId = params.id as string;

  const [reviewComment, setReviewComment] = useState("");
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);

  const {
    data: escalation,
    isLoading,
    isError,
    refetch,
  } = useEscalation(escalationId);
  const approveEscalation = useApproveEscalation();
  const rejectEscalation = useRejectEscalation();

  const isManager = user?.role === UserRole.MANAGER;
  const isPending = escalation?.status === EscalationStatus.PENDING;
  const canReview = isManager && isPending;

  const handleApprove = async () => {
    if (!escalation) return;
    setIsApproving(true);
    try {
      await approveEscalation.mutateAsync({
        escalationId: escalation.id,
        data: { comment: reviewComment.trim() || undefined },
      });
      toast.success("Escalation approved successfully");
      router.push("/escalations");
    } catch (error) {
      toast.error("Failed to approve escalation");
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async () => {
    if (!escalation) return;
    setIsRejecting(true);
    try {
      await rejectEscalation.mutateAsync({
        escalationId: escalation.id,
        data: { comment: reviewComment.trim() || undefined },
      });
      toast.success("Escalation rejected");
      router.push("/escalations");
    } catch (error) {
      toast.error("Failed to reject escalation");
    } finally {
      setIsRejecting(false);
    }
  };

  // Access check
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

  if (isLoading) {
    return <EscalationDetailSkeleton />;
  }

  if (isError || !escalation) {
    return (
      <ErrorState
        title="Failed to load escalation"
        message="The escalation request could not be found or there was an error loading it."
        onRetry={refetch}
      />
    );
  }

  return (
    <motion.div
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {/* Back button and header */}
      <motion.div variants={fadeInUp}>
        <Link
          href="/escalations"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Escalations
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">
              Escalation Request
            </h1>
            <p className="text-muted-foreground mt-1">
              For ticket: {escalation.ticket_title || "Untitled"}
            </p>
          </div>
          <Badge
            variant={getStatusVariant(escalation.status)}
            className="text-sm px-3 py-1"
          >
            {getStatusIcon(escalation.status)}
            <span className="ml-1">{escalation.status}</span>
          </Badge>
        </div>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main content */}
        <motion.div className="lg:col-span-2 space-y-6" variants={staggerItem}>
          {/* Reason */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <FileText className="h-5 w-5" />
                Escalation Reason
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-foreground whitespace-pre-wrap">
                {escalation.reason}
              </p>
            </CardContent>
          </Card>

          {/* Review Comment (if reviewed) */}
          {escalation.review_comment && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Review Comment</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground whitespace-pre-wrap">
                  {escalation.review_comment}
                </p>
                {escalation.reviewer_name && (
                  <p className="mt-2 text-sm text-muted-foreground">
                    — {escalation.reviewer_name}
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Manager Review Section */}
          {canReview && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  Review This Escalation
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="review-comment">Comment (optional)</Label>
                  <Textarea
                    id="review-comment"
                    placeholder="Add a comment about your decision..."
                    value={reviewComment}
                    onChange={(e) => setReviewComment(e.target.value)}
                    rows={3}
                  />
                </div>
                <div className="flex gap-3">
                  <Button
                    onClick={handleApprove}
                    disabled={isApproving || isRejecting}
                    className="flex-1 bg-green-600 hover:bg-green-700"
                  >
                    {isApproving ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Approving...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="mr-2 h-4 w-4" />
                        Approve
                      </>
                    )}
                  </Button>
                  <Button
                    onClick={handleReject}
                    disabled={isApproving || isRejecting}
                    variant="destructive"
                    className="flex-1"
                  >
                    {isRejecting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Rejecting...
                      </>
                    ) : (
                      <>
                        <XCircle className="mr-2 h-4 w-4" />
                        Reject
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>

        {/* Sidebar */}
        <motion.div className="space-y-6" variants={staggerItem}>
          {/* Details Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Requested By</p>
                <div className="flex items-center gap-2 mt-1">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">
                    {escalation.requester_name || "Unknown"}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Requested At</p>
                <p className="font-medium">
                  {formatDate(escalation.created_at, {
                    month: "long",
                    day: "numeric",
                    year: "numeric",
                    hour: "numeric",
                    minute: "2-digit",
                  })}
                </p>
              </div>
              {escalation.reviewed_at && (
                <div>
                  <p className="text-sm text-muted-foreground">Reviewed At</p>
                  <p className="font-medium">
                    {formatDate(escalation.reviewed_at, {
                      month: "long",
                      day: "numeric",
                      year: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              )}
              {escalation.reviewer_name && (
                <div>
                  <p className="text-sm text-muted-foreground">Reviewed By</p>
                  <div className="flex items-center gap-2 mt-1">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">
                      {escalation.reviewer_name}
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* View Ticket Card */}
          <Card>
            <CardContent className="p-4">
              <Link href={`/tickets/${escalation.ticket_id}`}>
                <Button variant="outline" className="w-full gap-2">
                  <ExternalLink className="h-4 w-4" />
                  View Original Ticket
                </Button>
              </Link>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  );
}
