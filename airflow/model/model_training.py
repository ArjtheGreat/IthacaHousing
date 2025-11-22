import numpy as np
import pandas as pd
import statsmodels.api as sm
import xgboost as xgb
from xgboost import XGBRegressor
from spreg import ML_Lag
from libpysal.weights import KNN, lag_spatial
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error, mean_absolute_error
from sklearn.neighbors import NearestNeighbors, kneighbors_graph, BallTree
from sklearn.cluster import SpectralClustering
from sklearn.preprocessing import OneHotEncoder
from h3 import latlng_to_cell


def define_X_Y_variables(apartments_for_rent):
    """
    Define X and y features for model training
    """
    safety_col = None
    if "valid_certificate_of_compliance" in apartments_for_rent.columns:
        safety_col = "valid_certificate_of_compliance"
    elif "OverallSafetyRatingPct" in apartments_for_rent.columns:
        safety_col = "OverallSafetyRatingPct"
    elif "overallsafetyratingpct" in apartments_for_rent.columns:
        safety_col = "overallsafetyratingpct"
    print(apartments_for_rent.columns)
    base_cols = [
        "LengthAvailable", 
        "Pets", 
        "combined_bedrooms_bathrooms", 
        "drive_time_urishall", 
        "transit_score", 
        "available_bedrooms_to_total_bedrooms_ratio", 
        # "sqft_per_sale_price", 
        "YR_BUILT_ENCODED",
        "Electricity Included",
        "Heat Included",
        "Water Included",
        "Internet Included",
        "Laundry Facilities",
        "Air Conditioning",
        "Furnished"
    ]

    if safety_col:
        base_cols.append(safety_col)
    
    available_cols = [col for col in base_cols if col in apartments_for_rent.columns]
    
    if len(available_cols) == 0:
        raise ValueError("No features available for model training. Check data columns.")
    
    print(f"📊 Using {len(available_cols)} features for model training")
    print(f"📋 Feature columns: {available_cols}")
    
    X = apartments_for_rent[available_cols]
    y = apartments_for_rent["rent_per_person"]

    return X, y


def add_h3_cells(df, h3_reses=(6,), lat_col='latitude', lon_col='longitude'):
    """
    Add H3 cell columns to dataframe for geospatial indexing.
    
    Args:
        df: DataFrame with latitude and longitude columns
        h3_reses: tuple of H3 resolution levels to add (default: (6,))
        lat_col: name of latitude column
        lon_col: name of longitude column
    
    Returns:
        DataFrame with added H3 columns (h3_{res} for each res in h3_reses)
    """
    df = df.copy()
    
    if lat_col not in df.columns or lon_col not in df.columns:
        raise ValueError(f"Dataframe must contain '{lat_col}' and '{lon_col}' columns")
    
    for res in h3_reses:
        col = f"h3_{res}"
        df[col] = [
            latlng_to_cell(float(lat), float(lon), res)
            for lat, lon in zip(df[lat_col].values, df[lon_col].values)
        ]
    
    return df


def knn_distance_weighted_lag_train_test(
    X_train_raw,
    X_test_raw,
    values_train,
    lat_col="latitude",
    lon_col="longitude",
    k=10,
):
    """
    Compute distance-weighted KNN lag for train & test.

    - Neighbors are drawn ONLY from the training set.
    - For train points: neighbors = other train points.
    - For test points: neighbors = train points.
    """

    coords_train = X_train_raw[[lat_col, lon_col]].to_numpy()
    coords_test  = X_test_raw[[lat_col, lon_col]].to_numpy()

    nn = NearestNeighbors(n_neighbors=k+1, algorithm="ball_tree")
    nn.fit(coords_train)

    dist_tr, idx_tr = nn.kneighbors(coords_train)
    lag_train = []
    for d, nbrs in zip(dist_tr, idx_tr):
        d = d[1:]
        nbrs = nbrs[1:]
        w = 1.0 / (d + 1e-6)
        lag_train.append(np.average(values_train[nbrs], weights=w))

    dist_te, idx_te = nn.kneighbors(coords_test)
    lag_test = []
    for d, nbrs in zip(dist_te, idx_te):
        w = 1.0 / (d + 1e-6)
        lag_test.append(np.average(values_train[nbrs], weights=w))

    lag_train = pd.Series(lag_train, index=X_train_raw.index)
    lag_test  = pd.Series(lag_test, index=X_test_raw.index)

    return lag_train, lag_test


