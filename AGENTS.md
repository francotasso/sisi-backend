# SISI Backend — AI Agent Documentation

## Stack

- **Runtime:** Python 3.14 (local), 3.12 (Docker)
- **Framework:** FastAPI + Uvicorn
- **ORM:** SQLAlchemy 2.0 async
- **DB:** PostgreSQL 16 (asyncpg), SQLite (tests with aiosqlite)
- **Auth:** Supabase Auth (JWK + HS256/ES256)
- **Migrations:** Alembic (async)
- **File upload:** Cloudinary (images)
- **Testing:** pytest + pytest-asyncio + respx + httpx.AsyncClient

## Project structure

```
sisi-backend/
├── .env                    # Environment variables (untracked)
├── .env.example            # Env vars template
├── .gitignore
├── .dockerignore
├── AGENTS.md               # This file
├── alembic.ini             # Alembic config
├── docker-compose.yml      # PostgreSQL + API
├── Dockerfile              # Multi-stage build
├── pyproject.toml          # Project metadata
├── pytest.ini              # asyncio_mode = auto
├── requirements.txt        # Dependencies
├── alembic/
│   ├── env.py              # Async Alembic config
│   ├── script.py.mako
│   └── versions/           # Migrations
│       ├── d956a19850bb_initial.py
│       ├── 11c1409893d5_add_discount_price_and_best_seller.py
│       ├── 586632952440_add_discount_price_and_best_seller.py
│       └── 70429d506162_feat_add_missing_indexes_pool_config_.py
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI app, middleware, routers
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── router.py   # Registers all modules
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py       # pydantic-settings (from .env)
│   │   ├── database.py     # Engine, session, Base, mixins
│   │   ├── exceptions.py   # NotFoundError, DuplicateError, ValidationError
│   │   ├── logging_config.py
│   │   ├── security.py     # JWT verification (HS256 + ES256/JWKS)
│   │   └── storage.py      # CloudinaryService (upload/delete)
│   ├── middleware/
│   │   └── logging.py      # LoggingMiddleware (method, path, status, time)
│   └── modules/
│       ├── auth/           # Authentication & users
│       │   ├── models.py   # (no local model, uses Supabase)
│       │   ├── schemas.py  # Login/Register/User CRUD
│       │   └── router.py   # 5 auth endpoints
│       ├── categories/     # Product categories
│       │   ├── models.py   # Category
│       │   ├── repository.py
│       │   ├── schemas.py  # CategoryCreate/Update/Response
│       │   ├── service.py  # Slug gen., duplicate check
│       │   └── router.py   # 5 endpoints
│       ├── products/       # Products with specs, FAQs, bulk, image upload
│       │   ├── models.py   # Product, ProductSpec, ProductFAQ
│       │   ├── repository.py
│       │   ├── schemas.py  # Create/Update/Detail/List/Bulk/Export
│       │   ├── service.py  # Slug, image upload/delete, bulk ops
│       │   └── router.py   # 9 endpoints
│       ├── store/          # Store singleton with nested contact/hours/social
│       │   ├── models.py   # Store, StoreContact, StoreHour, StoreSocialMedia
│       │   ├── repository.py
│       │   ├── schemas.py  # Nested create/update/response
│       │   ├── service.py  # Singleton enforcement
│       │   └── router.py   # 3 endpoints
│       └── testimonials/   # Public testimonials
│           ├── models.py   # Testimonial
│           ├── repository.py
│           ├── schemas.py  # TestimonialCreate/Response
│           ├── service.py
│           └── router.py   # 4 endpoints
└── tests/
    ├── conftest.py         # Fixtures: SQLite engine, auth overrides, data factories
    ├── test_auth.py        # 8 tests (login, register, list, update, delete, unauth)
    ├── test_categories.py  # 11 tests
    ├── test_products.py    # 17 tests (incl. image upload)
    ├── test_store.py       # 6 tests
    └── test_testimonials.py# 9 tests
```

## Endpoints (prefix: `/api/v1`)

### Auth (`/auth`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | — | Login with email+password, returns access_token |
| POST | `/auth/register` | admin | Create user via Supabase Admin API |
| GET | `/auth/users` | admin | List all users |
| PUT | `/auth/users/{user_id}` | admin | Update user (email, password, name, metadata) |
| DELETE | `/auth/users/{user_id}` | admin | Delete user |

