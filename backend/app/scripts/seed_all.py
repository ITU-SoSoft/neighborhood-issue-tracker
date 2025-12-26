"""Consolidated seed script for demo data.

Creates all necessary data for development, demo, and testing presentations.
This script combines functionality from all existing seed scripts into one
comprehensive, well-organized module.

Run with: uv run python -m app.scripts.seed_all
Or via Docker: docker exec -it <container> python -m app.scripts.seed_all

Options:
    --clear     Clear existing demo data before seeding (preserves categories, districts, default users)
    --tickets N Number of tickets to create (default: 300)

Examples:
    # Basic seeding
    python -m app.scripts.seed_all

    # Clear and re-seed
    python -m app.scripts.seed_all --clear

    # Custom ticket count
    python -m app.scripts.seed_all --tickets 500
"""

import argparse
import asyncio
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.database import async_session_maker, create_tables
from app.models.category import Category
from app.models.comment import Comment
from app.models.district import District
from app.models.escalation import EscalationRequest, EscalationStatus
from app.models.feedback import Feedback
from app.models.photo import Photo
from app.models.team import Team, TeamCategory, TeamDistrict
from app.models.ticket import Location, StatusLog, Ticket, TicketFollower, TicketStatus
from app.models.user import User, UserRole

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

# Default users that should be preserved during clear
DEFAULT_USER_EMAILS = [
    "manager@sosoft.com",
    "support@sosoft.com",
    "citizen@sosoft.com",
]

# Categories (6 total)
DEFAULT_CATEGORIES = [
    {
        "name": "Infrastructure",
        "description": "Road damage, sidewalk issues, building problems",
    },
    {
        "name": "Traffic",
        "description": "Traffic signals, road signs, pedestrian crossings",
    },
    {
        "name": "Lighting",
        "description": "Street lights, park lighting, public area illumination",
    },
    {
        "name": "Waste Management",
        "description": "Garbage collection, recycling, illegal dumping",
    },
    {"name": "Parks", "description": "Park maintenance, playgrounds, green spaces"},
    {
        "name": "Other",
        "description": "General neighborhood issues not in other categories",
    },
]

# All 39 Istanbul districts with approximate center coordinates
ISTANBUL_DISTRICTS = [
    # European Side - High density areas
    {"name": "Beyoğlu", "lat": 41.0369, "lng": 28.9784, "weight": 16},
    {"name": "Beşiktaş", "lat": 41.0431, "lng": 29.0075, "weight": 14},
    {"name": "Şişli", "lat": 41.0602, "lng": 28.9874, "weight": 13},
    {"name": "Fatih", "lat": 41.0082, "lng": 28.9784, "weight": 10},
    {"name": "Bakırköy", "lat": 40.9833, "lng": 28.8564, "weight": 9},
    {"name": "Sarıyer", "lat": 41.1602, "lng": 29.0466, "weight": 7},
    {"name": "Kağıthane", "lat": 41.0819, "lng": 28.9719, "weight": 7},
    {"name": "Eyüpsultan", "lat": 41.0550, "lng": 28.9336, "weight": 6},
    {"name": "Gaziosmanpaşa", "lat": 41.0650, "lng": 28.9120, "weight": 6},
    {"name": "Bahçelievler", "lat": 41.0022, "lng": 28.8594, "weight": 6},
    {"name": "Güngören", "lat": 41.0194, "lng": 28.8756, "weight": 5},
    {"name": "Zeytinburnu", "lat": 40.9947, "lng": 28.9033, "weight": 5},
    {"name": "Bayrampaşa", "lat": 41.0397, "lng": 28.9017, "weight": 5},
    {"name": "Esenler", "lat": 41.0436, "lng": 28.8761, "weight": 5},
    {"name": "Bağcılar", "lat": 41.0364, "lng": 28.8564, "weight": 5},
    {"name": "Küçükçekmece", "lat": 41.0050, "lng": 28.7800, "weight": 5},
    {"name": "Avcılar", "lat": 40.9794, "lng": 28.7214, "weight": 4},
    {"name": "Esenyurt", "lat": 41.0300, "lng": 28.6700, "weight": 4},
    {"name": "Beylikdüzü", "lat": 40.9833, "lng": 28.6333, "weight": 4},
    {"name": "Başakşehir", "lat": 41.0950, "lng": 28.8000, "weight": 4},
    {"name": "Sultangazi", "lat": 41.1050, "lng": 28.8650, "weight": 4},
    {"name": "Arnavutköy", "lat": 41.1833, "lng": 28.7333, "weight": 3},
    {"name": "Büyükçekmece", "lat": 41.0167, "lng": 28.5833, "weight": 3},
    {"name": "Çatalca", "lat": 41.1433, "lng": 28.4617, "weight": 2},
    {"name": "Silivri", "lat": 41.0733, "lng": 28.2467, "weight": 2},
    # Asian Side
    {"name": "Kadıköy", "lat": 40.9819, "lng": 29.0216, "weight": 15},
    {"name": "Üsküdar", "lat": 41.0214, "lng": 29.0097, "weight": 11},
    {"name": "Ataşehir", "lat": 40.9833, "lng": 29.1167, "weight": 8},
    {"name": "Maltepe", "lat": 40.9341, "lng": 29.1284, "weight": 7},
    {"name": "Kartal", "lat": 40.8957, "lng": 29.1897, "weight": 6},
    {"name": "Pendik", "lat": 40.8761, "lng": 29.2336, "weight": 6},
    {"name": "Ümraniye", "lat": 41.0167, "lng": 29.1167, "weight": 6},
    {"name": "Beykoz", "lat": 41.1167, "lng": 29.1000, "weight": 5},
    {"name": "Çekmeköy", "lat": 41.0333, "lng": 29.1833, "weight": 4},
    {"name": "Sancaktepe", "lat": 41.0000, "lng": 29.2333, "weight": 4},
    {"name": "Sultanbeyli", "lat": 40.9667, "lng": 29.2667, "weight": 4},
    {"name": "Tuzla", "lat": 40.8167, "lng": 29.3000, "weight": 4},
    {"name": "Şile", "lat": 41.1750, "lng": 29.6133, "weight": 2},
    {"name": "Adalar", "lat": 40.8833, "lng": 29.0833, "weight": 2},
]

