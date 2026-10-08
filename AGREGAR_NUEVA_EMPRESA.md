# ?? Guía: Agregar una Nueva Empresa

Esta guía explica cómo agregar una nueva empresa al sistema Proformas-Empresas, que es completamente multi-empresa y genera cotizaciones/proformas personalizadas por cada organización.

## ?? Descripción General

El sistema permite gestionar múltiples empresas sin tocar código. Cada empresa tiene:
- **Configuración JSON**: Datos bancarios, direcciones, notas
- **Assets (imágenes)**: Logo/encabezado y marca de agua personalizados
- **Automático**: El backend detecta nuevas empresas automáticamente

## ?? Pasos para Implementar una Nueva Empresa

### PASO 1: Crear el Archivo de Configuración JSON

**Ubicación**: `configs/companies/[nombre-empresa].json`

**Ejemplo**: `configs/companies/mi-empresa.json`

```json
{
  "company_id": "mi-empresa",
  "company_name": "MI EMPRESA S.A.C.",
  "payment_bcp_account": "0011-XXXX-XXXXXXXX",
  "payment_bcp_cci": "PE00 0011 XXXX XXXXXXXX",
  "payment_detracciones_account": "0011-YYYY-XXXXXXXX",
  "payment_bank_label": "Cuenta Corriente BCP Soles",
  "offer_note_primary": "Validez de la oferta: 30 días",
  "offer_note_secondary": "Incluye transporte e instalación",
  "workshop_address": "Av. Industrial 123, Lima 15001",
  "fiscal_address": "Jr. Fiscal 456, Lima 15001",
  "header_image": "companies/mi-empresa/header.png",
  "watermark_image": "companies/mi-empresa/watermark.png"
}
```

### Campos Obligatorios

| Campo | Tipo | Ejemplo | Descripción |
|-------|------|---------|-------------|
| `company_id` | string | `mi-empresa` | Identificador único (minúsculas, números, guiones) |
| `company_name` | string | `MI EMPRESA S.A.C.` | Nombre legal de la empresa |
| `payment_bcp_account` | string | `0011-1234-5678` | Número de cuenta bancaria BCP |
| `payment_bcp_cci` | string | `PE00 0011 1234...` | CCI/IBAN para transferencias |
| `payment_bank_label` | string | `Cuenta Corriente BCP` | Etiqueta mostrada en documentos |
| `offer_note_primary` | string | `Validez: 30 días` | Nota principal de oferta |
| `offer_note_secondary` | string | `Incluye instalación` | Nota secundaria de oferta |
| `workshop_address` | string | `Av. Principal 123` | Dirección del taller/oficina |
| `fiscal_address` | string | `Jr. Fiscal 456` | Dirección fiscal (RUC) |

### Campos Opcionales

| Campo | Tipo | Ejemplo | Descripción |
|-------|------|---------|-------------|
| `payment_detracciones_account` | string | `0011-YYYY-...` | Cuenta para retenciones (dejar vacío si no aplica) |
| `header_image` | string | `companies/mi-empresa/header.png` | Ruta del logo/encabezado en PDF |
| `watermark_image` | string | `companies/mi-empresa/watermark.png` | Ruta de la marca de agua |

### Validación

- El `company_id` **debe coincidir** con el nombre del archivo (sin .json)
- Solo caracteres: minúsculas, números y guiones (`^[a-z0-9-]+$`)
- Todos los campos obligatorios deben estar presentes
- Se valida automáticamente contra `configs/companies/schema.json`

---

### PASO 2: Crear Directorio de Imágenes

Crea la carpeta para los assets de la empresa:

```bash
mkdir -p static/assets/companies/mi-empresa
```

### Imágenes Requeridas

1. **header.png** - Encabezado/logo del documento
   - Tamaño recomendado: 1200×300px
   - Formato: PNG
   - Ubicación: `static/assets/companies/mi-empresa/header.png`

2. **watermark.png** - Marca de agua
   - Tamaño recomendado: 250×250px
   - Formato: PNG con transparencia
   - Ubicación: `static/assets/companies/mi-empresa/watermark.png`

### Copiar desde Plantilla Existente

Si no tienes imágenes personalizadas, puedes copiar las de `jc-services`:

```bash
# En Linux/Mac
cp -r static/assets/companies/jc-services/* static/assets/companies/mi-empresa/

# En Windows PowerShell
Copy-Item -Recurse "static/assets/companies/jc-services/*" "static/assets/companies/mi-empresa/"
```

---

### PASO 3: Verificar que Funciona

Ejecuta el servidor:

```bash
npm start
```

Luego prueba los endpoints:

#### Test 1: Listar todas las empresas
```bash
curl http://localhost:3000/api/companies
```

**Respuesta esperada**:
```json
{
  "companies": ["jc-services", "mi-empresa"]
}
```

