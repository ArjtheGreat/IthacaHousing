from sklearn.neighbors import NearestNeighbors
import numpy as np
import pandas as pd

def perform_cma(X, apartments_for_rent, n_neighbors=4):
    """
    Comparative Market Analysis (CMA) using KNN.
    Predicts rent as the average rent of nearest neighbors.
    
    Parameters
    X : np.array or DataFrame
        Feature matrix with spatial + property features.
    apartments_for_rent : pd.DataFrame
        DataFrame with at least ['ListingId', 'Rent'].
    n_neighbors : int
        Number of neighbors to consider (including the listing itself).
    
    Returns
    apartments_for_rent : pd.DataFrame
        With extra columns:
          - nearest_neighbor_listingIds (list of IDs)
          - predicted_rent_cma (float)
    """    
    X_array = np.asarray(X, dtype=np.float64)
    if not np.isfinite(X_array).all():
        X_array = np.nan_to_num(X_array, nan=0.0, posinf=0.0, neginf=0.0)

    nbrs = NearestNeighbors(n_neighbors=n_neighbors, algorithm="ball_tree")
    nbrs.fit(X_array)

    _, indices = nbrs.kneighbors(X_array)

    # Avoid Arrow-backed Series fancy-indexing (2D take → ArrowInvalid).
    listing_ids = np.asarray(
        apartments_for_rent["ListingId"].astype(str).tolist(), dtype=object
    )
    neighbor_ids = listing_ids[indices[:, 1:]]
    apartments_for_rent["nearest_neighbor_listingIds"] = [
        row.tolist() for row in neighbor_ids
    ]

    rents = pd.to_numeric(
        apartments_for_rent["rent_per_person"], errors="coerce"
    ).to_numpy(dtype=float)
    rents = np.nan_to_num(rents, nan=0.0)

    predicted_rents = [
        float(np.mean(rents[row_indices[1:]])) for row_indices in indices
    ]
    apartments_for_rent["predicted_rent_cma"] = predicted_rents

    return apartments_for_rent

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
