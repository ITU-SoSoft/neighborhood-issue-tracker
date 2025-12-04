"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth/context";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useUpdateUser } from "@/lib/queries/users";
import { UserRole } from "@/lib/api/types";
import {
  formatDate,
  getRoleVariant,
  getRoleLabel,
  getInitials,
} from "@/lib/utils";
import {
  fadeInUp,
  staggerContainer,
  staggerItem,
  scaleIn,
} from "@/lib/animations";
import {
  User,
  Phone,
  Mail,
  Calendar,
  Shield,
  Loader2,
  Edit2,
  Check,
  X,
} from "lucide-react";

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const updateUserMutation = useUpdateUser();

  // Edit mode state
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(user?.name || "");
  const [email, setEmail] = useState(user?.email || "");

  const handleStartEdit = () => {
    setName(user?.name || "");
    setEmail(user?.email || "");
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  const handleSave = async () => {
    if (!user) return;

    try {
      await updateUserMutation.mutateAsync({
        userId: user.id,
        data: {
          name: name.trim() || undefined,
          email: email.trim() || undefined,
        },
      });
      await refreshUser();
      setIsEditing(false);
      toast.success("Profile updated successfully!");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to update profile",
      );
    }
  };

  if (!user) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        {/* Header skeleton */}
        <div className="space-y-2">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-4 w-48" />
        </div>

        {/* Profile card skeleton */}
        <Card className="overflow-hidden">
          <div className="bg-primary/10 p-6">
            <div className="flex items-center gap-4">
              <Skeleton className="h-20 w-20 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-5 w-20 rounded-full" />
              </div>
            </div>
          </div>
          <div className="p-6 space-y-6">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-5 w-48" />
              </div>
            ))}
          </div>
        </Card>
      </div>
    );
  }

  return (
    <motion.div
      className="mx-auto max-w-2xl space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {/* Header */}
      <motion.div variants={fadeInUp}>
        <h1 className="text-2xl font-semibold text-foreground">Profile</h1>
        <p className="text-muted-foreground">Manage your account information</p>
      </motion.div>

      {/* Profile Card */}
      <motion.div variants={staggerItem}>
        <Card className="overflow-hidden">
          {/* Profile header */}
          <div className="bg-gradient-to-r from-primary to-primary/80 p-6">
            <div className="flex items-center gap-4">
              <motion.div
                className="flex h-20 w-20 items-center justify-center rounded-full bg-white/20 text-white"
                variants={scaleIn}
              >
                <span className="text-2xl font-semibold">
                  {getInitials(user.name)}
                </span>
              </motion.div>
              <div className="text-white">
                <h2 className="text-xl font-semibold">{user.name}</h2>
                <Badge variant={getRoleVariant(user.role)} className="mt-1">
                  {getRoleLabel(user.role)}
                </Badge>
              </div>
            </div>
          </div>

          {/* Profile details */}
          <div className="p-6">
            <motion.div
              className="space-y-6"
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
            >
              {/* Name */}
              <motion.div className="space-y-2" variants={staggerItem}>
                <Label className="flex items-center gap-2 text-muted-foreground">
                  <User className="h-4 w-4" />
                  Full Name
                </Label>
                {isEditing ? (
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter your name"
                  />
                ) : (
                  <p className="text-foreground">{user.name}</p>
                )}
              </motion.div>

              {/* Phone */}
              <motion.div className="space-y-2" variants={staggerItem}>
                <Label className="flex items-center gap-2 text-muted-foreground">
                  <Phone className="h-4 w-4" />
                  Phone Number
                </Label>
                <p className="text-foreground">{user.phone_number}</p>
              </motion.div>

              {/* Email */}
              <motion.div className="space-y-2" variants={staggerItem}>
                <Label className="flex items-center gap-2 text-muted-foreground">
                  <Mail className="h-4 w-4" />
                  Email Address
                </Label>
                {isEditing ? (
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                  />
                ) : (
                  <p className="text-foreground">
                    {user.email || "Not provided"}
                  </p>
                )}
              </motion.div>

              {/* Role */}
              <motion.div className="space-y-2" variants={staggerItem}>
                <Label className="flex items-center gap-2 text-muted-foreground">
                  <Shield className="h-4 w-4" />
                  Role
                </Label>
                <Badge variant={getRoleVariant(user.role)}>
                  {getRoleLabel(user.role)}
                </Badge>
              </motion.div>

              {/* Member since */}
              <motion.div className="space-y-2" variants={staggerItem}>
                <Label className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  Member Since
                </Label>
                <p className="text-foreground">
                  {formatDate(user.created_at, {
                    weekday: "long",
                    month: "long",
                    day: "numeric",
                    year: "numeric",
                  })}
                </p>
              </motion.div>
            </motion.div>

            {/* Actions */}
            <div className="mt-6 flex justify-end gap-3 border-t border-border pt-6">
              {isEditing ? (
                <>
                  <Button
                    variant="outline"
                    onClick={handleCancelEdit}
                    disabled={updateUserMutation.isPending}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSave}
                    disabled={updateUserMutation.isPending}
                  >
                    {updateUserMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Check className="mr-2 h-4 w-4" />
                        Save Changes
                      </>
                    )}
                  </Button>
                </>
              ) : (
                <Button variant="outline" onClick={handleStartEdit}>
                  <Edit2 className="mr-2 h-4 w-4" />
                  Edit Profile
                </Button>
              )}
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Account Status Card */}
      <motion.div variants={staggerItem}>
        <Card className="p-6">
          <h3 className="mb-4 text-lg font-semibold text-foreground">
            Account Status
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Verification Status</span>
              <Badge variant={user.is_verified ? "success" : "warning"}>
                {user.is_verified ? "Verified" : "Pending Verification"}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Account Status</span>
              <Badge variant={user.is_active ? "success" : "danger"}>
                {user.is_active ? "Active" : "Inactive"}
              </Badge>
            </div>
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