### Categories (`/categories`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/categories` | — | List all categories |
| GET | `/categories/{id}` | — | Get category by ID |
| POST | `/categories` | admin | Create category |
| PUT | `/categories/{id}` | admin | Update category |
| DELETE | `/categories/{id}` | admin | Delete category |

### Products (`/products`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/products` | — | List products (filters: category, price_min, price_max, stock, search; sort: price/name/created_at; pagination: skip/limit) |
| GET | `/products/export` | — | Export all products |
| GET | `/products/{slug}` | — | Get product by slug |
| POST | `/products` | editor | Create product (with specs and faqs) |
| PUT | `/products/{id}` | editor | Update product (deletes Cloudinary img if image changes) |
| DELETE | `/products/{id}` | editor | Soft-delete product |
| POST | `/products/bulk` | editor | Bulk create (max 500 items, no duplicates) |
| PUT | `/products/bulk` | editor | Replace all (hard delete + bulk create) |
| POST | `/products/{id}/image` | editor | Upload image to Cloudinary (multipart, types: jpeg/png/webp/gif, max 5MB) |

### Store (`/store`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/store` | — | Get store (singleton). 404 if not exists |
| POST | `/store` | admin | Create store with nested contact/hours/social_media |
| PUT | `/store` | admin | Update store (replaces nested relations completely) |

### Testimonials (`/testimonials`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/testimonials` | — | List testimonials (paginated) |
| GET | `/testimonials/{id}` | — | Get testimonial by ID |
| POST | `/testimonials` | — | Create testimonial (public, no auth) |
| DELETE | `/testimonials/{id}` | admin | Delete testimonial |

## Env vars (`.env`)

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sisi_db
DATABASE_ECHO=false
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
DB_POOL_RECYCLE=3600

