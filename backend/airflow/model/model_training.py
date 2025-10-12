import numpy as np
import statsmodels.api as sm
import pandas as pd
from spreg import ML_Lag
from libpysal.weights import KNN, lag_spatial
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error
from xgboost import XGBRegressor


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
    
    base_cols = ["LengthAvailable", "Pets", "combined_bedrooms_bathrooms", "drive_time_urishall", "transit_score", "amenities_score"]
    if safety_col:
        base_cols.append(safety_col)
    
    X = apartments_for_rent[base_cols]
    y = apartments_for_rent["rent_per_person"]

    return X, y

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
    ols_model = sm.OLS(y_clean, X_const).fit()
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
 
    sdm_model = ML_Lag(
        y_clean,
        X_clean,
        w=knn_weights,
        name_y="Log RentAmount",
        name_x=X_clean.columns.tolist(),
        slx_lags=1
    )

    y_pred = sdm_model.predy
    
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
        flagged = False
        apts_out, y_pred = model_func(X, y, apartments_for_rent.copy())
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        r2 = r2_score(y, y_pred)
        mape = mean_absolute_percentage_error(y, y_pred)

        if(flag_overfitting(r2)):
          flagged = True

        results[name] = {"RMSE": rmse, "R2": r2, "MAPE": mape, "flagged": flagged}

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
    X_spatial = get_spatial_coefficients(X, apartments_for_rent)
    
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