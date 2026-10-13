"""
01_unificar_chilecompra.py
==========================
PASO 1 DEL PIPELINE: Unificacion de archivos CSV crudos de ChileCompra.

Fuente  : datos_originales/ChileCompra_MercadoPublico/
          (CSVs descargados directamente desde mercadopublico.cl)
          Formato por archivo: <codigo_region><tipo>OC.csv
          Ejemplo: 05OCLicitacion.csv, 15OCConvenioMarco.csv

Salida  : analisis/compras_presupuesto_items.csv
          (todas las OC de MOP + MINVU/SERVIU, 2018-2019, unificadas)

Ejecutar desde: entrega final/
    python pipeline/01_unificar_chilecompra.py
"""

import pandas as pd
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ── Rutas ──────────────────────────────────────────────────────────────────
BASE_RAW  = Path("../01_datos/originales/ChileCompra_MercadoPublico")
BASE_OUT  = Path("../01_datos/procesados")
BASE_OUT.mkdir(exist_ok=True)

# ── Columnas que se conservan (subset de las 122 originales) ───────────────
COLS_OC = [
    "CodigoOC", "Anio", "Mes", "FechaEnvioOC",
    "Region", "RegionUnidad", "Servicio", "UnidadCompra",
    "TipoCompra", "MontoNetoItemCLP", "CantidadItem",
    "ProveedorRUT", "ProveedorNombre",
    "SubtituloItem", "Subtitulo",
    "CodBIP", "NombreProyecto", "Proy_Gasto_MM",
]

COLS_RENAME = {
    "CodigoOC"          : "codigoOC",
    "SubtituloItem"     : "SubtituloDesc",
}

# ── Tipos esperados para cada tipo de compra ───────────────────────────────
TIPO_MAP = {
    "OCLicitacion"    : "Licitacion",
    "OCConvenioMarco" : "Convenio Marco",
    "OCTratoDirecto"  : "Trato Directo",
    "OCCompraAgil"    : "Compra Agil",
}

# ── Encodings a intentar ───────────────────────────────────────────────────
ENCODINGS = ["latin-1", "utf-8-sig", "utf-8", "cp1252"]


def leer_csv_robusto(path: Path) -> pd.DataFrame | None:
    """Lee un CSV de ChileCompra probando distintos encodings."""
    for enc in ENCODINGS:
        try:
            df = pd.read_csv(path, sep=";", encoding=enc,
                             low_memory=False, dtype=str)
            # Normalizar nombres de columna
            df.columns = df.columns.str.strip()
            return df
        except Exception:
            continue
    print(f"  [ERROR] No se pudo leer: {path.name}")
    return None


def detectar_tipo(nombre_archivo: str) -> str:
    """Extrae el tipo de compra desde el nombre del archivo."""
    for patron, tipo in TIPO_MAP.items():
        if patron in nombre_archivo:
            return tipo
    return "Otro"


def normalizar_columnas(df: pd.DataFrame, tipo: str, archivo: str) -> pd.DataFrame:
    """Selecciona y normaliza columnas del DataFrame."""
    # Conservar solo las columnas que existan en este CSV
    cols_pres = [c for c in COLS_OC if c in df.columns]
    df = df[cols_pres].copy()
    df = df.rename(columns=COLS_RENAME)

    # Asegurar columna TipoCompra
    if "TipoCompra" not in df.columns:
        df["TipoCompra"] = tipo
    else:
        df["TipoCompra"] = df["TipoCompra"].fillna(tipo)

    # Convertir montos a numérico
    for col in ["MontoNetoItemCLP", "CantidadItem", "Proy_Gasto_MM"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].str.replace(",", ".", regex=False).str.strip(),
                errors="coerce"
            )

    # Convertir año y mes
    for col in ["Anio", "Mes"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["_archivo_origen"] = archivo
    return df


# ── MAIN ────────────────────────────────────────────────────────────────────
def main():
    archivos = sorted(BASE_RAW.glob("*.csv"))
    if not archivos:
        print(f"No se encontraron CSVs en {BASE_RAW}")
        print("Asegúrate de que los archivos originales estén en datos_originales/ChileCompra_MercadoPublico/")
        return

    print(f"Archivos encontrados: {len(archivos)}")
    partes = []

    for archivo in archivos:
        tipo = detectar_tipo(archivo.name)
        print(f"  Leyendo [{tipo:20s}]: {archivo.name}")
        df = leer_csv_robusto(archivo)
        if df is None:
            continue
        df = normalizar_columnas(df, tipo, archivo.name)
        partes.append(df)
        print(f"    -> {len(df):,} filas, {df.shape[1]} columnas")

    if not partes:
        print("No se procesó ningún archivo.")
        return

    # Unificar
    print("\nUnificando...")
    unificado = pd.concat(partes, ignore_index=True)

    # Filtrar solo 2018-2019
    if "Anio" in unificado.columns:
        antes = len(unificado)
        unificado = unificado[unificado["Anio"].isin([2018, 2019])]
        print(f"Filtrado a 2018-2019: {antes:,} -> {len(unificado):,} filas")

    # Eliminar montos nulos o negativos
    antes = len(unificado)
    unificado = unificado[unificado["MontoNetoItemCLP"].fillna(0) > 0]
    print(f"Filtrado monto > 0  : {antes:,} -> {len(unificado):,} filas")

    salida = BASE_OUT / "compras_presupuesto_items.csv"
    unificado.to_csv(salida, sep=";", index=False, encoding="utf-8-sig")

    size_mb = round(salida.stat().st_size / 1e6, 1)
    print(f"\nGuardado: {salida}")
    print(f"  Filas    : {len(unificado):,}")
    print(f"  Columnas : {unificado.shape[1]}")
    print(f"  Tamaño   : {size_mb} MB")
    print(f"  Tipos    : {unificado.TipoCompra.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