def spatial_spectral_clustering(df, n_clusters=6, lat_col='latitude', lon_col='longitude', n_neighbors=10):
    coords = df[[lat_col, lon_col]].to_numpy()

    knn_graph = kneighbors_graph(
        coords,
        n_neighbors=n_neighbors,
        include_self=False,
        mode='connectivity'
    )

    affinity = 0.5 * (knn_graph + knn_graph.T)

    clustering = SpectralClustering(
        n_clusters=n_clusters,
        affinity='precomputed',
        assign_labels='kmeans',
        random_state=42
    )

    df['spatial_cluster'] = clustering.fit_predict(affinity.toarray())
    return df


def spatial_block_cv_xgb(
    df,
    y,
    x_cols,
    cluster_col="spatial_cluster",
    h3_reses=(6, 7, ),
    k_knn=10,
    n_estimators=25,
    max_depth=6,
):
    """
    Spatial block CV for XGBoost with:
      - per-fold H3 target encoding
      - per-fold residual estimation
      - per-fold distance-weighted KNN lags of rent & residuals
      - proper one-hot encoding of categoricals only
    """

    if isinstance(y, pd.Series):
        y_series_all = y
    else:
        y_series_all = pd.Series(y, index=df.index)
    y_array = y_series_all.to_numpy().astype(float)

    metrics = []
    feature_importances = []

    blocks = df[cluster_col].unique()

    for blk in blocks:
        test_idx = df.index[df[cluster_col] == blk].to_numpy()
        train_idx = df.index[df[cluster_col] != blk].to_numpy()

        cols_with_coords = list(x_cols) + ['latitude', 'longitude']
        cols_with_coords = [col for col in cols_with_coords if col in df.columns]
        
        X_train = df.iloc[train_idx][cols_with_coords].copy()
        X_test  = df.iloc[test_idx][cols_with_coords].copy()

        y_train = y_array[train_idx]
        y_test  = y_array[test_idx]
        y_train_series = pd.Series(y_train, index=X_train.index)
        global_mean = y_train_series.mean()

        for res in h3_reses:
            h3_col = f"h3_{res}"
            te_col = f"h3_{res}_te"

            if h3_col not in X_train.columns:
                continue

            cell_means = y_train_series.groupby(X_train[h3_col]).mean()

            X_train[te_col] = X_train[h3_col].map(cell_means)
            X_test[te_col]  = X_test[h3_col].map(cell_means).fillna(global_mean)

        drop_cols = [f"h3_{res}" for res in h3_reses if f"h3_{res}" in X_train.columns]
        X_train = X_train.drop(columns=drop_cols, errors="ignore")
        X_test  = X_test.drop(columns=drop_cols, errors="ignore")

        baseline = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
        )

        X_train_baseline = X_train.drop(columns=['latitude', 'longitude'], errors='ignore')
        X_test_baseline = X_test.drop(columns=['latitude', 'longitude'], errors='ignore')
        
        for col in X_train_baseline.columns:
            if X_train_baseline[col].dtype == 'object':
                X_train_baseline[col] = pd.to_numeric(X_train_baseline[col], errors='coerce').fillna(0)
            if X_test_baseline[col].dtype == 'object':
                X_test_baseline[col] = pd.to_numeric(X_test_baseline[col], errors='coerce').fillna(0)
        
        baseline.fit(X_train_baseline, y_train)

        train_residuals = y_train - baseline.predict(X_train_baseline)
        test_residuals  = y_test  - baseline.predict(X_test_baseline)

        X_train["residual"] = train_residuals
        X_test["residual"]  = test_residuals

        rent_train = y_train.copy()
        rent_lag_tr, rent_lag_te = knn_distance_weighted_lag_train_test(
            X_train, X_test, rent_train, lat_col="latitude", lon_col="longitude", k=k_knn
        )
        X_train[f"knn_rent_dw_{k_knn}"] = rent_lag_tr
        X_test[f"knn_rent_dw_{k_knn}"]  = rent_lag_te

        resid_lag_tr, resid_lag_te = knn_distance_weighted_lag_train_test(
            X_train, X_test, train_residuals, lat_col="latitude", lon_col="longitude", k=k_knn
        )
        X_train[f"knn_resid_dw_{k_knn}"] = resid_lag_tr
        X_test[f"knn_resid_dw_{k_knn}"]  = resid_lag_te


        year_vals = X_train["YR_BUILT_ENCODED"].to_numpy()

        year_lag_tr, year_lag_te = knn_distance_weighted_lag_train_test(
            X_train, X_test, year_vals, lat_col="latitude", lon_col="longitude", k=k_knn
        )

        X_train[f"knn_yearbuilt_dw_{k_knn}"] = year_lag_tr
        X_test[f"knn_yearbuilt_dw_{k_knn}"]  = year_lag_te

        X_train_model = X_train.drop(columns=['latitude', 'longitude'], errors='ignore')
        X_test_model = X_test.drop(columns=['latitude', 'longitude'], errors='ignore')
        
        model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train_model, y_train)

        y_pred = model.predict(X_test_model)

        rmse = mean_squared_error(y_test, y_pred)
        mae  = mean_absolute_error(y_test, y_pred)
        r2   = r2_score(y_test, y_pred)
        bias = float(np.mean(y_pred - y_test))
        block_size = len(y_test)

        imp = pd.Series(
            model.feature_importances_,
            index=X_train_model.columns
        )
        feature_importances.append(imp)

        metrics.append({"block": blk, "rmse": rmse, "mae": mae, "r2": r2, "bias": bias, "block_size": block_size})
        print(f"Block {blk}: RMSE={rmse:.4f}, R²={r2:.4f}, Bias={bias:.4f} Block Size={block_size}")

    metrics_df = pd.DataFrame(metrics)
    avg = metrics_df.mean(numeric_only=True).to_dict()
    print("\n--- Overall Spatial CV Performance ---")
    print(f"Mean RMSE: {avg['rmse']:.4f}, Mean R²: {avg['r2']:.4f}, Mean Bias: {avg['bias']:.4f}")

    fi_df = pd.DataFrame(feature_importances)

    fi_mean = fi_df.mean().sort_values(ascending=False)

    print("\n--- Average Feature Importance Across Spatial Folds ---")
    print(fi_mean)

    return metrics_df, avg

