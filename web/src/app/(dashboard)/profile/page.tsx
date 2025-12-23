"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth/context";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useUpdateUser } from "@/lib/queries/users";
import {
  useSavedAddresses,
  useCreateSavedAddress,
  useDeleteSavedAddress,
} from "@/lib/queries/addresses";
import { SavedAddress, UserRole } from "@/lib/api/types";
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
  Loader2,
  Edit2,
  Check,
  X,
  MapPin,
  Plus,
  Trash2,
  Home,
} from "lucide-react";

// Dynamically import the map component to avoid SSR issues with Leaflet
const LocationPicker = dynamic(
  () =>
    import("@/components/map/location-picker").then((mod) => mod.LocationPicker),
  {
    ssr: false,
    loading: () => (
      <div className="h-[200px] rounded-xl bg-muted flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    ),
  }
);

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const updateUserMutation = useUpdateUser();

  // Saved addresses queries (disabled for managers)
  const { data: addressesData, isLoading: isLoadingAddresses } =
    useSavedAddresses({ enabled: user?.role !== UserRole.MANAGER });
  const createAddressMutation = useCreateSavedAddress();
  const deleteAddressMutation = useDeleteSavedAddress();

  // Edit mode state
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(user?.name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [phoneNumber, setPhoneNumber] = useState(user?.phone_number || "");

  // Add address state
  const [isAddingAddress, setIsAddingAddress] = useState(false);
  const [newAddressName, setNewAddressName] = useState("");
  const [newAddressLocation, setNewAddressLocation] = useState<{
    latitude: number;
    longitude: number;
    address?: string;
  } | null>(null);

  const handleStartEdit = () => {
    setName(user?.name || "");
    setEmail(user?.email || "");
    setPhoneNumber(user?.phone_number || "");
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
          phone_number: phoneNumber.trim() || undefined,
        },
      });
      await refreshUser();
      setIsEditing(false);
      toast.success("Profile updated successfully!");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to update profile"
      );
    }
  };

  const handleAddAddress = async () => {
    if (!newAddressName.trim()) {
      toast.error("Please enter a name for this address");
      return;
    }
    if (!newAddressLocation) {
      toast.error("Please select a location on the map");
      return;
    }

    try {
      await createAddressMutation.mutateAsync({
        name: newAddressName.trim(),
        address: newAddressLocation.address || "Selected location",
        latitude: newAddressLocation.latitude,
        longitude: newAddressLocation.longitude,
        city: "Istanbul",
      });
      toast.success("Address saved successfully!");
      setIsAddingAddress(false);
      setNewAddressName("");
      setNewAddressLocation(null);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to save address"
      );
    }
  };

  const handleDeleteAddress = async (address: SavedAddress) => {
    if (!confirm(`Are you sure you want to delete "${address.name}"?`)) return;

    try {
      await deleteAddressMutation.mutateAsync(address.id);
      toast.success("Address deleted successfully!");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to delete address"
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
            {Array.from({ length: 4 }).map((_, i) => (
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

  const savedAddresses = addressesData?.items ?? [];

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
                {isEditing ? (
                  <Input
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="+905XXXXXXXXX"
                    pattern="^\+90[0-9]{10}$"
                  />
                ) : (
                  <p className="text-foreground">{user.phone_number}</p>
                )}
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
                    <X className="mr-2 h-4 w-4" />
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

      {/* Saved Addresses Card - Hidden for Manager */}
      {user.role !== UserRole.MANAGER && (
        <motion.div variants={staggerItem}>
          <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
              <Home className="h-5 w-5" />
              Saved Addresses
            </h3>
            {!isAddingAddress && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsAddingAddress(true)}
                disabled={savedAddresses.length >= 10}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Address
              </Button>
            )}
          </div>

          {/* Add new address form */}
          <AnimatePresence>
            {isAddingAddress && (
              <motion.div
                className="mb-6 space-y-4 rounded-xl border border-border p-4 bg-muted/30"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
              >
                <div className="space-y-2">
                  <Label htmlFor="addressName">Address Name</Label>
                  <Input
                    id="addressName"
                    value={newAddressName}
                    onChange={(e) => setNewAddressName(e.target.value)}
                    placeholder="e.g., Home, Work, School"
                    maxLength={100}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Select Location</Label>
                  <LocationPicker onLocationSelect={setNewAddressLocation} />
                  {newAddressLocation?.address && (
                    <div className="mt-2 flex items-start gap-2 rounded-lg bg-primary/5 p-3 text-sm text-primary">
                      <MapPin className="h-4 w-4 shrink-0 mt-0.5" />
                      <span className="line-clamp-2">
                        {newAddressLocation.address}
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setIsAddingAddress(false);
                      setNewAddressName("");
                      setNewAddressLocation(null);
                    }}
                    disabled={createAddressMutation.isPending}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleAddAddress}
                    disabled={createAddressMutation.isPending}
                  >
                    {createAddressMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Check className="mr-2 h-4 w-4" />
                        Save Address
                      </>
                    )}
                  </Button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Address list */}
          {isLoadingAddresses ? (
            <div className="space-y-3">
              {Array.from({ length: 2 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full rounded-xl" />
              ))}
            </div>
          ) : savedAddresses.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <MapPin className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No saved addresses yet</p>
              <p className="text-sm">
                Add your frequently used locations for faster ticket creation
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {savedAddresses.map((address) => (
                <motion.div
                  key={address.id}
                  className="flex items-start justify-between rounded-xl border border-border p-4 hover:bg-muted/30 transition-colors"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-foreground flex items-center gap-2">
                      <Home className="h-4 w-4 text-primary" />
                      {address.name}
                    </h4>
                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                      {address.address}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-destructive shrink-0"
                    onClick={() => handleDeleteAddress(address)}
                    disabled={deleteAddressMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </motion.div>
              ))}
            </div>
          )}

          {savedAddresses.length >= 10 && (
            <p className="text-xs text-muted-foreground mt-4 text-center">
              Maximum 10 addresses allowed
            </p>
          )}
        </Card>
      </motion.div>
      )}

      {/* Account Status Card - Hidden for Manager */}
      {user.role !== UserRole.MANAGER && (
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
      )}
    </motion.div>
  );
}
