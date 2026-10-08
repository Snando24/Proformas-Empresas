# Arquitectura: Sistema Multi-Empresa de Proformas

## Visión General

La aplicación Proformas-Empresas ha sido refactorizada de una solución específica para "J&C Services" a un **sistema multi-empresa adaptable** que puede ser usado por cualquier compañía.

### Cambio Fundamental

**ANTES:**
- Constantes hardcodeadas para J&C Services
- Imposible cambiar sin editar código
- Un archivo = una empresa

**AHORA:**
- Configuración externalizadas en JSON
- Múltiples empresas simultáneamente
- Agregar empresa = crear 1 archivo + 2 imágenes

---

## Componentes Principales

### 1. **Capa de Configuración** (`configs/companies/`)

Cada empresa tiene un archivo JSON con sus datos específicos:

```
configs/companies/
??? schema.json                    # Validación (no modificar)
??? jc-services.json             # Empresa 1
??? example-company.json          # Plantilla
??? [tu-empresa].json             # Nueva empresa
```

**Ejemplo:**
```json
{
  "company_id": "jc-services",
  "company_name": "MULTISERVICIOS Y REPRESENTACIONES J & C E.I.R.L.",
  "payment_bcp_account": "0011-0202-0100061544",
  "payment_bcp_cci": "MULTISERVICIOS Y REPRESENTACIONES J & C E.I.R.L.",
  "workshop_address": "Planta de Trabajo: Jr. Tarapaca S/N, Pilcomayo",
  "fiscal_address": "Domicilio: Jr. Tarapaca S/N, Pilcomayo",
  "...": "..."
}
```

### 2. **Backend: Sistema de Configuración** (Python)

#### `proforma_app/company_config.py` (NUEVO)
Dataclass que representa la configuración de una empresa:

```python
@dataclass
class CompanyConfig:
    company_id: str
    company_name: str
    payment_bcp_account: str
    payment_bcp_cci: str
    # ... más campos
    
    @classmethod
    def from_json_file(cls, config_path: Path) -> "CompanyConfig":
        """Cargar desde archivo JSON"""
    
    def to_dict(self) -> dict[str, Any]:
        """Convertir a diccionario (para API responses)"""
```

**Clave:** Toda la lógica de datos está aquí, separada del motor de generación.

#### `proforma_app/server.py` (ACTUALIZADO)
Nuevos endpoints:

```
GET /api/companies               ? Lista todas las empresas disponibles
GET /api/config?company_id=...   ? Obtiene config de una empresa
POST /api/export/pdf             ? Genera PDF con config de la empresa
POST /api/export/docx            ? Genera DOCX con config de la empresa
```

**Cambio clave:**
```python
# ANTES: Constantes globales
DEFAULT_PAYMENT_BCP_ACCOUNT = "0011-0202-0100061544"

# AHORA: Cargadas dinámicamente
company_config = CompanyConfig.from_json_file(config_path)
payment_account = company_config.payment_bcp_account
```

#### `proforma_app/document_engine.py` (REFACTORIZADO)
El motor de generación ahora recibe la configuración:

```python
@dataclass
class ProformaData:
    # ... campos del documento
    company_config: CompanyConfig  # ? NUEVA
    
    @classmethod
    def from_payload(cls, payload: dict) -> "ProformaData":
        # Cargar config según company_id en el payload
        company_id = payload.get("company_id", "jc-services")
        config = CompanyConfig.from_json_file(...)
        
        return cls(
            # ... datos
            company_config=config  # ? Pasar al dataclass
        )
```

### 3. **Frontend: Carga Dinámica** (JavaScript/HTML)

#### `src/app.js` (ACTUALIZADO)

Global dinámico para la configuración actual:

```javascript
// Cargado al iniciar
let currentCompanyConfig = null;
let currentCompanyId = "jc-services";

async function loadCompanyConfig(companyId = "jc-services") {
  const response = await fetch(`/api/config?company_id=${companyId}`);
  currentCompanyConfig = await response.json();
  return currentCompanyConfig;
}

// Inicializar al cargar
window.addEventListener('load', async () => {
  currentCompanyConfig = await loadCompanyConfig(currentCompanyId);
  updateUI();
});
```

