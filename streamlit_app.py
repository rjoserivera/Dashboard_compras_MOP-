"""
streamlit_app.py
Punto de entrada para Streamlit Community Cloud.
Ejecuta el dashboard ubicado en 04_dashboard/dashboard_app.py.
"""
import runpy
from pathlib import Path

dashboard_path = Path(__file__).parent / "04_dashboard" / "dashboard_app.py"
runpy.run_path(str(dashboard_path), run_name="__main__")
