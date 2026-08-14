# Sir Device

A mobile-first marketplace for devices, mobile plans and internet offers. The implementation is deliberately independent of any network-owned storefront: Sir Device is the primary brand and network names appear only as offer labels.

## Technology selected

- Python 3.12+
- FastAPI with server-rendered Jinja templates
- SQLAlchemy 2 for persistence
- Alembic for schema migrations
- PostgreSQL in Docker and SQLite for local development/tests
- Vanilla JavaScript and responsive CSS
- PayFast hosted-checkout adapter
- Local encrypted-volume-ready uploads or private Amazon S3 storage
- SMTP notification outbox

The project is structured into domain, application, infrastructure and presentation layers. Services have narrow responsibilities, infrastructure implementations sit behind ports, statuses and domain choices are centralised as enums, and environment-dependent values live in configuration.

## What is implemented

### Storefront

- Premium responsive homepage based on the supplied Sir Device direction
- Device, mobile-plan, internet and promotions catalogues
- Search and filters for network, category, brand, budget and use context
- Product/deal details with verification, expiry and approval notices
- Three-offer comparison stored in the browser
- Guest cart for eligible once-off products
- Checkout and order creation
- Hosted-payment redirect generation when PayFast is configured
- Contract application flow
- Secure application-document upload
- Business quotation flow
- Order, application and quote status lookup
- Customer registration, authentication and account area
- Support enquiry capture

### Administration

- Role-based administration dashboard
- Network, product, deal and banner management
- CSV and XLSX deal import with full-file validation before commit
- Idempotent deal updates using `source_key`
- Automatic unpublishing of expired deals
- Application and document review workspace
- Business quote workflow
- Order and payment workspace
- Support enquiry workspace
- Staff user and role creation
- Audit records for material administration actions
- Notification outbox and SMTP dispatcher

### Data and integration readiness

- No product, offer, customer, order or dashboard mock data is seeded
- The CSV template contains headers only
- Network records are data, not hard-coded database assumptions
- All money is stored in integer cents
- Orders store immutable product/deal snapshots
- Product specifications and structured form details use JSON where fields vary
- PostgreSQL-ready schema and Alembic setup
- Scheduled PostgreSQL backup container with configurable retention
- File-storage port with local and S3 implementations
- Payment-gateway port with PayFast implementation
- API endpoints for catalogue reads

## Important commercial behaviour

- Sir Device is not described as an authorised reseller.
- Published prices remain subject to confirmation and network approval.
- Contract submissions do not promise automatic approval.
- Direct checkout is restricted to eligible once-off deal types.
- Monthly network contract payments are not processed by the MVP.
- Direct Vodacom and MTN APIs, credit checks, live stock, activations and porting integrations are intentionally left for later phases.

## Quick start with SQLite

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.create_admin
uvicorn app.main:app --reload
```

Open `http://localhost:8000` and sign in with the administrator created by the script.

The default development configuration creates the SQLite schema automatically. Production should use migrations and set `AUTO_CREATE_SCHEMA=false`.

## Production Docker stack

Use `.env.docker.example` as the production-like Docker template. Copy it to `.env`, set a real `SECRET_KEY`, database password, domain, SMTP settings and payment credentials, then start the full stack:

```bash
cp .env.docker.example .env
# Windows PowerShell: Copy-Item .env.docker.example .env
docker compose up -d --build
```

The Compose stack includes:

- `database`: PostgreSQL 17 with a persistent volume
- `migrate`: one-shot Alembic migration gate
- `web`: non-root production image with two Uvicorn workers
- `notifications`: notification outbox dispatcher
- `inventory-sync`: Vodacom catalogue refresh worker
- `backup`: scheduled PostgreSQL custom-format backups

The web service does not create tables at startup. Migrations run before web and worker services become available. For a one-off environment file without copying it to `.env`, set `ENV_FILE` explicitly:

```bash
ENV_FILE=.env.docker.example docker compose --env-file .env.docker.example up -d --build
```

PowerShell:

```powershell
$env:ENV_FILE = '.env.docker.example'
docker compose --env-file .env.docker.example up -d --build
```

For AWS, run the web image on ECS/Fargate or another container platform, use RDS PostgreSQL instead of the Compose database container, and run migrations as a release task. Use S3 for private uploads and CloudFront/S3 for mirrored catalogue images.

Change all example passwords and secrets before deploying.

### Automated PostgreSQL backups