def compute_fair_rent(
    apartments_for_rent,
    y,
    x_cols,
    cluster_col="spatial_cluster",
    h3_reses=(6,),
    k_knn=10,
    n_estimators=100,
    max_depth=6,
):
    """
    Produces:
       - OOF fair rent predictions (spatially valid)
       - mispricing (DifferenceInFairValue) = actual - fair
       - percent mispricing (DifferenceInFairValue)

    This is the CORRECT way to compute fair value.
    """

    if isinstance(y, pd.Series):
        y_series_all = y
    else:
        y_series_all = pd.Series(y, index=apartments_for_rent.index)
    y_array = y_series_all.to_numpy().astype(float)

    fair_pred = pd.Series(index=apartments_for_rent.index, dtype=float)

    blocks = apartments_for_rent[cluster_col].unique()

    for blk in blocks:
        print(f"Processing block {blk}...")

        test_idx = apartments_for_rent.index[apartments_for_rent[cluster_col] == blk].to_numpy()
        train_idx = apartments_for_rent.index[apartments_for_rent[cluster_col] != blk].to_numpy()

        cols_with_coords = list(x_cols) + ['latitude', 'longitude']
        cols_with_coords = [col for col in cols_with_coords if col in apartments_for_rent.columns]
        
        X_train = apartments_for_rent.loc[train_idx, cols_with_coords].copy()
        X_test  = apartments_for_rent.loc[test_idx,  cols_with_coords].copy()

        y_train = y_array[train_idx]
        y_test  = y_array[test_idx]
        y_train_series = pd.Series(y_train, index=X_train.index)

        global_mean = y_train_series.mean()

        for res in h3_reses:
            h3_col = f"h3_{res}"
            te_col = f"h3_{res}_te"

            if h3_col not in X_train.columns:
                continue

            cell_means = y_train_series.groupby(X_train[h3_col]).mean()

            X_train[te_col] = X_train[h3_col].map(cell_means)
            X_test[te_col]  = X_test[h3_col].map(cell_means).fillna(global_mean)

        drop_cols = [f"h3_{res}" for res in h3_reses if f"h3_{res}" in X_train.columns]
        X_train = X_train.drop(columns=drop_cols, errors="ignore")
        X_test  = X_test.drop(columns=drop_cols, errors="ignore")

        X_train_baseline = X_train.drop(columns=['latitude', 'longitude'], errors='ignore')
        X_test_baseline = X_test.drop(columns=['latitude', 'longitude'], errors='ignore')
        
        for col in X_train_baseline.columns:
            if X_train_baseline[col].dtype == 'object':
                X_train_baseline[col] = pd.to_numeric(X_train_baseline[col], errors='coerce').fillna(0)
            if X_test_baseline[col].dtype == 'object':
                X_test_baseline[col] = pd.to_numeric(X_test_baseline[col], errors='coerce').fillna(0)
        
        baseline = xgb.XGBRegressor(
            n_estimators=50,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
        )
        baseline.fit(X_train_baseline, y_train)

        train_resid = y_train - baseline.predict(X_train_baseline)
        test_resid  = y_test  - baseline.predict(X_test_baseline)

        X_train["residual"] = train_resid
        X_test["residual"]  = test_resid

        rent_lag_tr, rent_lag_te = knn_distance_weighted_lag_train_test(
            X_train, X_test, y_train,
            lat_col="latitude", lon_col="longitude", k=k_knn
        )
        X_train[f"knn_rent_dw_{k_knn}"] = rent_lag_tr
        X_test[f"knn_rent_dw_{k_knn}"]  = rent_lag_te

        resid_lag_tr, resid_lag_te = knn_distance_weighted_lag_train_test(
            X_train, X_test, train_resid,
            lat_col="latitude", lon_col="longitude", k=k_knn
        )
        X_train[f"knn_resid_dw_{k_knn}"] = resid_lag_tr
        X_test[f"knn_resid_dw_{k_knn}"]  = resid_lag_te

        year_vals = X_train["YR_BUILT_ENCODED"].to_numpy()
        year_lag_tr, year_lag_te = knn_distance_weighted_lag_train_test(
            X_train, X_test, year_vals,
            lat_col="latitude", lon_col="longitude", k=k_knn
        )
        X_train[f"knn_yearbuilt_dw_{k_knn}"] = year_lag_tr
        X_test[f"knn_yearbuilt_dw_{k_knn}"]  = year_lag_te

        X_train_model = X_train.drop(columns=['latitude', 'longitude'], errors='ignore')
        X_test_model = X_test.drop(columns=['latitude', 'longitude'], errors='ignore')
        
        for col in X_train_model.columns:
            if X_train_model[col].dtype == 'object':
                X_train_model[col] = pd.to_numeric(X_train_model[col], errors='coerce').fillna(0)
            if X_test_model[col].dtype == 'object':
                X_test_model[col] = pd.to_numeric(X_test_model[col], errors='coerce').fillna(0)
        
        model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train_model, y_train)

        y_pred_test = model.predict(X_test_model)
        fair_pred.loc[test_idx] = y_pred_test

    apartments_for_rent_out = apartments_for_rent.copy()
    apartments_for_rent_out["log_rent"] = y_series_all
    apartments_for_rent_out["log_PredictedRent"] = fair_pred

    apartments_for_rent_out["actual_rent"] = np.exp(apartments_for_rent_out["log_rent"])
    apartments_for_rent_out["PredictedRent"] = np.exp(apartments_for_rent_out["log_PredictedRent"])

    apartments_for_rent_out["DifferenceInFairValue"] = apartments_for_rent_out["actual_rent"] - apartments_for_rent_out["PredictedRent"]
    apartments_for_rent_out["DifferenceInFairValuePct"] = (apartments_for_rent_out["DifferenceInFairValue"]) / apartments_for_rent_out["actual_rent"]


    return apartments_for_rent_out

