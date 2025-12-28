"""Utility functions for load tests."""

from faker import Faker
from typing import Any
import random

fake = Faker("tr_TR")  # Turkish locale for realistic data


def generate_ticket_data(category_ids: list[str], district_ids: list[str]) -> dict[str, Any]:
    """Generate realistic ticket creation data."""
    # Common neighborhood issue titles
    issue_types = [
        "Kaldırım çukuru tehlikeli durumda",
        "Sokak lambası arızalı",
        "Çöp konteyneri taşıyor",
        "Park bankı kırık",
        "Trafik işareti düşmüş",
        "Kanalizasyon kapağı açık",
        "Ağaç dalları tehlikeli",
        "Yol çökmesi mevcut",
        "Duvar grafitisi",
        "Gürültü şikayeti",
        "Başıboş hayvan sorunu",
        "Elektrik direği tehlikeli",
    ]
    
    return {
        "title": random.choice(issue_types) + f" - {fake.street_name()}",
        "description": fake.paragraph(nb_sentences=5) + " " + fake.paragraph(nb_sentences=3),
        "category_id": random.choice(category_ids) if category_ids else None,
        "location": {
            "latitude": 41.0082 + random.uniform(-0.1, 0.1),  # Around Istanbul
            "longitude": 28.9784 + random.uniform(-0.1, 0.1),
            "address": fake.address(),
            "district_id": random.choice(district_ids) if district_ids else None,
            "city": "Istanbul",
        },
    }


def generate_comment_data() -> dict[str, str]:
    """Generate realistic comment data."""
    comments = [
        "Bu sorun acil ilgilenilmeli.",
        "Durumu fotoğrafladım, gerçekten tehlikeli.",
        "Komşular da şikayetçi bu durumdan.",
        "Bir haftadır bu sorun devam ediyor.",
        "Lütfen en kısa sürede çözüme kavuşturun.",
        "Belediyeye daha önce de bildirmiştim.",
        "Çocuklar için tehlikeli bir ortam oluşturmuş.",
        fake.paragraph(nb_sentences=2),
    ]
    return {"content": random.choice(comments)}


def get_random_status() -> str:
    """Get a random ticket status for updates."""
    statuses = ["in_progress", "resolved", "new"]
    return random.choice(statuses)


class TokenManager:
    """Manage authentication tokens for load test users."""
    
    def __init__(self):
        self.tokens: dict[str, str] = {}
    
    def set_token(self, user_type: str, token: str) -> None:
        """Store a token for a user type."""
        self.tokens[user_type] = token
    
    def get_token(self, user_type: str) -> str | None:
        """Get the token for a user type."""
        return self.tokens.get(user_type)
    
    def get_auth_header(self, user_type: str) -> dict[str, str]:
        """Get authorization header for a user type."""
        token = self.get_token(user_type)
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}


# Global token manager instance
token_manager = TokenManager()
