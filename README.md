# Generador de Proformas - Sistema Multi-Empresa

Aplicación adaptable para cualquier empresa que genera proformas profesionales en PDF y Word (DOCX), con soporte para web, PWA y móvil Android.

## ✨ Características Principales

- **✓ Multi-Empresa:** Configurable para cualquier empresa sin modificar código
- **✓ Web Responsive:** Funciona en desktop, tablet y móvil
- **✓ Generación Local:** PDF y Word directamente en el navegador o servidor
- **✓ PWA:** Instalable como app en el navegador
- **✓ Android:** Disponible como APK via Capacitor
- **✓ Sin Base de Datos:** Configuración basada en archivos JSON
- **✓ Documentación Completa:** Guías para agregar nuevas empresas

## 📋 Qué Incluye

### Frontend
- Interfaz HTML/CSS/JS responsive
- Carga dinámica de configuración de empresa
- Vista previa en tiempo real de PDF
- Validación de datos
- Generación de PDF via jsPDF (navegador)
- Generación de DOCX via docx.js (navegador)

### Backend (Python)
- Servidor HTTP simple y ligero
- Endpoints REST para exportación
- Generación de PDF via reportlab
- Generación de DOCX via python-docx
- API de configuración multi-empresa

### Datos por Empresa
- Nombre y datos de contacto
- Información bancaria (BCP, detracciones)
- Direcciones (fiscal, taller)
- Encabezados y marcas de agua personalizadas
- Notas personalizadas en ofertas

## 🚀 Uso Rápido

### 1. Ejecutar el servidor

```bash
python app.py
```

Abre http://127.0.0.1:8000

### 2. Generar proforma

1. Rellena el formulario
2. Haz clic en "Descargar PDF" o "Descargar DOCX"
3. El archivo se descarga con los datos de tu empresa

### 3. Agregar nueva empresa

Ver: [docs/ADD_NEW_COMPANY.md](docs/ADD_NEW_COMPANY.md)

En resumen:
1. Crear `configs/companies/[empresa].json`
2. Copiar imágenes a `static/assets/companies/[empresa]/`
3. Reiniciar servidor

¡Listo! La nueva empresa está disponible automáticamente.

## 📁 Estructura del Proyecto

```
Proformas-Empresas/
├── app.py                          # Punto de entrada
├── proforma_app/
│   ├── __init__.py
│   ├── company_config.py          # ★ Config de empresa (NUEVO)
│   ├── document_engine.py         # Generación PDF/DOCX
│   └── server.py                  # Servidor HTTP
├── configs/companies/             # ★ Configuración (NUEVO)
│   ├── schema.json                # Validación
│   ├── jc-services.json           # Ejemplo
│   └── [tu-empresa].json          # Nueva empresa
├── src/
│   └── app.js                     # Frontend (compilado)
├── static/                        # Assets servidos
│   ├── index.html
│   ├── app.js                     # JavaScript compilado
│   ├── styles.css
│   └── assets/
│       └── companies/             # ★ Imágenes por empresa (NUEVO)
├── output/                        # Documentos generados
│   ├── pdf/
│   └── docx/
├── docs/                          # ★ Documentación (NUEVO)
│   ├── ADD_NEW_COMPANY.md
│   └── ARCHITECTURE.md
└── android/                       # App Android con Capacitor
```

**★ = NUEVO en refactorización multi-empresa**

## 🔧 Configuración de Empresa

### Archivo JSON

Cada empresa es un archivo `configs/companies/[id].json`:

```json
{
  "company_id": "mi-empresa",
  "company_name": "MI EMPRESA S.A.C.",
  "payment_bcp_account": "0011-1234-5678",
  "payment_bcp_cci": "MI EMPRESA S.A.C.",
  "payment_detracciones_account": "00-123-456789",
  "payment_bank_label": "Cuenta BCP Soles",
  "offer_note_primary": "Validez: 30 días",
  "offer_note_secondary": "Incluye instalación",
  "workshop_address": "Jr. Taller 123, Lima",
  "fiscal_address": "Jr. Fiscal 456, Lima",
  "header_image": "companies/mi-empresa/header.png",
  "watermark_image": "companies/mi-empresa/watermark.png"
}
```

### Imágenes

- **header.png:** Encabezado (recomendado 1200x300px)
- **watermark.png:** Marca de agua (recomendado 250x250px, transparente)

Ubicación: `static/assets/companies/[empresa]/`

## 📱 Ejecutar en Diferentes Plataformas

### Windows - Escritorio (simplificado)