### 
# OLD MODEL STORAGE
# FOR MEMORIES
###
def train_model(X, y, apartments_for_rent):
    """
    Defines X and Y Variables, scales variables throughto RobustScaler
    Log Transform Rental Prices, perform Spatial Regression on Coordinates, calculate residuals
    Trains Linear Regression Model
    Args:
        apartments_for_rent: dataframe with housing data
    """
    X = sm.add_constant(X)
    ols_model = sm.OLS(y, X).fit()

    y_pred = ols_model.predict(X)
    
    apartments_for_rent = find_residual_rental_amounts(y_pred, apartments_for_rent)

    return apartments_for_rent


def train_linear_model(X, y, apartments_for_rent):
    """
    Train linear regression model with spatial features
    """
    y_clean = y.copy()
    y_clean = np.nan_to_num(y_clean, nan=0.0, posinf=0.0, neginf=0.0)
    
    X_const = sm.add_constant(X)
    try:
        ols_model = sm.OLS(y_clean, X_const).fit()
    except np.linalg.LinAlgError as e:
        print(f"⚠️ Singular matrix error in Linear Regression: {e}")
        print(f"\n📊 Correlation matrix for X (features):")
        print(X.corr())
        print(f"Shape of X: {X.shape}")
        print(f"Columns in X: {X.columns.tolist()}")
        try:
            cond_num = np.linalg.cond(X_const.values)
            print(f"Condition number of X: {cond_num}")
        except:
            print("Condition number calculation failed (likely singular matrix)")
        raise 
    
    y_pred = ols_model.predict(X_const)
    apartments_for_rent = find_residual_rental_amounts(y_pred, apartments_for_rent)
    return apartments_for_rent, y_pred

