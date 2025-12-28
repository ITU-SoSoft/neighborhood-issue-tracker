"""
Load test scenarios for Neighborhood Issue Tracker API.
Updated: 2025-12-28T20:31

This file contains three main user types:
1. CitizenUser - Creates tickets and adds comments
2. SupportUser - Lists tickets only (status updates removed)
3. ManagerUser - Accesses analytics endpoints (team fetch removed)

Run with:
    locust -f locustfile.py --host=http://localhost:8000

Or headless:
    locust -f locustfile.py --headless -u 10 -r 2 -t 60s --host=http://localhost:8000
"""

import random
from locust import HttpUser, task, between, events
from locust.exception import StopUser

from config import API_PREFIX, TEST_USERS, MIN_WAIT, MAX_WAIT
from utils import (
    generate_ticket_data,
    generate_comment_data,
    token_manager,
)


class CitizenUser(HttpUser):
    """
    Simulates citizen users who:
    - Create new tickets
    - View their tickets
    - Add comments to tickets
    """
    
    wait_time = between(MIN_WAIT, MAX_WAIT)
    weight = 5  # Most common user type
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.user_id = None
        self.created_tickets = []
        self.category_ids = []
        self.district_ids = []
    
    def on_start(self):
        """Login and fetch required data before starting tests."""
        self._login()
        self._fetch_categories()
        self._fetch_districts()
    
    def _login(self):
        """Authenticate as a citizen user."""
        credentials = TEST_USERS["citizen"]
        response = self.client.post(
            f"{API_PREFIX}/auth/login",
            json={
                "email": credentials["email"],
                "password": credentials["password"],
            },
            name="[Auth] Citizen Login",
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            token_manager.set_token("citizen", self.token)
        else:
            # Log error details before stopping
            print(f"Citizen login failed: {response.status_code} - {response.text}")
            raise StopUser()
    
    def _get_headers(self):
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def _fetch_categories(self):
        """Fetch available categories for ticket creation."""
        response = self.client.get(
            f"{API_PREFIX}/categories",
            headers=self._get_headers(),
            name="[Setup] Fetch Categories",
        )
        if response.status_code == 200:
            data = response.json()
            # Categories returns {items: [...], total: N}
            items = data.get("items", []) if isinstance(data, dict) else data
            self.category_ids = [cat["id"] for cat in items if isinstance(cat, dict)]
    
    def _fetch_districts(self):
        """Fetch available districts for ticket location."""
        response = self.client.get(
            f"{API_PREFIX}/districts",
            headers=self._get_headers(),
            name="[Setup] Fetch Districts",
        )
        if response.status_code == 200:
            data = response.json()
            # Handle both list and {items: [...]} formats
            items = data.get("items", data) if isinstance(data, dict) else data
            if isinstance(items, list):
                self.district_ids = [d["id"] for d in items if isinstance(d, dict)]
    
    @task(10)
    def create_ticket(self):
        """Create a new ticket - PRIMARY LOAD TEST SCENARIO."""
        if not self.category_ids:
            return
        
        ticket_data = generate_ticket_data(self.category_ids, self.district_ids)
        
        response = self.client.post(
            f"{API_PREFIX}/tickets/",
            json=ticket_data,
            headers=self._get_headers(),
            name="[Ticket] Create Ticket",
        )
        
        if response.status_code == 201:
            data = response.json()
            self.created_tickets.append(data["id"])
    
    @task(3)
    def view_my_tickets(self):
        """View citizen's own tickets."""
        self.client.get(
            f"{API_PREFIX}/tickets/my",
            headers=self._get_headers(),
            name="[Ticket] View My Tickets",
        )
    
    @task(2)
    def view_ticket_detail(self):
        """View a specific ticket's details."""
        if not self.created_tickets:
            return
        
        ticket_id = random.choice(self.created_tickets)
        self.client.get(
            f"{API_PREFIX}/tickets/{ticket_id}",
            headers=self._get_headers(),
            name="[Ticket] View Ticket Detail",
        )
    
    @task(1)
    def add_comment(self):
        """Add a comment to a ticket."""
        if not self.created_tickets:
            return
        
        ticket_id = random.choice(self.created_tickets)
        comment_data = generate_comment_data()
        
        self.client.post(
            f"{API_PREFIX}/tickets/{ticket_id}/comments",
            json=comment_data,
            headers=self._get_headers(),
            name="[Ticket] Add Comment",
        )


class SupportUser(HttpUser):
    """
    Simulates support staff who:
    - List and filter tickets
    - Update ticket status
    - Assign tickets to teams
    """
    
    wait_time = between(MIN_WAIT, MAX_WAIT)
    weight = 3  # Less common than citizens
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.ticket_ids = []
    
    def on_start(self):
        """Login and fetch required data."""
        self._login()
        self._fetch_tickets()
    
    def _login(self):
        """Authenticate as support staff."""
        credentials = TEST_USERS["support"]
        response = self.client.post(
            f"{API_PREFIX}/auth/staff/login",
            json={
                "email": credentials["email"],
                "password": credentials["password"],
            },
            name="[Auth] Support Login",
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            token_manager.set_token("support", self.token)
        else:
            raise StopUser()
    
    def _get_headers(self):
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def _fetch_tickets(self):
        """Fetch available tickets for operations."""
        response = self.client.get(
            f"{API_PREFIX}/tickets/",
            headers=self._get_headers(),
            params={"page_size": 50},
            name="[Setup] Fetch Tickets",
        )
        if response.status_code == 200:
            data = response.json()
            self.ticket_ids = [t["id"] for t in data.get("items", [])]
    
    
    @task(5)
    def list_tickets(self):
        """List tickets with optional filters."""
        params = {"page": 1, "page_size": 20}
        
        # Randomly apply filters
        if random.random() > 0.5:
            params["status_filter"] = random.choice(["NEW", "IN_PROGRESS", "RESOLVED"])
        
        self.client.get(
            f"{API_PREFIX}/tickets/",
            headers=self._get_headers(),
            params=params,
            name="[Ticket] List Tickets",
        )
    
    
    
    @task(2)
    def view_assigned_tickets(self):
        """View tickets assigned to current user."""
        self.client.get(
            f"{API_PREFIX}/tickets/assigned",
            headers=self._get_headers(),
            name="[Ticket] View Assigned",
        )


class ManagerUser(HttpUser):
    """
    Simulates manager users who:
    - Access analytics dashboards
    - View team performance
    - Generate reports
    """
    
    wait_time = between(MIN_WAIT + 1, MAX_WAIT + 2)  # Slightly longer waits
    weight = 1  # Least common user type
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
    
    def on_start(self):
        """Login and fetch required data."""
        self._login()
    
    def _login(self):
        """Authenticate as manager."""
        credentials = TEST_USERS["manager"]
        response = self.client.post(
            f"{API_PREFIX}/auth/staff/login",
            json={
                "email": credentials["email"],
                "password": credentials["password"],
            },
            name="[Auth] Manager Login",
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            token_manager.set_token("manager", self.token)
        else:
            raise StopUser()
    
    def _get_headers(self):
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    
    @task(10)
    def get_dashboard_kpis(self):
        """Get dashboard KPIs - ANALYTICS LOAD TEST."""
        days = random.choice([7, 30, 90])
        
        self.client.get(
            f"{API_PREFIX}/analytics/dashboard",
            headers=self._get_headers(),
            params={"days": days},
            name="[Analytics] Dashboard KPIs",
        )
    
    @task(8)
    def get_ticket_heatmap(self):
        """Get ticket heatmap data - ANALYTICS LOAD TEST."""
        self.client.get(
            f"{API_PREFIX}/analytics/heatmap",
            headers=self._get_headers(),
            params={"days": 30},
            name="[Analytics] Ticket Heatmap",
        )
    
    @task(5)
    def get_team_performance(self):
        """Get team performance metrics."""
        self.client.get(
            f"{API_PREFIX}/analytics/teams/performance",
            headers=self._get_headers(),
            params={"days": 30},
            name="[Analytics] Team Performance",
        )
    

    
    @task(5)
    def get_category_statistics(self):
        """Get category statistics."""
        self.client.get(
            f"{API_PREFIX}/analytics/categories",
            headers=self._get_headers(),
            params={"days": 30},
            name="[Analytics] Category Stats",
        )
    
    @task(4)
    def get_neighborhood_statistics(self):
        """Get neighborhood statistics."""
        self.client.get(
            f"{API_PREFIX}/analytics/neighborhoods",
            headers=self._get_headers(),
            params={"days": 30, "limit": 10},
            name="[Analytics] Neighborhood Stats",
        )
    
    @task(3)
    def get_feedback_trends(self):
        """Get feedback trends."""
        self.client.get(
            f"{API_PREFIX}/analytics/feedback/trends",
            headers=self._get_headers(),
            params={"days": 30},
            name="[Analytics] Feedback Trends",
        )


# Event hooks for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log additional metrics for each request."""
    if exception:
        print(f"Request failed: {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when a new load test starts."""
    print("=" * 60)
    print("LOAD TEST STARTING")
    print(f"Target host: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the load test stops."""
    print("=" * 60)
    print("LOAD TEST COMPLETED")
    print("=" * 60)