```bash
run_windows.bat
```

Abre automáticamente http://127.0.0.1:8000 en tu navegador.

### Web - Desde celular en la misma red

```bash
python app.py
```

El servidor imprime la URL LAN (ej: http://192.168.1.100:8000).

Abre esa URL desde tu celular.

### PWA - Instalar como app en navegador

1. Abre la URL en Chrome/Edge
2. Botón "Instalar" en la barra de dirección
3. Se instala como app en tu dispositivo

### Android APK

Capacitor genera APK automáticamente. Ver:
- [android/app/build/outputs/apk/debug/](android/app/build/outputs/apk/debug/app-debug.apk)

## 🌐 API Endpoints

### Listar empresas disponibles

```bash
GET /api/companies
```

Respuesta:
```json
{
  "companies": ["jc-services", "acme-corp", "mi-empresa"]
}
```

### Obtener configuración de empresa

```bash
GET /api/config?company_id=acme-corp
```

Respuesta: JSON con todos los datos de la empresa

### Generar PDF

```bash
POST /api/export/pdf
```

Body: JSON con datos de proforma + `company_id`

### Generar DOCX

```bash
POST /api/export/docx
```

Body: JSON con datos de proforma + `company_id`

## 📚 Documentación

- [ADD_NEW_COMPANY.md](docs/ADD_NEW_COMPANY.md) - Cómo agregar empresas *(START HERE)*
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Arquitectura técnica del sistema
- [configs/README.md](configs/README.md) - Schema de configuración

## 🔄 Cambios Respecto a Versión Original

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| Empresa | Hardcodeada (J&C Services) | Configurable en JSON |
| Agregar empresa | Editar código Python | Crear archivo JSON + imágenes |
| Datos bancarios | Constantes globales | En archivo de config |
| Validación | Manual | JSON Schema automática |
| API | Solo export | +/api/config, +/api/companies |
| Frontend | Constantes locales | Carga dinámica |

## 🛠️ Desarrollo

### Compilar JavaScript (esbuild)

```bash
node build-web.mjs
```

Compila `src/app.js` → `static/app.js`

### Estructura de código Python

- `proforma_app/company_config.py` - Dataclass de configuración
- `proforma_app/server.py` - Servidor HTTP y endpoints
- `proforma_app/document_engine.py` - Generación de documentos

### Testing

Scripts de verificación en `tests/`:

```bash
python tests/unit/verify_advances.py
python tests/unit/verify_tax_mode.py
node tests/unit/verify_pdf_import.mjs
```

## 📦 Requisitos

### Python
- Python 3.9+
- `reportlab` - Generación PDF
- `python-docx` - Generación DOCX

### JavaScript
- Node.js 16+ (para compilación)
- `esbuild` - Bundler

### Android
- JDK 21 (incluido en proyecto)
- Android SDK (incluido en proyecto)
- Capacitor 5+

## 🚢 Despliegue en Producción

### Web

```bash
# Compilar frontend
node build-web.mjs

# Ejecutar servidor
python app.py
```

### Docker (futuro)

```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

### APK/EXE

Ver scripts:
- `build_exe.bat` - Genera executable para Windows (requiere PyInstaller)
- `android/` - Proyecto Capacitor para APK

## 📋 Próximos Pasos

### Corto plazo
- [ ] Selector dinámico de empresa en UI
- [ ] Guardar preferencias en localStorage
- [ ] Tests de integración

### Mediano plazo
- [ ] Panel de administración
- [ ] Carga de imágenes sin reiniciar
- [ ] Base de datos de historial

### Largo plazo
- [ ] Autenticación
- [ ] Reportes por empresa
- [ ] Integración con sistemas externos

## 🤝 Contribuciones

Ver [docs/ADD_NEW_COMPANY.md](docs/ADD_NEW_COMPANY.md) para entender la arquitectura antes de contribuir.

## 📞 Soporte

### Error: "Configuración de empresa no encontrada"

Verifica que el archivo `configs/companies/[empresa].json` existe.

### Error: "Archivo no encontrado: companies/[empresa]/header.png"

Copia las imágenes a `static/assets/companies/[empresa]/`

### El PDF no se genera

Comprueba los logs del servidor. Verifica que la configuración de la empresa es válida.

## 📄 Licencia

Según se determine en el proyecto.

---

**¿Primera vez?** Empieza por [docs/ADD_NEW_COMPANY.md](docs/ADD_NEW_COMPANY.md) para entender cómo funciona el sistema de configuración.

