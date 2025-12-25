"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/lib/auth/context";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TicketListSkeleton } from "@/components/shared/skeletons";
import {
  EmptyTickets,
  EmptySearchResults,
} from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import {
  useTickets,
  useMyTickets,
  useAssignedTickets,
  useFollowedTickets,
  useAllUserTickets,
  useCategories,
  useTeams,
} from "@/lib/queries";
import { Ticket, TicketStatus, UserRole } from "@/lib/api/types";
import {
  formatRelativeTime,
  getStatusVariant,
  getStatusLabel,
} from "@/lib/utils";
import {
  fadeInUp,
  staggerContainer,
  staggerItem,
  cardHover,
  cardTap,
  accordionVariants,
} from "@/lib/animations";
import {
  Plus,
  Search,
  Filter,
  MapPin,
  MessageCircle,
  Users,
  ChevronLeft,
  ChevronRight,
  X,
  Check,
  EyeOff,
} from "lucide-react";

const PAGE_SIZE = 10;

// ============================================================================
// TICKET CARD COMPONENT
// ============================================================================

interface TicketCardProps {
  ticket: Ticket;
}

function TicketCard({ ticket }: TicketCardProps) {
  return (
    <Link href={`/tickets/${ticket.id}`}>
      <motion.div
        variants={staggerItem}
        whileHover={cardHover}
        whileTap={cardTap}
      >
        <Card className="p-5 transition hover:border-primary/30 hover:shadow-md">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0 flex-1 space-y-2">
              <div className="flex items-start gap-3">
                <h3 className="font-semibold text-foreground line-clamp-1">
                  {ticket.title}
                </h3>
                <Badge
                  variant={getStatusVariant(ticket.status)}
                  className="shrink-0"
                >
                  {getStatusLabel(ticket.status)}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground line-clamp-2">
                {ticket.description}
              </p>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5" />
                  {ticket.location.address || ticket.location.city}
                </span>
                {ticket.category_name && (
                  <Badge variant="secondary" className="text-xs">
                    {ticket.category_name}
                  </Badge>
                )}
                <span className="flex items-center gap-1">
                  <MessageCircle className="h-3.5 w-3.5" />
                  {ticket.comment_count}
                </span>
                <span className="flex items-center gap-1">
                  <Users className="h-3.5 w-3.5" />
                  {ticket.follower_count}
                </span>
              </div>
            </div>
            <div className="shrink-0 text-right text-xs text-muted-foreground sm:text-sm">
              <p>{formatRelativeTime(ticket.created_at)}</p>
              {ticket.reporter_name && (
                <p className="mt-1">by {ticket.reporter_name}</p>
              )}
            </div>
          </div>
        </Card>
      </motion.div>
    </Link>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function TicketsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();

  // Filter state
  const [statusFilter, setStatusFilter] = useState<TicketStatus | "">("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [teamFilter, setTeamFilter] = useState<string>("");
  const [viewFilter, setViewFilter] = useState<
    "all" | "my" | "assigned" | "followed"
  >("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [hideClosed, setHideClosed] = useState(false);

  // Track if we're updating from URL to prevent loops
  const isUpdatingFromUrl = useRef(false);
  const previousSearchParams = useRef<string>("");

  // Queries
  const { data: categoriesData } = useCategories();
  const categories = categoriesData?.items ?? [];
  const { data: teamsData } = useTeams();
  const teams = teamsData?.items ?? [];

  // Check if user is support/manager (can see all tickets)
  const isStaff =
    user?.role === UserRole.SUPPORT || user?.role === UserRole.MANAGER;

  // Select the right query based on view filter
  // For "all" view: staff users see all tickets, citizens see own + followed tickets
  const allTicketsQuery = useTickets(
    {
      status_filter: statusFilter || undefined,
      category_id: categoryFilter || undefined,
      team_id: teamFilter || undefined,
      page: currentPage,
      page_size: PAGE_SIZE,
    },
    { enabled: viewFilter === "all" && isStaff },
  );

  const allUserTicketsQuery = useAllUserTickets(
    {
      status_filter: statusFilter || undefined,
      category_id: categoryFilter || undefined,
      page: currentPage,
      page_size: PAGE_SIZE,
    },
    { enabled: viewFilter === "all" && !isStaff },
  );

  const myTicketsQuery = useMyTickets(
    {
      status_filter: statusFilter || undefined,
      category_id: categoryFilter || undefined,
      page: currentPage,
      page_size: PAGE_SIZE,
    },
    { enabled: viewFilter === "my" },
  );

  const assignedTicketsQuery = useAssignedTickets(
    {
      status_filter: statusFilter || undefined,
      category_id: categoryFilter || undefined,
      page: currentPage,
      page_size: PAGE_SIZE,
    },
    { enabled: viewFilter === "assigned" && isStaff },
  );

  const followedTicketsQuery = useFollowedTickets(
    {
      status_filter: statusFilter || undefined,
      category_id: categoryFilter || undefined,
      page: currentPage,
      page_size: PAGE_SIZE,
    },
    { enabled: viewFilter === "followed" },
  );

  // Get the active query
  const activeQuery =
    viewFilter === "my"
      ? myTicketsQuery
      : viewFilter === "assigned"
        ? assignedTicketsQuery
        : viewFilter === "followed"
          ? followedTicketsQuery
          : isStaff
            ? allTicketsQuery
            : allUserTicketsQuery;

  const tickets = activeQuery.data?.items ?? [];
  const totalTickets = activeQuery.data?.total ?? 0;
  const isLoading = activeQuery.isLoading;
  const isError = activeQuery.isError;

  // Initialize filters from URL params
  useEffect(() => {
    const currentParams = searchParams.toString();
    
    // Only update if URL actually changed (not from our own update)
    if (currentParams === previousSearchParams.current) {
      return;
    }
    
    previousSearchParams.current = currentParams;
    isUpdatingFromUrl.current = true;
    
    const status = searchParams.get("status") as TicketStatus | null;
    const category = searchParams.get("category");
    const team = searchParams.get("team");
    const view = searchParams.get("view") as
      | "all"
      | "my"
      | "assigned"
      | "followed"
      | null;
    const page = searchParams.get("page");
    const hideClosedParam = searchParams.get("hideClosed");

    if (status) setStatusFilter(status);
    else setStatusFilter("");
    
    if (category) setCategoryFilter(category);
    else setCategoryFilter("");
    
    if (team) setTeamFilter(team);
    else setTeamFilter("");
    
    // Set viewFilter - default to "all" if no view param
    setViewFilter(view || "all");
    
    if (page) setCurrentPage(parseInt(page, 10));
    else setCurrentPage(1);

    // Set hideClosed from URL param
    setHideClosed(hideClosedParam === "true");

    // Reset flag after state updates
    requestAnimationFrame(() => {
      isUpdatingFromUrl.current = false;
    });
  }, [searchParams]);

  // Update URL when filters change (but not when initializing from URL)
  useEffect(() => {
    // Don't update URL if we're currently initializing from URL
    if (isUpdatingFromUrl.current) {
      return;
    }

    const params = new URLSearchParams();
    if (statusFilter) params.set("status", statusFilter);
    if (categoryFilter) params.set("category", categoryFilter);
    if (teamFilter) params.set("team", teamFilter);
    if (user?.role !== UserRole.MANAGER && viewFilter !== "all")
      params.set("view", viewFilter);
    if (currentPage > 1) params.set("page", currentPage.toString());
    if (hideClosed) params.set("hideClosed", "true");

    const newQuery = params.toString();
    const newUrl = `/tickets${newQuery ? `?${newQuery}` : ""}`;
    
    // Only update if URL is different from what we last set
    if (newQuery !== previousSearchParams.current) {
      previousSearchParams.current = newQuery;
      router.push(newUrl, { scroll: false });
    }
  }, [statusFilter, categoryFilter, teamFilter, viewFilter, currentPage, hideClosed, user?.role, router]);

  const totalPages = Math.ceil(totalTickets / PAGE_SIZE);

  const clearFilters = () => {
    setStatusFilter("");
    setCategoryFilter("");
    setTeamFilter("");
    setViewFilter("all");
    setHideClosed(false);
    setCurrentPage(1);
  };

  const hasActiveFilters =
    statusFilter ||
    categoryFilter ||
    (user?.role === UserRole.MANAGER && teamFilter) ||
    (user?.role !== UserRole.MANAGER && viewFilter !== "all");

  // Filter tickets by search query and hide closed (client-side)
  let filteredTickets = tickets;
  
  // Filter out closed tickets if hideClosed is enabled
  if (hideClosed) {
    filteredTickets = filteredTickets.filter(
      (t) => t.status !== TicketStatus.CLOSED
    );
  }
  
  // Filter by search query
  if (searchQuery) {
    filteredTickets = filteredTickets.filter(
      (t) =>
        t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.category_name?.toLowerCase().includes(searchQuery.toLowerCase()),
    );
  }

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
          <h1 className="text-2xl font-semibold text-foreground">Tickets</h1>
          <p className="text-muted-foreground">
            {hideClosed || searchQuery
              ? `${filteredTickets.length} ${filteredTickets.length === 1 ? "ticket" : "tickets"} found`
              : `${totalTickets} ${totalTickets === 1 ? "ticket" : "tickets"} found`}
          </p>
        </div>
        {user?.role !== UserRole.MANAGER && (
          <Link href="/tickets/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Report Issue
            </Button>
          </Link>
        )}
      </motion.div>

      {/* Search and Filters */}
      <motion.div variants={fadeInUp}>
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col gap-4">
              {/* Search bar */}
              <div className="flex gap-3">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search tickets..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Button
                  variant="outline"
                  onClick={() => setShowFilters(!showFilters)}
                  className={
                    showFilters ? "bg-primary/10 border-primary/30" : ""
                  }
                >
                  <Filter className="mr-2 h-4 w-4" />
                  Filters
                  {hasActiveFilters && (
                    <>
                      <span className="sr-only">
                        {
                          [
                            statusFilter,
                            categoryFilter,
                            user?.role === UserRole.MANAGER && teamFilter,
                            user?.role !== UserRole.MANAGER &&
                              viewFilter !== "all",
                          ].filter(Boolean).length
                        }{" "}
                        active filters
                      </span>
                      <span
                        aria-hidden="true"
                        className="ml-2 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground"
                      >
                        {
                          [
                            statusFilter,
                            categoryFilter,
                            user?.role === UserRole.MANAGER && teamFilter,
                            user?.role !== UserRole.MANAGER &&
                              viewFilter !== "all",
                          ].filter(Boolean).length
                        }
                      </span>
                    </>
                  )}
                </Button>
              </div>

              {/* Filter options */}
              <AnimatePresence>
                {showFilters && (
                  <motion.div
                    className="flex flex-wrap gap-3 border-t border-border pt-4"
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                    variants={accordionVariants}
                  >
                    {/* View filter - Hidden for Manager */}
                    {user?.role !== UserRole.MANAGER && (
                      <div className="min-w-[140px]">
                        <label className="mb-1 block text-xs font-medium text-muted-foreground">
                          View
                        </label>
                        <Select
                          value={viewFilter}
                          onValueChange={(value: string) => {
                            setViewFilter(
                              value as "all" | "my" | "assigned" | "followed",
                            );
                            setCurrentPage(1);
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {user?.role === UserRole.SUPPORT ? (
                              <>
                                <SelectItem value="all">All Tickets</SelectItem>
                                <SelectItem value="assigned">
                                  Assigned to Me
                                </SelectItem>
                              </>
                            ) : (
                              <>
                                <SelectItem value="all">All Tickets</SelectItem>
                                <SelectItem value="my">My Reports</SelectItem>
                                <SelectItem value="followed">
                                  Followed Tickets
                                </SelectItem>
                              </>
                            )}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {/* Status filter */}
                    <div className="min-w-[140px]">
                      <label className="mb-1 block text-xs font-medium text-muted-foreground">
                        Status
                      </label>
                      <Select
                        value={statusFilter || "all-statuses"}
                        onValueChange={(value: string) => {
                          setStatusFilter(
                            value === "all-statuses"
                              ? ""
                              : (value as TicketStatus),
                          );
                          setCurrentPage(1);
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all-statuses">
                            All Statuses
                          </SelectItem>
                          <SelectItem value={TicketStatus.NEW}>New</SelectItem>
                          <SelectItem value={TicketStatus.IN_PROGRESS}>
                            In Progress
                          </SelectItem>
                          <SelectItem value={TicketStatus.RESOLVED}>
                            Resolved
                          </SelectItem>
                          <SelectItem value={TicketStatus.CLOSED}>
                            Closed
                          </SelectItem>
                          <SelectItem value={TicketStatus.ESCALATED}>
                            Escalated
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Category filter */}
                    <div className="min-w-[160px]">
                      <label className="mb-1 block text-xs font-medium text-muted-foreground">
                        Category
                      </label>
                      <Select
                        value={categoryFilter || "all-categories"}
                        onValueChange={(value: string) => {
                          setCategoryFilter(
                            value === "all-categories" ? "" : value,
                          );
                          setCurrentPage(1);
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all-categories">
                            All Categories
                          </SelectItem>
                          {categories.map((category) => (
                            <SelectItem key={category.id} value={category.id}>
                              {category.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Team filter - only for manager */}
                    {user?.role === UserRole.MANAGER && (
                      <div className="min-w-[160px]">
                        <label className="mb-1 block text-xs font-medium text-muted-foreground">
                          Team
                        </label>
                        <Select
                          value={teamFilter || "all-teams"}
                          onValueChange={(value: string) => {
                            setTeamFilter(value === "all-teams" ? "" : value);
                            setCurrentPage(1);
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all-teams">All Teams</SelectItem>
                            {teams.map((team: any) => (
                              <SelectItem key={team.id} value={team.id}>
                                {team.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}

                    {/* Hide Closed Tickets toggle */}
                    <div className="flex items-end">
                      <Button
                        type="button"
                        variant={hideClosed ? "default" : "outline"}
                        size="sm"
                        onClick={() => {
                          setHideClosed(!hideClosed);
                          setCurrentPage(1);
                        }}
                        className="gap-2"
                      >
                        {hideClosed ? (
                          <>
                            <Check className="h-4 w-4" />
                            Hide Closed Tickets
                          </>
                        ) : (
                          <>
                            <EyeOff className="h-4 w-4" />
                            Hide Closed Tickets
                          </>
                        )}
                      </Button>
                    </div>

                    {/* Clear filters */}
                    {hasActiveFilters && (
                      <div className="flex items-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={clearFilters}
                        >
                          <X className="mr-1 h-4 w-4" />
                          Clear
                        </Button>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Tickets List */}
      {isLoading ? (
        <motion.div variants={fadeInUp}>
          <TicketListSkeleton count={5} />
        </motion.div>
      ) : isError ? (
        <motion.div variants={fadeInUp}>
          <ErrorState
            title="Failed to load tickets"
            message="There was a problem loading the tickets. Please try again."
            onRetry={() => activeQuery.refetch()}
          />
        </motion.div>
      ) : filteredTickets.length === 0 ? (
        searchQuery ? (
          <motion.div variants={fadeInUp}>
            <EmptySearchResults />
          </motion.div>
        ) : (
          <motion.div variants={fadeInUp}>
            <Card>
              <CardContent className="py-12">
                <EmptyTickets
                  onCreateTicket={() => router.push("/tickets/new")}
                />
                {hasActiveFilters && (
                  <div className="flex justify-center mt-4">
                    <Button variant="outline" onClick={clearFilters}>
                      Clear filters
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )
      ) : (
        <motion.div
          className="space-y-4"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          key={`${viewFilter}-${statusFilter}-${categoryFilter}-${currentPage}-${hideClosed}`}
        >
          <AnimatePresence mode="popLayout">
            {filteredTickets.map((ticket) => (
              <TicketCard key={ticket.id} ticket={ticket} />
            ))}
          </AnimatePresence>
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
            {Math.min(currentPage * PAGE_SIZE, totalTickets)} of {totalTickets}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
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
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
