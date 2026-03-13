# 🎮 LuckyDraw — Demo Gaming Platform

> **⚠️ IMPORTANT DISCLAIMER**: This is a **DEMO / SIMULATION** platform only.
> No real money is involved. All coins are virtual with zero monetary value.
> This platform is for entertainment and educational purposes only.
> It is not a gambling platform. No payments, no prizes, no real stakes.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.0, Django REST Framework |
| Database | PostgreSQL 16 |
| Queue/Cache | Redis 7 + Celery |
| Frontend | Django Templates + TailwindCSS CDN |
| Deployment | Docker + Docker Compose + Nginx + Gunicorn |
| Auth | JWT (SimpleJWT) + Session |

---

## Games

### 🎯 Wingo (1-Minute Rounds)
- Draw: Random number 0–9
- Color mapping: 0=Red+Violet, 5=Green+Violet, odd=Green, even=Red
- Bets: Number (9x), Color (2x/4.5x), Big/Small (2x)

### 🎲 K3 (3-Minute Rounds)
- Draw: 3 dice, each 1–6
- Bets: Total (varying odds up to 207x), Size, Parity, Triples, Doubles
- Totals 3 and 18 (triples) don't count for Big/Small

### 🔢 5D (5-Minute Rounds)
- Draw: 5 independent digits A–E (0–9 each)
- Bets: Position exact digit (9x), Total Big/Small (2x), Parity (2x), Exact Total (50x)

---

## Quick Start

### 1. Clone & Configure

```bash
git clone <repo>
cd gaming_platform
cp .env.example .env
# Edit .env with your values
```

### 2. Run with Docker Compose

```bash
docker-compose up --build -d
```

### 3. Initialize Database

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py setup_game_schedules
```

### 4. Access

| Service | URL |
|---------|-----|
| Frontend | http://localhost/ |
| Admin | http://localhost/admin/ |
| API | http://localhost/api/ |

---

## Development Setup (Local)

```bash
# Install Python deps
pip install -r requirements.txt

# Set up local PostgreSQL and Redis, then:
cp .env.example .env
# Set DB_HOST=localhost, REDIS_URL=redis://localhost:6379/0

# Migrate
python manage.py migrate --settings=config.settings.dev

# Create admin
python manage.py createsuperuser --settings=config.settings.dev

# Setup Celery schedules
python manage.py setup_game_schedules --settings=config.settings.dev

# Run Django
python manage.py runserver --settings=config.settings.dev

# Run Celery worker (separate terminal)
celery -A config.celery_app worker --loglevel=info

# Run Celery beat (separate terminal)
celery -A config.celery_app beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## Architecture

```
gaming_platform/
├── config/
│   ├── settings/
│   │   ├── base.py          # Shared settings
│   │   ├── dev.py           # Development
│   │   └── prod.py          # Production
│   ├── urls.py
│   ├── celery_app.py
│   └── wsgi.py
│
├── apps/
│   ├── users/               # Auth, referrals, profiles
│   ├── wallet/              # Demo wallet, transactions
│   └── games/
│       ├── wingo/           # 1-min color prediction
│       ├── k3/              # 3-dice game
│       └── five_d/          # 5-digit lottery
│
├── core/
│   ├── utils/               # Secure RNG, helpers
│   ├── services/            # WalletService (atomic ops)
│   └── middleware.py        # Request logging
│
├── templates/               # Django HTML templates
├── static/                  # CSS, JS, PWA manifest
└── docker/                  # Dockerfile, nginx.conf
```

Each game module has:
- `models.py` — Round + Bet models with DB constraints
- `engine.py` — Pure game logic (result generation, payout calculation)
- `services.py` — Business logic (atomic bets, round settlement)
- `views.py` — Template views
- `views_api.py` — REST API views
- `serializers.py` — DRF serializers
- `tasks.py` — Celery tasks (round timers)
- `admin.py` — Django admin
- `urls.py` / `urls_api.py` — URL routing

---

## API Endpoints

### Auth
```
POST /api/auth/register/     Register new user
POST /api/auth/login/        Get JWT tokens
POST /api/auth/token/refresh/ Refresh token
GET  /api/auth/profile/      User profile
GET  /api/auth/referrals/    Referral info
```

### Wallet
```
GET /api/wallet/balance/       Current balance
GET /api/wallet/transactions/  Transaction history
```

### Wingo
```
GET  /api/games/wingo/current/   Current round
GET  /api/games/wingo/history/   Completed rounds
POST /api/games/wingo/bet/       Place bet
GET  /api/games/wingo/my-bets/   User's bets
```

### K3
```
GET  /api/games/k3/current/
GET  /api/games/k3/history/
POST /api/games/k3/bet/
GET  /api/games/k3/my-bets/
```

### 5D
```
GET  /api/games/5d/current/
GET  /api/games/5d/history/
POST /api/games/5d/bet/
GET  /api/games/5d/my-bets/
```

---

## Admin Features

Visit `/admin/` to:
- **Manage users** — block/unblock, view referrals
- **Wallet admin** — Credit user demo wallets (no real money)
- **Round history** — View all game rounds and results
- **Bet history** — View all bets placed
- **Export CSV** — Wallets and transactions
- **Game schedules** — Control via Django Celery Beat

### Credit a User's Wallet (Admin)
1. Go to Admin → Wallet → Select wallet
2. Click "Credit" action or navigate to the credit URL
3. Enter amount and description
4. This is tracked as `ADMIN_CREDIT` in transactions

---

## Security Features

- CSRF protection on all forms
- JWT tokens with rotation and blacklisting
- Rate limiting on all endpoints (10 bets/min, 100 API calls/min)
- Anti double-bet DB constraints (unique per user/round/type/value)
- `select_for_update()` row-level locking on wallet operations
- `ATOMIC_REQUESTS = True` for DB transaction integrity
- Cryptographically secure RNG (`secrets` module)
- Server-side bet locking 5 seconds before round ends
- All bet values validated server-side
- Logging middleware for all requests

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | False |
| `DB_*` | PostgreSQL config | Required |
| `REDIS_URL` | Redis connection | Required |
| `DEMO_SIGNUP_BONUS` | Coins on registration | 1000 |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | JWT expiry | 60 |

---

## Compliance Notes

This platform is designed with compliance in mind:

1. **No real money** — Only virtual demo coins
2. **No payment gateways** — Admin-only balance management
3. **Full audit trail** — All transactions logged with references
4. **Transparent RNG** — Seed hashes stored for verification
5. **Demo disclaimer** — Shown prominently across the entire UI
6. **Modular design** — Can be extended with proper licensing for regulated markets

---

## License

MIT — For educational and demonstration purposes only.
This codebase must not be deployed as a real-money gambling platform without proper licensing.
