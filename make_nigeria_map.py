"""
Make data/nigeria_states.geojson for the Streamlit app (run ONCE).

Reads the GADM state boundaries already in your pipeline folder,
simplifies them so the file stays small, matches the state names to the
names used in forecasts.csv, and adds a label point for each state.

Run from the foodsec-streamlit folder, with the .venv active:
    pip install geopandas
    python make_nigeria_map.py
geopandas is only needed for this step — do NOT add it to requirements.txt.
"""
import json, re
from pathlib import Path
import geopandas as gpd
import pandas as pd

GPKG = Path.home() / "Thesis (Jis)/foodsec/data/raw/boundaries/gadm41_NGA.gpkg"
OUT = Path("data/nigeria_states.geojson")

norm = lambda s: re.sub(r"[^a-z]", "", str(s).lower())
ALIAS = {"nassarawa": "nasarawa", "fct": "federalcapitalterritory", "abuja": "federalcapitalterritory"}

layers = gpd.list_layers(GPKG).name.tolist() if hasattr(gpd, "list_layers") else ["ADM_ADM_1"]
layer = next(l for l in layers if l.endswith("1"))
g = gpd.read_file(GPKG, layer=layer)[["NAME_1", "geometry"]]

ours = set(pd.read_csv("data/history.csv").state) | set(pd.read_csv("data/forecasts.csv").state)
lookup = {norm(s): s for s in ours}
g["state"] = [lookup.get(ALIAS.get(norm(n), norm(n))) for n in g.NAME_1]
missing = g[g.state.isna()].NAME_1.tolist()
g["state"] = g.state.fillna(g.NAME_1)

g = g.to_crs(4326)
g["geometry"] = g.geometry.simplify(0.01, preserve_topology=True)

# Plotly draws maps with d3, which needs outer rings CLOCKWISE; otherwise
# each state is drawn "inside out" and covers the whole globe.
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.polygon import orient
def cw(geom):
    if isinstance(geom, Polygon):
        return orient(geom, sign=-1.0)
    if isinstance(geom, MultiPolygon):
        return MultiPolygon([orient(p, sign=-1.0) for p in geom.geoms])
    return geom
g["geometry"] = g.geometry.apply(cw)
pts = g.geometry.representative_point()
g["lon"], g["lat"] = pts.x.round(3), pts.y.round(3)
g = g[["state", "lon", "lat", "geometry"]]

OUT.write_text(g.to_json(drop_id=True))
print(f"Wrote {OUT}  ({OUT.stat().st_size / 1000:.0f} KB, {len(g)} states)")
print("Unmatched boundary names:", missing or "none")
print("App states with no boundary:", sorted(ours - set(g.state)) or "none")