**Valores dinámicos en el formulario:**
```javascript
// ANTES: Constantes hardcodeadas
const WORKSHOP_ADDRESS = "Planta de Trabajo: Jr. Tarapaca S/N...";

// AHORA: Del objeto de config
const workshopAddress = currentCompanyConfig?.workshop_address || "";
```

#### `static/index.html` (SIN CAMBIOS MAYORES)

El HTML permanece genérico. Selector de empresa puede agregarse más tarde:

```html
<!-- Futuro: selector dinámico -->
<select id="company-selector">
  <option value="jc-services">J&C Services</option>
  <option value="acme-corp">Acme Corporation</option>
</select>
```

### 4. **Assets de Empresa** (`static/assets/companies/`)

Estructura por empresa:

```
static/assets/companies/
??? jc-services/
?   ??? header_pintura.png
?   ??? header_generales.png
?   ??? watermark_general.png
?   ??? watermark_pintura.png
?   ??? config.json
??? example-company/
?   ??? header.png
?   ??? watermark.png
??? [nueva-empresa]/
    ??? header.png
    ??? watermark.png
```

**Mapeo en config JSON:**
```json
{
  "header_image": "companies/jc-services/header_pintura.png",
  "watermark_image": "companies/jc-services/watermark_general.png"
}
```

---

## Flujo de Generación de Documento

```
USUARIO (UI)
    ?
    ?? Rellena formulario
    ?? Selecciona empresa (future)
    ?? Click "Generar PDF"
            ?
            ?
POST /api/export/pdf
    ?
    ?? Recibe payload + company_id
    ???????????????????????????????????
                                      ?
                    ???????????????????
ProformaData.from_payload()
    ?
    ?? Valida empresa_id
    ?? Carga CompanyConfig
    ?? Valida datos del formulario
    ???????????????????????????????????
                                      ?
                    ???????????????????
build_pdf(data: ProformaData)
    ?
    ?? Accede data.company_config
    ?? Usa direcciones, datos bancarios
    ?? Carga imágenes de assets
    ?? Genera PDF personalizado
            ?
            ?
Archivo PDF descargado
    ?? Contiene datos de la empresa correcta
```

---

## Ciclo de Vida de Configuración

### 1. **Inicialización del Servidor**

```python
# app.py
from proforma_app.server import run_server
run_server()

# server.py ? Se carga lista de empresas disponibles
companies = _get_available_companies()
# ["jc-services", "acme-corp", ...]

# Se imprime en consola
print(f"Empresas disponibles: {', '.join(companies)}")
```

### 2. **Solicitud del Cliente**

```javascript
// Usuario selecciona/especifica empresa
const payload = {
  customer_name: "...",
  company_id: "acme-corp"  // ? Indica qué empresa
};

fetch('/api/export/pdf', {
  method: 'POST',
  body: JSON.stringify(payload)
});
```

### 3. **Validación en Backend**

```python
# server.py
def do_POST(self):
    payload = self._read_json_body()
    data = ProformaData.from_payload(payload)
    # ? Si company_id no existe ? ValueError
    # ? Si falta field requerido ? ValueError
```

### 4. **Generación del Documento**

```python
# document_engine.py
def build_pdf(data: ProformaData):
    # data.company_config contiene todo lo necesario
    pdf.drawString(data.company_config.workshop_address, ...)
    pdf.addImage(data.company_config.header_image, ...)
    # ...
    return output_file
```

---

## Estructura de Datos

### Payload del Cliente ? Servidor

```javascript
{
  customer_name: "Cliente XYZ",
  phone: "987654321",
  ruc: "10123456789",
  issue_date: "2026-10-08",
  
  document_kind: "proforma",
  tax_mode: "sin_igv",
  header_kind: "generales",
  watermark_kind: "proforma",
  
  summary: "Descripción del trabajo",
  items: [
    { description: "Item 1", amount: "1000.00" },
    { description: "Item 2", amount: "500.00" }
  ],
  advance_payments: [
    { payment_date: "2026-10-15", amount: "250.00" }
  ],
  
  company_id: "acme-corp",           // ? NUEVO
  show_payment_details: true,
  // Nota: datos bancarios vienen de config, no del cliente
}
```

### Respuesta de `/api/config`

