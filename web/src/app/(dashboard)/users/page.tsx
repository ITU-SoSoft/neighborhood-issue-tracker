"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth/context";
import { Card, CardContent } from "@/components/ui/card";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { ErrorState } from "@/components/shared/error-state";
import { useUsers, useUpdateUserRole } from "@/lib/queries/users";
import { User, UserRole } from "@/lib/api/types";
import { formatDate, getRoleLabel, getRoleVariant } from "@/lib/utils";
import { fadeInUp, staggerContainer, staggerItem } from "@/lib/animations";
import {
  Users as UsersIcon,
  User as UserIcon,
  Mail,
  Phone,
  Calendar,
  Shield,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from "lucide-react";

const PAGE_SIZE = 20;

const roleFilterOptions = [
  { value: "all", label: "All Roles" },
  { value: UserRole.CITIZEN, label: "Citizens" },
  { value: UserRole.SUPPORT, label: "Support" },
  { value: UserRole.MANAGER, label: "Managers" },
];

function UserCardSkeleton() {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-10 rounded-full" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-48" />
        </div>
        <Skeleton className="h-6 w-20" />
      </div>
    </Card>
  );
}

interface RoleChangeDialogProps {
  user: User | null;
  open: boolean;
  onClose: () => void;
  onConfirm: (role: UserRole) => Promise<void>;
  isLoading: boolean;
}

function RoleChangeDialog({
  user,
  open,
  onClose,
  onConfirm,
  isLoading,
}: RoleChangeDialogProps) {
  const [selectedRole, setSelectedRole] = useState<UserRole | "">(
    user?.role || "",
  );

  const handleConfirm = async () => {
    if (selectedRole && user) {
      await onConfirm(selectedRole);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Change User Role</DialogTitle>
          <DialogDescription>
            Update the role for {user?.name}. This will change their permissions
            in the system.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Current Role</Label>
            <Badge variant={getRoleVariant(user?.role || UserRole.CITIZEN)}>
              {getRoleLabel(user?.role || UserRole.CITIZEN)}
            </Badge>
          </div>
          <div className="space-y-2">
            <Label htmlFor="new-role">New Role</Label>
            <Select
              value={selectedRole}
              onValueChange={(value) => setSelectedRole(value as UserRole)}
            >
              <SelectTrigger id="new-role">
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={UserRole.CITIZEN}>Citizen</SelectItem>
                <SelectItem value={UserRole.SUPPORT}>Support</SelectItem>
                <SelectItem value={UserRole.MANAGER}>Manager</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!selectedRole || selectedRole === user?.role || isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Updating...
              </>
            ) : (
              "Update Role"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [roleFilter, setRoleFilter] = useState<UserRole | "all">("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const updateRoleMutation = useUpdateUserRole();

  const { data, isLoading, isError, refetch } = useUsers({
    role: roleFilter === "all" ? undefined : roleFilter,
    page: currentPage,
    page_size: PAGE_SIZE,
  });

  const users = data?.items ?? [];
  const totalUsers = data?.total ?? 0;
  const totalPages = Math.ceil(totalUsers / PAGE_SIZE);

  // Access check - Manager only
  if (currentUser && currentUser.role !== UserRole.MANAGER) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <UsersIcon className="h-12 w-12 text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold text-foreground">Access Denied</h2>
        <p className="text-muted-foreground mt-2">
          User management is only available to managers.
        </p>
        <Link href="/dashboard">
          <Button className="mt-4">Go to Dashboard</Button>
        </Link>
      </div>
    );
  }

  const handleRoleChange = async (newRole: UserRole) => {
    if (!selectedUser) return;

    try {
      await updateRoleMutation.mutateAsync({
        userId: selectedUser.id,
        data: { role: newRole },
      });
      toast.success(
        `Updated ${selectedUser.name}'s role to ${getRoleLabel(newRole)}`,
      );
      setIsDialogOpen(false);
      setSelectedUser(null);
    } catch (error) {
      toast.error("Failed to update user role");
    }
  };

  const openRoleDialog = (user: User) => {
    setSelectedUser(user);
    setIsDialogOpen(true);
  };

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
          <h1 className="text-2xl font-semibold text-foreground">Users</h1>
          <p className="text-muted-foreground">
            {totalUsers} {totalUsers === 1 ? "user" : "users"} in the system
          </p>
        </div>
        <Select
          value={roleFilter}
          onValueChange={(value) => {
            setRoleFilter(value as UserRole | "all");
            setCurrentPage(1);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {roleFilterOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </motion.div>

      {/* Users List */}
      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 10 }).map((_, i) => (
            <UserCardSkeleton key={i} />
          ))}
        </div>
      ) : isError ? (
        <ErrorState
          title="Failed to load users"
          message="There was a problem loading the users list. Please try again."
          onRetry={refetch}
        />
      ) : users.length === 0 ? (
        <motion.div variants={fadeInUp}>
          <Card>
            <CardContent className="py-12 text-center">
              <UsersIcon className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-semibold text-foreground">
                No users found
              </h3>
              <p className="mt-2 text-muted-foreground">
                {roleFilter !== "all"
                  ? `No ${getRoleLabel(roleFilter).toLowerCase()}s found.`
                  : "No users in the system yet."}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      ) : (
        <motion.div
          className="space-y-3"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {users.map((user) => (
            <motion.div key={user.id} variants={staggerItem}>
              <Card className="p-4 hover:border-primary/30 transition">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
                      <UserIcon className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-foreground truncate">
                          {user.name}
                        </h3>
                        <Badge variant={getRoleVariant(user.role)}>
                          {getRoleLabel(user.role)}
                        </Badge>
                        {!user.is_active && (
                          <Badge variant="danger">Inactive</Badge>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-sm text-muted-foreground">
                        {user.email && (
                          <span className="flex items-center gap-1">
                            <Mail className="h-3.5 w-3.5" />
                            {user.email}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Phone className="h-3.5 w-3.5" />
                          {user.phone_number}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5" />
                          Joined {formatDate(user.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 sm:shrink-0">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openRoleDialog(user)}
                      disabled={user.id === currentUser?.id}
                      title={
                        user.id === currentUser?.id
                          ? "You cannot change your own role"
                          : "Change role"
                      }
                    >
                      <Shield className="mr-2 h-4 w-4" />
                      Change Role
                    </Button>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* Pagination */}
      {totalPages > 1 && !isLoading && (
        <motion.div
          className="flex items-center justify-between"
          variants={fadeInUp}
        >
          <p className="text-sm text-muted-foreground">
            Showing {(currentPage - 1) * PAGE_SIZE + 1} to{" "}
            {Math.min(currentPage * PAGE_SIZE, totalUsers)} of {totalUsers}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="px-3 text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              aria-label="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </motion.div>
      )}

      {/* Role Change Dialog */}
      <RoleChangeDialog
        user={selectedUser}
        open={isDialogOpen}
        onClose={() => {
          setIsDialogOpen(false);
          setSelectedUser(null);
        }}
        onConfirm={handleRoleChange}
        isLoading={updateRoleMutation.isPending}
      />
    </motion.div>
  );
}
