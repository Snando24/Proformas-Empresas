# Generador de Proformas

Aplicación base para escritorio y móvil que toma como referencia `PDF_MODIFICADO.pdf` y genera proformas en PDF y Word.

## Qué incluye

- Interfaz responsive para usarla en escritorio o desde el navegador del móvil.
- Captura de cliente, fecha, RUC, teléfono, tipo de documento, descripción, ítems y adelanto.
- Exportación a `PDF` con `reportlab`.
- Exportación a `DOCX` con `python-docx`.
- Encabezado visual sincronizado con `PDF_MODIFICADO.pdf`.

## Cómo ejecutarla

1. Abre una terminal en `C:\Users\andy_\Documents\Taller\APP_TALLER`.
2. Ejecuta:

```powershell
& 'C:\Users\andy_\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' app.py
```

3. Abre `http://127.0.0.1:8000`.
4. Si quieres abrirla desde tu celular en la misma red, usa la URL LAN que imprime el servidor.

## Probarla como app de escritorio

Puedes abrirla sin escribir comandos con:

```powershell
C:\Users\andy_\Documents\Taller\APP_TALLER\run_windows.bat
```

Eso levanta el servidor local y abre la app en tu navegador.

## Generar `.exe` cuando PyInstaller este disponible

Dejé preparado:

- [desktop_launcher.py](C:/Users/andy_/Documents/Taller/APP_TALLER/desktop_launcher.py)
- [build_exe.bat](C:/Users/andy_/Documents/Taller/APP_TALLER/build_exe.bat)

Cuando `PyInstaller` esté instalado, ejecuta:

```powershell
C:\Users\andy_\Documents\Taller\APP_TALLER\build_exe.bat
```

Y el ejecutable quedará en `dist\ProformasTractotec.exe`.

## Instalarla en el móvil

1. Ejecuta `app.py` en tu PC.
2. Desde tu móvil, abre la URL LAN que imprime el servidor.
3. En Chrome Android usa `Agregar a pantalla principal` o `Instalar app`.

Queda como app instalada tipo PWA y funciona con la misma interfaz móvil.

## APK Android

También quedó compilado un APK debug en:

- [app-debug.apk](C:/Users/andy_/Documents/Taller/APP_TALLER/android/app/build/outputs/apk/debug/app-debug.apk)

Para instalarlo:

1. Copia el APK a tu teléfono Android.
2. Ábrelo desde el gestor de archivos.
3. Si Android lo pide, habilita `Instalar apps desconocidas` para esa app origen.

## Proyecto Android

Se creó un proyecto Capacitor en:

- [android](C:/Users/andy_/Documents/Taller/APP_TALLER/android)

El build usa herramientas portables dentro del proyecto:

- [JDK 21 portable](C:/Users/andy_/Documents/Taller/APP_TALLER/.tools/jdk21)
- [Android SDK portable](C:/Users/andy_/Documents/Taller/APP_TALLER/.tools/android-sdk)

## Archivos generados

- PDF: `output/pdf/`
- Word: `output/docx/`

## Arquitectura

- `app.py`: punto de entrada.
- `proforma_app/server.py`: servidor HTTP simple y endpoints de exportación.
- `proforma_app/document_engine.py`: validación de datos y generación PDF/DOCX.
- `static/`: interfaz, estilos y vista previa.

## Siguiente paso recomendado

Si quieres, el siguiente sprint puede ser cualquiera de estos:

1. Guardar clientes y proformas en SQLite.
2. Agregar numeración automática de proformas.
3. Empaquetar esta misma base como `.exe` real y evaluar wrapper Android/APK.
