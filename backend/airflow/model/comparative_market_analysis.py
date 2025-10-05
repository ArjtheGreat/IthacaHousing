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
    X_array = np.array(X)
    
    nbrs = NearestNeighbors(n_neighbors=n_neighbors, algorithm='ball_tree')
    nbrs.fit(X_array)
    
    distances, indices = nbrs.kneighbors(X_array)
    listing_ids = apartments_for_rent['ListingId'].values
    
    nearest_neighbor_listingIds = listing_ids[indices[:, 1:]]
    apartments_for_rent["nearest_neighbor_listingIds"] = nearest_neighbor_listingIds.tolist()
    
    rents = apartments_for_rent['rent_per_person'].values
    predicted_rents = []
    
    for row_indices in indices:
        neighbor_ids = row_indices[1:] 
        neighbor_rents = rents[neighbor_ids]
        predicted_rents.append(np.mean(neighbor_rents))
    
    apartments_for_rent["predicted_rent_cma"] = predicted_rents
    
    return apartments_for_rent

def define_X_for_cma(apartments_for_rent):
    """
    Define X for CMA with data cleaning
    """
    X = apartments_for_rent[["LengthAvailable", "Pets", "combined_bedrooms_bathrooms", "drive_time", "transit_score", "amenities_score", "overallsafetyratingpct", "GmapLatitude", "GmapLongitude"]]

    X_clean = X.copy()
    for col in X_clean.columns:
        X_clean[col] = pd.to_numeric(X_clean[col], errors='coerce')
    X_clean = X_clean.fillna(X_clean.median())
    X_clean = X_clean.fillna(0)

    X_clean = X_clean.replace([np.inf, -np.inf], np.nan)
    X_clean = X_clean.fillna(0)

    X_clean = X_clean.astype('float64')
    
    return X_clean