def ml_durbin_model(X, y, apartments_for_rent):
    """
    Defines X and Y Variables, scales variables throughto RobustScaler
    Log Transform Rental Prices, perform Spatial Regression on Coordinates, calculate residuals
    Trains Spatial Durbin Model
    Args:
        apartments_for_rent: dataframe with housing data
    """
    X_clean = X.copy()
    for col in X_clean.columns:
        X_clean[col] = pd.to_numeric(X_clean[col], errors='coerce')
    X_clean = X_clean.fillna(X_clean.median())
    X_clean = X_clean.astype('float64')
    
    y_clean = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
    y_clean = pd.Series(y_clean).fillna(pd.Series(y_clean).median())
    
    if X_clean.isnull().any().any():
        print("Warning: X_clean still contains NaN values, filling with 0")
        X_clean = X_clean.fillna(0)
    
    if pd.isnull(y_clean).any():
        print("Warning: y_clean still contains NaN values, filling with median")
        y_clean = y_clean.fillna(y_clean.median())
    
    coords = apartments_for_rent[["latitude", "longitude"]].values
    knn_weights = KNN.from_array(coords, k=12)
    knn_weights.transform = 'R'
 
    try:
        sdm_model = ML_Lag(
            y_clean,
            X_clean,
            w=knn_weights,
            name_y="Log RentAmount",
            name_x=X_clean.columns.tolist(),
            slx_lags=1
        )

        y_pred = sdm_model.predy
        
    except (np.linalg.LinAlgError, ValueError) as e:
        print(f"⚠️ Singular matrix error in Spatial Durbin Model: {e}")
        print(f"\n📊 Correlation matrix for X_clean (features):")
        print(X_clean.corr())
        print(f"Shape of X_clean: {X_clean.shape}")
        print(f"Columns in X_clean: {X_clean.columns.tolist()}")
        
        print("⚠️ Falling back to linear regression...")
        X_const = sm.add_constant(X_clean)
        ols_model = sm.OLS(y_clean, X_const).fit()
        y_pred = ols_model.predict(X_const)
    
    apartments_for_rent = find_residual_rental_amounts(y_pred, apartments_for_rent)

    return apartments_for_rent, y_pred

