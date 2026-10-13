"""
03_generar_tablas_analisis.py
==============================
PASO 3 DEL PIPELINE: Generación de tablas analíticas y paneles para el análisis.

Entrada : analisis/compras_presupuesto_items.csv  (del Paso 1)
          analisis/compras_presupuesto_resumen.csv (del Paso 2)

Salidas : analisis/panel_region_mes.csv
          analisis/panel_region_servicio.csv
          + tablas intermedias para el notebook 03

Ejecutar desde: entrega final/
    python pipeline/03_generar_tablas_analisis.py
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path("../01_datos/procesados")


def main():
    print("Cargando datos procesados...")
    it  = pd.read_csv(BASE / "compras_presupuesto_items.csv",  sep=";", low_memory=False)
    res = pd.read_csv(BASE / "compras_presupuesto_resumen.csv", sep=";", encoding="utf-8-sig")

    # Normalizar
    it  = it[pd.to_numeric(it["MontoNetoItemCLP"], errors="coerce").fillna(0) > 0].copy()
    it["MM"]  = pd.to_numeric(it["MontoNetoItemCLP"], errors="coerce") / 1e6
    it["Anio"] = pd.to_numeric(it["Anio"], errors="coerce")
    it["Mes"]  = pd.to_numeric(it["Mes"],  errors="coerce")
    it["Trimestre"] = ((it["Mes"] - 1) // 3 + 1).map({1:"Q1",2:"Q2",3:"Q3",4:"Q4"})

    # Columna OC normalizada
    col_oc = "codigoOC" if "codigoOC" in it.columns else "CodigoOC"

    print(f"  Items  : {len(it):,}")
    print(f"  Resumen: {len(res):,}")

    # ── Panel Región x Mes ───────────────────────────────────────────────
    print("\nGenerando panel_region_mes.csv...")
    panel_mes = (it.groupby(["Region","Anio","Mes","Trimestre"], as_index=False)
                 .agg(
                     Compras_MM   = ("MM","sum"),
                     OC           = (col_oc,"nunique"),
                     N_Proveedores= ("ProveedorRUT","nunique"),
                 ))
    panel_mes["Ticket_Medio_MM"] = panel_mes["Compras_MM"] / panel_mes["OC"].replace(0, np.nan)
    panel_mes.to_csv(BASE/"panel_region_mes.csv", sep=";", index=False, encoding="utf-8-sig")
    print(f"  Guardado: {len(panel_mes):,} filas")

    # ── Panel Región x Servicio ──────────────────────────────────────────
    print("Generando panel_region_servicio.csv...")
    panel_serv = (it.groupby(["Region","Servicio","Anio"], as_index=False)
                  .agg(
                      Compras_MM   = ("MM","sum"),
                      OC           = (col_oc,"nunique"),
                      N_Proveedores= ("ProveedorRUT","nunique"),
                  ))
    panel_serv["Ticket_Medio_MM"] = panel_serv["Compras_MM"] / panel_serv["OC"].replace(0, np.nan)
    panel_serv.to_csv(BASE/"panel_region_servicio.csv", sep=";", index=False, encoding="utf-8-sig")
    print(f"  Guardado: {len(panel_serv):,} filas")

    # ── Tabla A: Región x Año x Modalidad ────────────────────────────────
    print("Generando tabla_A_region_anio_modalidad.csv...")
    tabla_A = (it.groupby(["Region","Anio","TipoCompra"], as_index=False)
               .agg(N_OC=( col_oc,"nunique"), MM=("MM","sum"),
                    N_Prov=("ProveedorRUT","nunique")))
    tabla_A["Ticket_Medio_MM"] = tabla_A["MM"] / tabla_A["N_OC"].replace(0, np.nan)
    tabla_A.to_csv(BASE/"tabla_A_region_anio_modalidad.csv", sep=";", index=False, encoding="utf-8-sig")
    print(f"  Guardado: {len(tabla_A):,} filas")

    # ── Tabla E: Trato Directo por Servicio ──────────────────────────────
    print("Generando tabla_E_trato_directo.csv...")
    oc_tipo = it.groupby([col_oc,"Servicio","TipoCompra"]).MM.sum().reset_index()
    td_pct  = (oc_tipo.groupby("Servicio")
                .apply(lambda d: 100*(d["TipoCompra"]=="Trato Directo").mean(),
                       include_groups=False)
                .rename("Pct_TD_OC").reset_index())
    td_mm   = (oc_tipo[oc_tipo["TipoCompra"]=="Trato Directo"]
                .groupby("Servicio").MM.sum().rename("MM_Trato_Directo").reset_index())
    tabla_E = td_pct.merge(td_mm, on="Servicio", how="left").sort_values("Pct_TD_OC", ascending=False)
    tabla_E.to_csv(BASE/"tabla_E_trato_directo.csv", sep=";", index=False, encoding="utf-8-sig")
    print(f"  Guardado: {len(tabla_E):,} filas")

    # ── Tabla B: Perfil de proveedores ────────────────────────────────────
    print("Generando tabla_B_perfil_proveedores.csv...")
    tabla_B = (it.groupby(["ProveedorRUT","TipoCompra"], as_index=False)
               .agg(N_OC=(col_oc,"nunique"), MM_total=("MM","sum"),
                    N_Regiones=("Region","nunique"), N_Servicios=("Servicio","nunique"),
                    Anios=("Anio","nunique"))
               .sort_values("MM_total", ascending=False))
    tabla_B["Ticket_Medio_MM"] = tabla_B["MM_total"] / tabla_B["N_OC"].replace(0, np.nan)
    tabla_B.to_csv(BASE/"tabla_B_perfil_proveedores.csv", sep=";", index=False, encoding="utf-8-sig")
    print(f"  Guardado: {len(tabla_B):,} filas")

    # ── Resumen final ─────────────────────────────────────────────────────
    print("\n=== PIPELINE PASO 3 COMPLETADO ===")
    print("Archivos generados en analisis/:")
    for f in sorted(BASE.glob("*.csv")):
        size_kb = round(f.stat().st_size / 1e3, 0)
        print(f"  {f.name:50s} {size_kb:>8.0f} KB")


if __name__ == "__main__":
    main()
