import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { TicketStatus, EscalationStatus, UserRole } from "@/lib/api/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ============================================================================
// DATE FORMATTING
// ============================================================================

/**
 * Format a date string to a human-readable format
 */
export function formatDate(
  date: string | Date,
  options: Intl.DateTimeFormatOptions = {
    month: "short",
    day: "numeric",
    year: "numeric",
  },
): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString("en-US", options);
}

/**
 * Format a date string to include time
 */
export function formatDateTime(date: string | Date): string {
  return formatDate(date, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/**
 * Format a date to relative time (e.g., "2 hours ago", "3 days ago")
 */
export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  const diffWeek = Math.floor(diffDay / 7);
  const diffMonth = Math.floor(diffDay / 30);

  if (diffSec < 60) return "just now";
  if (diffMin < 60) return `${diffMin} minute${diffMin === 1 ? "" : "s"} ago`;
  if (diffHour < 24) return `${diffHour} hour${diffHour === 1 ? "" : "s"} ago`;
  if (diffDay < 7) return `${diffDay} day${diffDay === 1 ? "" : "s"} ago`;
  if (diffWeek < 4) return `${diffWeek} week${diffWeek === 1 ? "" : "s"} ago`;
  if (diffMonth < 12)
    return `${diffMonth} month${diffMonth === 1 ? "" : "s"} ago`;
  return formatDate(d);
}

// ============================================================================
// STATUS VARIANTS (for Badge component)
// ============================================================================

type BadgeVariant =
  | "default"
  | "secondary"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "outline";

/**
 * Get badge variant for ticket status
 */
export function getStatusVariant(status: TicketStatus): BadgeVariant {
  switch (status) {
    case TicketStatus.NEW:
      return "info";
    case TicketStatus.IN_PROGRESS:
      return "warning";
    case TicketStatus.RESOLVED:
      return "success";
    case TicketStatus.CLOSED:
      return "secondary";
    case TicketStatus.ESCALATED:
      return "danger";
    default:
      return "default";
  }
}

/**
 * Get human-readable label for ticket status
 */
export function getStatusLabel(status: TicketStatus): string {
  switch (status) {
    case TicketStatus.NEW:
      return "New";
    case TicketStatus.IN_PROGRESS:
      return "In Progress";
    case TicketStatus.RESOLVED:
      return "Resolved";
    case TicketStatus.CLOSED:
      return "Closed";
    case TicketStatus.ESCALATED:
      return "Escalated";
    default:
      return status;
  }
}

/**
 * Get badge variant for escalation status
 */
export function getEscalationStatusVariant(
  status: EscalationStatus,
): BadgeVariant {
  switch (status) {
    case EscalationStatus.PENDING:
      return "warning";
    case EscalationStatus.APPROVED:
      return "success";
    case EscalationStatus.REJECTED:
      return "danger";
    default:
      return "default";
  }
}

/**
 * Get human-readable label for escalation status
 */
export function getEscalationStatusLabel(status: EscalationStatus): string {
  switch (status) {
    case EscalationStatus.PENDING:
      return "Pending Review";
    case EscalationStatus.APPROVED:
      return "Approved";
    case EscalationStatus.REJECTED:
      return "Rejected";
    default:
      return status;
  }
}

/**
 * Get badge variant for user role
 */
export function getRoleVariant(role: UserRole): BadgeVariant {
  switch (role) {
    case UserRole.MANAGER:
      return "danger";
    case UserRole.SUPPORT:
      return "info";
    case UserRole.CITIZEN:
      return "secondary";
    default:
      return "default";
  }
}

/**
 * Get human-readable label for user role
 */
export function getRoleLabel(role: UserRole): string {
  switch (role) {
    case UserRole.MANAGER:
      return "Manager";
    case UserRole.SUPPORT:
      return "Support Staff";
    case UserRole.CITIZEN:
      return "Citizen";
    default:
      return role;
  }
}

// ============================================================================
// TEXT UTILITIES
// ============================================================================

/**
 * Truncate text to a maximum length with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}

/**
 * Get initials from a name (e.g., "John Doe" -> "JD")
 */
export function getInitials(name: string | null | undefined): string {
  if (!name) return "?";
  return name
    .split(" ")
    .map((part) => part.charAt(0).toUpperCase())
    .slice(0, 2)
    .join("");
}

/**
 * Format a phone number for display
 */
export function formatPhoneNumber(phone: string): string {
  // Remove all non-digits
  const digits = phone.replace(/\D/g, "");

  // Format as (XXX) XXX-XXXX for US numbers
  if (digits.length === 10) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  }
  if (digits.length === 11 && digits.startsWith("1")) {
    return `+1 (${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7)}`;
  }

  // Return original if format doesn't match
  return phone;
}

// ============================================================================
// NUMBER UTILITIES
// ============================================================================

/**
 * Format a number with commas (e.g., 1000 -> "1,000")
 */
export function formatNumber(num: number): string {
  return num.toLocaleString("en-US");
}

/**
 * Format a percentage value that is already in percentage format (e.g., 85.6 -> "85.6%")
 * Note: Backend returns values in percentage format (0-100 range), not decimal (0-1 range)
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format hours to a readable duration (e.g., 25.5 -> "1d 1h")
 */
export function formatDuration(hours: number | null): string {
  if (hours === null) return "N/A";

  if (hours < 1) {
    const minutes = Math.round(hours * 60);
    return `${minutes}m`;
  }

  if (hours < 24) {
    return `${Math.round(hours)}h`;
  }

  const days = Math.floor(hours / 24);
  const remainingHours = Math.round(hours % 24);

  if (remainingHours === 0) {
    return `${days}d`;
  }

  return `${days}d ${remainingHours}h`;
}

/**
 * Format a rating (e.g., 4.5 -> "4.5/5")
 */
export function formatRating(rating: number | null): string {
  if (rating === null) return "N/A";
  return `${rating.toFixed(1)}/5`;
}

// ============================================================================
// PLATFORM DETECTION
// ============================================================================

/**
 * Check if the current platform is macOS
 * Returns false during SSR (server-side rendering)
 */
export function isMacOS(): boolean {
  if (typeof window === "undefined") return false;
  return navigator.platform.toLowerCase().includes("mac");
}

/**
 * Get the platform-appropriate modifier key symbol
 * Returns "⌘" for macOS, "Ctrl" for Windows/Linux
 */
export function getModifierKey(): string {
  return isMacOS() ? "⌘" : "Ctrl";
}

// ============================================================================
// COLOR UTILITIES
// ============================================================================

/**
 * Generate a consistent color for a category based on its name
 * Uses predefined colors for common categories, generates hash-based colors for others
 */
export function getCategoryColor(categoryName: string): string {
  // Predefined colors for common categories
  const predefinedColors: Record<string, string> = {
    Infrastructure: "#0088FE",
    Traffic: "#00C49F",
    Lighting: "#FFBB28",
    "Waste Management": "#FF8042",
    Parks: "#8884d8",
    Football: "#FF6B9D",
    Other: "#82ca9d",
  };

  // Return predefined color if exists
  if (predefinedColors[categoryName]) {
    return predefinedColors[categoryName];
  }

  // Generate color from string hash for new categories
  let hash = 0;
  for (let i = 0; i < categoryName.length; i++) {
    hash = categoryName.charCodeAt(i) + ((hash << 5) - hash);
  }

  // Convert hash to RGB with good saturation and brightness
  const hue = Math.abs(hash) % 360;
  const saturation = 65 + (Math.abs(hash >> 8) % 20); // 65-85%
  const lightness = 50 + (Math.abs(hash >> 16) % 15); // 50-65%

  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}