# Teams configuration with their district and category assignments
# Designed to cover all 39 Istanbul districts with specialized teams
TEAMS_CONFIG = [
    # === ASIAN SIDE (Anadolu Yakası) ===
    {
        "name": "Kadıköy Altyapı Ekibi",
        "description": "Kadıköy ve Ataşehir bölgesi altyapı ve aydınlatma sorunları",
        "districts": ["Kadıköy", "Ataşehir"],
        "categories": ["Infrastructure", "Lighting"],
    },
    {
        "name": "Kadıköy Çevre Ekibi",
        "description": "Kadıköy ve Ataşehir bölgesi çevre ve park sorunları",
        "districts": ["Kadıköy", "Ataşehir"],
        "categories": ["Waste Management", "Parks", "Other"],
    },
    {
        "name": "Üsküdar Altyapı Ekibi",
        "description": "Üsküdar ve Beykoz bölgesi altyapı ve trafik sorunları",
        "districts": ["Üsküdar", "Beykoz"],
        "categories": ["Infrastructure", "Traffic"],
    },
    {
        "name": "Üsküdar Park ve Bahçeler",
        "description": "Üsküdar ve Beykoz bölgesi park ve aydınlatma işleri",
        "districts": ["Üsküdar", "Beykoz"],
        "categories": ["Parks", "Lighting", "Waste Management", "Other"],
    },
    {
        "name": "Pendik Altyapı Ekibi",
        "description": "Pendik, Kartal, Maltepe ve Tuzla bölgesi altyapı ve trafik sorunları",
        "districts": ["Pendik", "Kartal", "Maltepe", "Tuzla"],
        "categories": ["Infrastructure", "Traffic", "Lighting"],
    },
    {
        "name": "Pendik Çevre Ekibi",
        "description": "Pendik, Kartal, Maltepe ve Tuzla bölgesi çevre sorunları",
        "districts": ["Pendik", "Kartal", "Maltepe", "Tuzla"],
        "categories": ["Waste Management", "Parks", "Other"],
    },
    {
        "name": "Ümraniye Altyapı Ekibi",
        "description": "Ümraniye, Çekmeköy ve Sancaktepe bölgesi altyapı sorunları",
        "districts": ["Ümraniye", "Çekmeköy", "Sancaktepe", "Sultanbeyli"],
        "categories": ["Infrastructure", "Traffic", "Lighting"],
    },
    {
        "name": "Ümraniye Çevre Ekibi",
        "description": "Ümraniye, Çekmeköy ve Sancaktepe bölgesi çevre sorunları",
        "districts": ["Ümraniye", "Çekmeköy", "Sancaktepe", "Sultanbeyli"],
        "categories": ["Waste Management", "Parks", "Other"],
    },
    {
        "name": "Adalar Ekibi",
        "description": "Adalar ve Şile bölgesi tüm sorunlar",
        "districts": ["Adalar", "Şile"],
        "categories": [
            "Infrastructure",
            "Traffic",
            "Lighting",
            "Waste Management",
            "Parks",
            "Other",
        ],
    },
    # === EUROPEAN SIDE - CENTRAL (Avrupa Yakası - Merkez) ===
    {
        "name": "Beyoğlu Altyapı Ekibi",
        "description": "Beyoğlu ve Fatih bölgesi altyapı ve trafik sorunları",
        "districts": ["Beyoğlu", "Fatih"],
        "categories": ["Infrastructure", "Traffic", "Lighting"],
    },
    {
        "name": "Beyoğlu Çevre Ekibi",
        "description": "Beyoğlu ve Fatih bölgesi çevre ve park sorunları",
        "districts": ["Beyoğlu", "Fatih"],
        "categories": ["Waste Management", "Parks", "Other"],
    },
    {
        "name": "Beşiktaş Altyapı Ekibi",
        "description": "Beşiktaş ve Şişli bölgesi altyapı ve trafik sorunları",
        "districts": ["Beşiktaş", "Şişli"],
        "categories": ["Infrastructure", "Traffic", "Lighting"],
    },
    {
        "name": "Beşiktaş Çevre Ekibi",
        "description": "Beşiktaş ve Şişli bölgesi çevre ve park sorunları",
        "districts": ["Beşiktaş", "Şişli"],
        "categories": ["Waste Management", "Parks", "Other"],
    },
    {
        "name": "Sarıyer Ekibi",
        "description": "Sarıyer bölgesi tüm sorunlar",
        "districts": ["Sarıyer"],
        "categories": [
            "Infrastructure",
            "Traffic",
            "Lighting",
            "Waste Management",
            "Parks",
            "Other",
        ],
    },
    {
        "name": "Kağıthane Ekibi",
        "description": "Kağıthane ve Eyüpsultan bölgesi tüm sorunlar",
        "districts": ["Kağıthane", "Eyüpsultan"],
        "categories": [
            "Infrastructure",
            "Traffic",
            "Lighting",
            "Waste Management",
            "Parks",
            "Other",
        ],
    },
    # === EUROPEAN SIDE - WEST (Avrupa Yakası - Batı) ===
    {
        "name": "Bakırköy Altyapı Ekibi",
        "description": "Bakırköy, Bahçelievler ve Zeytinburnu bölgesi altyapı sorunları",
        "districts": ["Bakırköy", "Bahçelievler", "Zeytinburnu", "Güngören"],
        "categories": ["Infrastructure", "Traffic", "Lighting"],
    },
    {
        "name": "Bakırköy Çevre Ekibi",
        "description": "Bakırköy, Bahçelievler ve Zeytinburnu bölgesi çevre sorunları",
        "districts": ["Bakırköy", "Bahçelievler", "Zeytinburnu", "Güngören"],
        "categories": ["Waste Management", "Parks", "Other"],
    },
    {
        "name": "Bağcılar Altyapı Ekibi",
        "description": "Bağcılar, Esenler ve Bayrampaşa bölgesi altyapı sorunları",
        "districts": ["Bağcılar", "Esenler", "Bayrampaşa"],
        "categories": ["Infrastructure", "Traffic", "Lighting"],
    },
    {
        "name": "Bağcılar Çevre Ekibi",
        "description": "Bağcılar, Esenler ve Bayrampaşa bölgesi çevre sorunları",
        "districts": ["Bağcılar", "Esenler", "Bayrampaşa"],
        "categories": ["Waste Management", "Parks", "Other"],
    },
    {
        "name": "Gaziosmanpaşa Ekibi",
        "description": "Gaziosmanpaşa ve Sultangazi bölgesi tüm sorunlar",
        "districts": ["Gaziosmanpaşa", "Sultangazi"],
        "categories": [
            "Infrastructure",
            "Traffic",
            "Lighting",
            "Waste Management",
            "Parks",
            "Other",
        ],
    },
    {
        "name": "Küçükçekmece Altyapı Ekibi",
        "description": "Küçükçekmece ve Avcılar bölgesi altyapı sorunları",
        "districts": ["Küçükçekmece", "Avcılar"],
        "categories": ["Infrastructure", "Traffic", "Lighting"],
    },
    {
        "name": "Küçükçekmece Çevre Ekibi",
        "description": "Küçükçekmece ve Avcılar bölgesi çevre sorunları",
        "districts": ["Küçükçekmece", "Avcılar"],
        "categories": ["Waste Management", "Parks", "Other"],
    },
    {
        "name": "Esenyurt Ekibi",
        "description": "Esenyurt ve Beylikdüzü bölgesi tüm sorunlar",
        "districts": ["Esenyurt", "Beylikdüzü"],
        "categories": [
            "Infrastructure",
            "Traffic",
            "Lighting",
            "Waste Management",
            "Parks",
            "Other",
        ],
    },
    {
        "name": "Başakşehir Ekibi",
        "description": "Başakşehir ve Arnavutköy bölgesi tüm sorunlar",
        "districts": ["Başakşehir", "Arnavutköy"],
        "categories": [
            "Infrastructure",
            "Traffic",
            "Lighting",
            "Waste Management",
            "Parks",
            "Other",
        ],
    },
    {
        "name": "Büyükçekmece Ekibi",
        "description": "Büyükçekmece, Çatalca ve Silivri bölgesi tüm sorunlar",
        "districts": ["Büyükçekmece", "Çatalca", "Silivri"],
        "categories": [
            "Infrastructure",
            "Traffic",
            "Lighting",
            "Waste Management",
            "Parks",
            "Other",
        ],
    },
    # === FALLBACK TEAM ===
    {
        "name": "İstanbul Genel Ekip",
        "description": "Tüm İstanbul genelinde genel sorunlar için yedek ekip. Bu ekip silinemez.",
        "districts": "ALL",  # Special marker for all districts
        "categories": "ALL",  # Special marker for all categories
    },
]

