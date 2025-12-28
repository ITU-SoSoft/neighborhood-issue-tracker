# Load Testing Guide

Bu dokümantasyon, Neighborhood Issue Tracker API için load testing yapılandırmasını açıklar.

## 🛠️ Kurulum

```bash
# Load testing bağımlılıklarını yükle
cd backend
pip install -r requirements-loadtest.txt
```

## 🗂️ Test Kullanıcıları Oluşturma

Load testleri çalıştırmadan önce test kullanıcılarını oluşturun:

```bash
cd backend
python -m loadtests.seed_test_users
```

Bu komut şu kullanıcıları oluşturur:
| Kullanıcı | Email | Şifre | Rol |
|-----------|-------|-------|-----|
| Citizen | loadtest_citizen@example.com | LoadTest123! | citizen |
| Support | loadtest_support@example.com | LoadTest123! | support |
| Manager | loadtest_manager@example.com | LoadTest123! | manager |

## 🚀 Testleri Çalıştırma

### Web UI ile (Önerilen)

```bash
cd backend
locust -f loadtests/locustfile.py --host=http://localhost:8000
```

Tarayıcıda http://localhost:8089 adresine gidin.

### Headless Mode (CI/CD için)

```bash
# Light load - 10 kullanıcı
locust -f loadtests/locustfile.py --headless \
  -u 10 -r 2 -t 60s \
  --host=http://localhost:8000 \
  --csv=results/light_test

# Medium load - 50 kullanıcı
locust -f loadtests/locustfile.py --headless \
  -u 50 -r 5 -t 120s \
  --host=http://localhost:8000 \
  --csv=results/medium_test

# Heavy load - 100 kullanıcı
locust -f loadtests/locustfile.py --headless \
  -u 100 -r 10 -t 180s \
  --host=http://localhost:8000 \
  --csv=results/heavy_test \
  --html=results/heavy_test_report.html
```

### 🐳 Docker ile Production'a Karşı Test

```bash
cd backend

# Container'ları başlat (4 worker ile)
docker compose -f docker-compose.loadtest.yml up --build

# Tarayıcıda http://localhost:8089 aç
# Target host otomatik olarak https://api.help.sagbas.io
```

**Worker sayısını artırmak için:**
```bash
docker compose -f docker-compose.loadtest.yml up --build --scale locust-worker=8
```

**Headless mode (container):**
```bash
docker compose -f docker-compose.loadtest.yml run --rm locust-master \
  locust -f loadtests/locustfile.py --headless \
  -u 100 -r 10 -t 180s \
  --host=https://api.help.sagbas.io \
  --csv=results/prod_test \
  --html=results/prod_report.html
```

### Parametreler

| Parametre | Açıklama |
|-----------|----------|
| `-u` | Toplam kullanıcı sayısı |
| `-r` | Spawn rate (saniyede kaç kullanıcı başlatılacak) |
| `-t` | Test süresi (örn: 60s, 5m, 1h) |
| `--csv` | CSV çıktı prefix'i |
| `--html` | HTML rapor dosyası |

## 📊 Test Senaryoları

### 1. CitizenUser (weight: 5)
Vatandaş kullanıcı davranışlarını simüle eder:
- ✅ Ticket oluşturma (ağırlık: 10)
- ✅ Kendi ticketlarını görüntüleme (ağırlık: 3)
- ✅ Ticket detayı görüntüleme (ağırlık: 2)
- ✅ Yorum ekleme (ağırlık: 1)

### 2. SupportUser (weight: 3)
Destek personeli davranışlarını simüle eder:
- ✅ Ticket listeleme (ağırlık: 5)
- ✅ Ticket durumu güncelleme (ağırlık: 8)
- ✅ Ticket atama (ağırlık: 3)
- ✅ Atanmış ticketları görüntüleme (ağırlık: 2)

### 3. ManagerUser (weight: 1)
Yönetici analytics davranışlarını simüle eder:
- ✅ Dashboard KPIs (ağırlık: 10)
- ✅ Ticket heatmap (ağırlık: 8)
- ✅ Takım performansı (ağırlık: 5)
- ✅ Kategori istatistikleri (ağırlık: 5)
- ✅ Mahalle istatistikleri (ağırlık: 4)
- ✅ Feedback trendleri (ağırlık: 3)

## 📈 Metrikler

### Locust Çıktıları

| Metrik | Açıklama |
|--------|----------|
| **RPS** | Saniyedeki request sayısı |
| **Response Time** | min/avg/max/median/95th percentile (ms) |
| **Failure Rate** | Başarısız request yüzdesi |
| **# Users** | Anlık aktif kullanıcı sayısı |

### CSV Dosyaları

Test tamamlandığında oluşan dosyalar:

```
results/
├── test_run_stats.csv          # Genel istatistikler
├── test_run_stats_history.csv  # Zaman serisi verileri
├── test_run_failures.csv       # Hata detayları
└── test_run_exceptions.csv     # Exception'lar
```

### Örnek Metrik Çıktısı

```
Name                          # reqs    # fails  Avg    Min    Max   Median  req/s
----------------------------------------------------------------------------------
[Ticket] Create Ticket          1523      12    234     45   1823    180    12.5
[Ticket] Update Status           892       3    156     32    987    120     7.3
[Analytics] Dashboard KPIs       234       0    567     89   2345    450     1.9
----------------------------------------------------------------------------------
Total                          2649      15    287     32   2345    180    21.7
```

## 🎯 Performans Hedefleri

Önerilen kabul kriterleri:

| Metrik | Hedef |
|--------|-------|
| Avg Response Time | < 500ms |
| 95th Percentile | < 2000ms |
| Failure Rate | < 1% |
| Min RPS (100 user) | > 50 req/s |

## 🔧 Konfigürasyon

`loadtests/config.py` dosyasında ayarlar değiştirilebilir:

```python
# Farklı yük seviyeleri
SPAWN_RATES = {
    "light": {"users": 10, "spawn_rate": 2},
    "medium": {"users": 50, "spawn_rate": 5},
    "heavy": {"users": 100, "spawn_rate": 10},
    "stress": {"users": 200, "spawn_rate": 20},
}
```

## ⚠️ Önemli Notlar

1. **Test ortamı kullanın** - Production veritabanında test yapmayın
2. **Rate limiting** - API rate limiting'i geçici olarak devre dışı bırakın
3. **Monitoring** - Test sırasında CPU/RAM/DB connection'ları izleyin
4. **Cleanup** - Test sonrası oluşan verileri temizleyin
