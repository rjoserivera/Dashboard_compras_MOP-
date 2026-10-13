"""
02_unir_compras_presupuesto.py
================================
PASO 2 DEL PIPELINE: Cruce de OC con presupuesto MOP por proyecto BIP.

Entradas:
  - analisis/compras_presupuesto_items.csv    (generado en Paso 1)
  - datos_originales/Presupuesto_MOP/         (archivos Excel MOP)

Salidas:
  - analisis/compras_presupuesto_resumen.csv  (agregado por Servicio x Año)
  - analisis/presupuesto_2018_2019_unificado.csv

Ejecutar desde: entrega final/
    python pipeline/02_unir_compras_presupuesto.py
"""

import pandas as pd
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE_ITEMS  = Path("../01_datos/procesados/compras_presupuesto_items.csv")
BASE_PRES   = Path("../01_datos/originales/Presupuesto_MOP")
BASE_OUT    = Path("../01_datos/procesados")

# ── Columnas del Excel MOP ─────────────────────────────────────────────────
COLS_PRES = {
    "Anio"               : ["Anio", "Año", "AÑO", "year"],
    "CodBIP"             : ["CodBIP", "Codigo BIP", "CodigoBIP", "CODIGO_BIP", "BIP"],
    "NombreProyecto"     : ["NombreProyecto", "Proyecto", "Nombre Proyecto", "NOMBRE_PROYECTO"],
    "Servicio"           : ["Servicio", "SERVICIO", "Unidad"],
    "Region"             : ["Region", "REGION", "Región"],
    "Presupuesto_MM"     : ["Presupuesto_MM", "Presupuesto Vigente MM$", "PresVigente", "Presupuesto"],
    "Gasto_MM"           : ["Gasto_MM", "Gasto Devengado MM$", "GastoDevengado", "Gasto"],
}


def estandarizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Mapea columnas del Excel MOP a nombres estándar."""
    df.columns = df.columns.str.strip()
    rename_map = {}
    for nombre_estandar, alternativas in COLS_PRES.items():
        for alt in alternativas:
            if alt in df.columns:
                rename_map[alt] = nombre_estandar
                break
    return df.rename(columns=rename_map)


def leer_excel_mop(path: Path) -> pd.DataFrame | None:
    """Lee un archivo Excel del MOP y estandariza columnas."""
    try:
        df = pd.read_excel(path, sheet_name=0, dtype=str)
        df = estandarizar_columnas(df)
        print(f"  Leído: {path.name} -> {len(df):,} filas")
        return df
    except Exception as e:
        print(f"  [ERROR] {path.name}: {e}")
        return None


def main():
    # ── 1. Cargar compras unificadas ─────────────────────────────────────
    print("Cargando compras_presupuesto_items.csv...")
    if not BASE_ITEMS.exists():
        print(f"ERROR: No existe {BASE_ITEMS}")
        print("Ejecuta primero: python pipeline/01_unificar_chilecompra.py")
        return

    it = pd.read_csv(BASE_ITEMS, sep=";", low_memory=False)
    it["MM"] = pd.to_numeric(it["MontoNetoItemCLP"], errors="coerce") / 1e6
    print(f"  {len(it):,} filas cargadas")

    # ── 2. Cargar y unificar presupuesto MOP ─────────────────────────────
    print("\nCargando archivos de Presupuesto MOP...")
    excels = sorted(BASE_PRES.glob("*.xlsx")) + sorted(BASE_PRES.glob("*.xls"))
    if not excels:
        print(f"No se encontraron Excel en {BASE_PRES}")
        return

    partes_pres = []
    for f in excels:
        df = leer_excel_mop(f)
        if df is not None:
            # Agregar el año si viene del nombre del archivo
            if "Anio" not in df.columns:
                import re
                match = re.search(r"(201[0-9])", f.name)
                if match:
                    df["Anio"] = int(match.group(1))
            partes_pres.append(df)

    presupuesto = pd.concat(partes_pres, ignore_index=True)

    # Convertir numéricos
    for col in ["Presupuesto_MM", "Gasto_MM"]:
        if col in presupuesto.columns:
            presupuesto[col] = pd.to_numeric(
                presupuesto[col].astype(str).str.replace(",", ".").str.strip(),
                errors="coerce"
            )

    # Filtrar 2018-2019
    if "Anio" in presupuesto.columns:
        presupuesto["Anio"] = pd.to_numeric(presupuesto["Anio"], errors="coerce")
        presupuesto = presupuesto[presupuesto["Anio"].isin([2018, 2019])]

    print(f"\nPresupuesto unificado: {len(presupuesto):,} filas, {presupuesto.shape[1]} columnas")

    # Guardar presupuesto unificado
    sal_pres = BASE_OUT / "presupuesto_2018_2019_unificado.csv"
    presupuesto.to_csv(sal_pres, sep=";", index=False, encoding="utf-8-sig")
    print(f"Guardado: {sal_pres}")

    # ── 3. Cruce: compras x presupuesto por CodBIP ──────────────────────
    print("\nCruzando compras con presupuesto por CodBIP...")
    if "CodBIP" in presupuesto.columns and "CodBIP" in it.columns:
        proy_gasto = (presupuesto.groupby(["CodBIP","Anio"], as_index=False)
                      .agg(Proy_Gasto_MM=("Gasto_MM","sum"),
                           Proy_Presupuesto_MM=("Presupuesto_MM","sum"),
                           NombreProyecto=("NombreProyecto","first")))
        it["Anio_num"] = pd.to_numeric(it["Anio"], errors="coerce")
        it["CodBIP"]   = it["CodBIP"].astype(str).str.strip()
        proy_gasto["CodBIP"] = proy_gasto["CodBIP"].astype(str).str.strip()

        it = it.merge(proy_gasto.drop(columns=["NombreProyecto"], errors="ignore"),
                      left_on=["CodBIP","Anio_num"],
                      right_on=["CodBIP","Anio"],
                      how="left",
                      suffixes=("","_pres"))
        n_con_bip = it["Proy_Gasto_MM"].notna().sum()
        print(f"  Items con match BIP: {n_con_bip:,} ({100*n_con_bip/len(it):.1f}%)")

        # Sobrescribir el CSV items con las columnas de gasto del proyecto
        it.to_csv(BASE_ITEMS, sep=";", index=False, encoding="utf-8-sig")
        print(f"  Actualizado: {BASE_ITEMS}")

    # ── 4. Resumen por Servicio x Año ────────────────────────────────────
    print("\nGenerando resumen por Servicio x Año...")
    servicios_validos = [s for s in it["Servicio"].dropna().unique()
                         if not str(s).startswith(("MINVU_otros", "MOP_otros"))]

    resumen = (it[it["Servicio"].isin(servicios_validos)]
               .groupby(["Servicio","Region","Anio"], as_index=False)
               .agg(
                   Compras_MM           = ("MM","sum"),
                   OC                   = ("codigoOC" if "codigoOC" in it.columns else "CodigoOC","nunique"),
                   N_Proveedores        = ("ProveedorRUT","nunique"),
                   ComprasInversion_MM  = ("MM", lambda x: x[it.loc[x.index,"Subtitulo"].fillna(-1).astype(str)=="31"].sum()),
               ))

    # Agregar columnas de presupuesto si están disponibles
    if "Gasto_MM" in presupuesto.columns and "Servicio" in presupuesto.columns:
        pres_serv = (presupuesto.groupby(["Servicio","Anio"], as_index=False)
                     .agg(RS_Presupuesto_MM=("Presupuesto_MM","sum"),
                          RS_Gasto_MM      =("Gasto_MM","sum")))
        resumen = resumen.merge(pres_serv, on=["Servicio","Anio"], how="left")

    sal_res = BASE_OUT / "compras_presupuesto_resumen.csv"
    resumen.to_csv(sal_res, sep=";", index=False, encoding="utf-8-sig")
    print(f"Guardado: {sal_res}")
    print(f"  {len(resumen):,} filas, {resumen.shape[1]} columnas")

    # ── 5. Paneles por región y mes ──────────────────────────────────────
    print("\nGenerando paneles adicionales...")

    panel_mes = (it.groupby(["Region","Anio","Mes"], as_index=False)
                 .agg(Compras_MM=("MM","sum"),
                      OC=("codigoOC" if "codigoOC" in it.columns else "CodigoOC","nunique")))
    panel_mes.to_csv(BASE_OUT/"panel_region_mes.csv", sep=";", index=False, encoding="utf-8-sig")

    panel_serv = (it.groupby(["Region","Servicio","Anio"], as_index=False)
                  .agg(Compras_MM=("MM","sum"),
                       OC=("codigoOC" if "codigoOC" in it.columns else "CodigoOC","nunique")))
    panel_serv.to_csv(BASE_OUT/"panel_region_servicio.csv", sep=";", index=False, encoding="utf-8-sig")

    print("Guardados: panel_region_mes.csv, panel_region_servicio.csv")
    print("\n=== Pipeline Paso 2 completado ===")


if __name__ == "__main__":
    main()