```json
{
  "company_id": "acme-corp",
  "company_name": "ACME CORPORATION S.A.",
  "payment_bcp_account": "0011-9876-5432",
  "payment_bcp_cci": "ACME CORPORATION S.A.",
  "payment_detracciones_account": "00-123-456789",
  "payment_bank_label": "Cuenta Corriente BCP",
  "offer_note_primary": "Oferta válida por 60 días",
  "offer_note_secondary": "Incluye instalación",
  "workshop_address": "Zona Industrial Parque, Lima",
  "fiscal_address": "Jr. Comercial 999, Lima",
  "header_image": "companies/acme-corp/header.png",
  "watermark_image": "companies/acme-corp/watermark.png"
}
```

---

## Puntos de Integración

### Backend ? Frontend
- **GET `/api/config`** - Frontend carga datos de empresa
- **GET `/api/companies`** - Frontend lista empresas para selector (futuro)

### Frontend ? Backend
- **POST `/api/export/pdf`** - Frontend envía `company_id` en payload
- **POST `/api/export/docx`** - Frontend envía `company_id` en payload

### Validación
- **JSON Schema** - `configs/companies/schema.json` valida estructura
- **Python Dataclass** - `CompanyConfig` valida tipos y valores
- **Endpoints** - Retornan errores 400/404 si hay problemas

---

## Decisiones de Diseño

### ¿Por qué JSON en lugar de base de datos?

? **Ventajas:**
- No requiere instalación adicional
- Fácil de version control (Git)
- Fácil de compartir entre equipos
- Portable

? **Limitaciones:**
- Sin interfaz de administración
- Edición manual de archivos
- Sin auditoria de cambios

### ¿Por qué dataclass `CompanyConfig`?

? **Ventajas:**
- Type-safe (validación de tipos)
- Documentación clara
- Serializable a JSON

? **Alternativas:**
- Diccionario Python (menos seguro)
- ORM + Base de datos (sobre-engineered para ahora)

### ¿Por qué pasar company_id en payload?

? **Ventajas:**
- Flexible para multi-empresa en mismo request
- No depende de sesiones/cookies
- Stateless (REST puro)

? **Alternativas:**
- Header HTTP (menos visible)
- JWT/Token (más complejo)
- URL path `/api/export/pdf/acme-corp` (menos flexible)

---

## Próximos Pasos de Evolución

### Corto plazo (1-2 sprints)
- [ ] Selector dinámico de empresa en UI
- [ ] Guardar empresa seleccionada en localStorage
- [ ] Tests de configuración multi-empresa

### Mediano plazo (1-2 meses)
- [ ] Panel de administración de empresas (agregar/editar)
- [ ] Carga de imágenes sin reiniciar servidor
- [ ] Base de datos de proformas por empresa

### Largo plazo (3+ meses)
- [ ] Autenticación por empresa
- [ ] Reportes por empresa
- [ ] Integración con sistemas contables
- [ ] API pública para terceros

---

## Referencias de Código

### Archivos clave:

| Archivo | Rol | Líneas |
|---------|-----|--------|
| `proforma_app/company_config.py` | Dataclass de config | ~60 |
| `configs/companies/*.json` | Datos de empresa | JSON |
| `proforma_app/server.py` | HTTP + endpoints | ~180 |
| `proforma_app/document_engine.py` | Motor de PDF/DOCX | ~800 |
| `src/app.js` | Frontend dinámico | ~2000 |
| `static/index.html` | UI sin cambios | ~250 |

### Flujo de lectura recomendado:

1. [ADD_NEW_COMPANY.md](ADD_NEW_COMPANY.md) - Cómo agregar empresa
2. `proforma_app/company_config.py` - Estructura de datos
3. `proforma_app/server.py` - Carga y API
4. `proforma_app/document_engine.py` - Generación con config
5. `src/app.js` - Consumo en frontend

---

## Troubleshooting

### P: ¿Cómo cambio datos de una empresa?

R: Edita el archivo `configs/companies/[empresa].json` y reinicia el servidor.

### P: ¿Cómo veo qué empresas están disponibles?

R: Llamar a `GET /api/companies` o revisar output al iniciar servidor.

### P: ¿Qué pasa si falta `company_id` en el payload?

R: Usa default "jc-services". Puedes cambiar en `document_engine.py` línea ~60.

### P: ¿Puedo tener dos proformas de empresas diferentes simultáneamente?

R: Sí, el payload lleva `company_id`, cada PDF es independiente.

### P: ¿Dónde se validan los datos de config?

R: En `CompanyConfig.from_json_file()` contra `schema.json`.

