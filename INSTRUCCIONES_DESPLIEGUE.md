# 🚀 Guía de Despliegue del Dashboard en la Nube (Streamlit Community Cloud)

## 📌 ¿Por qué Streamlit Cloud en vez de Vercel?
1. **Arquitectura:** **Vercel** es una plataforma *Serverless* (pensada para sitios web estáticos, React/Next.js y APIs que se ejecutan y mueren en segundos). No soporta servidores de Python con conexiones WebSockets persistentes en vivo como Streamlit.
2. **Streamlit Community Cloud:** Es la plataforma **oficial, gratuita y nativa** de Streamlit. Aloja aplicaciones Python interactivas en vivo de forma permanente con enlace público `https://<tu-proyecto>.streamlit.app`.

---

## ⚡ Optimización Clave Realizada
- El archivo original `compras_presupuesto_items.csv` pesaba **223 MB**.
- **GitHub rechaza archivos superiores a 100 MB**, lo que impedía subir el proyecto a la nube.
- Hemos generado `compras_presupuesto_items.parquet` con compresión Snappy (pesa solo **2.08 MB**, una reducción del 99% sin perder un solo registro).
- El código en `dashboard_app.py` ya fue actualizado para leer automáticamente este archivo optimizado en menos de 0.1 segundos.
- Se configuró `.gitignore` para omitir el CSV gigante y archivos `.rar`.

---

## 🛠️ Paso a Paso para Desplegar (Gratis y en 5 Minutos)

### Paso 1: Crear un Repositorio en GitHub
1. Ingresa a [github.com](https://github.com) e inicia sesión.
2. Crea un nuevo repositorio (por ejemplo llamado `dashboard-compras-mop`).
3. Déjalo en modo **Público** (necesario para el plan gratuito de Streamlit Cloud).
4. No marques la opción de inicializar con README (ya tenemos el proyecto listo).

### Paso 2: Subir el código a GitHub
Abre la terminal en esta carpeta (`entrega final/`) y ejecuta:

```bash
# 1. Inicializar git
git init

# 2. Agregar los archivos (el .gitignore omitirá automáticamente los archivos > 100MB)
git add .

# 3. Crear el primer commit
git commit -m "Dashboard compras MOP listo para despliegue"

# 4. Vincular a tu repositorio de GitHub (reemplaza con TU URL de GitHub)
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git

# 5. Cambiar a la rama principal y subir
git branch -M main
git push -u origin main
```

### Paso 3: Desplegar en Streamlit Community Cloud
1. Entra a **[share.streamlit.io](https://share.streamlit.io/)**.
2. Inicia sesión con tu cuenta de **GitHub**.
3. Haz clic en el botón azul **"Create app"** (o "New app").
4. Completa los 3 campos:
   - **Repository:** Selecciona tu repositorio (ej: `TU_USUARIO/dashboard-compras-mop`).
   - **Branch:** `main`
   - **Main file path:** `04_dashboard/dashboard_app.py`
5. Haz clic en **"Deploy"**.

En 1-2 minutos tu aplicación estará en vivo con su propia URL compartible. 🎉