# Turkish names for realistic user data
TURKISH_FIRST_NAMES = [
    "Ahmet",
    "Mehmet",
    "Mustafa",
    "Ali",
    "Hüseyin",
    "İbrahim",
    "Osman",
    "Yusuf",
    "Murat",
    "Emre",
    "Burak",
    "Serkan",
    "Tolga",
    "Onur",
    "Kaan",
    "Ayşe",
    "Fatma",
    "Emine",
    "Hatice",
    "Zeynep",
    "Elif",
    "Merve",
    "Esra",
    "Şeyma",
    "Büşra",
    "Gamze",
    "Derya",
    "Selin",
    "Cansu",
    "Pınar",
]

TURKISH_LAST_NAMES = [
    "Yılmaz",
    "Demir",
    "Kaya",
    "Çelik",
    "Şahin",
    "Arslan",
    "Öztürk",
    "Aydın",
    "Yıldız",
    "Kılıç",
    "Çetin",
    "Koç",
    "Korkmaz",
    "Özdemir",
    "Erdoğan",
    "Aksoy",
    "Polat",
    "Taş",
    "Kara",
    "Aktaş",
    "Yalçın",
    "Güneş",
    "Doğan",
]

# Realistic Turkish ticket titles
TICKET_TITLES_TR = [
    "Kaldırım taşları kırık, yürümek tehlikeli",
    "Sokak lambası yanmıyor, karanlıkta kalıyoruz",
    "Çöp konteyneri taşıyor, koku yapıyor",
    "Trafik işareti hasar görmüş, görünmüyor",
    "Yolda büyük çukur var, araçlar zarar görüyor",
    "Park bankı kırık, oturulamıyor",
    "Ağaç dalları yola sarkmış, tehlike oluşturuyor",
    "Duvar yazıları temizlenmeli",
    "Çöpler toplanmıyor, birikti",
    "Parktaki çeşme bozuk, su akmıyor",
    "Yaya geçidi çizgileri silinmiş",
    "Gürültü şikayeti - gece inşaat yapılıyor",
    "Rögar kapağı eksik, tehlikeli",
    "Cadde aydınlatması yetersiz",
    "Park çimleri bakımsız, uzamış",
    "Bisiklet yolu engelli, park edilmiş araç var",
    "Otobüs durağı camı kırık",
    "Su borusu patlamış, yol su altında",
    "Elektrik direği eğilmiş, düşecek gibi",
    "Çocuk parkı oyun grupları kırık",
    "Yangın musluğu önü araçla kapatılmış",
    "Yol çökmüş, tamir gerekiyor",
    "Köprü korkulukları paslanmış",
    "Merdiven basamakları kırık",
    "Kapı zili çalışmıyor, duyulmuyor",
]

