# 📊 Tablero Interactivo de Compras MOP y MINVU/SERVIU (2018-2019)

Tablero interactivo desarrollado en **Streamlit** y **Plotly** para el análisis y visualización de compras públicas en Mercado Público (ChileCompra) cruzadas con la ejecución presupuestaria del Ministerio de Obras Públicas (MOP) de Chile.

---

## 🎯 Objetivo
Identificar patrones de compra, estacionalidad del gasto, concentración de compras a fin de año (último trimestre) y participación de modalidades de contratación (Trato Directo, Convenio Marco, Licitación Pública) para mejorar la planificación y focalizar la fiscalización.

---

## 🚀 Despliegue en Streamlit Community Cloud
Esta aplicación está optimizada para desplegarse directamente en **[Streamlit Community Cloud](https://share.streamlit.io/)**:

- **Ruta del archivo principal (Main file):** `04_dashboard/dashboard_app.py`
- **Requisitos:** gestionados automáticamente mediante `requirements.txt`.
- **Datos optimizados:** Los datos analíticos se cargan desde `compras_presupuesto_items.parquet` (2.08 MB) para un rendimiento instantáneo.

---

## 📁 Estructura del Proyecto

```text
├── 01_datos/
│   ├── originales/             # Datos crudos de ChileCompra y Presupuesto MOP
│   └── procesados/             # Datasets procesados y unificados (Parquet y CSVs)
├── 02_pipeline/                # Scripts Python para unificación y procesamiento
├── 03_notebooks/               # Notebooks Jupyter de análisis exploratorio y modelado
├── 04_dashboard/
│   └── dashboard_app.py        # Aplicación interactiva de Streamlit
├── 05_figuras/                 # Gráficos e infografías generadas
├── 06_doc/                     # Informes técnicos, presentaciones y pautas
├── .streamlit/
│   └── config.toml             # Configuración de diseño y tema
├── requirements.txt            # Dependencias del proyecto
└── README.md
```

---

## 💻 Ejecución Local

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/rjoserivera/Dashboard_compras_MOP-.git
   cd Dashboard_compras_MOP-
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar el dashboard:**
   ```bash
   streamlit run 04_dashboard/dashboard_app.py
   ```

---

## 🛠️ Tecnologías Utilizadas
- **Python 3.10+**
- **Streamlit** (Frontend y UI interactiva)
- **Plotly** (Visualizaciones dinámicas e interactivas)
- **Pandas & PyArrow** (Manipulación de datos y almacenamiento columnar)
- **SciPy** (Modelado estadístico y regresión log-log)
