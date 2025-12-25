"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/lib/auth/context";
import { useCategories } from "@/lib/queries/categories";
import { useCreateTicket, useUploadTicketPhoto } from "@/lib/queries/tickets";
import { useSavedAddresses } from "@/lib/queries/addresses";
import { PhotoType, LocationCreate, SavedAddress, NearbyTicket, UserRole } from "@/lib/api/types";
import { getNearbyTickets } from "@/lib/api/client";
import {
  fadeInUp,
  staggerContainer,
  staggerItem,
  scaleIn,
} from "@/lib/animations";
import {
  ArrowLeft,
  X,
  MapPin,
  Loader2,
  Camera,
  AlertCircle,
  Upload,
  Home,
  Navigation,
  AlertTriangle,
  ExternalLink,
} from "lucide-react";

// Dynamically import the map component to avoid SSR issues with Leaflet
const LocationPicker = dynamic(
  () => import("@/components/map/location-picker").then((mod) => mod.LocationPicker),
  {
    ssr: false,
    loading: () => (
      <div className="h-[300px] rounded-xl bg-muted flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    ),
  }
);

interface PhotoPreview {
  file: File;
  preview: string;
}

// İstanbul sınırları (yaklaşık) - Silivri dahil, Kocaeli hariç
const ISTANBUL_BOUNDS = {
  minLat: 40.80,
  maxLat: 41.40,
  minLng: 28.00,
  maxLng: 29.45, // Gebze/Şile sınırı - Kocaeli'yi hariç tutar
};

function isWithinIstanbulBounds(latitude: number, longitude: number): boolean {
  return (
    latitude >= ISTANBUL_BOUNDS.minLat &&
    latitude <= ISTANBUL_BOUNDS.maxLat &&
    longitude >= ISTANBUL_BOUNDS.minLng &&
    longitude <= ISTANBUL_BOUNDS.maxLng
  );
}

export default function CreateTicketPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { user } = useAuth();

  // TanStack Query hooks
  const { data: categoriesData, isLoading: isLoadingCategories } = useCategories();
  const categories = categoriesData?.items ?? [];
  const { data: addressesData } = useSavedAddresses();
  const savedAddresses = addressesData?.items ?? [];

  const createTicketMutation = useCreateTicket();
  const uploadPhotoMutation = useUploadTicketPhoto();

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [location, setLocation] = useState<{
    latitude: number;
    longitude: number;
    address?: string;
    district_id?: string;
  } | null>(null);
  const [photos, setPhotos] = useState<PhotoPreview[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<string>("");
  const [locationMode, setLocationMode] = useState<"map" | "saved">("map");

  // Nearby tickets state
  const [nearbyTickets, setNearbyTickets] = useState<NearbyTicket[]>([]);
  const [isLoadingNearby, setIsLoadingNearby] = useState(false);

  // Validation error state
  const [validationError, setValidationError] = useState<string | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);

  // Handle saved address selection
  const handleSavedAddressSelect = (addressId: string) => {
    setSelectedAddressId(addressId);
    setLocationError(null);
    if (addressId === "map") {
      setLocationMode("map");
      setLocation(null);
    } else {
      setLocationMode("saved");
      const address = savedAddresses.find((a) => a.id === addressId);
      if (address) {
        // Citizen için İstanbul sınır kontrolü
        const isCitizen = user?.role === UserRole.CITIZEN;
        if (isCitizen && !isWithinIstanbulBounds(address.latitude, address.longitude)) {
          setLocationError("You can only create tickets within Istanbul city limits.");
          setLocation(null);
          return;
        }
        setLocation({
          latitude: address.latitude,
          longitude: address.longitude,
          address: address.address,
          // Saved addresses don't have district_id yet
        });
      }
    }
  };

  // Handle location selection from map
  const handleLocationSelect = (selectedLocation: {
    latitude: number;
    longitude: number;
    address?: string;
    district_id?: string;
  }) => {
    setLocationError(null);
    // Citizen için İstanbul sınır kontrolü
    const isCitizen = user?.role === UserRole.CITIZEN;
    if (isCitizen && !isWithinIstanbulBounds(selectedLocation.latitude, selectedLocation.longitude)) {
      setLocationError("You can only create tickets within Istanbul city limits.");
      setLocation(null);
      return;
    }
    setLocation(selectedLocation);
  };

  // Clean up photo previews on unmount
  useEffect(() => {
    return () => {
      photos.forEach((photo) => URL.revokeObjectURL(photo.preview));
    };
  }, [photos]);

  // Fetch nearby tickets when location or category changes
  useEffect(() => {
    const fetchNearbyTickets = async () => {
      if (!location || !location.latitude || !location.longitude) {
        setNearbyTickets([]);
        return;
      }

      setIsLoadingNearby(true);
      try {
        const tickets = await getNearbyTickets({
          latitude: location.latitude,
          longitude: location.longitude,
          radius_meters: 500,
          category_id: categoryId || undefined,
        });
        setNearbyTickets(tickets);
      } catch (error) {
        console.error("Failed to fetch nearby tickets:", error);
        setNearbyTickets([]);
      } finally {
        setIsLoadingNearby(false);
      }
    };

    // Debounce the search to avoid too many API calls
    const timeoutId = setTimeout(() => {
      fetchNearbyTickets();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [location, categoryId]);

  const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newPhotos: PhotoPreview[] = [];
    for (let i = 0; i < files.length && photos.length + newPhotos.length < 5; i++) {
      const file = files[i];
      if (file.type.startsWith("image/")) {
        newPhotos.push({
          file,
          preview: URL.createObjectURL(file),
        });
      }
    }

    setPhotos((prev) => [...prev, ...newPhotos]);
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removePhoto = (index: number) => {
    setPhotos((prev) => {
      URL.revokeObjectURL(prev[index].preview);
      return prev.filter((_, i) => i !== index);
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setLocationError(null);

    // Validation
    if (!title.trim()) {
      setValidationError("Please enter a title");
      return;
    }
    if (!description.trim()) {
      setValidationError("Please enter a description");
      return;
    }
    if (!categoryId) {
      setValidationError("Please select a category");
      return;
    }
    if (!location) {
      setValidationError("Please select a location on the map");
      return;
    }

    // Citizen için İstanbul sınır kontrolü
    const isCitizen = user?.role === UserRole.CITIZEN;
    if (isCitizen && !isWithinIstanbulBounds(location.latitude, location.longitude)) {
      setLocationError("You can only create tickets within Istanbul city limits.");
      setValidationError("Location must be within Istanbul city limits.");
      return;
    }

    try {
      // Create the ticket
      const ticketLocation: LocationCreate = {
        latitude: location.latitude,
        longitude: location.longitude,
        address: location.address,
        district_id: location.district_id,
        city: "Istanbul", // Default city, could be extracted from address
      };

      const ticket = await createTicketMutation.mutateAsync({
        title: title.trim(),
        description: description.trim(),
        category_id: categoryId,
        location: ticketLocation,
      });

      // Upload photos if any
      if (photos.length > 0) {
        await Promise.all(
          photos.map((photo) =>
            uploadPhotoMutation.mutateAsync({
              ticketId: ticket.id,
              file: photo.file,
              photoType: PhotoType.REPORT,
            })
          )
        );
      }

      toast.success("Issue reported successfully!");
      // Navigate to the ticket detail page
      router.push(`/tickets/${ticket.id}`);
    } catch (err) {
      console.error("Failed to create ticket:", err);
      toast.error(
        err instanceof Error ? err.message : "Failed to create ticket. Please try again."
      );
    }
  };

  const isSubmitting = createTicketMutation.isPending || uploadPhotoMutation.isPending;

  return (
    <motion.div 
      className="mx-auto max-w-2xl space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {/* Header */}
      <motion.div className="flex items-center gap-4" variants={fadeInUp}>
        <Link href="/tickets">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Report an Issue</h1>
          <p className="text-muted-foreground">Help improve your neighborhood</p>
        </div>
      </motion.div>

      {/* Form */}
      <motion.form onSubmit={handleSubmit} variants={fadeInUp}>
        <Card className="p-6 space-y-6">
          {/* Error message */}
          <AnimatePresence>
            {validationError && (
              <motion.div 
                className="flex items-center gap-2 rounded-lg bg-destructive/10 p-4 text-destructive"
                role="alert"
                aria-live="polite"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <AlertCircle className="h-5 w-5 shrink-0" aria-hidden="true" />
                <p className="text-sm">{validationError}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">
              Title <span className="text-destructive">*</span>
            </Label>
            <Input
              id="title"
              placeholder="Brief description of the issue"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={100}
              aria-describedby="title-hint"
            />
            <p id="title-hint" className="text-xs text-muted-foreground">{title.length}/100 characters</p>
          </div>

          {/* Category */}
          <div className="space-y-2">
            <Label htmlFor="category">
              Category <span className="text-destructive">*</span>
            </Label>
            {isLoadingCategories ? (
              <div className="flex items-center gap-2 py-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Loading categories...</span>
              </div>
            ) : (
              <Select value={categoryId} onValueChange={setCategoryId}>
                <SelectTrigger id="category">
                  <SelectValue placeholder="Select a category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((category) => (
                    <SelectItem key={category.id} value={category.id}>
                      {category.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">
              Description <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="description"
              placeholder="Provide details about the issue. Include any relevant information that could help resolve it."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              maxLength={1000}
              aria-describedby="description-hint"
            />
            <p id="description-hint" className="text-xs text-muted-foreground">{description.length}/1000 characters</p>
          </div>

          {/* Location */}
          <div className="space-y-4">
            <Label id="location-label">
              Location <span className="text-destructive">*</span>
            </Label>
            
            {/* Saved addresses quick select */}
            {savedAddresses.length > 0 && (
              <div className="space-y-2 relative z-[1100]">
                <Label className="text-sm text-muted-foreground flex items-center gap-2">
                  <Home className="h-4 w-4" />
                  Use a saved address
                </Label>
                <Select value={selectedAddressId} onValueChange={handleSavedAddressSelect}>
                  <SelectTrigger className="relative z-10 bg-background">
                    <SelectValue placeholder="Select a saved address or pick on map" />
                  </SelectTrigger>
                  <SelectContent className="z-[1200] shadow-xl">
                    <SelectItem value="map">
                      <div className="flex items-center gap-2">
                        <Navigation className="h-4 w-4" />
                        Pick location on map
                      </div>
                    </SelectItem>
                    {savedAddresses.map((address) => (
                      <SelectItem key={address.id} value={address.id}>
                        <div className="flex items-center gap-2">
                          <Home className="h-4 w-4" />
                          <span className="font-medium">{address.name}</span>
                          <span className="text-muted-foreground text-xs truncate max-w-[200px]">
                            - {address.address}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {locationError && locationMode === "saved" && (
                  <div className="mt-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <span>{locationError}</span>
                  </div>
                )}
              </div>
            )}

            {/* Map picker - show when no saved addresses or "map" is selected */}
            {(savedAddresses.length === 0 || locationMode === "map") && (
              <div className="space-y-2">
                {savedAddresses.length > 0 && (
                  <Label className="text-sm text-muted-foreground flex items-center gap-2">
                    <MapPin className="h-4 w-4" />
                    Or pick a location on the map
                  </Label>
                )}
                <LocationPicker onLocationSelect={handleLocationSelect} />
                {locationError && locationMode === "map" && (
                  <div className="mt-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <span>{locationError}</span>
                  </div>
                )}
              </div>
            )}

            {/* Selected location display */}
            {location?.address && (
              <div className="flex items-start gap-2 rounded-lg bg-primary/5 p-3 text-sm text-primary">
                <MapPin className="h-4 w-4 shrink-0 mt-0.5" aria-hidden="true" />
                <span className="line-clamp-2">{location.address}</span>
              </div>
            )}
          </div>

          {/* Nearby Similar Tickets */}
          {location && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
                <Label className="text-base font-semibold">
                  Similar Issues Nearby
                </Label>
              </div>
              
              {isLoadingNearby ? (
                <div className="flex items-center gap-2 py-4 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">Checking for similar issues...</span>
                </div>
              ) : nearbyTickets.length > 0 ? (
                <motion.div
                  className="space-y-2"
                  variants={staggerContainer}
                  initial="hidden"
                  animate="visible"
                >
                  <p className="text-sm text-muted-foreground">
                    We found {nearbyTickets.length} similar issue{nearbyTickets.length !== 1 ? "s" : ""} nearby. 
                    You might want to check if your issue is already reported.
                  </p>
                  <div className="space-y-2 max-h-[300px] overflow-y-auto">
                    {nearbyTickets.map((ticket) => (
                      <motion.div
                        key={ticket.id}
                        variants={fadeInUp}
                        className="group relative rounded-lg border border-border bg-card p-4 transition hover:border-primary/50 hover:shadow-md"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 space-y-1">
                            <h4 className="font-medium text-sm leading-tight">
                              {ticket.title}
                            </h4>
                            <div className="flex items-center gap-3 text-xs text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <MapPin className="h-3 w-3" />
                                {Math.round(ticket.distance_meters)}m away
                              </span>
                              <span className="flex items-center gap-1">
                                <span className="capitalize">{ticket.status.replace("_", " ")}</span>
                              </span>
                              {ticket.follower_count > 0 && (
                                <span>{ticket.follower_count} follower{ticket.follower_count !== 1 ? "s" : ""}</span>
                              )}
                            </div>
                            <div className="text-xs">
                              <span className="text-muted-foreground">Category: </span>
                              <span className="font-medium">{ticket.category_name}</span>
                            </div>
                          </div>
                          <Link href={`/tickets/${ticket.id}`}>
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0 opacity-0 transition group-hover:opacity-100"
                            >
                              <ExternalLink className="h-4 w-4" />
                              <span className="sr-only">View ticket</span>
                            </Button>
                          </Link>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              ) : location ? (
                <div className="rounded-lg border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
                  No similar issues found nearby. You can proceed to create a new ticket.
                </div>
              ) : null}
            </div>
          )}

          {/* Photos */}
          <div className="space-y-2">
            <Label>
              Photos <span className="text-muted-foreground font-normal">(optional, max 5)</span>
            </Label>
            
            {/* Photo grid */}
            <motion.div 
              className="grid grid-cols-2 gap-3 sm:grid-cols-3"
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
            >
              <AnimatePresence mode="popLayout">
                {photos.map((photo, index) => (
                  <motion.div
                    key={photo.preview}
                    className="relative aspect-square overflow-hidden rounded-xl border border-border"
                    variants={scaleIn}
                    initial="hidden"
                    animate="visible"
                    exit={{ opacity: 0, scale: 0.8 }}
                    layout
                  >
                    <img
                      src={photo.preview}
                      alt={`Photo preview: ${photo.file.name}`}
                      className="h-full w-full object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => removePhoto(index)}
                      className="absolute right-2 top-2 rounded-full bg-black/50 p-1 text-white transition hover:bg-black/70"
                      aria-label={`Remove photo ${index + 1}`}
                    >
                      <X className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {/* Add photo button */}
              {photos.length < 5 && (
                  <motion.button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex aspect-square flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border text-muted-foreground transition hover:border-primary hover:bg-primary/5 hover:text-primary"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  layout
                  aria-label="Add a photo"
                >
                  <Camera className="h-6 w-6" aria-hidden="true" />
                  <span className="text-xs font-medium">Add Photo</span>
                </motion.button>
              )}
            </motion.div>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handlePhotoSelect}
              className="hidden"
              aria-label="Upload photos"
            />
            <p className="text-xs text-muted-foreground">
              Add photos to help identify the issue. Supports JPG, PNG formats.
            </p>
          </div>

          {/* Submit button */}
          <div className="flex justify-end gap-3 border-t border-border pt-6">
            <Link href="/tickets">
              <Button type="button" variant="outline" disabled={isSubmitting}>
                Cancel
              </Button>
            </Link>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Submit Report
                </>
              )}
            </Button>
          </div>
        </Card>
      </motion.form>
    </motion.div>
  );
}
