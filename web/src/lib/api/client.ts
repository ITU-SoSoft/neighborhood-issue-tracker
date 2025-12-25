import {
  APIError,
  Category,
  CategoryCreate,
  CategoryListResponse,
  CategoryUpdate,
  Comment as TicketComment,
  CommentCreate,
  CommentListResponse,
  DashboardKPIs,
  Escalation,
  EscalationCreate,
  EscalationListResponse,
  EscalationReview,
  EscalationStatus,
  Feedback,
  FeedbackCreate,
  FeedbackTrendsResponse,
  HeatmapResponse,
  LoginRequest,
  LoginResponse,
  MemberPerformanceResponse,
  NearbyTicket,
  Notification,
  NotificationListResponse,
  PhotoUploadResponse,
  PhotoType,
  QuarterlyReport,
  RefreshTokenRequest,
  RegisterRequest,
  RegisterResponse,
  RequestOTPRequest,
  RequestOTPResponse,
  SavedAddress,
  SavedAddressCreate,
  SavedAddressListResponse,
  SavedAddressUpdate,
  StaffLoginRequest,
  TeamPerformanceResponse,
  Ticket,
  TicketAssignUpdate,
  TicketCreate,
  TicketDetail,
  TicketListResponse,
  TicketStatus,
  TicketStatusUpdate,
  TokenResponse,
  User,
  UserCreateRequest,
  UserListResponse,
  UserRole,
  UserRoleUpdate,
  UserUpdate,
  VerifyOTPRequest,
  VerifyOTPResponse,
  CategoryStatsResponse,
  NeighborhoodStatsResponse,

  // ✅ TEAMS (EĞER types.ts içinde tanımlıysa kullan)
  TeamListResponse,
  TeamDetailResponse,
  TeamResponse,
  TeamCreate,
  TeamUpdate,
  District,
  DistrictListResponse,
} from "./types";

const API_BASE_URL =
  (process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000/api/v1");

// Token storage keys
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

// Token management
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// API Error handling
export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = "An unexpected error occurred";
    try {
      const error = await response.json();
      // Handle FastAPI validation errors (array format)
      if (Array.isArray(error.detail)) {
        detail = error.detail
          .map((err: { loc?: string[]; msg?: string }) => {
            const field = err.loc?.slice(-1)[0] || "field";
            return `${field}: ${err.msg}`;
          })
          .join(", ");
      } else if (typeof error.detail === "string") {
        detail = error.detail;
      } else if (error.message) {
        detail = error.message;
      }
      console.error("API Error:", error);
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiError(response.status, detail);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  try {
    const text = await response.text();
    if (!text) {
      return {} as T;
    }
    return JSON.parse(text) as T;
  } catch (error) {
    console.error("Failed to parse response:", error, "Response status:", response.status);
    return {} as T;
  }
}

// Build headers with optional auth
function buildHeaders(includeAuth = true): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  if (includeAuth) {
    const token = getAccessToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  return headers;
}

// Generic fetch wrapper with token refresh
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  requiresAuth = true,
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      ...buildHeaders(requiresAuth),
      ...(options.headers || {}),
    },
  });

  // Handle 401 - try to refresh token
  if (response.status === 401 && requiresAuth) {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      try {
        const tokenResponse = await refreshAccessToken({
          refresh_token: refreshToken,
        });
        setTokens(tokenResponse.access_token, tokenResponse.refresh_token);

        // Retry the original request
        const retryResponse = await fetch(url, {
          ...options,
          headers: {
            ...buildHeaders(true),
            ...(options.headers || {}),
          },
        });
        return handleResponse<T>(retryResponse);
      } catch {
        // Refresh failed, clear tokens
        clearTokens();
        throw new ApiError(401, "Session expired. Please log in again.");
      }
    }
  }

  return handleResponse<T>(response);
}

// ============================================================================
// AUTH API
// ============================================================================

export async function requestOTP(
  data: RequestOTPRequest,
): Promise<RequestOTPResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/request-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<RequestOTPResponse>(response);
}

