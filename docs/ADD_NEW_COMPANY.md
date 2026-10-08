# Agregar una Nueva Empresa

Esta guía te muestra paso a paso cómo agregar una nueva empresa al sistema de proformas.

## Requisitos

1. Configuración de la empresa (nombre, datos bancarios, direcciones)
2. Imágenes:
   - Header/encabezado (recomendado: 1200x300px, PNG)
   - Watermark/marca de agua (PNG transparente, recomendado: 250x250px)

## Paso 1: Crear el archivo de configuración

Abre `configs/companies/` y crea un nuevo archivo JSON con el nombre de tu empresa en minúsculas y con guiones:

**Ejemplo:** `configs/companies/mi-empresa.json`

```json
{
  "company_id": "mi-empresa",
  "company_name": "MI EMPRESA S.A.C.",
  "payment_bcp_account": "0011-1234-5678",
  "payment_bcp_cci": "MI EMPRESA S.A.C.",
  "payment_detracciones_account": "",
  "payment_bank_label": "Cuenta en Soles BCP",
  "offer_note_primary": "Validez de la oferta: 30 dias",
  "offer_note_secondary": "Precios incluyen servicio",
  "workshop_address": "Av. Principal 123, Lima",
  "fiscal_address": "Jr. Legal 456, Lima",
  "header_image": "companies/mi-empresa/header.png",
  "watermark_image": "companies/mi-empresa/watermark.png"
}
```

### Campos requeridos:

- **company_id**: Identificador único (minúsculas, guiones, sin espacios)
- **company_name**: Nombre legal de la empresa
- **payment_bcp_account**: Número de cuenta BCP
- **payment_bcp_cci**: CCI (Código de Cuenta Interbancaria)
- **payment_bank_label**: Etiqueta para mostrar (ej: "Cuenta en Soles BCP")
- **offer_note_primary**: Nota de validez de oferta
- **offer_note_secondary**: Nota secundaria
- **workshop_address**: Dirección del taller/producción
- **fiscal_address**: Dirección fiscal/legal
- **header_image**: Ruta relativa a `static/assets/` (crear)
- **watermark_image**: Ruta relativa a `static/assets/` (crear)

### Campos opcionales:

- **payment_detracciones_account**: Cuenta de detracciones (puede estar vacío)

## Paso 2: Crear directorio de assets

Crea una carpeta para los assets de tu empresa:

```
mkdir static/assets/companies/mi-empresa
```

## Paso 3: Copiar imágenes

Copia tus imágenes de encabezado y marca de agua al directorio creado:

```
static/assets/companies/mi-empresa/
??? header.png         # Tu encabezado personalizado
??? watermark.png      # Tu marca de agua
```

## Paso 4: Validar la configuración

El servidor valida automáticamente tu configuración contra `configs/companies/schema.json` al iniciar.

Errores comunes:
- `company_id` no coincide con el nombre del archivo
- Campos requeridos faltando
- Ruta de imágenes incorrecta

## Paso 5: Usar la empresa en la aplicación

### Desde el navegador web:

```javascript
// Cargar configuración específica
const response = await fetch('/api/config?company_id=mi-empresa');
const config = await response.json();
```

### Desde el formulario:

Agregar `company_id` al payload cuando generes PDF/DOCX:

```javascript
const payload = {
  customer_name: "Cliente XYZ",
  phone: "987654321",
  // ... otros campos
  company_id: "mi-empresa"  // ? IMPORTANTE
};

await fetch('/api/export/pdf', {
  method: 'POST',
  body: JSON.stringify(payload)
});
```

### Listar empresas disponibles:

```bash
curl http://localhost:8000/api/companies
# Respuesta:
# {"companies": ["jc-services", "mi-empresa", "example-company"]}
```

## Paso 6: Recomendaciones de diseño

### Imágenes de encabezado:

- **Tamaño**: 1200x300px (proporciones 4:1)
- **Formato**: PNG con fondo transparente o sólido
- **Contenido**: Logo, nombre empresa, contacto
- **Resolución**: 72-150 DPI para web

### Marcas de agua:

- **Tamaño**: 250x250px
- **Formato**: PNG con transparencia (importante)
- **Opacidad**: Recomendado 6.5% de opacidad
- **Contenido**: Logo o texto sutilmente visible

## Solución de problemas

### Error: "Configuración de empresa no encontrada"

**Causa**: El archivo JSON no existe o el `company_id` en el payload no coincide.

**Solución**:
1. Verifica que el archivo existe en `configs/companies/`
2. Verifica que el `company_id` en el JSON coincide con el nombre del archivo
3. Revisa el nombre en minúsculas y con guiones

### Error: "Archivo no encontrado: companies/mi-empresa/header.png"

**Causa**: Las imágenes no están en el lugar correcto.

**Solución**:
1. Copia tus imágenes a `static/assets/companies/mi-empresa/`
2. Asegúrate de que los nombres coinciden exactamente con los del JSON
3. Verifica que las imágenes tienen permisos de lectura

### El PDF se genera pero falta encabezado

**Causa**: La imagen del header no se encontró, el servidor continúa sin fallar.

**Solución**:
1. Verifica que `static/assets/companies/tu-empresa/header.png` existe
2. Verifica que es un PNG válido
3. Intenta convertir a PNG si viene de otro formato

## Ejemplo completo

Para agregar empresa "Acme Corp":

### 1. Crear archivo de configuración

**`configs/companies/acme-corp.json`:**
```json
{
  "company_id": "acme-corp",
  "company_name": "ACME CORPORATION S.A.",
  "payment_bcp_account": "0011-9876-5432",
  "payment_bcp_cci": "ACME CORPORATION S.A.",
  "payment_detracciones_account": "00-123-456789",
  "payment_bank_label": "Cuenta Corriente BCP",
  "offer_note_primary": "Oferta válida por 60 días",
  "offer_note_secondary": "Incluye instalación y capacitación",
  "workshop_address": "Zona Industrial Parque, Lima",
  "fiscal_address": "Jr. Comercial 999, Lima",
  "header_image": "companies/acme-corp/header.png",
  "watermark_image": "companies/acme-corp/watermark.png"
}
```

### 2. Crear carpeta y copiar imágenes

```bash
mkdir static/assets/companies/acme-corp
cp logo-acme.png static/assets/companies/acme-corp/header.png
cp marca-agua.png static/assets/companies/acme-corp/watermark.png
```

### 3. Reiniciar servidor

El servidor detectará automáticamente el nuevo archivo de configuración.

### 4. Usar en la aplicación

```javascript
// Generar proforma para Acme Corp
await fetch('/api/export/pdf', {
  method: 'POST',
  body: JSON.stringify({
    customer_name: "Cliente Importante",
    company_id: "acme-corp",  // ? Nueva empresa
    // ... resto de datos
  })
});
```

## Próximos pasos

- Implementar selector dinámico de empresa en la UI
- Guardar empresa seleccionada en localStorage
- Crear panel de administración de empresas
- Permitir cambio de imágenes sin reiniciar servidor

## Referencias

- [schemas/companies](configs/companies/schema.json) — Validación JSON
- [Configuración JC Services](configs/companies/jc-services.json) — Ejemplo actual
- [Archivos de ejemplo](configs/companies/example-company.json) — Template