#### Test 2: Cargar configuración de la empresa
```bash
curl "http://localhost:3000/api/config?company_id=mi-empresa"
```

**Respuesta esperada**: Objeto JSON completo con todos los campos

#### Test 3: En el navegador (Consola DevTools)
```javascript
await loadCompanyConfig("mi-empresa");
console.log(currentCompanyConfig);
// Debe mostrar todos los datos de la empresa
```

---

### PASO 4: Cambiar Empresa por Defecto (Opcional)

Si quieres que `mi-empresa` sea la empresa por defecto en lugar de `jc-services`:

#### Opción A: Backend
**Archivo**: `proforma_app/server.py` (línea ~54)

```python
company_id = query_params.get("company_id", ["mi-empresa"])[0]  # Cambiar de "jc-services"
```

#### Opción B: Frontend
**Archivo**: `src/app.js` (línea ~30)

```javascript
let currentCompanyId = "mi-empresa";  // Cambiar de "jc-services"
```

---

### PASO 5: Generar Documentos con la Nueva Empresa

#### Opción A: Desde el Navegador
1. Abre `http://localhost:3000`
2. La configuración de `mi-empresa` se carga automáticamente (si es default)
3. Completa el formulario de proforma
4. Genera PDF o DOCX

#### Opción B: Desde cURL (Línea de Comandos)

**Generar PDF**:
```bash
curl -X POST http://localhost:3000/api/export/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "mi-empresa",
    "issue_date": "2024-01-15",
    "customer_name": "Cliente Ejemplo S.A.C.",
    "items": [
      {"description": "Servicio Profesional", "quantity": 1, "unit_price": 1000.00},
      {"description": "Material", "quantity": 5, "unit_price": 50.00}
    ],
    "tax_mode": "con_igv"
  }' \
  --output proforma.pdf
```

**Generar DOCX**:
```bash
curl -X POST http://localhost:3000/api/export/docx \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "mi-empresa",
    "issue_date": "2024-01-15",
    "customer_name": "Cliente Ejemplo S.A.C.",
    "items": [
      {"description": "Servicio Profesional", "quantity": 1, "unit_price": 1000.00}
    ],
    "tax_mode": "con_igv"
  }' \
  --output proforma.docx
```

Los archivos se guardan automáticamente en:
- PDFs: `output/pdf/`
- DOCX: `output/docx/`

---

## ?? Checklist de Implementación

Antes de subir cambios al repositorio, verifica:

```
CONFIGURACIÓN:
? Archivo configs/companies/[empresa].json creado
? company_id es válido (minúsculas, números, guiones)
? Todos los campos obligatorios están presentes
? Datos bancarios verificados
? Direcciones correctas

IMÁGENES:
? Carpeta static/assets/companies/[empresa]/ creada
? header.png presente (1200×300px aprox.)
? watermark.png presente (250×250px aprox.)
? Ambas imágenes en formato PNG

VERIFICACIÓN:
? npm start ejecuta sin errores
? GET /api/companies incluye la nueva empresa
? GET /api/config?company_id=[empresa] retorna datos completos
? PDF/DOCX se generan correctamente
? Images se cargan en los documentos

OPCIONAL:
? Si es empresa default, actualizado server.py
? Si es empresa default, actualizado app.js
? README.md actualizado si es necesario
```

---

## ?? Flujo Completo: Ejemplo "TractorTec"

Supongamos que quieres agregar la empresa **TractorTec**:

### 1. Crear `configs/companies/tractortec.json`:
```json
{
  "company_id": "tractortec",
  "company_name": "TRACTORTEC SERVICIOS INDUSTRIALES S.A.C.",
  "payment_bcp_account": "0011-2205-0500123456",
  "payment_bcp_cci": "PE00001122050500123456",
  "payment_detracciones_account": "0011-2205-0400654321",
  "payment_bank_label": "Cuenta Corriente BCP",
  "offer_note_primary": "Garantía: 12 meses",
  "offer_note_secondary": "Incluye mantenimiento preventivo por 3 meses",
  "workshop_address": "Av. Transportistas 789, La Oroya, Junín",
  "fiscal_address": "Jr. Minería 321, La Oroya, Junín 12100",
  "header_image": "companies/tractortec/header.png",
  "watermark_image": "companies/tractortec/watermark.png"
}
```

### 2. Crear directorio e imágenes:
```bash
mkdir -p static/assets/companies/tractortec
cp static/assets/companies/jc-services/header.png static/assets/companies/tractortec/
cp static/assets/companies/jc-services/watermark.png static/assets/companies/tractortec/
```

### 3. Probar:
```bash
npm start
# Luego en otra terminal:
curl "http://localhost:3000/api/config?company_id=tractortec"
```

### 4. Usar en frontend:
```javascript
await loadCompanyConfig("tractortec");
// Ahora se generan documentos con datos de TractorTec
```

---

## ?? Estructura de Archivos Final

