from sklearn.neighbors import NearestNeighbors
import numpy as np
import pandas as pd

def perform_cma(X, apartments_for_rent, n_neighbors=4):
    """Find comparable listings at OTHER properties, never the subject building.

    n_neighbors retains its legacy convention: 4 means up to 3 comparables.
    Both displayed IDs and the CMA rent mean use the exact same eligible rows.
    """
    if len(X) != len(apartments_for_rent):
        raise ValueError("CMA features and listing rows must be aligned")
    if "ListingId" not in apartments_for_rent or "rent_per_person" not in apartments_for_rent:
        raise ValueError("CMA requires ListingId and rent_per_person")
    if n_neighbors < 2:
        raise ValueError("n_neighbors must be at least 2")

    out = apartments_for_rent.copy()
    ids = out["ListingId"].astype(str).to_numpy()
    if "PropertyId" in out:
        properties = out["PropertyId"].astype(str).to_numpy()
    else:
        properties = np.array([identifier.rsplit("-", 1)[0] for identifier in ids])
    rents = pd.to_numeric(out["rent_per_person"], errors="coerce").to_numpy(dtype=float)
    features = np.asarray(X, dtype=np.float64)
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    # Enough candidate neighbors to skip even the largest same-property group.
    # Exclude nonpositive and missing rents as well.
    valid_rent = np.isfinite(rents) & (rents > 0)
    maximum_group = int(pd.Series(properties).value_counts().max()) if len(ids) else 0
    n_candidates = min(len(ids), maximum_group + n_neighbors - 1 +
                       int((~valid_rent).sum()))
    if not len(ids):
        out["nearest_neighbor_listingIds"] = []
        out["predicted_rent_cma"] = pd.Series(dtype=float)
        return out

    neighbors = NearestNeighbors(
        n_neighbors=max(1, n_candidates), algorithm="auto"
    ).fit(features)
    _, indices = neighbors.kneighbors(features)
    neighbor_ids = []
    predicted_rents = []
    for i, candidates in enumerate(indices):
        selected = [
            j for j in candidates
            if properties[j] != properties[i] and valid_rent[j] and ids[j] != ids[i]
        ][:n_neighbors - 1]
        neighbor_ids.append(ids[selected].tolist())
        predicted_rents.append(float(np.mean(rents[selected])) if selected else np.nan)

    out["nearest_neighbor_listingIds"] = neighbor_ids
    out["predicted_rent_cma"] = predicted_rents
    return out

def define_X_for_cma(apartments_for_rent):
    """
    Define X for CMA with data cleaning.
    Note: scraped AvailableFrom is availability text/date, not lease length.
    LengthAvailable is only used if it is already numeric (legacy API data).
    """
    df = apartments_for_rent.copy()

    if "GmapLatitude" not in df.columns and "latitude" in df.columns:
        df["GmapLatitude"] = df["latitude"]
    if "GmapLongitude" not in df.columns and "longitude" in df.columns:
        df["GmapLongitude"] = df["longitude"]

    # Only keep LengthAvailable when it is already a numeric lease-length signal.
    # Availability strings like "Now" / "08-01-2027" must not be treated as months.
    if "LengthAvailable" in df.columns:
        df["LengthAvailable"] = pd.to_numeric(df["LengthAvailable"], errors="coerce")

    safety_col = None
    if "valid_certificate_of_compliance" in df.columns:
        safety_col = "valid_certificate_of_compliance"
    elif "OverallSafetyRatingPct" in df.columns:
        safety_col = "OverallSafetyRatingPct"
    elif "overallsafetyratingpct" in df.columns:
        safety_col = "overallsafetyratingpct"
    
    base_cols = [
        "LengthAvailable",
        "Pets",
        "combined_bedrooms_bathrooms",
        "drive_time_urishall",
        "walk_time_urishall",
        "transit_score",
        "amenities_score",
        "GmapLatitude",
        "GmapLongitude",
    ]
    if safety_col:
        base_cols.append(safety_col)

    available_cols = [c for c in base_cols if c in df.columns]
    if not available_cols:
        raise ValueError("No CMA feature columns available")

    print(f"📋 CMA features: {available_cols}")
    X = df[available_cols]

    X_clean = X.copy()
    for col in X_clean.columns:
        X_clean[col] = pd.to_numeric(X_clean[col], errors='coerce')
    X_clean = X_clean.fillna(X_clean.median())
    X_clean = X_clean.fillna(0)

    X_clean = X_clean.replace([np.inf, -np.inf], np.nan)
    X_clean = X_clean.fillna(0)

    X_clean = X_clean.astype('float64')
    
    return X_clean
