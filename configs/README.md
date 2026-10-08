# Company Configurations

This directory contains JSON configuration files for each company that can use the Proformas-Empresas application.

## Structure

```
configs/companies/
??? schema.json                  # JSON Schema for validation
??? jc-services.json            # Configuration for J&C Services
??? example-company.json        # Template for new companies
```

## How to Add a New Company

### Step 1: Create Configuration File

Copy `example-company.json` and rename it with your company ID (lowercase, hyphenated):

```bash
cp example-company.json my-company-name.json
```

### Step 2: Fill Required Fields

Update all fields in your new JSON file:

- **company_id**: Unique identifier (lowercase, hyphens only) - must match filename
- **company_name**: Full legal name
- **payment_bcp_account**: BCP account number
- **payment_bcp_cci**: CCI (Código de Cuenta Interbancaria)
- **payment_detracciones_account**: Detracciones account (can be empty)
- **payment_bank_label**: Display label for bank (e.g., "Cuenta Corriente BCP")
- **offer_note_primary**: Primary offer validity note
- **offer_note_secondary**: Secondary offer note
- **workshop_address**: Production/workshop address
- **fiscal_address**: Legal/fiscal address
- **header_image**: Path to company header image (relative to `static/assets/`)
- **watermark_image**: Path to company watermark (relative to `static/assets/`)

### Step 3: Prepare Assets

Create a directory for your company's images:

```
static/assets/companies/my-company-name/
??? header.png          # Company header (recommended: 1200x300px)
??? watermark.png       # Watermark (transparent PNG recommended)
```

### Step 4: Validate Configuration

The application will validate against `schema.json` on startup. Errors will show:
- Missing required fields
- Invalid company_id format
- Asset file not found

### Example

**configs/companies/acme-corp.json:**
```json
{
  "company_id": "acme-corp",
  "company_name": "ACME CORPORATION S.A.",
  "payment_bcp_account": "0011-1234-5678",
  "payment_bcp_cci": "ACME CORPORATION S.A.",
  "payment_detracciones_account": "",
  "payment_bank_label": "Cuenta en Soles BCP",
  "offer_note_primary": "Validez de la oferta: 30 dias",
  "offer_note_secondary": "Servicio incluye garantia",
  "workshop_address": "Zona Industrial Lote 5, Lima",
  "fiscal_address": "Jr. Comercio 789, Lima",
  "header_image": "companies/acme-corp/header.png",
  "watermark_image": "companies/acme-corp/watermark.png"
}
```

Then create assets at:
- `static/assets/companies/acme-corp/header.png`
- `static/assets/companies/acme-corp/watermark.png`

## Validation

All configurations must pass the JSON Schema validation defined in `schema.json`. 

Key rules:
- `company_id` must match `^[a-z0-9-]+$` pattern
- All required fields must be present
- No additional properties are allowed

## Default Company

Currently, `jc-services` is the default company used if no `company_id` is specified in requests.

To change the default, update `proforma_app/server.py` and `src/app.js`.

## Loading Configuration

In Python:
```python
from proforma_app.company_config import CompanyConfig
from pathlib import Path

config = CompanyConfig.from_json_file(
    Path("configs/companies/my-company-name.json")
)
```

In JavaScript:
```javascript
const response = await fetch("/api/config?company_id=my-company-name");
const config = await response.json();
```

## API Endpoints

- `GET /api/companies` — List all available companies
- `GET /api/config` — Get configuration for a company (default: `jc-services`)
- `GET /api/config?company_id=my-company-name` — Get specific company configuration