The Docker stack includes a `backup` service. It creates a compressed custom-format PostgreSQL dump when the stack starts and repeats on the configured interval. Backups are stored in the named `backups` volume and old dumps are removed according to `BACKUP_RETENTION_DAYS`.

```text
BACKUP_INTERVAL_SECONDS=86400
BACKUP_RETENTION_DAYS=14
```

Restore a selected dump only after testing the recovery process in a non-production environment:

```bash
docker compose run --rm backup pg_restore --clean --if-exists \
  --host=database --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" \
  /backups/<selected-backup>.dump
```

## Deal import

Use `data/deal-import-template.csv`, an equivalent `.xlsx` workbook, or download the CSV template from the administration catalogue page.

Every row must include a stable `source_key`. Re-importing the same key updates the existing deal instead of duplicating it. The importer validates the entire file before applying any row. If one row is invalid, no catalogue changes are committed.

Supported enum values are defined in `app/domain/enums.py`. Notable CSV values include:

- Categories: `smartphone`, `tablet`, `laptop`, `router`, `mobile_plan`, `sim_only`, `fibre`, `lte`, `5g`, `accessory`
- Deal types: `cash_purchase`, `device_contract`, `sim_only`, `internet`, `accessory`, `deposit`
- Stock: `in_stock`, `limited`, `preorder`, `out_of_stock`, `subject_to_confirmation`
- Use context: `personal`, `business`, `both`

Dates use ISO 8601. Prices use decimal rand values and are converted to cents.

Vodacom inventory is refreshed immediately when the Docker inventory worker starts and then on the configured interval. Manual refreshes are safe to run repeatedly:

```bash
python -m scripts.sync_vodacom_inventory
python -m scripts.sync_mtn_inventory data/mtn-contracts-ready.csv --prepared --import
```

Each command upserts only its own network. An MTN import does not remove Vodacom inventory.

## Payment setup

The checkout adapter fails closed when credentials or endpoints are absent. Orders are still saved as `awaiting_payment`, allowing finance to follow up without pretending that a payment completed.

Configure these values using the current settings supplied by the payment provider:

```text
PAYFAST_MERCHANT_ID=
PAYFAST_MERCHANT_KEY=
PAYFAST_PASSPHRASE=
PAYFAST_PROCESS_URL=
PAYFAST_VALIDATE_URL=
PAYFAST_ALLOWED_IPS=
```

The adapter signs outgoing requests, checks notification signatures, checks the paid amount, optionally restricts callback IPs and can call the configured validation endpoint. Production must use HTTPS and provider-approved callback configuration.

## Document storage

Development defaults to local private storage:

```text
UPLOAD_BACKEND=local
UPLOAD_DIRECTORY=./var/uploads
```

For S3:

```text
UPLOAD_BACKEND=s3
AWS_REGION=af-south-1
S3_BUCKET=your-private-bucket
```

The S3 implementation uses server-side encryption and presigned download URLs. Keep the bucket private and apply retention, malware scanning and lifecycle policies appropriate to POPIA and your legal advice.

## Notifications

Status changes enqueue notifications. Run the dispatcher from a scheduler or worker:

```bash
python -m scripts.send_notifications
```

SMTP configuration is in `.env.example`. The database outbox prevents the web request from depending on immediate email delivery.

## Tests and architecture checks

```bash
pytest -q
python scripts/check_file_sizes.py
```

The test suite checks public rendering without seed data, password/session security, atomic and idempotent CSV import, guest cart/checkout behaviour, and the under-500-line rule.

## Project structure

```text
app/
  domain/             enums, policies and ports
  application/        use-case services
  infrastructure/     database, repositories, storage, payments, email
  presentation/       routes, templates, CSS and JavaScript
alembic/               database migrations
data/                  header-only import template
scripts/               operational commands and database backup
 tests/                automated verification
```

## Before a real launch

The code provides a functional first system, but production launch still requires business-specific values and operational approval:

- confirmed reseller wording and partner permissions
- real network deal files, images and terms
- live contact details and WhatsApp number
- approved privacy, returns, delivery, cookie and POPIA documents
- payment merchant credentials and end-to-end sandbox certification
- email domain and SMTP configuration
- S3 security, malware scanning and retention controls
- backups, monitoring, HTTPS, secrets management and incident procedures
- accessibility and device/browser acceptance testing
- network-specific application document rules

No sample products or prices are silently presented as live inventory.
