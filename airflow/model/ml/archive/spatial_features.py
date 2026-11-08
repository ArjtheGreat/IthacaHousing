"""Leakage-resistant spatial features for property-grouped rent prediction.

H3 target encodings and KNN rent lags use OTHER PROPERTIES for training
observations; held-out properties draw only on outer-fold training properties.
No same-property units or own labels enter target-derived spatial features.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from h3 import latlng_to_cell


def add_spatial_fold_features(train, test, y_train, k=10, h3_reses=(6, 7)):
    """Return feature frames with out-of-property H3 and KNN spatial signals.

    Coordinates are used to build the H3 and KNN columns and are left on the
    returned frames so the model can also use latitude and longitude directly.
    Property-level averages prevent large buildings dominating comparisons.
    """
    tr = train.copy()
    te = test.copy()
    for df in (tr, te):
        for col in ("latitude", "longitude"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    reference = tr[["PropertyId", "latitude", "longitude"]].copy()
    reference["_log_rent"] = np.asarray(y_train, dtype=float)
    if "YR_BUILT_ENCODED" in tr:
        reference["_year"] = pd.to_numeric(tr["YR_BUILT_ENCODED"], errors="coerce")
    else:
        reference["_year"] = np.nan
    props = reference.groupby("PropertyId", as_index=False).agg(
        latitude=("latitude", "mean"),
        longitude=("longitude", "mean"),
        log_rent=("_log_rent", "mean"),
        year=("_year", "mean"),
    )
    props = props.dropna(subset=["latitude", "longitude"])
    if len(props) < 2:
        raise ValueError("Spatial OOF requires at least two coordinate-bearing training properties")

    for res in h3_reses:
        cell_col = f"_h3_{res}"
        props[cell_col] = [
            latlng_to_cell(float(lat), float(lon), res)
            for lat, lon in zip(props.latitude, props.longitude)
        ]

    ref_pid = props["PropertyId"].astype(str).to_numpy()
    ref_lat = np.radians(props["latitude"].to_numpy(float))
    ref_lon = np.radians(props["longitude"].to_numpy(float))
    ref_rent = props["log_rent"].to_numpy(float)
    ref_year = props["year"].to_numpy(float)

    def build_features(frame, exclude_own):
        q_pid = frame["PropertyId"].astype(str).to_numpy()
        q_lat = np.radians(frame["latitude"].to_numpy(float))
        q_lon = np.radians(frame["longitude"].to_numpy(float))
        # Haversine distance in km. At Ithaca scale this is more meaningful
        # than Euclidean distances in decimal degrees.
        lat_delta = q_lat[:, None] - ref_lat[None, :]
        lon_delta = q_lon[:, None] - ref_lon[None, :]
        a = (
            np.sin(lat_delta / 2) ** 2
            + np.cos(q_lat[:, None]) * np.cos(ref_lat[None, :])
            * np.sin(lon_delta / 2) ** 2
        )
        distances = 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
        distances[~np.isfinite(distances)] = np.inf
        if exclude_own:
            distances[q_pid[:, None] == ref_pid[None, :]] = np.inf

        result = pd.DataFrame(index=frame.index)
        # Do not give one same-coordinate property effectively infinite weight.
        # All weights are capped at the equivalent of 30 meters.
        for value_col, values in (
            ("knn_rent_log", ref_rent), ("knn_yearbuilt", ref_year),
        ):
            outputs = []
            for row in distances:
                ok = np.isfinite(row) & np.isfinite(values)
                choices = np.flatnonzero(ok)
                if choices.size == 0:
                    outputs.append(np.nan)
                    continue
                nearest = choices[np.argsort(row[choices])[:k]]
                weights = 1.0 / np.maximum(row[nearest], 0.03)
                outputs.append(float(np.average(values[nearest], weights=weights)))
            result[value_col] = outputs

        for res in h3_reses:
            cell_col = f"_h3_{res}"
            cells = props[cell_col].to_numpy()
            q_cells = [
                latlng_to_cell(float(lat), float(lon), res)
                if np.isfinite(lat) and np.isfinite(lon) else None
                for lat, lon in zip(frame["latitude"], frame["longitude"])
            ]
            means = []
            for pid, cell in zip(q_pid, q_cells):
                eligible = cells == cell
                if exclude_own:
                    eligible &= ref_pid != pid
                if np.any(eligible):
                    means.append(float(np.mean(ref_rent[eligible])))
                else:
                    fallback = ref_pid != pid if exclude_own else np.ones(len(ref_pid), bool)
                    means.append(float(np.mean(ref_rent[fallback])) if np.any(fallback) else np.nan)
            result[f"h3_{res}_te"] = means
        return result

    train_features = build_features(tr, exclude_own=True)
    test_features = build_features(te, exclude_own=False)
    for col in train_features.columns:
        tr[col] = train_features[col]
        te[col] = test_features[col]
    return tr, te
