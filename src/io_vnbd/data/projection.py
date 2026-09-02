"""
Convert V- GPS lat/lon into a local metric (x, y) frame centered on a run's
first GPS fix, using pyproj's AzimuthalEquidistant projection. This is a
prerequisite for src/windowing.py's `xy` argument and for ATE/RPE in
src/evaluate.py, since raw lat/lon degrees are not linearly comparable to
meters.

Usage:
    from scripts.project_gps import project_to_local_xy
    xy = project_to_local_xy(v_df["lat"], v_df["lon"])
"""

import pandas as pd
from pyproj import Transformer


def project_to_local_xy(lat: pd.Series, lon: pd.Series) -> pd.DataFrame:
    origin_lat, origin_lon = lat.iloc[0], lon.iloc[0]
    proj_str = f"+proj=aeqd +lat_0={origin_lat} +lon_0={origin_lon} +units=m +datum=WGS84"
    transformer = Transformer.from_crs("EPSG:4326", proj_str, always_xy=True)
    x, y = transformer.transform(lon.values, lat.values)
    return pd.DataFrame({"x": x, "y": y})