# Realistic Turkish descriptions
TICKET_DESCRIPTIONS_TR = [
    "Bu sorunu dün akşam saatlerinde fark ettim. Acil müdahale gerekiyor.",
    "Bir haftadır devam eden bir sorun. Mahalle sakinleri endişeli.",
    "Birçok komşu bu sorunu bildirdi. Lütfen inceleyin.",
    "Güvenlik açısından tehlike oluşturuyor, en kısa sürede çözülmeli.",
    "Bugün ilk kez fark ettim. Hızlı bir çözüm bekliyorum.",
    "Bu durum mahallede günlük yaşamı olumsuz etkiliyor.",
    "Çocuklar için tehlike oluşturuyor, acil önlem alınmalı.",
    "Yaşlı vatandaşlar özellikle zorluk çekiyor.",
    "Yağmurlu havalarda durum daha da kötüleşiyor.",
    "Birkaç kez belediyeye bildirdim ama hala çözülmedi.",
]

# Feedback comments in Turkish
FEEDBACK_COMMENTS_TR = [
    "Hızlı müdahale için teşekkürler!",
    "Beklenenden uzun sürdü ama sonunda çözüldü.",
    "Hizmetten çok memnunum.",
    "Sorun giderildi ama arkada dağınıklık bırakıldı.",
    "Mükemmel çalışma, ekip çok profesyoneldi.",
    "Hala kalıcı bir çözüm bekliyorum.",
    "Çok hızlı dönüş yaptınız, teşekkürler!",
    "Daha iyi olabilirdi.",
    "Yardımınız için minnettarım.",
    "Tamamen memnunum, elinize sağlık.",
    "Ekip çok ilgiliydi, sağ olsunlar.",
    "Biraz geç kaldınız ama sonuç iyi.",
]

# Escalation reasons in Turkish
ESCALATION_REASONS_TR = [
    "Sorun daha önce giderilmesine rağmen tekrar etti",
    "Acil müdahale gerektiren güvenlik tehlikesi",
    "2 haftadır hiçbir işlem yapılmadı",
    "Sağlanan çözüm eksik kaldı",
    "Vatandaş özellikle yönetici incelemesi talep etti",
    "Teknik ekip sorunu çözemedi, uzman gerekiyor",
    "Birden fazla şikayet var, önceliklendirilmeli",
]

# Comment templates
COMMENT_TEMPLATES_TR = [
    "Ekip sahaya gönderildi, inceleme yapılacak.",
    "Malzeme tedariki bekleniyor.",
    "İş emri oluşturuldu, sıraya alındı.",
    "Vatandaşla iletişime geçildi, bilgi verildi.",
    "Çalışmalar başladı, tahmini süre 2 gün.",
    "İlk müdahale yapıldı, takip edilecek.",
    "Kalıcı çözüm için proje hazırlanıyor.",
    "Diğer birimlerle koordinasyon sağlandı.",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def generate_turkish_name() -> str:
    """Generate a random Turkish full name."""
    first = random.choice(TURKISH_FIRST_NAMES)
    last = random.choice(TURKISH_LAST_NAMES)
    return f"{first} {last}"


def generate_phone_number() -> str:
    """Generate a random Turkish phone number."""
    return f"+9053{random.randint(0, 9)}{random.randint(1000000, 9999999)}"


def slugify(text: str) -> str:
    """Convert text to ASCII-safe slug for email generation."""
    # Turkish character replacements
    replacements = {
        "ı": "i",
        "İ": "I",
        "ğ": "g",
        "Ğ": "G",
        "ü": "u",
        "Ü": "U",
        "ş": "s",
        "Ş": "S",
        "ö": "o",
        "Ö": "O",
        "ç": "c",
        "Ç": "C",
    }
    for tr_char, ascii_char in replacements.items():
        text = text.replace(tr_char, ascii_char)
    # Remove any remaining non-ASCII and convert to lowercase
    return "".join(c for c in text if c.isalnum() or c in "-_").lower()


def get_weighted_district() -> dict:
    """Get a random district using weighted selection for realistic clustering."""
    weights = [d["weight"] for d in ISTANBUL_DISTRICTS]
    return random.choices(ISTANBUL_DISTRICTS, weights=weights, k=1)[0]


def get_random_date(days_history: int = 90) -> datetime:
    """Generate a random date with higher density in recent days."""
    rand = random.random()
    if rand < 0.40:  # 40% in last 7 days
        days_ago = random.randint(0, 7)
    elif rand < 0.80:  # 40% in days 8-30
        days_ago = random.randint(8, 30)
    else:  # 20% in days 31-90
        days_ago = random.randint(31, days_history)

    base_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
    # Add random hours for more variety
    hours_offset = random.randint(0, 23)
    minutes_offset = random.randint(0, 59)
    return base_date.replace(hour=hours_offset, minute=minutes_offset)


def get_rating_weighted() -> int:
    """Get a weighted random rating (skewed towards positive)."""
    # Distribution: 1★=5%, 2★=10%, 3★=20%, 4★=40%, 5★=25%
    return random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 40, 25], k=1)[0]


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================