```
Proformas-Empresas/
??? configs/companies/
?   ??? schema.json                 (no modificar)
?   ??? jc-services.json            (existente)
?   ??? example-company.json        (plantilla de referencia)
?   ??? mi-empresa.json             ? NUEVO
??? static/assets/companies/
?   ??? jc-services/
?   ?   ??? header.png
?   ?   ??? watermark.png
?   ??? mi-empresa/                 ? NUEVO
?       ??? header.png              ? NUEVO
?       ??? watermark.png           ? NUEVO
??? proforma_app/
?   ??? server.py                   (no requiere cambios)
?   ??? company_config.py           (no requiere cambios)
??? src/app.js                      (no requiere cambios)
```

---

## ?? Cómo Funciona Internamente

### Backend

1. **Detección automática** (`_get_available_companies` en `server.py`):
   - Escanea `configs/companies/*.json`
   - Excluye `schema.json`
   - Retorna lista de empresas

2. **Carga de configuración** (`CompanyConfig.from_json_file`):
   - Lee archivo JSON
   - Valida contra schema
   - Retorna objeto `CompanyConfig`

### Frontend

1. **Inicialización**:
   ```javascript
   loadCompanyConfig(currentCompanyId)  // Por defecto: "jc-services"
   ```

2. **Generación de documentos**:
   ```javascript
   // Los datos se usan en:
   build_pdf(proformaData)   // Encabezado, dirección fiscal, cuenta bancaria
   build_docx(proformaData)  // Mismos datos en formato Word
   ```

3. **Rutas de imágenes**:
   ```javascript
   // Convertidas a rutas completas:
   "companies/mi-empresa/header.png" ? "/static/assets/companies/mi-empresa/header.png"
   ```

---

## ? Validación Automática

El archivo `configs/companies/schema.json` valida:

```json
{
  "type": "object",
  "properties": {
    "company_id": {"type": "string", "pattern": "^[a-z0-9-]+$"},
    "company_name": {"type": "string", "minLength": 1},
    "payment_bcp_account": {"type": "string"},
    // ... más campos
  },
  "required": [
    "company_id", "company_name", "payment_bcp_account",
    "payment_bcp_cci", "payment_bank_label", "offer_note_primary",
    "offer_note_secondary", "workshop_address", "fiscal_address"
  ]
}
```

Si algo es inválido:
- El servidor retorna **HTTP 404** con mensaje de error
- Se especifica qué campo falta o es inválido

---

## ?? Troubleshooting

### La empresa no aparece en `/api/companies`
- Verifica que el archivo esté en `configs/companies/`
- Verifica que tenga extensión `.json`
- Verifica que el JSON sea válido (sin caracteres especiales)

### Error: "Invalid company_id"
- El `company_id` solo permite: a-z, 0-9, guiones
- No puede contener mayúsculas, espacios o caracteres especiales

### Las imágenes no aparecen en el PDF
- Verifica que las rutas en el JSON sean correctas
- Verifica que los archivos existan en `static/assets/companies/[empresa]/`
- Verifica que sean PNG (no JPG u otro formato)

### El servidor retorna 404 al cargar configuración
- Verifica que la empresa exista en `/api/companies`
- Verifica que el JSON sea válido en `configs/companies/schema.json`
- Revisa logs del servidor para más detalles

---

## ?? Notas de Seguridad

- **No guardar datos sensibles** en el repositorio (cuentas reales, CCI, etc.)
- Usar `.gitignore` para archivos sensibles si es necesario
- Las imágenes públicas están OK en el repo
- Los datos de configuración son accesibles vía API (no incluir información privada)

---

## ?? Preguntas Frecuentes

**P: ¿Puedo tener múltiples empresas activas al mismo tiempo?**
R: No. Solo una empresa activa por sesión. El usuario selecciona qué empresa usar.

**P: ¿Necesito reiniciar el servidor para que vea la nueva empresa?**
R: No. El backend detecta nuevas empresas automáticamente en cada request.

**P: ¿Puedo cambiar la empresa default?**
R: Sí. Actualiza `server.py` línea ~54 y `app.js` línea ~30.

**P: ¿Dónde se guardan los PDFs generados?**
R: En `output/pdf/` para PDFs y `output/docx/` para documentos Word.

**P: ¿Puedo eliminar una empresa?**
R: Sí. Solo elimina el archivo JSON y la carpeta de imágenes. No afecta otros datos.

**P: ¿Qué pasa si dos empresas tienen el mismo company_id?**
R: El sistema solo usa la primera encontrada. Usa IDs únicos.

---

## ?? Archivos de Referencia

- `configs/companies/example-company.json` - Plantilla con todos los campos
- `configs/companies/jc-services.json` - Ejemplo real
- `proforma_app/company_config.py` - Implementación backend
- `src/app.js` - Implementación frontend (buscar `loadCompanyConfig`)

---

**¡Listo para agregar nuevas empresas! ??**