export async function verifyOTP(
  data: VerifyOTPRequest,
): Promise<VerifyOTPResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/verify-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<VerifyOTPResponse>(response);
}

export async function register(
  data: RegisterRequest,
): Promise<RegisterResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<RegisterResponse>(response);
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<LoginResponse>(response);
}

export async function staffLogin(
  data: StaffLoginRequest,
): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/staff/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<LoginResponse>(response);
}

export async function refreshAccessToken(
  data: RefreshTokenRequest,
): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<TokenResponse>(response);
}

export async function getCurrentUser(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

// ============================================================================
// USERS API
// ============================================================================

export async function getUsers(params?: {
  role?: UserRole;
  team_id?: string;
  page?: number;
  page_size?: number;
}): Promise<UserListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.role) searchParams.set("role", params.role);
  if (params?.team_id) searchParams.set("team_id", params.team_id);
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.page_size)
    searchParams.set("page_size", params.page_size.toString());

  const query = searchParams.toString();
  return apiFetch<UserListResponse>(`/users/${query ? `?${query}` : ""}`);
}

export async function getUserById(userId: string): Promise<User> {
  return apiFetch<User>(`/users/${userId}`);
}

export async function createUser(data: UserCreateRequest): Promise<User> {
  return apiFetch<User>("/users/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateUser(
  userId: string,
  data: UserUpdate,
): Promise<User> {
  return apiFetch<User>(`/users/${userId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function updateUserRole(
  userId: string,
  data: UserRoleUpdate,
): Promise<User> {
  return apiFetch<User>(`/users/${userId}/role`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteUser(userId: string): Promise<void> {
  return apiFetch<void>(`/users/${userId}`, {
    method: "DELETE",
  });
}

// ============================================================================
// ✅ TEAMS API  (manager-only endpoints)
// ============================================================================
//
// Backend routes'in senin teams.py ile uyumlu:
// GET    /teams
// GET    /teams/{team_id}
// POST   /teams
// PUT    /teams/{team_id}
// DELETE /teams/{team_id}
// POST   /teams/{team_id}/members/{user_id}
// DELETE /teams/{team_id}/members/{user_id}
//

export async function getTeams(): Promise<TeamListResponse> {
  return apiFetch<TeamListResponse>("/teams");
}

export async function getTeamById(teamId: string): Promise<TeamDetailResponse> {
  return apiFetch<TeamDetailResponse>(`/teams/${teamId}`);
}

export async function createTeam(data: TeamCreate): Promise<TeamResponse> {
  return apiFetch<TeamResponse>("/teams", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateTeam(
  teamId: string,
  data: TeamUpdate,
): Promise<TeamResponse> {
  return apiFetch<TeamResponse>(`/teams/${teamId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteTeam(teamId: string): Promise<void> {
  return apiFetch<void>(`/teams/${teamId}`, {
    method: "DELETE",
  });
}

export async function getTicketsByTeam(
  teamId: string,
  page: number = 1,
  pageSize: number = 100
): Promise<TicketListResponse> {
  const params = new URLSearchParams({
    team_id: teamId,
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  return apiFetch<TicketListResponse>(`/tickets/?${params.toString()}`);
}

export async function addTeamMember(
  teamId: string,
  userId: string,
): Promise<TeamDetailResponse> {
  return apiFetch<TeamDetailResponse>(`/teams/${teamId}/members/${userId}`, {
    method: "POST",
  });
}

export async function removeTeamMember(
  teamId: string,
  userId: string,
): Promise<void> {
  return apiFetch<void>(`/teams/${teamId}/members/${userId}`, {
    method: "DELETE",
  });
}

// ============================================================================
// CATEGORIES API
// ============================================================================

export async function getCategories(
  activeOnly = true,
): Promise<CategoryListResponse> {
  const query = activeOnly ? "?active_only=true" : "";
  return apiFetch<CategoryListResponse>(`/categories${query}`, {}, false);
}

export async function getCategoryById(categoryId: string): Promise<Category> {
  return apiFetch<Category>(`/categories/${categoryId}`, {}, false);
}

export async function createCategory(data: CategoryCreate): Promise<Category> {
  return apiFetch<Category>("/categories", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateCategory(
  categoryId: string,
  data: CategoryUpdate,
): Promise<Category> {
  return apiFetch<Category>(`/categories/${categoryId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteCategory(categoryId: string): Promise<void> {
  return apiFetch<void>(`/categories/${categoryId}`, {
    method: "DELETE",
  });
}

// ============================================================================
// DISTRICTS
// ============================================================================

export async function getDistricts(): Promise<DistrictListResponse> {
  return apiFetch<DistrictListResponse>("/districts", {}, false);
}

// ============================================================================
// TICKETS API
// ============================================================================

export async function createTicket(data: TicketCreate): Promise<Ticket> {
  return apiFetch<Ticket>("/tickets/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getTickets(params?: {
  status_filter?: TicketStatus;
  category_id?: string;
  team_id?: string;
  page?: number;
  page_size?: number;
}): Promise<TicketListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status_filter)
    searchParams.set("status_filter", params.status_filter);
  if (params?.category_id) searchParams.set("category_id", params.category_id);
  if (params?.team_id) searchParams.set("team_id", params.team_id);
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.page_size)
    searchParams.set("page_size", params.page_size.toString());

  const query = searchParams.toString();
  return apiFetch<TicketListResponse>(`/tickets/${query ? `?${query}` : ""}`);
}

export async function getMyTickets(params?: {
  status_filter?: TicketStatus;
  category_id?: string;
  page?: number;
  page_size?: number;
}): Promise<TicketListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status_filter)
    searchParams.set("status_filter", params.status_filter);
  if (params?.category_id) searchParams.set("category_id", params.category_id);
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.page_size)
    searchParams.set("page_size", params.page_size.toString());

  const query = searchParams.toString();
  return apiFetch<TicketListResponse>(`/tickets/my${query ? `?${query}` : ""}`);
}

export async function getAssignedTickets(params?: {
  status_filter?: TicketStatus;
  category_id?: string;
  page?: number;
  page_size?: number;
}): Promise<TicketListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status_filter)
    searchParams.set("status_filter", params.status_filter);
  if (params?.category_id) searchParams.set("category_id", params.category_id);
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.page_size)
    searchParams.set("page_size", params.page_size.toString());

  const query = searchParams.toString();
  return apiFetch<TicketListResponse>(
    `/tickets/assigned${query ? `?${query}` : ""}`,
  );
}

export async function getFollowedTickets(params?: {
  status_filter?: TicketStatus;
  category_id?: string;
  page?: number;
  page_size?: number;
}): Promise<TicketListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status_filter)
    searchParams.set("status_filter", params.status_filter);
  if (params?.category_id) searchParams.set("category_id", params.category_id);
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.page_size)
    searchParams.set("page_size", params.page_size.toString());

  const query = searchParams.toString();
  return apiFetch<TicketListResponse>(
    `/tickets/followed${query ? `?${query}` : ""}`,
  );
}

export async function getAllUserTickets(params?: {
  status_filter?: TicketStatus;
  category_id?: string;
  page?: number;
  page_size?: number;
}): Promise<TicketListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status_filter)
    searchParams.set("status_filter", params.status_filter);
  if (params?.category_id) searchParams.set("category_id", params.category_id);
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.page_size)
    searchParams.set("page_size", params.page_size.toString());

  const query = searchParams.toString();
  return apiFetch<TicketListResponse>(
    `/tickets/all${query ? `?${query}` : ""}`,
  );
}

export async function getNearbyTickets(params: {
  latitude: number;
  longitude: number;
  radius_meters?: number;
  category_id?: string;
}): Promise<NearbyTicket[]> {
  const searchParams = new URLSearchParams();
  searchParams.set("latitude", params.latitude.toString());
  searchParams.set("longitude", params.longitude.toString());
  if (params.radius_meters)
    searchParams.set("radius_meters", params.radius_meters.toString());
  if (params.category_id) searchParams.set("category_id", params.category_id);

  return apiFetch<NearbyTicket[]>(
    `/tickets/nearby?${searchParams.toString()}`,
  );
}

export async function getTicketById(ticketId: string): Promise<TicketDetail> {
  return apiFetch<TicketDetail>(`/tickets/${ticketId}`);
}

export async function updateTicketStatus(
  ticketId: string,
  data: TicketStatusUpdate,
): Promise<Ticket> {
  return apiFetch<Ticket>(`/tickets/${ticketId}/status`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function assignTicket(
  ticketId: string,
  data: TicketAssignUpdate,
): Promise<Ticket> {
  return apiFetch<Ticket>(`/tickets/${ticketId}/assign`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function uploadTicketPhoto(
  ticketId: string,
  file: File,
  photoType: PhotoType,
): Promise<PhotoUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("photo_type", photoType);

  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/photos`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  return handleResponse<PhotoUploadResponse>(response);
}

export async function followTicket(
  ticketId: string,
): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(`/tickets/${ticketId}/follow`, {
    method: "POST",
  });
}

export async function unfollowTicket(ticketId: string): Promise<void> {
  return apiFetch<void>(`/tickets/${ticketId}/follow`, {
    method: "DELETE",
  });
}

// ============================================================================
// COMMENTS API
// ============================================================================

export async function getTicketComments(
  ticketId: string,
): Promise<CommentListResponse> {
  return apiFetch<CommentListResponse>(`/tickets/${ticketId}/comments`);
}

export async function createComment(
  ticketId: string,
  data: CommentCreate,
): Promise<TicketComment> {
  return apiFetch<TicketComment>(`/tickets/${ticketId}/comments`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ============================================================================
// FEEDBACK API
// ============================================================================

export async function submitFeedback(
  ticketId: string,
  data: FeedbackCreate,
): Promise<Feedback> {
  return apiFetch<Feedback>(`/feedback/tickets/${ticketId}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getTicketFeedback(ticketId: string): Promise<Feedback> {
  return apiFetch<Feedback>(`/feedback/tickets/${ticketId}`);
}

// ============================================================================
// ESCALATIONS API
// ============================================================================

export async function createEscalation(
  data: EscalationCreate,
): Promise<Escalation> {
  return apiFetch<Escalation>("/escalations", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getEscalations(params?: {
  status_filter?: EscalationStatus;
  ticket_id?: string;
  page?: number;
  page_size?: number;
}): Promise<EscalationListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status_filter)
    searchParams.set("status_filter", params.status_filter);
  if (params?.ticket_id)
    searchParams.set("ticket_id", params.ticket_id);
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.page_size)
    searchParams.set("page_size", params.page_size.toString());

  const query = searchParams.toString();
  return apiFetch<EscalationListResponse>(
    `/escalations${query ? `?${query}` : ""}`,
  );
}

export async function getEscalationById(
  escalationId: string,
): Promise<Escalation> {
  return apiFetch<Escalation>(`/escalations/${escalationId}`);
}

export async function approveEscalation(
  escalationId: string,
  data: EscalationReview,
): Promise<Escalation> {
  return apiFetch<Escalation>(`/escalations/${escalationId}/approve`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function rejectEscalation(
  escalationId: string,
  data: EscalationReview,
): Promise<Escalation> {
  return apiFetch<Escalation>(`/escalations/${escalationId}/reject`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ============================================================================
// ANALYTICS API
// ============================================================================

export async function getDashboardKPIs(days = 30): Promise<DashboardKPIs> {
  return apiFetch<DashboardKPIs>(`/analytics/dashboard?days=${days}`);
}

export async function getHeatmap(params?: {
  days?: number;
  category_id?: string;
  status?: TicketStatus;
}): Promise<HeatmapResponse> {
  const searchParams = new URLSearchParams();
  if (params?.days) searchParams.set("days", params.days.toString());
  if (params?.category_id) searchParams.set("category_id", params.category_id);
  if (params?.status) searchParams.set("status", params.status);

  const query = searchParams.toString();
  return apiFetch<HeatmapResponse>(
    `/analytics/heatmap${query ? `?${query}` : ""}`,
  );
}

export async function getTeamPerformance(days = 30): Promise<TeamPerformanceResponse> {
  return apiFetch<TeamPerformanceResponse>(`/analytics/teams?days=${days}`);
}

export async function getMemberPerformance(
  teamId: string,
  days = 30,
): Promise<MemberPerformanceResponse> {
  return apiFetch<MemberPerformanceResponse>(
    `/analytics/teams/${teamId}/members?days=${days}`,
  );
}

export async function getCategoryStats(days = 30): Promise<CategoryStatsResponse> {
  return apiFetch<CategoryStatsResponse>(`/analytics/categories?days=${days}`);
}

export async function getNeighborhoodStats(
  days = 30,
  limit = 5,
): Promise<NeighborhoodStatsResponse> {
  return apiFetch<NeighborhoodStatsResponse>(
    `/analytics/neighborhoods?days=${days}&limit=${limit}`,
  );
}

export async function getFeedbackTrends(
  days = 30,
): Promise<FeedbackTrendsResponse> {
  return apiFetch<FeedbackTrendsResponse>(
    `/analytics/feedback-trends?days=${days}`,
  );
}

export async function getQuarterlyReport(
  year: number,
  quarter: number,
): Promise<QuarterlyReport> {
  return apiFetch<QuarterlyReport>(
    `/analytics/quarterly-report?year=${year}&quarter=${quarter}`,
  );
}

// ============================================================================
// SAVED ADDRESSES API
// ============================================================================

export async function getSavedAddresses(): Promise<SavedAddressListResponse> {
  return apiFetch<SavedAddressListResponse>("/addresses");
}

export async function getSavedAddressById(addressId: string): Promise<SavedAddress> {
  return apiFetch<SavedAddress>(`/addresses/${addressId}`);
}

export async function createSavedAddress(
  data: SavedAddressCreate,
): Promise<SavedAddress> {
  return apiFetch<SavedAddress>("/addresses", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateSavedAddress(
  addressId: string,
  data: SavedAddressUpdate,
): Promise<SavedAddress> {
  return apiFetch<SavedAddress>(`/addresses/${addressId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteSavedAddress(addressId: string): Promise<void> {
  return apiFetch<void>(`/addresses/${addressId}`, {
    method: "DELETE",
  });
}

// ============================================================================
// NOTIFICATIONS API
// ============================================================================

export async function getNotifications(params?: {
  unread_only?: boolean;
  page?: number;
  page_size?: number;
}): Promise<NotificationListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.unread_only) searchParams.set("unread_only", "true");
  if (params?.page) searchParams.set("page", params.page.toString());
  if (params?.page_size)
    searchParams.set("page_size", params.page_size.toString());

  const query = searchParams.toString();
  return apiFetch<NotificationListResponse>(
    `/notifications${query ? `?${query}` : ""}`,
  );
}

export async function getUnreadNotificationCount(): Promise<{ count: number }> {
  return apiFetch<{ count: number }>("/notifications/unread-count");
}

export async function markNotificationAsRead(
  notificationId: string,
): Promise<Notification> {
  return apiFetch<Notification>(`/notifications/${notificationId}/read`, {
    method: "PATCH",
  });
}

export async function markAllNotificationsAsRead(): Promise<{ message: string }> {
  return apiFetch<{ message: string }>("/notifications/read-all", {
    method: "PATCH",
  });
}

export async function deleteNotification(
  notificationId: string,
): Promise<void> {
  return apiFetch<void>(`/notifications/${notificationId}`, {
    method: "DELETE",
  });
}