async def clear_demo_data() -> None:
    """Clear existing demo data while preserving categories, districts, and default users."""
    logger.info("=" * 60)
    logger.info("🗑️  Clearing existing demo data...")
    logger.info("=" * 60)

    async with async_session_maker() as session:
        # Get default user IDs to preserve
        result = await session.execute(
            select(User.id).where(User.email.in_(DEFAULT_USER_EMAILS))
        )
        default_user_ids = [row[0] for row in result.all()]
        logger.info(f"Preserving {len(default_user_ids)} default users")

        # Delete in order (respecting foreign key constraints)

        # 1. Delete feedback
        await session.execute(delete(Feedback))
        logger.info("  ✓ Deleted feedback")

        # 2. Delete escalations
        await session.execute(delete(EscalationRequest))
        logger.info("  ✓ Deleted escalations")

        # 3. Delete comments
        await session.execute(delete(Comment))
        logger.info("  ✓ Deleted comments")

        # 4. Delete photos
        await session.execute(delete(Photo))
        logger.info("  ✓ Deleted photos")

        # 5. Delete status logs
        await session.execute(delete(StatusLog))
        logger.info("  ✓ Deleted status logs")

        # 6. Delete ticket followers
        await session.execute(delete(TicketFollower))
        logger.info("  ✓ Deleted ticket followers")

        # 7. Delete tickets
        await session.execute(delete(Ticket))
        logger.info("  ✓ Deleted tickets")

        # 8. Delete locations
        await session.execute(delete(Location))
        logger.info("  ✓ Deleted locations")

        # 9. Delete non-default users
        if default_user_ids:
            await session.execute(delete(User).where(User.id.notin_(default_user_ids)))
        else:
            await session.execute(delete(User))
        logger.info("  ✓ Deleted non-default users")

        # 10. Delete team assignments
        await session.execute(delete(TeamCategory))
        await session.execute(delete(TeamDistrict))
        logger.info("  ✓ Deleted team assignments")

        # 11. Delete teams
        await session.execute(delete(Team))
        logger.info("  ✓ Deleted teams")

        await session.commit()

    logger.info("✅ Demo data cleared successfully!")
    logger.info("")


async def seed_categories() -> dict[str, Category]:
    """Seed categories and return a name->Category mapping."""
    logger.info("📁 Seeding categories...")

    async with async_session_maker() as session:
        result = await session.execute(select(Category))
        existing = {c.name: c for c in result.scalars().all()}

        for cat_data in DEFAULT_CATEGORIES:
            if cat_data["name"] not in existing:
                category = Category(
                    name=cat_data["name"],
                    description=cat_data["description"],
                )
                session.add(category)
                logger.info(f"  + Created category: {cat_data['name']}")
            else:
                logger.info(f"  ✓ Category exists: {cat_data['name']}")

        await session.commit()

        # Refresh to get all categories
        result = await session.execute(select(Category))
        categories = {c.name: c for c in result.scalars().all()}

    logger.info(f"✅ {len(categories)} categories ready")
    return categories


async def seed_districts() -> dict[str, District]:
    """Seed all Istanbul districts and return a name->District mapping."""
    logger.info("🏘️  Seeding districts...")

    async with async_session_maker() as session:
        result = await session.execute(select(District))
        existing = {d.name: d for d in result.scalars().all()}

        created_count = 0
        for dist_data in ISTANBUL_DISTRICTS:
            if dist_data["name"] not in existing:
                district = District(
                    name=dist_data["name"],
                    city="Istanbul",
                )
                session.add(district)
                created_count += 1

        if created_count > 0:
            await session.commit()
            logger.info(f"  + Created {created_count} new districts")

        # Refresh to get all districts
        result = await session.execute(select(District))
        districts = {d.name: d for d in result.scalars().all()}

    logger.info(f"✅ {len(districts)} districts ready")
    return districts


