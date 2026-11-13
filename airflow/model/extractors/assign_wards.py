"""Assign the 2022 City of Ithaca ward as a categorical, property-level feature.

Wards are administrative areas (not rental submarkets). Unknown / outside-city
locations remain missing; they must not be assigned to the nearest ward.
"""
from pathlib import Path

import geopandas as gpd
import pandas as pd


WARD_FILE = Path(__file__).resolve().parents[1] / "data" / "Wards_2022.geojson"
WARD_NAMES = tuple(f"Ward {i}" for i in range(1, 6))


def assign_wards(frame: pd.DataFrame) -> pd.DataFrame:
    """Return frame with nullable ward labels via a WGS84 polygon spatial join.

    Every input listing row is retained. Boundary coincidences are resolved
    deterministically by WardNum, without duplicating listings.
    """
    out = frame.copy().reset_index(drop=True)
    if not {"latitude", "longitude"}.issubset(out.columns):
        raise ValueError("Ward assignment requires latitude and longitude")
    if not WARD_FILE.is_file():
        raise FileNotFoundError(f"Ward GeoJSON missing: {WARD_FILE}")

    wards = gpd.read_file(WARD_FILE)[["WardNum", "geometry"]]
    if wards.crs is None:
        raise ValueError("Wards_2022.geojson must declare a geographic CRS")
    wards = wards.to_crs("EPSG:4326")
    if set(wards["WardNum"].astype(int)) != set(range(1, 6)):
        raise ValueError("Expected exactly Ithaca WardNum values 1 through 5")

    lat = pd.to_numeric(out["latitude"], errors="coerce")
    lon = pd.to_numeric(out["longitude"], errors="coerce")
    valid = lat.between(-90, 90) & lon.between(-180, 180)
    out["ward"] = pd.Series(pd.NA, index=out.index, dtype="string")
    if not valid.any():
        return out

    pts = gpd.GeoDataFrame(
        {"_row": out.index[valid]},
        geometry=gpd.points_from_xy(lon[valid], lat[valid]),
        crs="EPSG:4326",
    )
    matches = gpd.sjoin(pts, wards, how="left", predicate="intersects")
    # Intersections also include exact shared boundaries. Keep the smallest
    # ward ID in the rare event a point touches more than one polygon.
    matches = matches.dropna(subset=["WardNum"]).sort_values(["_row", "WardNum"])
    matches = matches.drop_duplicates("_row", keep="first")
    out.loc[matches["_row"].to_numpy(), "ward"] = (
        "Ward " + matches["WardNum"].astype(int).astype(str).to_numpy()
    )
    print(f"🏘️ 2022 ward classification: {out['ward'].notna().sum()}/{len(out)} listings within city wards")
    return out


def add_ward_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    """One-hot categories for ML; missing/outside-city remain NaN."""
    out = frame.copy()
    wards = out["ward"] if "ward" in out else pd.Series(pd.NA, index=out.index)
    wards = wards.astype("string")
    for label in WARD_NAMES:
        out["ward_" + label.split()[-1]] = wards.eq(label).astype("Float64").astype(float)
    return out
