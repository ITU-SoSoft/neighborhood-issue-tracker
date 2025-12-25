"use client";

import { useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { X, Check, CheckCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useNotifications,
  useUnreadNotificationCount,
  useMarkNotificationAsRead,
  useMarkAllNotificationsAsRead,
  useDeleteNotification,
} from "@/lib/queries/notifications";
import { Notification, NotificationType } from "@/lib/api/types";
import { formatRelativeTime } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface NotificationPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const getNotificationIcon = (type: NotificationType) => {
  switch (type) {
    case NotificationType.TICKET_CREATED:
      return "🎫";
    case NotificationType.TICKET_STATUS_CHANGED:
      return "🔄";
    case NotificationType.TICKET_FOLLOWED:
      return "👥";
    case NotificationType.COMMENT_ADDED:
      return "💬";
    case NotificationType.TICKET_ASSIGNED:
      return "📋";
    case NotificationType.NEW_TICKET_FOR_TEAM:
      return "🆕";
    case NotificationType.ESCALATION_REQUESTED:
      return "⚠️";
    case NotificationType.ESCALATION_APPROVED:
      return "✅";
    case NotificationType.ESCALATION_REJECTED:
      return "❌";
    default:
      return "🔔";
  }
};

function NotificationItem({
  notification,
  onMarkAsRead,
  onDelete,
  onClose,
}: {
  notification: Notification;
  onMarkAsRead: (id: string) => void;
  onDelete: (id: string) => void;
  onClose: () => void;
}) {
  const isRead = notification.is_read;

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className={cn(
        "group relative rounded-lg border p-4 transition hover:bg-muted/50",
        !isRead && "bg-primary/5 border-primary/20"
      )}
    >
      <div className="flex items-start gap-3">
        <div className="text-2xl shrink-0">{getNotificationIcon(notification.notification_type)}</div>
        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex items-start justify-between gap-2">
            <h4 className={cn("text-sm font-medium", !isRead && "font-semibold")}>
              {notification.title}
            </h4>
            {!isRead && (
              <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5" />
            )}
          </div>
          <p className="text-xs text-muted-foreground line-clamp-2">
            {notification.message}
          </p>
          <div className="flex items-center justify-between gap-2 mt-2">
            <span className="text-xs text-muted-foreground">
              {formatRelativeTime(notification.created_at)}
            </span>
            {notification.ticket_id && (
              <Link
                href={`/tickets/${notification.ticket_id}`}
                className="text-xs text-primary hover:underline"
                onClick={onClose}
              >
                View ticket
              </Link>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          {!isRead && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition"
              onClick={() => onMarkAsRead(notification.id)}
              aria-label="Mark as read"
            >
              <Check className="h-3 w-3" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition text-muted-foreground hover:text-destructive"
            onClick={() => onDelete(notification.id)}
            aria-label="Delete notification"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

export function NotificationPanel({ isOpen, onClose }: NotificationPanelProps) {
  const { data, isLoading, error, refetch } = useNotifications({ page_size: 20 });
  const { data: unreadData, refetch: refetchUnread } = useUnreadNotificationCount();
  const markAsReadMutation = useMarkNotificationAsRead();
  const markAllAsReadMutation = useMarkAllNotificationsAsRead();
  const deleteNotificationMutation = useDeleteNotification();

  const notifications = data?.items ?? [];
  const unreadCount = unreadData?.count ?? 0;

  // Refetch when panel opens
  useEffect(() => {
    if (isOpen) {
      refetch();
      refetchUnread();
    }
  }, [isOpen, refetch, refetchUnread]);

  const handleMarkAsRead = (id: string) => {
    markAsReadMutation.mutate(id);
  };

  const handleMarkAllAsRead = () => {
    markAllAsReadMutation.mutate();
  };

  const handleDelete = (id: string) => {
    deleteNotificationMutation.mutate(id);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20"
            style={{ zIndex: 99998 }}
          />

          {/* Panel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-full w-full max-w-md bg-background border-l border-border shadow-xl flex flex-col"
            style={{ zIndex: 99999 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border p-4">
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold">Notifications</h2>
                {unreadCount > 0 && (
                  <Badge variant="destructive" className="h-5 min-w-5 px-1.5 text-xs">
                    {unreadCount}
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleMarkAllAsRead}
                    disabled={markAllAsReadMutation.isPending}
                    className="text-xs"
                  >
                    {markAllAsReadMutation.isPending ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <>
                        <CheckCheck className="h-3 w-3 mr-1" />
                        Mark all read
                      </>
                    )}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onClose}
                  className="h-8 w-8"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {isLoading ? (
                <div className="space-y-3">
                  {[...Array(5)].map((_, i) => (
                    <Card key={i} className="p-4">
                      <Skeleton className="h-4 w-3/4 mb-2" />
                      <Skeleton className="h-3 w-full mb-1" />
                      <Skeleton className="h-3 w-2/3" />
                    </Card>
                  ))}
                </div>
              ) : error ? (
                <Card className="p-6 text-center">
                  <p className="text-sm text-muted-foreground">
                    Failed to load notifications
                  </p>
                </Card>
              ) : notifications.length === 0 ? (
                <Card className="p-12 text-center">
                  <p className="text-sm text-muted-foreground">
                    No notifications yet
                  </p>
                </Card>
              ) : (
                notifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onMarkAsRead={handleMarkAsRead}
                    onDelete={handleDelete}
                    onClose={onClose}
                  />
                ))
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