async def seed_teams(
    categories: dict[str, Category],
    districts: dict[str, District],
) -> list[Team]:
    """Seed teams with their category and district assignments."""
    logger.info("👥 Seeding teams...")

    async with async_session_maker() as session:
        result = await session.execute(select(Team))
        existing_teams = {t.name: t for t in result.scalars().all()}

        created_teams = []

        for team_data in TEAMS_CONFIG:
            if team_data["name"] in existing_teams:
                logger.info(f"  ✓ Team exists: {team_data['name']}")
                created_teams.append(existing_teams[team_data["name"]])
                continue

            # Create team
            team = Team(
                name=team_data["name"],
                description=team_data["description"],
            )
            session.add(team)
            await session.flush()

            # Assign categories
            if team_data["categories"] == "ALL":
                cats_to_assign = list(categories.values())
            else:
                cats_to_assign = [
                    categories[c] for c in team_data["categories"] if c in categories
                ]

            for category in cats_to_assign:
                tc = TeamCategory(team_id=team.id, category_id=category.id)
                session.add(tc)

            # Assign districts
            if team_data["districts"] == "ALL":
                dists_to_assign = list(districts.values())
            else:
                dists_to_assign = [
                    districts[d] for d in team_data["districts"] if d in districts
                ]

            for district in dists_to_assign:
                td = TeamDistrict(team_id=team.id, district_id=district.id)
                session.add(td)

            created_teams.append(team)
            logger.info(
                f"  + Created team: {team_data['name']} "
                f"({len(cats_to_assign)} categories, {len(dists_to_assign)} districts)"
            )

        await session.commit()

        # Reload teams with relationships
        result = await session.execute(
            select(Team).options(
                selectinload(Team.team_categories),
                selectinload(Team.team_districts).selectinload(TeamDistrict.district),
            )
        )
        teams = list(result.scalars().all())

    logger.info(f"✅ {len(teams)} teams ready")
    return teams


async def seed_users(teams: list[Team]) -> dict[str, list[User]]:
    """Seed all users: default users, citizens, support staff, and managers."""
    logger.info("👤 Seeding users...")

    users_by_role: dict[str, list[User]] = {
        "citizens": [],
        "support": [],
        "managers": [],
    }

    async with async_session_maker() as session:
        # Check existing users
        result = await session.execute(select(User))
        existing_users = {u.email: u for u in result.scalars().all()}

        # 1. Create/verify default users
        default_users_data = [
            {
                "name": "Demo Yönetici",
                "email": "manager@sosoft.com",
                "phone_number": "+905001234567",
                "password": "manager123!",
                "role": UserRole.MANAGER,
            },
            {
                "name": "Demo Destek",
                "email": "support@sosoft.com",
                "phone_number": "+905001234568",
                "password": "support123!",
                "role": UserRole.SUPPORT,
            },
            {
                "name": "Demo Vatandaş",
                "email": "citizen@sosoft.com",
                "phone_number": "+905001234569",
                "password": "citizen123!",
                "role": UserRole.CITIZEN,
            },
        ]

        for user_data in default_users_data:
            if user_data["email"] in existing_users:
                user = existing_users[user_data["email"]]
                logger.info(f"  ✓ Default user exists: {user_data['email']}")
            else:
                user = User(
                    name=user_data["name"],
                    email=user_data["email"],
                    phone_number=user_data["phone_number"],
                    password_hash=hash_password(user_data["password"]),
                    role=user_data["role"],
                    is_verified=True,
                    is_active=True,
                )
                session.add(user)
                logger.info(f"  + Created default user: {user_data['email']}")

            # Add to appropriate list
            if user_data["role"] == UserRole.CITIZEN:
                users_by_role["citizens"].append(user)
            elif user_data["role"] == UserRole.SUPPORT:
                users_by_role["support"].append(user)
            else:
                users_by_role["managers"].append(user)

        await session.flush()

        # 2. Create citizen users (15 total including default)
        citizen_count = 14  # +1 default = 15
        citizens_created = 0
        for i in range(citizen_count):
            email = f"vatandas{i + 1}@example.com"
            if email not in existing_users:
                user = User(
                    name=generate_turkish_name(),
                    email=email,
                    phone_number=generate_phone_number(),
                    password_hash=hash_password("test123!"),
                    role=UserRole.CITIZEN,
                    is_verified=True,
                    is_active=True,
                )
                session.add(user)
                citizens_created += 1

        logger.info(f"  + Created {citizens_created} citizen users")

        # 3. Create support staff (2 per team)
        support_created = 0
        for team in teams:
            # Use full team name slug to avoid duplicates (e.g., "Kadıköy Altyapı" vs "Kadıköy Çevre")
            team_slug = slugify("_".join(team.name.split()[:2]))  # First two words
            for i in range(2):
                email = f"destek_{team_slug}_{i + 1}@sosoft.com"
                if email not in existing_users:
                    user = User(
                        name=f"{team.name} Destek {i + 1}",
                        email=email,
                        phone_number=generate_phone_number(),
                        password_hash=hash_password("test123!"),
                        role=UserRole.SUPPORT,
                        is_verified=True,
                        is_active=True,
                        team_id=team.id,
                    )
                    session.add(user)
                    support_created += 1

        logger.info(f"  + Created {support_created} support staff users")

        # 4. Create managers (1 per team)
        managers_created = 0
        for team in teams:
            # Use full team name slug to avoid duplicates
            team_slug = slugify("_".join(team.name.split()[:2]))  # First two words
            email = f"yonetici_{team_slug}@sosoft.com"
            if email not in existing_users:
                user = User(
                    name=f"{team.name} Yönetici",
                    email=email,
                    phone_number=generate_phone_number(),
                    password_hash=hash_password("test123!"),
                    role=UserRole.MANAGER,
                    is_verified=True,
                    is_active=True,
                    team_id=team.id,
                )
                session.add(user)
                managers_created += 1

        logger.info(f"  + Created {managers_created} manager users")

        await session.commit()

        # Refresh user lists
        result = await session.execute(
            select(User).where(User.role == UserRole.CITIZEN)
        )
        users_by_role["citizens"] = list(result.scalars().all())

        result = await session.execute(
            select(User).where(User.role == UserRole.SUPPORT)
        )
        users_by_role["support"] = list(result.scalars().all())

        result = await session.execute(
            select(User).where(User.role == UserRole.MANAGER)
        )
        users_by_role["managers"] = list(result.scalars().all())

    total = sum(len(v) for v in users_by_role.values())
    logger.info(
        f"✅ {total} users ready ({len(users_by_role['citizens'])} citizens, "
        f"{len(users_by_role['support'])} support, {len(users_by_role['managers'])} managers)"
    )
    return users_by_role


