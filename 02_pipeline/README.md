# PIPELINE DE PROCESAMIENTO DE DATOS
## Proyecto: Análisis de Compras MOP + MINVU en ChileCompra (2018-2019)

---

## Flujo completo del pipeline

```
DATOS ORIGINALES (RAW)
    01_datos/originales/
    ├── ChileCompra_MercadoPublico/
    │   ├── 16OCLicitacion.csv
    │   ├── 16OCConvenioMarco.csv
    │   └── 16OCTratoDirecto.csv
    └── Presupuesto_MOP/
        ├── ejecucion-presupuestaria-mop-...-2018.xlsx
        └── ejecucion-...-2019.xlsx
           │
           ▼  python 02_pipeline/01_unificar_chilecompra.py
           │
    01_datos/procesados/compras_presupuesto_items.csv
           │
           ▼  python 02_pipeline/02_unir_compras_presupuesto.py
           │
    01_datos/procesados/compras_presupuesto_resumen.csv
    01_datos/procesados/presupuesto_2018_2019_unificado.csv
           │
           ▼  python 02_pipeline/03_generar_tablas_analisis.py
           │
    01_datos/procesados/panel_region_mes.csv
    01_datos/procesados/panel_region_servicio.csv
    01_datos/procesados/tabla_A_region_anio_modalidad.csv
    01_datos/procesados/tabla_B_perfil_proveedores.csv
    01_datos/procesados/tabla_E_trato_directo.csv
           │
           ▼  03_notebooks/ (análisis y modelado)
```

---

## Orden de ejecución

Ejecutar todos los scripts desde la carpeta **`entrega final/`**:

```bash
# Paso 1: Unificar CSVs crudos de ChileCompra
python 02_pipeline/01_unificar_chilecompra.py

# Paso 2: Cruzar con presupuesto MOP y generar resumen
python 02_pipeline/02_unir_compras_presupuesto.py

# Paso 3: Generar tablas analíticas y paneles
python 02_pipeline/03_generar_tablas_analisis.py
```

---

## Descripción de cada script

### `01_unificar_chilecompra.py`
- **Entrada:** CSVs en `01_datos/originales/ChileCompra_MercadoPublico/`
- **Qué hace:**
  - Lee todos los CSVs por tipo (Licitacion, TratoDirecto, ConvenioMarco, CompraAgil)
  - Prueba múltiples encodings (latin-1, utf-8, cp1252)
  - Normaliza nombres de columnas
  - Filtra solo 2018-2019, elimina montos ≤ 0
  - Une todo en un solo CSV
- **Salida:** `01_datos/procesados/compras_presupuesto_items.csv`

### `02_unir_compras_presupuesto.py`
- **Entrada:** items CSV + Excel MOP en `01_datos/originales/Presupuesto_MOP/`
- **Qué hace:**
  - Lee los Excel de presupuesto MOP 2018-2019
  - Estandariza columnas del Excel
  - Cruza compras con presupuesto por código BIP del proyecto
  - Genera resumen por Servicio × Año
- **Salida:**
  - `01_datos/procesados/presupuesto_2018_2019_unificado.csv`
  - `01_datos/procesados/compras_presupuesto_resumen.csv`

### `03_generar_tablas_analisis.py`
- **Entrada:** archivos en `01_datos/procesados/`
- **Qué hace:**
  - Panel Región × Mes y Región × Servicio
  - Tabla por modalidad con ticket medio
  - Perfil de proveedores
  - % Trato Directo por servicio (indicador de riesgo)
- **Salida:** tablas analíticas en `01_datos/procesados/`

---

## Dependencias Python

```bash
pip install pandas numpy openpyxl
```