def get_spatial_coefficients(X, apartments_for_rent):
    """
    Extract Spatial Coefficients Using Spatial Lag
    """
    coords = apartments_for_rent[["latitude", "longitude"]].values
    knn_weights = KNN.from_array(coords, k=5)
    knn_weights.transform = 'R'

    X_numeric = X.copy()
    for col in X_numeric.columns:
        X_numeric[col] = pd.to_numeric(X_numeric[col], errors='coerce')
    
    X_numeric = X_numeric.fillna(X_numeric.median())
    
    X_numeric = X_numeric.astype('float64')
    
    print(f"X_numeric dtypes: {X_numeric.dtypes}")
    print(f"X_numeric shape: {X_numeric.shape}")

    X_with_spatial = X_numeric.copy()
    for col in X_numeric.columns:
        try:
            spatial_lag = lag_spatial(knn_weights, X_numeric[col])
            spatial_lag = np.nan_to_num(spatial_lag, nan=0.0, posinf=0.0, neginf=0.0)
            X_with_spatial[f"W_{col}"] = spatial_lag
        except Exception as e:
            print(f"Error processing column {col}: {e}")
            print(f"Column {col} dtype: {X_numeric[col].dtype}")
            print(f"Column {col} sample values: {X_numeric[col].head()}")
            raise e

    X_with_spatial = X_with_spatial.replace([np.inf, -np.inf], np.nan)
    X_with_spatial = X_with_spatial.fillna(0)
    
    print(f"X_with_spatial shape: {X_with_spatial.shape}")
    print(f"X_with_spatial has inf: {np.isinf(X_with_spatial).any().any()}")
    print(f"X_with_spatial has NaN: {X_with_spatial.isnull().any().any()}")

    return X_with_spatial

def spatial_random_forest_regressor(X_with_spatial, y, apartments_for_rent):
    """
    Fits Spatial Durbin Model, extracts spatial lag features, 
    trains Random Forest on full data, and attaches residuals back to the dataframe.
    """
    y_clean = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
    
    rf = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42)
    rf.fit(X_with_spatial, y_clean)
    y_pred = rf.predict(X_with_spatial)
    apartments_for_rent = find_residual_rental_amounts(y_pred, apartments_for_rent)
    return apartments_for_rent, y_pred


def spatial_xgboost_regressor(X_with_spatial, y, apartments_for_rent):
    """
    Train XGBoost model with spatial features
    """
    y_clean = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
    
    for col in X_with_spatial.columns:
        if X_with_spatial[col].dtype == 'object':
            X_with_spatial[col] = pd.to_numeric(X_with_spatial[col], errors='coerce').fillna(0)
    
    xgb = XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=8,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    
    xgb.fit(X_with_spatial, y_clean)
    y_pred = xgb.predict(X_with_spatial)
    apartments_for_rent = find_residual_rental_amounts(y_pred, apartments_for_rent)
    return apartments_for_rent, y_pred



def find_residual_rental_amounts(y_pred, apartments_for_rent):
    """
    Predicts rental value based on SAR and Hedonic Regression Model
    Args:
        ols_model: fitted Model
        apartments_for_rent: dataframe with housing data
    """
    
    apartments_for_rent["PredictedRent"] = np.exp(y_pred)
    apartments_for_rent["DifferenceinFairValue"] = apartments_for_rent["rent_per_person"] - apartments_for_rent["PredictedRent"]

    return apartments_for_rent