async def seed_tickets(
    num_tickets: int,
    categories: dict[str, Category],
    teams: list[Team],
    users: dict[str, list[User]],
) -> None:
    """Seed tickets with full history (status logs, feedback, escalations, comments)."""
    logger.info(f"📋 Seeding {num_tickets} tickets with full history...")

    # Status distribution: NEW=15%, IN_PROGRESS=30%, ESCALATED=10%, RESOLVED=35%, CLOSED=10%
    status_weights = {
        TicketStatus.NEW: 15,
        TicketStatus.IN_PROGRESS: 30,
        TicketStatus.ESCALATED: 10,
        TicketStatus.RESOLVED: 35,
        TicketStatus.CLOSED: 10,
    }
    statuses = list(status_weights.keys())
    weights = list(status_weights.values())

    citizens = users["citizens"]
    support_staff = users["support"]
    managers = users["managers"]
    all_staff = support_staff + managers

    category_list = list(categories.values())

    # Build district->coordinate lookup
    district_coords = {d["name"]: d for d in ISTANBUL_DISTRICTS}

    async with async_session_maker() as session:
        # Pre-load team relationships for assignment logic
        result = await session.execute(
            select(Team).options(
                selectinload(Team.team_categories),
                selectinload(Team.team_districts).selectinload(TeamDistrict.district),
            )
        )
        teams_with_rels = list(result.scalars().all())

        tickets_created = 0
        feedback_created = 0
        escalations_created = 0
        comments_created = 0

        for i in range(num_tickets):
            # Select random data
            reporter = random.choice(citizens)
            category = random.choice(category_list)
            district_data = get_weighted_district()
            created_at = get_random_date()
            status = random.choices(statuses, weights=weights, k=1)[0]

            # Create location with slight coordinate variation
            lat_var = random.uniform(-0.003, 0.003)
            lng_var = random.uniform(-0.003, 0.003)
            location = Location(
                latitude=district_data["lat"] + lat_var,
                longitude=district_data["lng"] + lng_var,
                address=f"{district_data['name']} Mahallesi, Istanbul",
                district=district_data["name"],
                city="Istanbul",
                coordinates=f"POINT({district_data['lng'] + lng_var} {district_data['lat'] + lat_var})",
            )
            session.add(location)
            await session.flush()

            # Find appropriate team (category + district match)
            # Prefer specialized teams over the fallback "İstanbul Genel Ekip"
            assigned_team = None
            candidates = []
            fallback_team = None

            # Separate fallback team from specialized teams
            specialized_teams = []
            for team in teams_with_rels:
                if "Genel" in team.name:
                    fallback_team = team
                else:
                    specialized_teams.append(team)

            # First try: category + district match (specialized teams only)
            for team in specialized_teams:
                cat_match = any(
                    tc.category_id == category.id for tc in team.team_categories
                )
                dist_match = any(
                    td.district and td.district.name == district_data["name"]
                    for td in team.team_districts
                )
                if cat_match and dist_match:
                    candidates.append(team)

            # Second try: category match only (specialized teams only)
            if not candidates:
                candidates = [
                    t
                    for t in specialized_teams
                    if any(tc.category_id == category.id for tc in t.team_categories)
                ]

            # Third try: district match only (specialized teams only)
            if not candidates:
                candidates = [
                    t
                    for t in specialized_teams
                    if any(
                        td.district and td.district.name == district_data["name"]
                        for td in t.team_districts
                    )
                ]

            # Last resort: use fallback team
            if not candidates:
                candidates = [fallback_team] if fallback_team else specialized_teams

            assigned_team = random.choice(candidates)

            # Create ticket
            ticket = Ticket(
                title=random.choice(TICKET_TITLES_TR),
                description=random.choice(TICKET_DESCRIPTIONS_TR),
                category_id=category.id,
                location_id=location.id,
                reporter_id=reporter.id,
                team_id=assigned_team.id,
                status=status,
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(ticket)
            await session.flush()
            tickets_created += 1

            # Auto-follow by reporter
            follower = TicketFollower(
                ticket_id=ticket.id, user_id=reporter.id, followed_at=created_at
            )
            session.add(follower)

            # Create status log: NEW
            log_new = StatusLog(
                ticket_id=ticket.id,
                old_status=None,
                new_status=TicketStatus.NEW.value,
                changed_by_id=reporter.id,
                created_at=created_at,
            )
            session.add(log_new)

            # Process status transitions
            if status != TicketStatus.NEW:
                staff = random.choice(all_staff)
                hours_to_progress = random.randint(1, 48)
                in_progress_at = created_at + timedelta(hours=hours_to_progress)

                # Log: IN_PROGRESS
                log_progress = StatusLog(
                    ticket_id=ticket.id,
                    old_status=TicketStatus.NEW.value,
                    new_status=TicketStatus.IN_PROGRESS.value,
                    changed_by_id=staff.id,
                    created_at=in_progress_at,
                )
                session.add(log_progress)
                ticket.updated_at = in_progress_at

                # Add comment (30% chance)
                if random.random() < 0.30:
                    comment = Comment(
                        ticket_id=ticket.id,
                        user_id=staff.id,
                        content=random.choice(COMMENT_TEMPLATES_TR),
                        is_internal=random.random() < 0.3,  # 30% internal
                        created_at=in_progress_at
                        + timedelta(minutes=random.randint(5, 120)),
                    )
                    session.add(comment)
                    comments_created += 1

                # Handle RESOLVED or CLOSED
                if status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
                    hours_to_resolve = random.randint(2, 72)
                    resolved_at = in_progress_at + timedelta(hours=hours_to_resolve)
                    ticket.resolved_at = resolved_at
                    ticket.updated_at = resolved_at

                    # Log: RESOLVED
                    log_resolved = StatusLog(
                        ticket_id=ticket.id,
                        old_status=TicketStatus.IN_PROGRESS.value,
                        new_status=TicketStatus.RESOLVED.value,
                        changed_by_id=staff.id,
                        created_at=resolved_at,
                    )
                    session.add(log_resolved)

                    # If CLOSED, add another transition
                    if status == TicketStatus.CLOSED:
                        closed_at = resolved_at + timedelta(days=random.randint(1, 7))
                        ticket.updated_at = closed_at
                        log_closed = StatusLog(
                            ticket_id=ticket.id,
                            old_status=TicketStatus.RESOLVED.value,
                            new_status=TicketStatus.CLOSED.value,
                            changed_by_id=staff.id,
                            created_at=closed_at,
                        )
                        session.add(log_closed)

                    # Add feedback (80% of resolved/closed tickets)
                    if random.random() < 0.80:
                        feedback_at = (ticket.resolved_at or resolved_at) + timedelta(
                            days=random.randint(1, 5)
                        )
                        feedback = Feedback(
                            ticket_id=ticket.id,
                            user_id=reporter.id,
                            rating=get_rating_weighted(),
                            comment=random.choice(FEEDBACK_COMMENTS_TR)
                            if random.random() < 0.7
                            else None,
                            created_at=feedback_at,
                        )
                        session.add(feedback)
                        feedback_created += 1

                # Handle ESCALATED
                elif status == TicketStatus.ESCALATED:
                    hours_to_escalate = random.randint(4, 48)
                    escalated_at = in_progress_at + timedelta(hours=hours_to_escalate)
                    ticket.updated_at = escalated_at

                    # Log: ESCALATED
                    log_escalated = StatusLog(
                        ticket_id=ticket.id,
                        old_status=TicketStatus.IN_PROGRESS.value,
                        new_status=TicketStatus.ESCALATED.value,
                        changed_by_id=staff.id,
                        created_at=escalated_at,
                    )
                    session.add(log_escalated)

                    # Create escalation request
                    escalation = EscalationRequest(
                        ticket_id=ticket.id,
                        requester_id=staff.id,
                        reason=random.choice(ESCALATION_REASONS_TR),
                        status=EscalationStatus.PENDING,
                        created_at=escalated_at,
                    )

                    # 60% of escalations are processed
                    if random.random() < 0.60:
                        reviewer = random.choice(managers)
                        escalation.reviewer_id = reviewer.id
                        escalation.status = random.choice(
                            [EscalationStatus.APPROVED, EscalationStatus.REJECTED]
                        )
                        escalation.reviewed_at = escalated_at + timedelta(
                            hours=random.randint(1, 24)
                        )
                        escalation.review_comment = "İncelendi ve değerlendirildi."

                    session.add(escalation)
                    escalations_created += 1

            # Progress logging
            if (i + 1) % 50 == 0:
                logger.info(f"  Progress: {i + 1}/{num_tickets} tickets created...")
                await session.commit()

        await session.commit()

    logger.info(f"✅ Created {tickets_created} tickets")
    logger.info(f"   - {feedback_created} feedback records")
    logger.info(f"   - {escalations_created} escalation requests")
    logger.info(f"   - {comments_created} comments")


# =============================================================================
# MAIN ORCHESTRATION
# =============================================================================


async def main(clear: bool = False, num_tickets: int = 300) -> None:
    """Main seed function that orchestrates all seeding operations."""
    logger.info("=" * 60)
    logger.info("🌱 SoSoft Demo Data Seeding")
    logger.info("=" * 60)
    logger.info("")

    start_time = datetime.now()

    # Ensure tables exist
    logger.info("📊 Ensuring database tables exist...")
    await create_tables()
    logger.info("")

    # Clear existing data if requested
    if clear:
        await clear_demo_data()

    # Seed in order (respecting dependencies)
    categories = await seed_categories()
    logger.info("")

    districts = await seed_districts()
    logger.info("")

    teams = await seed_teams(categories, districts)
    logger.info("")

    users = await seed_users(teams)
    logger.info("")

    await seed_tickets(num_tickets, categories, teams, users)
    logger.info("")

    # Summary
    elapsed = datetime.now() - start_time
    logger.info("=" * 60)
    logger.info("🎉 Demo data seeding complete!")
    logger.info("=" * 60)
    logger.info(f"⏱️  Total time: {elapsed.total_seconds():.1f} seconds")
    logger.info("")
    logger.info("📝 Default login credentials:")
    logger.info("   Manager:  manager@sosoft.com / manager123!")
    logger.info("   Support:  support@sosoft.com / support123!")
    logger.info("   Citizen:  citizen@sosoft.com / citizen123!")
    logger.info("")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed demo data for SoSoft Neighborhood Issue Tracker"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing demo data before seeding (preserves categories, districts, default users)",
    )
    parser.add_argument(
        "--tickets",
        type=int,
        default=300,
        help="Number of tickets to create (default: 300)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(clear=args.clear, num_tickets=args.tickets))
