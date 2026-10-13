"""
dashboard_app.py
Tablero interactivo de compras MOP 2018-2019 (ChileCompra × presupuesto de inversión MOP).
Indicador 3.1.5.I.5. Todos los valores se calculan en vivo desde los CSV del proyecto.

Ejecutar desde la carpeta 'entrega final/':
    pip install streamlit plotly pandas scipy
    streamlit run 04_dashboard/dashboard_app.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

st.set_page_config(page_title="Compras MOP 2018-2019", page_icon="📊", layout="wide")

# Paleta apta para daltonismo (Okabe-Ito) + texto con contraste AA
AZUL, NARANJA, VERDE, ROJO, GRIS = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#4A4A4A"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def buscar(nombre, obligatorio=True):
    aqui = Path(__file__).resolve().parent
    # Buscar en distintas combinaciones de rutas según dónde se ejecute streamlit
    candidatos = [
        aqui.parent / "01_datos" / "procesados" / nombre,   # desde 04_dashboard/
        aqui / "01_datos" / "procesados" / nombre,          # si datos estuviera en la misma carpeta
        Path.cwd() / "01_datos" / "procesados" / nombre,    # cwd = entrega final/
        Path.cwd() / "entrega final" / "01_datos" / "procesados" / nombre, # cwd = raíz del repo
        Path.cwd().parent / "01_datos" / "procesados" / nombre,
        aqui.parent / nombre,
        aqui / nombre,
    ]
    for p in candidatos:
        if p.exists():
            return p
    if obligatorio:
        rutas = '\n'.join(str(c) for c in candidatos)
        st.error(f"No se encontró {nombre}.\nBuscado en:\n{rutas}")
        st.stop()
    return None


@st.cache_data(show_spinner="Cargando órdenes de compra…")
def cargar():
    p_parquet = buscar("compras_presupuesto_items.parquet", obligatorio=False)
    if p_parquet:
        it = pd.read_parquet(p_parquet)
    else:
        it = pd.read_csv(buscar("compras_presupuesto_items.csv"), sep=";", encoding="utf-8-sig", low_memory=False,
                         usecols=["TipoCompra", "codigoOC", "Anio", "Mes", "MontoNetoItemCLP", "Region",
                                  "Servicio", "Subtitulo", "ProveedorRUT"])
    if "MM" not in it.columns:
        it["MM"] = it.MontoNetoItemCLP / 1e6
    res = pd.read_csv(buscar("compras_presupuesto_resumen.csv"), sep=";", encoding="utf-8-sig")
    return it, res


it, res = cargar()

# ------------------------------------------------------------------ filtros
st.sidebar.header("Filtros")
anios = st.sidebar.multiselect("Año", sorted(it.Anio.dropna().unique().astype(int)), default=[2018, 2019])
regiones = st.sidebar.multiselect("Región (vacío = todas)", sorted(it.Region.dropna().unique()))
servicios = st.sidebar.multiselect("Servicio (vacío = todos)", sorted(it.Servicio.dropna().unique()))
tipos = st.sidebar.multiselect("Modalidad", sorted(it.TipoCompra.dropna().unique()),
                               default=sorted(it.TipoCompra.dropna().unique()))

f = it[it.Anio.isin(anios) & it.TipoCompra.isin(tipos)]
r = res[res.Anio.isin(anios)]
if regiones:
    f, r = f[f.Region.isin(regiones)], r[r.Region.isin(regiones)]
if servicios:
    f, r = f[f.Servicio.isin(servicios)], r[r.Servicio.isin(servicios)]

st.sidebar.markdown("---")
st.sidebar.caption(
    "**Trazabilidad**\n\n"
    "• Compras: datos abiertos Mercado Público (ChileCompra)\n\n"
    "• Presupuesto: inversión MOP por proyecto BIP\n\n"
    "• Unión: región × servicio × año, y código BIP cuando aparece en la OC\n\n"
    "• Archivos: `compras_presupuesto_items.csv`, `compras_presupuesto_resumen.csv`"
)

if f.empty:
    st.warning("La combinación de filtros no tiene órdenes de compra.")
    st.stop()

# ------------------------------------------------------------------ KPIs
st.title("Compras del MOP y MINVU/SERVIU en Mercado Público, 2018-2019")
st.caption("¿Dónde concentrar la fiscalización y cómo planificar mejor el calendario de compras?")

def fmt(v, d=0):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

tot = f.MM.sum()
n_oc = f.codigoOC.nunique()
td = 100 * f.loc[f.TipoCompra == "Trato Directo", "MM"].sum() / tot
mes = f.groupby("Mes").MM.sum().reindex(range(1, 13), fill_value=0)
q4 = 100 * mes.loc[10:12].sum() / mes.sum()
mop_r = r[~r.Servicio.fillna("").str.startswith("MINVU")]
cob = 100 * mop_r.Compras_MM.sum() / mop_r.RS_Gasto_MM.sum() if mop_r.RS_Gasto_MM.sum() > 0 else np.nan

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Monto contratado", f"$ {fmt(tot)} MM")
c2.metric("Órdenes de compra", fmt(n_oc))
c3.metric("% monto por trato directo", f"{fmt(td, 1)} %",
          delta="sobre 25 %: revisar" if td > 25 else "bajo 25 %", delta_color="inverse" if td > 25 else "normal")
c4.metric("% del monto en oct-dic", f"{fmt(q4, 1)} %",
          delta="sobre 30 %: concentrado" if q4 > 30 else "bajo 30 %", delta_color="inverse" if q4 > 30 else "normal")
c5.metric("Compras / gasto inversión MOP", "s/d" if np.isnan(cob) else f"{fmt(cob, 1)} %",
          help="Solo servicios MOP (sin MINVU). Mercado Público no registra los grandes contratos de obra.")

t1, t2, t3 = st.tabs(["Estacionalidad", "Presupuesto vs compras", "Modalidad y servicio"])

with t1:
    g = f.groupby(["Anio", "Mes"]).agg(MM=("MM", "sum"), OC=("codigoOC", "nunique")).reset_index()
    fig = go.Figure()
    for a, col in zip(sorted(g.Anio.unique()), (AZUL, NARANJA)):
        d = g[g.Anio == a]
        fig.add_bar(x=[MESES[m - 1] for m in d.Mes], y=d.MM, name=f"Monto {int(a)} (MM$)", marker_color=col)
    tot_oc = g.groupby("Mes").OC.sum()
    fig.add_scatter(x=[MESES[m - 1] for m in tot_oc.index], y=tot_oc.values, name="N.º OC (total)",
                    yaxis="y2", mode="lines+markers", line=dict(color=GRIS, width=2))
    fig.update_layout(barmode="group", template="plotly_white", height=430,
                      yaxis=dict(title="Monto (millones $)"),
                      yaxis2=dict(title="N.º de OC", overlaying="y", side="right", showgrid=False),
                      legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Lectura: el último trimestre reúne el {fmt(q4, 1)} % del monto filtrado. "
               "Un calendario de licitación más temprano reduciría la carga de fin de año.")

with t2:
    rs = r[~r.Servicio.fillna("").str.startswith(("MINVU", "MOP otros"))]
    y_col = st.radio("Compras a comparar", ["Compras_MM", "ComprasInversion_MM"], horizontal=True,
                     format_func=lambda c: "Todas las compras" if c == "Compras_MM" else "Solo subtítulo 31 (inversión)")
    d = rs[(rs.RS_Gasto_MM > 0) & (rs[y_col] > 0)].copy()
    if len(d) >= 5:
        lx, ly = np.log10(d.RS_Gasto_MM), np.log10(d[y_col])
        reg = stats.linregress(lx, ly)
        d["Año"] = d.Anio.astype(int).astype(str)
        fig = px.scatter(d, x="RS_Gasto_MM", y=y_col, color="Año", log_x=True, log_y=True,
                         hover_data=["Region", "Servicio"], template="plotly_white", height=430,
                         color_discrete_sequence=[AZUL, NARANJA],
                         labels={"RS_Gasto_MM": "Gasto de inversión MOP (MM$, log)", y_col: "Compras en OC (MM$, log)"})
        xs = np.linspace(lx.min(), lx.max(), 50)
        fig.add_scatter(x=10 ** xs, y=10 ** (reg.intercept + reg.slope * xs), mode="lines",
                        name="Ajuste log-log", line=dict(color=GRIS, dash="dash"))
        st.plotly_chart(fig, use_container_width=True)
        p_txt = "< 0,001" if reg.pvalue < 0.001 else fmt(reg.pvalue, 3)
        st.markdown(f"**n = {len(d)} · pendiente = {fmt(reg.slope, 2)} · R² = {fmt(reg.rvalue ** 2, 2)} · p {p_txt}**")
        st.caption("La pendiente es una elasticidad: con 0,5, un 10 % más de gasto se asocia a ~5 % más de compras. "
                   "Es una asociación, no un efecto causal; el R² indica cuánta variación queda sin explicar.")
    else:
        st.info("Muy pocas combinaciones región × servicio con estos filtros para ajustar la regresión.")

with t3:
    a, b = st.columns(2)
    m = f.groupby("TipoCompra").MM.sum().sort_values()
    a.plotly_chart(px.bar(x=m.values, y=m.index, orientation="h", template="plotly_white", height=360,
                          labels={"x": "Monto (MM$)", "y": ""}, color_discrete_sequence=[AZUL],
                          title="Monto por modalidad"), use_container_width=True)
    oc = f.groupby(["codigoOC", "Servicio", "TipoCompra"]).MM.sum().reset_index()
    s = oc.groupby("Servicio").agg(OC=("codigoOC", "nunique"), Monto_MM=("MM", "sum"),
                                   Mediana_CLP=("MM", lambda v: 1e6 * v.median()),
                                   TD_pct=("TipoCompra", lambda v: 100 * (v == "Trato Directo").mean()))
    s["Alerta"] = np.where(s.TD_pct > 25, "Revisar", "")
    s = s.sort_values("Monto_MM", ascending=False)
    b.plotly_chart(px.bar(s.reset_index(), x="TD_pct", y="Servicio", orientation="h", template="plotly_white",
                          height=360, color=s.TD_pct > 25, color_discrete_map={True: ROJO, False: GRIS},
                          labels={"TD_pct": "% de OC por trato directo", "Servicio": "", "color": "> 25 %"},
                          title="Trato directo por servicio (% de OC)"), use_container_width=True)
    st.dataframe(s.style.format({"OC": "{:,.0f}", "Monto_MM": "{:,.0f}", "Mediana_CLP": "{:,.0f}", "TD_pct": "{:.1f} %"}),
                 use_container_width=True)
    st.download_button("Descargar tabla (CSV)", s.to_csv(sep=";").encode("utf-8-sig"), "servicios_filtrados.csv")