def evaluate_models(models, X, y, apartments_for_rent, weights=None):
    """
    Evaluate models and return raw + normalized metrics.
    
    weights: dict of metric weights, e.g. {"RMSE": 0.4, "R2": 0.4, "MAPE": 0.2}
    """
    results = {}

    for name, model_func in models.items():
        try:
            flagged = False
            apts_out, y_pred = model_func(X, y, apartments_for_rent.copy())
            rmse = np.sqrt(mean_squared_error(y, y_pred))
            r2 = r2_score(y, y_pred)
            mape = mean_absolute_percentage_error(y, y_pred)

            if(flag_overfitting(r2)):
              flagged = True

            results[name] = {"RMSE": rmse, "R2": r2, "MAPE": mape, "flagged": flagged}
        
        except np.linalg.LinAlgError as e:
            print(f"⚠️ LinAlgError (Singular matrix) for model '{name}': {e}")
            print(f"\n📊 Correlation matrix for X (features):")
            print(X.corr())
            print(f"\n❌ Skipping model '{name}' and continuing with other models...\n")
        
        except Exception as e:
            print(f"⚠️ Error training model '{name}': {e}")
            import traceback
            traceback.print_exc()
            print(f"❌ Skipping model '{name}' and continuing with other models...\n")

    if not results:
        raise ValueError("All models failed to train!")
    
    df = pd.DataFrame(results).T

    return df


def flag_overfitting(r2, overfitting_flag_value=0.96):
    """
    Flags if model seriously overfitting (NOT GOOD)
    """
    return r2 > overfitting_flag_value


def select_best_model(results_df, r2_weight=0.5, rmse_weight=0.5):
    """
    Select the best model based on R² (as-is) and normalized RMSE, ignoring flagged ones.

    results_df: DataFrame returned from evaluate_models
    r2_weight: weight to give R² (higher is better)
    rmse_weight: weight to give RMSE (lower is better)

    Returns: (best_model_name, scored DataFrame)
    """
    df = results_df[results_df["flagged"] == False].copy()
    if df.empty:
        raise ValueError("All models were flagged as overfit!")

    df["RMSE_norm"] = 1 - (df["RMSE"] - df["RMSE"].min()) / (df["RMSE"].max() - df["RMSE"].min() + 1e-9)

    df["Score"] = r2_weight * df["R2"] + rmse_weight * df["RMSE_norm"]

    best_model_name = df["Score"].idxmax()
    return best_model_name, df.sort_values("Score", ascending=False)


def train_and_evaluate_models(X, y, apartments_for_rent):
    """
    Main function to train and evaluate all models, then select the best one.
    Returns the best model name and the apartments_for_rent dataframe with predictions.
    """    
    try:
        X_spatial = get_spatial_coefficients(X, apartments_for_rent)
    except Exception as e:
        print(f"⚠️ Error getting spatial coefficients: {e}")
        print("⚠️ Using regular X instead of spatial features...")
        X_spatial = X
    
    spatial_models = {
        "LinearRegression (Spatial)": lambda X, y, df: train_linear_model(X, y, df),
        "RandomForest (Spatial)": lambda X, y, df: spatial_random_forest_regressor(X, y, df),
        "XGBoost (Spatial)": lambda X, y, df: spatial_xgboost_regressor(X, y, df),
    }
    
    non_spatial_models = {
        "Spatial Durbin": lambda X, y, df: ml_durbin_model(X, y, df),
    }
    
    spatial_results = evaluate_models(spatial_models, X_spatial, y, apartments_for_rent)
    non_spatial_results = evaluate_models(non_spatial_models, X, y, apartments_for_rent)
    
    results = pd.concat([spatial_results, non_spatial_results])
    
    best_model_name, scored_df = select_best_model(results)
    print(f"\n🏆 Champion model: {best_model_name}")
    print("\nModel Performance Summary:")
    print(scored_df[['R2', 'RMSE', 'MAPE', 'Score']])
    
    if best_model_name in spatial_models:
        best_model_func = spatial_models[best_model_name]
        input_X = X_spatial
        print(f"Using spatial features for {best_model_name}")
    else:
        best_model_func = non_spatial_models[best_model_name]
        input_X = X
        print(f"Using regular features for {best_model_name}")
    
    apartments_for_rent, final_predictions = best_model_func(input_X, y, apartments_for_rent.copy())
    return apartments_for_rent, results, X, X_spatial, y, best_model_name