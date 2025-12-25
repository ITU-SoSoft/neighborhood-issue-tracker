// API Types based on backend schemas

// Enums
export enum UserRole {
  CITIZEN = "CITIZEN",
  SUPPORT = "SUPPORT",
  MANAGER = "MANAGER",
}

export enum TicketStatus {
  NEW = "NEW",
  IN_PROGRESS = "IN_PROGRESS",
  RESOLVED = "RESOLVED",
  CLOSED = "CLOSED",
  ESCALATED = "ESCALATED",
}

export enum PhotoType {
  REPORT = "REPORT",
  PROOF = "PROOF",
}

export enum EscalationStatus {
  PENDING = "PENDING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
}

// User types
export interface User {
  id: string;
  phone_number: string;
  name: string;
  email: string | null;
  role: UserRole;
  is_verified: boolean;
  is_active: boolean;
  team_id: string | null;
  team_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserListResponse {
  items: User[];
  total: number;
}

export interface UserUpdate {
  name?: string;
  email?: string;
  phone_number?: string;
  current_password?: string;
  new_password?: string;
}

export interface UserCreateRequest {
  name: string;
  email: string;
  password: string;
  phone_number: string;
  role?: UserRole;
  team_id?: string;
}

// Saved Address types
export interface SavedAddress {
  id: string;
  user_id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  city: string | null;
  created_at: string;
  updated_at: string;
}

export interface SavedAddressCreate {
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  city?: string;
}

export interface SavedAddressUpdate {
  name?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  city?: string;
}

export interface SavedAddressListResponse {
  items: SavedAddress[];
  total: number;
}

export interface UserRoleUpdate {
  role: UserRole;
  team_id?: string;
}

// ============================================================================
// ✅ TEAM TYPES (ADDED)
// ============================================================================

/**
 * Member object returned in Team detail response.
 * Backend: TeamMemberResponse
 */
export interface TeamMemberResponse {
  id: string;
  name: string;
  phone_number: string;
  /**
   * Backend returns role.value (string). We keep it compatible with UserRole.
   */
  role: UserRole | string;
}

/**
 * For list page (/teams): TeamListResponse (paginated)
 */
export interface TeamListResponse {
  items: TeamResponse[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Basic team response after create/update: TeamResponse
 */
export interface TeamResponse {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  member_count?: number;
  active_ticket_count?: number;
}

/**
 * Detailed team response including members: TeamDetailResponse
 */
export interface TeamDetailResponse {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  member_count?: number;
  active_ticket_count?: number;
  categories: TeamCategoryResponse[];
  districts: TeamDistrictResponse[];
  members: TeamMemberResponse[];
}

/**
 * Create payload: TeamCreate
 */
export interface TeamCreate {
  name: string;
  description?: string | null;
  category_ids?: string[];
  district_ids?: string[];
}

/**
 * Update payload: TeamUpdate
 */
export interface TeamUpdate {
  name?: string;
  description?: string | null;
}

// Category types
export interface Category {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryListResponse {
  items: Category[];
  total: number;
}

export interface CategoryCreate {
  name: string;
  description?: string;
}

export interface CategoryUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
}

// District types
export interface District {
  id: string;
  name: string;
  city: string;
  created_at: string;
  updated_at: string;
}

export interface DistrictListResponse {
  items: District[];
  total: number;
}

// Team-Category and Team-District association types
export interface TeamCategoryResponse {
  team_id: string;
  category_id: string;
  category_name: string;
}

export interface TeamDistrictResponse {
  team_id: string;
  district_id: string;
  district_name: string;
  city: string;
}

// Location types
export interface Location {
  id: string;
  latitude: number;
  longitude: number;
  address: string | null;
  district: string | null;
  city: string;
}

export interface LocationCreate {
  latitude?: number;
  longitude?: number;
  address?: string;
  district_id?: string;
  city?: string;
}

// Photo types
export interface Photo {
  id: string;
  url: string;
  filename: string;
  photo_type: PhotoType;
  uploaded_by_id: string | null;
  uploaded_at: string;
}

export interface PhotoUploadResponse {
  id: string;
  url: string;
  filename: string;
  message: string;
}

// Comment types
export interface Comment {
  id: string;
  ticket_id: string;
  user_id: string | null;
  user_name: string | null;
  content: string;
  is_internal: boolean;
  created_at: string;
}

export interface CommentCreate {
  content: string;
  is_internal?: boolean;
}

export interface CommentListResponse {
  items: Comment[];
  total: number;
}

// Feedback types
export interface Feedback {
  id: string;
  ticket_id: string;
  user_id: string | null;
  user_name: string | null;
  rating: number;
  comment: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface FeedbackCreate {
  rating: number;
  comment?: string;
}

export interface FeedbackUpdate {
  rating?: number;
  comment?: string;
}

// Ticket types
export interface Ticket {
  id: string;
  title: string;
  description: string;
  status: TicketStatus;
  category_id: string;
  category_name: string | null;
  location: Location;
  reporter_id: string;
  reporter_name: string | null;
  team_id: string | null;
  team_name: string | null;
  resolved_at: string | null;
  photo_count: number;
  comment_count: number;
  follower_count: number;
  created_at: string;
  updated_at: string;
}

export interface StatusLog {
  id: string;
  ticket_id: string;
  old_status: string | null;
  new_status: string;
  changed_by_id: string | null;
  changed_by_name: string | null;
  comment: string | null;
  created_at: string;
}

export interface TicketDetail extends Ticket {
  photos: Photo[];
  comments: Comment[];
  status_logs: StatusLog[];
  has_feedback: boolean;
  has_escalation: boolean;
  can_escalate: boolean;
  is_following: boolean;
}

export interface NearbyTicket {
  id: string;
  title: string;
  status: TicketStatus;
  category_name: string;
  distance_meters: number;
  follower_count: number;
}

// Notification types
export enum NotificationType {
  TICKET_CREATED = "TICKET_CREATED",
  TICKET_STATUS_CHANGED = "TICKET_STATUS_CHANGED",
  TICKET_FOLLOWED = "TICKET_FOLLOWED",
  COMMENT_ADDED = "COMMENT_ADDED",
  TICKET_ASSIGNED = "TICKET_ASSIGNED",
  ESCALATION_REQUESTED = "ESCALATION_REQUESTED",
  ESCALATION_APPROVED = "ESCALATION_APPROVED",
  ESCALATION_REJECTED = "ESCALATION_REJECTED",
  NEW_TICKET_FOR_TEAM = "NEW_TICKET_FOR_TEAM",
}

export interface Notification {
  id: string;
  user_id: string;
  ticket_id: string | null;
  notification_type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  page: number;
  page_size: number;
}

export interface TicketListResponse {
  items: Ticket[];
  total: number;
  page: number;
  page_size: number;
}

export interface TicketCreate {
  title: string;
  description: string;
  category_id: string;
  location: LocationCreate;
}

export interface TicketStatusUpdate {
  status: TicketStatus;
  comment?: string;
}

export interface TicketAssignUpdate {
  team_id: string;
}

// Escalation types
export interface Escalation {
  id: string;
  ticket_id: string;
  ticket_title: string | null;
  requester_id: string | null;
  requester_name: string | null;
  reviewer_id: string | null;
  reviewer_name: string | null;
  reason: string;
  status: EscalationStatus;
  review_comment: string | null;
  created_at: string;
  reviewed_at: string | null;
}

export interface EscalationCreate {
  ticket_id: string;
  reason: string;
}

export interface EscalationReview {
  comment?: string;
}

export interface EscalationListResponse {
  items: Escalation[];
  total: number;
}

// Analytics types
export interface DashboardKPIs {
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  closed_tickets: number;
  escalated_tickets: number;
  resolution_rate: number;
  average_rating: number | null;
  average_resolution_hours: number | null;
}

export interface HeatmapPoint {
  latitude: number;
  longitude: number;
  count: number;
  intensity: number;
}

export interface HeatmapResponse {
  points: HeatmapPoint[];
  total_tickets: number;
  max_count: number;
}

export interface TeamPerformance {
  team_id: string;
  team_name: string;
  total_assigned: number;
  total_resolved: number;
  open_tickets: number;
  resolution_rate: number;
  average_resolution_hours: number | null;
  average_rating: number | null;
  member_count: number;
}

export interface TeamPerformanceResponse {
  items: TeamPerformance[];
}

export interface MemberPerformance {
  user_id: string;
  user_name: string;
  total_assigned: number;
  total_resolved: number;
  resolution_rate: number;
  average_resolution_hours: number | null;
  average_rating: number | null;
}

export interface MemberPerformanceResponse {
  items: MemberPerformance[];
}

export interface CategoryStats {
  category_id: string;
  category_name: string;
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  average_rating: number | null;
}

export interface CategoryStatsResponse {
  items: CategoryStats[];
}

export interface NeighborhoodCategoryBreakdown {
  category_name: string;
  ticket_count: number;
}

export interface NeighborhoodStats {
  district: string;
  total_tickets: number;
  category_breakdown: NeighborhoodCategoryBreakdown[];
}

export interface NeighborhoodStatsResponse {
  items: NeighborhoodStats[];
}

export interface FeedbackTrend {
  category_id: string;
  category_name: string;
  total_feedbacks: number;
  average_rating: number;
  rating_distribution: Record<number, number>;
}

export interface FeedbackTrendsResponse {
  items: FeedbackTrend[];
}

export interface QuarterlyReport {
  quarter: string;
  year: number;
  total_tickets: number;
  resolved_tickets: number;
  resolution_rate: number;
  average_resolution_days: number | null;
  average_rating: number | null;
  top_categories: CategoryStats[];
  team_rankings: TeamPerformance[];
}

// Auth types
export interface RequestOTPRequest {
  phone_number: string;
}

export interface RequestOTPResponse {
  message: string;
  expires_in_seconds: number;
}

export interface VerifyOTPRequest {
  phone_number: string;
  code: string;
}

export interface VerifyOTPResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: string;
  requires_registration: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: string;
}

export interface RegisterRequest {
  phone_number: string;
  full_name: string;
  email: string;
  password: string;
}

export interface RegisterResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: string;
}

export interface StaffLoginRequest {
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// API Error
export interface APIError {
  detail: string;
}
