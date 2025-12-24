"use client";

import { useState, use } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth/context";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { ErrorState } from "@/components/shared/error-state";
import { TicketDetailSkeleton } from "@/components/shared/skeletons";
import {
  useTicket,
  useUpdateTicketStatus,
  useAssignTicket,
  useFollowTicket,
  useUnfollowTicket,
  useCreateComment,
  useSubmitFeedback,
} from "@/lib/queries/tickets";
import { useCreateEscalation } from "@/lib/queries/escalations";
import { TicketStatus, UserRole, Comment as TicketComment } from "@/lib/api/types";
import {
  formatRelativeTime,
  formatDateTime,
  getStatusVariant,
  getStatusLabel,
  getInitials,
} from "@/lib/utils";
import {
  fadeInUp,
  staggerContainer,
  staggerItem,
  scaleIn,
} from "@/lib/animations";
import {
  ArrowLeft,
  MapPin,
  Calendar,
  User as UserIcon,
  MessageCircle,
  Users,
  Heart,
  Send,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Star,
  Image as ImageIcon,
  Lock,
} from "lucide-react";

// Dynamically import the map component
const TicketMap = dynamic(
  () => import("@/components/map/ticket-map").then((mod) => mod.TicketMap),
  {
    ssr: false,
    loading: () => (
      <div className="h-[200px] rounded-xl bg-muted flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    ),
  }
);

function getStatusIcon(status: TicketStatus) {
  switch (status) {
    case TicketStatus.NEW:
      return <AlertCircle className="h-4 w-4" />;
    case TicketStatus.IN_PROGRESS:
      return <Clock className="h-4 w-4" />;
    case TicketStatus.RESOLVED:
      return <CheckCircle2 className="h-4 w-4" />;
    case TicketStatus.CLOSED:
      return <CheckCircle2 className="h-4 w-4" />;
    case TicketStatus.ESCALATED:
      return <AlertTriangle className="h-4 w-4" />;
    default:
      return null;
  }
}

export default function TicketDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { user } = useAuth();

  // TanStack Query hooks
  const { data: ticket, isLoading, error, refetch } = useTicket(id);

  // Mutations
  const updateStatusMutation = useUpdateTicketStatus();
  const followMutation = useFollowTicket();
  const unfollowMutation = useUnfollowTicket();
  const createCommentMutation = useCreateComment();
  const submitFeedbackMutation = useSubmitFeedback();
  const createEscalationMutation = useCreateEscalation();

  // Comment state
  const [newComment, setNewComment] = useState("");
  const [isInternalComment, setIsInternalComment] = useState(false);

  // Modal states
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<TicketStatus | "">("");
  const [statusComment, setStatusComment] = useState("");

  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState(5);
  const [feedbackComment, setFeedbackComment] = useState("");

  const [showEscalationModal, setShowEscalationModal] = useState(false);
  const [escalationReason, setEscalationReason] = useState("");

  const [selectedPhoto, setSelectedPhoto] = useState<string | null>(null);

  // Handlers
  const handleFollow = async () => {
    // Only citizens can follow/unfollow tickets
    if (!ticket || user.role !== UserRole.CITIZEN) return;
    try {
      if (ticket.is_following) {
        await unfollowMutation.mutateAsync(ticket.id);
        toast.success("Unfollowed ticket");
      } else {
        await followMutation.mutateAsync(ticket.id);
        toast.success("Following ticket");
      }
    } catch (err) {
      toast.error("Failed to update follow status");
    }
  };

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || !ticket) return;

    try {
      await createCommentMutation.mutateAsync({
        ticketId: ticket.id,
        data: {
          content: newComment.trim(),
          is_internal: isInternalComment,
        },
      });
      setNewComment("");
      setIsInternalComment(false);
      toast.success("Comment added");
    } catch (err) {
      toast.error("Failed to add comment");
    }
  };

  const handleStatusUpdate = async () => {
    if (!selectedStatus || !ticket) return;

    try {
      await updateStatusMutation.mutateAsync({
        ticketId: ticket.id,
        data: {
          status: selectedStatus,
          comment: statusComment || undefined,
        },
      });
      setShowStatusModal(false);
      setSelectedStatus("");
      setStatusComment("");
      toast.success("Status updated");
    } catch (err) {
      toast.error("Failed to update status");
    }
  };

  const handleSubmitFeedback = async () => {
    if (!ticket) return;

    try {
      await submitFeedbackMutation.mutateAsync({
        ticketId: ticket.id,
        data: {
          rating: feedbackRating,
          comment: feedbackComment || undefined,
        },
      });
      setShowFeedbackModal(false);
      setFeedbackRating(5);
      setFeedbackComment("");
      toast.success("Thank you for your feedback!");
    } catch (err) {
      toast.error("Failed to submit feedback");
    }
  };

  const handleSubmitEscalation = async () => {
    if (!escalationReason.trim() || !ticket) return;

    try {
      await createEscalationMutation.mutateAsync({
        ticket_id: ticket.id,
        reason: escalationReason.trim(),
      });
      setShowEscalationModal(false);
      setEscalationReason("");
      toast.success("Escalation request submitted");
    } catch (err) {
      toast.error("Failed to submit escalation");
    }
  };

  // Permission checks
  const canUpdateStatus =
    user?.role === UserRole.SUPPORT || user?.role === UserRole.MANAGER;
  const canGiveFeedback =
    ticket?.status === TicketStatus.RESOLVED &&
    !ticket.has_feedback &&
    ticket.reporter_id === user?.id;
  const canEscalate =
    (user?.role === UserRole.SUPPORT || user?.role === UserRole.MANAGER) &&
    ticket?.can_escalate;

  const canFollow = user && user.role === UserRole.CITIZEN;

  // Loading state
  if (isLoading) {
    return <TicketDetailSkeleton />;
  }

  // Error state
  if (error || !ticket) {
    return (
      <ErrorState
        title="Ticket Not Found"
        message={error instanceof Error ? error.message : "The ticket you're looking for doesn't exist."}
        action={
          <Link href="/tickets">
            <Button>Back to Tickets</Button>
          </Link>
        }
      />
    );
  }

  const isFollowPending = followMutation.isPending || unfollowMutation.isPending;

  return (
    <motion.div 
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {/* Header */}
      <motion.div 
        className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
        variants={fadeInUp}
      >
        <div className="flex items-start gap-4">
          <Link href="/tickets">
            <Button variant="ghost" size="sm" aria-label="Back to tickets">
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-semibold text-foreground">{ticket.title}</h1>
              <Badge variant={getStatusVariant(ticket.status)} className="flex items-center gap-1">
                {getStatusIcon(ticket.status)}
                {getStatusLabel(ticket.status)}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Reported {formatRelativeTime(ticket.created_at)} by {ticket.reporter_name || "Anonymous"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {canFollow && (
            <Button
              variant={ticket.is_following ? "default" : "outline"}
              size="sm"
              onClick={handleFollow}
              disabled={isFollowPending}
            >
              {isFollowPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Heart className={`mr-2 h-4 w-4 ${ticket.is_following ? "fill-current" : ""}`} />
              )}
              {ticket.is_following ? "Following" : "Follow"}
            </Button>
          )}
          {canUpdateStatus && (
            <Button variant="outline" size="sm" onClick={() => setShowStatusModal(true)}>
              Update Status
            </Button>
          )}
        </div>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main content */}
        <motion.div 
          className="lg:col-span-2 space-y-6"
          variants={staggerContainer}
        >
          {/* Description */}
          <motion.div variants={staggerItem}>
            <Card className="p-6">
              <h2 className="text-lg font-semibold text-foreground mb-4">Description</h2>
              <p className="text-muted-foreground whitespace-pre-wrap">{ticket.description}</p>
            </Card>
          </motion.div>

          {/* Activity Log */}
          {ticket.status_logs && ticket.status_logs.length > 0 && (
            <motion.div variants={staggerItem}>
              <Card className="p-6">
                <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Activity Log
                </h2>
                <div className="space-y-4">
                  {ticket.status_logs.map((log, index) => {
                    // Convert string status to TicketStatus enum
                    const stringToStatus = (status: string | null): TicketStatus | null => {
                      if (!status) return null;
                      return status as TicketStatus;
                    };

                    const oldStatus = stringToStatus(log.old_status);
                    const newStatus = stringToStatus(log.new_status);

                    return (
                      <div
                        key={log.id}
                        className="flex gap-4 pb-4 border-b last:border-b-0 last:pb-0"
                      >
                        <div className="flex-shrink-0">
                          <div className="w-2 h-2 rounded-full bg-primary mt-2" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <p className="text-sm font-medium text-foreground flex items-center gap-2 flex-wrap">
                                {log.old_status ? (
                                  <>
                                    Status changed from{" "}
                                    {oldStatus ? (
                                      <Badge variant={getStatusVariant(oldStatus)} className="flex items-center gap-1">
                                        {getStatusIcon(oldStatus)}
                                        {getStatusLabel(oldStatus)}
                                      </Badge>
                                    ) : (
                                      <span className="font-semibold">{log.old_status}</span>
                                    )}{" "}
                                    to{" "}
                                    {newStatus ? (
                                      <Badge variant={getStatusVariant(newStatus)} className="flex items-center gap-1">
                                        {getStatusIcon(newStatus)}
                                        {getStatusLabel(newStatus)}
                                      </Badge>
                                    ) : (
                                      <span className="font-semibold">{log.new_status}</span>
                                    )}
                                  </>
                                ) : (
                                  <>
                                    Ticket created with status{" "}
                                    {newStatus ? (
                                      <Badge variant={getStatusVariant(newStatus)} className="flex items-center gap-1">
                                        {getStatusIcon(newStatus)}
                                        {getStatusLabel(newStatus)}
                                      </Badge>
                                    ) : (
                                      <span className="font-semibold">{log.new_status}</span>
                                    )}
                                  </>
                                )}
                              </p>
                              {log.changed_by_name && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  by {log.changed_by_name}
                                </p>
                              )}
                              {log.comment && (
                                <p className="text-sm text-muted-foreground mt-2 italic">
                                  "{log.comment}"
                                </p>
                              )}
                            </div>
                            <div className="flex-shrink-0 text-xs text-muted-foreground">
                              {formatRelativeTime(log.created_at)}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>
            </motion.div>
          )}

          {/* Photos */}
          {ticket.photos.length > 0 && (
            <motion.div variants={staggerItem}>
              <Card className="p-6">
                <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                  <ImageIcon className="h-5 w-5" />
                  Photos ({ticket.photos.length})
                </h2>
                <motion.div 
                  className="grid grid-cols-2 gap-3 sm:grid-cols-3"
                  variants={staggerContainer}
                >
                  {ticket.photos.map((photo) => (
                    <motion.button
                      key={photo.id}
                      onClick={() => setSelectedPhoto(photo.url)}
                      className="aspect-square overflow-hidden rounded-xl border border-border transition hover:border-primary"
                      variants={scaleIn}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      aria-label={`View photo: ${photo.filename}`}
                    >
                      <img
                        src={photo.url}
                        alt={photo.filename}
                        className="h-full w-full object-cover"
                      />
                    </motion.button>
                  ))}
                </motion.div>
              </Card>
            </motion.div>
          )}

          {/* Comments */}
          <motion.div variants={staggerItem}>
            <Card className="p-6">
              <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                <MessageCircle className="h-5 w-5" />
                Comments ({ticket.comment_count})
              </h2>

              {/* Comments list */}
              {ticket.comments.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">No comments yet</p>
              ) : (
                <motion.div 
                  className="space-y-4 mb-6"
                  variants={staggerContainer}
                  initial="hidden"
                  animate="visible"
                >
                  <AnimatePresence>
                    {ticket.comments.map((comment, index) => (
                      <motion.div
                        key={comment.id}
                        variants={staggerItem}
                        initial="hidden"
                        animate="visible"
                        transition={{ delay: index * 0.05 }}
                        className={`rounded-xl p-4 ${
                          comment.is_internal
                            ? "bg-amber-50 border border-amber-200"
                            : "bg-muted"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                              <span className="text-xs font-medium text-primary">
                                {getInitials(comment.user_name)}
                              </span>
                            </div>
                            <span className="font-medium text-foreground">
                              {comment.user_name || "Anonymous"}
                            </span>
                            {comment.is_internal && (
                              <Badge variant="warning" className="text-xs">
                                <Lock className="h-3 w-3 mr-1" />
                                Internal
                              </Badge>
                            )}
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {formatRelativeTime(comment.created_at)}
                          </span>
                        </div>
                        <p className="text-muted-foreground text-sm whitespace-pre-wrap">
                          {comment.content}
                        </p>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </motion.div>
              )}

              {/* Add comment form */}
              <form onSubmit={handleSubmitComment} className="space-y-3">
                <Textarea
                  placeholder="Add a comment..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  rows={3}
                />
                <div className="flex items-center justify-between">
                  {(user?.role === UserRole.SUPPORT || user?.role === UserRole.MANAGER) && (
                    <label className="flex items-center gap-2 text-sm text-muted-foreground">
                      <input
                        id="internal-comment"
                        type="checkbox"
                        checked={isInternalComment}
                        onChange={(e) => setIsInternalComment(e.target.checked)}
                        className="rounded border-border text-primary focus:ring-primary"
                      />
                      Internal note (only visible to staff)
                    </label>
                  )}
                  <Button
                    type="submit"
                    disabled={!newComment.trim() || createCommentMutation.isPending}
                    className="ml-auto"
                  >
                    {createCommentMutation.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="mr-2 h-4 w-4" />
                    )}
                    Send
                  </Button>
                </div>
              </form>
            </Card>
          </motion.div>
        </motion.div>

        {/* Sidebar */}
        <motion.div 
          className="space-y-6"
          variants={staggerContainer}
        >
          {/* Details */}
          <motion.div variants={staggerItem}>
            <Card className="p-6">
              <h2 className="text-lg font-semibold text-foreground mb-4">Details</h2>
              <dl className="space-y-4">
                <div>
                  <dt className="text-xs font-medium text-muted-foreground uppercase">Category</dt>
                  <dd className="mt-1">
                    <Badge variant="secondary">{ticket.category_name}</Badge>
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted-foreground uppercase">Status</dt>
                  <dd className="mt-1">
                    <Badge variant={getStatusVariant(ticket.status)} className="flex items-center gap-1 w-fit">
                      {getStatusIcon(ticket.status)}
                      {getStatusLabel(ticket.status)}
                    </Badge>
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted-foreground uppercase">Reporter</dt>
                  <dd className="mt-1 flex items-center gap-2 text-sm text-foreground">
                    <UserIcon className="h-4 w-4 text-muted-foreground" />
                    {ticket.reporter_name || "Anonymous"}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted-foreground uppercase">Assigned Team</dt>
                  <dd className="mt-1 flex items-center gap-2 text-sm text-foreground">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    {ticket.team_name || "Unassigned"}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted-foreground uppercase">Created</dt>
                  <dd className="mt-1 flex items-center gap-2 text-sm text-foreground">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    {formatDateTime(ticket.created_at)}
                  </dd>
                </div>
                {ticket.resolved_at && (
                  <div>
                    <dt className="text-xs font-medium text-muted-foreground uppercase">Resolved</dt>
                    <dd className="mt-1 flex items-center gap-2 text-sm text-foreground">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      {formatDateTime(ticket.resolved_at)}
                    </dd>
                  </div>
                )}
                <div>
                  <dt className="text-xs font-medium text-muted-foreground uppercase">Followers</dt>
                  <dd className="mt-1 flex items-center gap-2 text-sm text-foreground">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    {ticket.follower_count}
                  </dd>
                </div>
              </dl>
            </Card>
          </motion.div>

          {/* Location */}
          <motion.div variants={staggerItem}>
            <Card className="p-6">
              <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                Location
              </h2>
              <TicketMap
                latitude={ticket.location.latitude}
                longitude={ticket.location.longitude}
              />
              {ticket.location.address && (
                <p className="mt-3 text-sm text-muted-foreground">{ticket.location.address}</p>
              )}
            </Card>
          </motion.div>

          {/* Actions - Only visible for non-Citizen users */}
          {user?.role !== UserRole.CITIZEN && (
            <motion.div variants={staggerItem}>
              <Card className="p-6">
                <h2 className="text-lg font-semibold text-foreground mb-4">Actions</h2>
                <div className="space-y-3">
                  {canGiveFeedback && (
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => setShowFeedbackModal(true)}
                    >
                      <Star className="mr-2 h-4 w-4" />
                      Leave Feedback
                    </Button>
                  )}
                  {canEscalate && (
                    <Button
                      variant="outline"
                      className="w-full justify-start text-amber-600 hover:bg-amber-50"
                      onClick={() => setShowEscalationModal(true)}
                    >
                      <AlertTriangle className="mr-2 h-4 w-4" />
                      Request Escalation
                    </Button>
                  )}
                  {ticket.has_feedback && (
                    <p className="text-sm text-green-600 flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4" />
                      Feedback submitted
                    </p>
                  )}
                  {!ticket.can_escalate && ticket.has_escalation && (
                    <p className="text-sm text-amber-600 flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4" />
                      Can't escalate
                    </p>
                  )}
                </div>
              </Card>
            </motion.div>
          )}
        </motion.div>
      </div>

      {/* Status Update Dialog */}
      <Dialog open={showStatusModal} onOpenChange={setShowStatusModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Status</DialogTitle>
            <DialogDescription>
              Change the status of this ticket
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>New Status</Label>
              <Select value={selectedStatus} onValueChange={(value) => setSelectedStatus(value as TicketStatus)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={TicketStatus.IN_PROGRESS}>In Progress</SelectItem>
                  <SelectItem value={TicketStatus.RESOLVED}>Resolved</SelectItem>
                  <SelectItem value={TicketStatus.CLOSED}>Closed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Comment (optional)</Label>
              <Textarea
                value={statusComment}
                onChange={(e) => setStatusComment(e.target.value)}
                placeholder="Add a note about this status change..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowStatusModal(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleStatusUpdate} 
              disabled={!selectedStatus || updateStatusMutation.isPending}
            >
              {updateStatusMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Update
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Feedback Dialog */}
      <Dialog open={showFeedbackModal} onOpenChange={setShowFeedbackModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Leave Feedback</DialogTitle>
            <DialogDescription>
              Rate your experience with the resolution of this issue
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label id="rating-label">Rating</Label>
              <div className="flex items-center gap-2" role="group" aria-labelledby="rating-label">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setFeedbackRating(star)}
                    className="focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded"
                    aria-label={`Rate ${star} star${star > 1 ? "s" : ""}`}
                    aria-pressed={feedbackRating >= star}
                  >
                    <Star
                      className={`h-8 w-8 transition ${
                        star <= feedbackRating
                          ? "text-amber-400 fill-amber-400"
                          : "text-muted-foreground"
                      }`}
                      aria-hidden="true"
                    />
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <Label>Comment (optional)</Label>
              <Textarea
                value={feedbackComment}
                onChange={(e) => setFeedbackComment(e.target.value)}
                placeholder="Share your experience..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFeedbackModal(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmitFeedback} 
              disabled={submitFeedbackMutation.isPending}
            >
              {submitFeedbackMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Submit Feedback
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Escalation Dialog */}
      <Dialog open={showEscalationModal} onOpenChange={setShowEscalationModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Request Escalation</DialogTitle>
            <DialogDescription>
              Escalation requests will be reviewed by a manager. Please provide a detailed reason.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Reason for Escalation</Label>
              <Textarea
                value={escalationReason}
                onChange={(e) => setEscalationReason(e.target.value)}
                placeholder="Explain why this ticket needs to be escalated..."
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEscalationModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmitEscalation}
              disabled={!escalationReason.trim() || createEscalationMutation.isPending}
            >
              {createEscalationMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Submit Request
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Photo Dialog */}
      <Dialog open={!!selectedPhoto} onOpenChange={() => setSelectedPhoto(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Photo</DialogTitle>
          </DialogHeader>
          {selectedPhoto && (
            <img
              src={selectedPhoto}
              alt="Full size view of ticket photo"
              className="w-full rounded-lg"
            />
          )}
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