# Supabase Auth
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# App
CORS_ORIGINS=["*"]
LOG_LEVEL=INFO
```

MAX_IMAGE_SIZE default: 5_242_880 (5MB)

## Auth

- **Two roles:** `admin` and `editor`
- `verify_admin_token` → admin only
- `verify_editor_access` → admin or editor
- JWT verification: first HS256 with SUPABASE_JWT_SECRET, fallback to ES256 with JWKS from `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`
- Endpoints without auth: list/get for products, categories, store, testimonials; POST testimonials; POST login
- In tests, mocked via `app.dependency_overrides`

## Testing

### Configuration
- `pytest.ini`: `asyncio_mode = auto`, `testpaths = tests`
- DB: SQLite + aiosqlite (no local PostgreSQL needed)
- Auth: dependency overrides returning fake payloads
- Supabase: mocked with `respx` (intercepts `*.supabase.co/auth/v1/*`)
- Cloudinary: mocked with `unittest.mock.patch('cloudinary.uploader.upload')`

### Main fixtures (`tests/conftest.py`)
| Fixture | Scope | Description |
|---------|-------|-------------|
| `engine` | session | SQLite async engine with WAL+FK |
| `tables` | session | create_all / drop_all |
| `db_session` | function | Session with auto rollback |
| `override_get_db` | function | Dependency override |
| `client` | function | AsyncClient with admin+editor auth |
| `editor_client` | function | AsyncClient with editor auth only |
| `client_no_auth` | function | AsyncClient without auth |
| `mock_supabase_auth` | function | respx mock for auth/v1 |
| `category` | function | Persisted Category |
| `product` | function | Persisted Product with category |
| `store_data` | function | Store dict for POST/PUT |

### Tests by module

| File | Tests | Coverage |
|---------|-------|-----------|
| `test_auth.py` | 8 | login success/failure, register success/duplicate, list users, update user, delete user, unauthorized access |
| `test_categories.py` | 11 | list empty/with-data, get by id/not-found, create, duplicate name→409, invalid→422, update, update not-found, delete, delete not-found |
| `test_products.py` | 17 | list empty/with-data/pagination, get by slug/not-found, create, create with specs+faqs, invalid→422, update, update not-found, soft delete, soft delete not-found, export, bulk create, bulk replace, upload image, upload invalid type→422, upload product not found→404 |
| `test_store.py` | 6 | get empty→404, create with nested, get with data, update, update nested, create twice→404 |
| `test_testimonials.py` | 9 | list empty/with-data, create, invalid rating→422, get by id/not-found, delete, delete not-found |

**Total: 51 tests**

### How to run tests
```bash
pytest tests/ -v --tb=short          # All
pytest tests/test_products.py -v --tb=short   # Products only
```

## Cloudinary

### Config (`app/core/storage.py`)
- `ALLOWED_CONTENT_TYPES`: `image/jpeg`, `image/png`, `image/webp`, `image/gif`
- `CloudinaryService.upload(file, folder="products")` → validates type and size, uploads, returns `secure_url`
- `CloudinaryService.delete(url)` → extracts public_id from Cloudinary URL, destroys. If URL is not from Cloudinary, does nothing
- `CloudinaryService.extract_public_id(url)` → extracts public_id from a Cloudinary URL
- SDK config is done at module import with `cloudinary.config()`

### Delete behavior
- `POST /products/{id}/image` → deletes previous Cloudinary image if it existed, then uploads the new one
- `PUT /products/{id}` with `image` in body → deletes previous Cloudinary image if it existed and the new URL is different
- `PUT /products/{id}` with `image: null` → does not delete (field is set to null)
- `cloudinary_service.delete()` is safe: if the previous URL was manual (not from Cloudinary), it does nothing

## Data models

### Category
- `id` UUID PK, `created_at`, `updated_at` (TimestampMixin)
- `name` VARCHAR(255) unique, `slug` VARCHAR(255) unique indexed

### Product
- `id` UUID PK, `created_at`, `updated_at`, `deleted_at` (TimestampMixin + SoftDeleteMixin)
- `name` VARCHAR(255) indexed, `slug` VARCHAR(255) unique indexed
- `price` NUMERIC(10,2), `discount_price` NUMERIC(10,2) nullable, `best_seller` BOOLEAN
- `category_id` UUID FK → categories
- `image` VARCHAR(500) nullable
- `description` TEXT nullable, `short_description` VARCHAR(500) nullable
- `stock` BOOLEAN, `stock_count` INTEGER, `sku` VARCHAR(100) unique nullable
- Relationships: `specs` (ProductSpec, uselist=False), `faqs` (ProductFAQ list), `category`
- **Partial indexes** (deleted_at IS NULL): `ix_products_active_slug`, `ix_products_active_category_price`
- **Composite indexes**: `ix_products_category_price`, `ix_products_stock_price`

### ProductSpec
- `product_id` UUID FK unique → products, plus specific fields (brand, finish, size, ingredients, etc.)

### ProductFAQ
- `product_id` UUID FK → products, `question`, `answer`

### Store + StoreContact + StoreHour + StoreSocialMedia
- Store singleton: only one row (controlled by service)
- Contact: uselist=False, one-to-one
- Hours: list, day+open_time+close_time+is_closed
- SocialMedia: list, platform+url

### Testimonial
- `name`, `text`, `rating` (1-5), `avatar` nullable

## Best practices & rules

### Code
- No comments in code (unless explicitly asked)
- `from __future__ import annotations` for forward references
- Always use type hints
- UUIDs are passed as strings in JSON (FastAPI handles it automatically)
- Response schemas use `model_config = ConfigDict(from_attributes=True)`

### Async SQLAlchemy
- Always use `await db.execute()`, `await db.flush()`, `await db.refresh()`
- After `flush()`: refresh simple columns with `await db.refresh(product)`, then relationships with `await db.refresh(product, ["category", "specs", "faqs"])`
- Lazy-loaded relationships don't work in async context → use `joinedload()` in queries or explicit `refresh()`
- `expire_on_commit=False` on the session factory

### Tests
- Each test module has its own class (e.g. `TestProducts`)
- Use `client` (with admin auth) as default fixture
- Use `client_no_auth` for 401 tests
- Mock Cloudinary: `with patch("cloudinary.uploader.upload") as mock: mock.return_value = {"secure_url": "..."}`
- Don't mock `cloudinary_service.delete()` — it's safe to call (does nothing if URL is not from Cloudinary)
- Imports of uuid4, patch, etc. inside each test or at the top of the file as needed
- Fixtures return model objects (not schemas)
- `await db_session.flush()` to persist without commit

### Migrations
- `alembic revision --autogenerate -m "message"`
- `alembic upgrade head`
- Migrations are tracked in git (not in .gitignore)
