"""Archived spatial OOF rent model.

Property-grouped XGBoost with H3 neighborhood means and other-property KNN
lags. Latitude and longitude stay as predictors. Not called by the production
rerun pipeline.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import GroupKFold

from ml.archive.spatial_features import add_spatial_fold_features
from ml.model_training import _dollar_metrics, _model_features, group_by_property_df


def compute_fair_rent_oof_spatial(
    apartments_for_rent,
    y,
    x_cols,
    h3_reses=(6, 7),
    k_knn=10,
    n_splits=5,
    n_estimators=100,
    max_depth=6,
):
    """Run a SECOND single-XGBoost OOF model with property-excluded spatial signals.

    Adds H3 neighborhood mean log rents and distance-weighted KNN mean log
    rent/building age, all constructed without the target property's labels.
    Raw latitude and longitude stay in the model. Projected x/y coordinates
    do not. Output signature matches compute_fair_rent_oof.
    """
    frame = apartments_for_rent.copy().reset_index(drop=True)
    log_y = np.asarray(y, dtype=float).reshape(-1)
    if len(frame) != len(log_y):
        raise ValueError("Length mismatch between listings and log-rent target")
    if not np.isfinite(log_y).all():
        raise ValueError("OOF log-rent targets must be finite")

    groups = group_by_property_df(frame)
    n_props = int(groups.nunique())
    folds = min(n_splits, n_props)
    if folds < 2:
        raise ValueError(f"At least two distinct properties required, found {n_props}")

    # Explicitly use only requested available numerical predictors, and avoid
    # target-derived fields even if a caller accidentally includes them.
    forbidden = {
        "rent_per_person", "rentamount", "RentAmount", "actual_rent",
        "fair_rent", "predictedrent", "log_rent", "log_fair_rent",
        "pct_mispricing", "mispricing", "mispricing_pct",
        "rent_per_person_original", "total_rent_amount",
    }
    # Latitude and longitude are predictors. Projected x/y coordinates are not.
    features = [
        col for col in dict.fromkeys(list(x_cols) + ["latitude", "longitude"])
        if col in frame.columns and col not in forbidden
        and col not in ("x_meters", "y_meters")
        and not str(col).startswith(("knn_", "h3_"))
        and col != "spatial_cluster"
    ]
    spatial_cols = ["knn_rent_log", "knn_yearbuilt"] + [
        f"h3_{res}_te" for res in h3_reses
    ]
    features += spatial_cols
    if not features:
        raise ValueError("No model features available after excluding target columns")

    log_pred = np.full(len(frame), np.nan)
    fold_rows = []
    importance = []

    print(f"🗺️ Spatial OOF XGBoost: {n_props} properties, {folds} folds, "
          f"{len(frame)} unit rows, {len(features)} predictors")

    splitter = GroupKFold(n_splits=folds)
    for fold_id, (train_pos, test_pos) in enumerate(
        splitter.split(frame, log_y, groups), start=1
    ):
        # Include property identity only for excluding same-building target
        # rents; it is NOT passed to XGBoost as a predictor.
        train_spatial, test_spatial = add_spatial_fold_features(
            frame.iloc[train_pos], frame.iloc[test_pos],
            log_y[train_pos], k=k_knn, h3_reses=h3_reses,
        )
        x_train, x_test = _model_features(
            train_spatial[features], test_spatial[features],
        )
        model = xgb.XGBRegressor(
            n_estimators=n_estimators, max_depth=max_depth,
            learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1, missing=np.nan,
        )
        model.fit(x_train, log_y[train_pos])
        fold_log_pred = model.predict(x_test)
        log_pred[test_pos] = fold_log_pred

        actual = np.exp(log_y[test_pos])
        predicted = np.exp(fold_log_pred)
        row = {
            "fold": fold_id,
            "train_properties": int(groups.iloc[train_pos].nunique()),
            "test_properties": int(groups.iloc[test_pos].nunique()),
            "test_listings": int(len(test_pos)),
            **_dollar_metrics(actual, predicted),
        }
        fold_rows.append(row)
        print(
            f"  Fold {fold_id}/{folds}: {row['test_properties']} held-out properties "
            f"({row['test_listings']} listings) | R²={row['r2']:.3f} | "
            f"RMSE=${row['rmse']:,.0f} | MAE=${row['mae']:,.0f} | "
            f"bias(actual−pred)=${row['bias']:+,.0f} | "
            f"residual SD=${row['residual_std']:,.0f}"
        )

        # XGBoost gain measures predictive split improvement, not causality.
        gains = model.get_booster().get_score(importance_type="gain")
        score = pd.Series({name: float(gains.get(name, 0.0)) for name in features})
        if score.sum() > 0:
            score = score / score.sum()
        importance.append(score.rename(f"fold_{fold_id}"))

    if not np.isfinite(log_pred).all():
        raise ValueError("Missing or non-finite OOF predictions")
    actual_all = np.exp(log_y)
    predicted_all = np.exp(log_pred)
    overall = {
        "n_properties": n_props,
        "n_listings": len(frame),
        "n_folds": folds,
        **_dollar_metrics(actual_all, predicted_all),
    }
    print(
        f"📊 OVERALL OOF (pooled {len(frame)} listings): "
        f"R²={overall['r2']:.3f} | RMSE=${overall['rmse']:,.0f} | "
        f"MAE=${overall['mae']:,.0f} | bias(actual−pred)=${overall['bias']:+,.0f} | "
        f"p90 absolute error=${overall['p90_abs_error']:,.0f}"
    )
    print("ℹ️ Bias/residuals use actual minus predicted: positive = model underpredicts.")

    importance_df = (
        pd.concat(importance, axis=1)
        .mean(axis=1)
        .sort_values(ascending=False)
        .rename("mean_normalized_gain")
        .reset_index()
        .rename(columns={"index": "feature"})
    )
    print("⭐ Top overall spatial-model features (mean normalized XGBoost gain across folds):")
    for _, rec in importance_df.head(15).iterrows():
        print(f"  {rec['feature']}: {rec['mean_normalized_gain']:.1%}")
    print("ℹ️ Feature gain is predictive importance, not a causal effect.")

    frame["log_rent"] = log_y
    frame["log_fair_rent"] = log_pred
    frame["actual_rent"] = actual_all
    frame["fair_rent"] = predicted_all
    frame["mispricing"] = actual_all - predicted_all
    frame["pct_mispricing"] = frame["mispricing"] / predicted_all
    frame["mispricing_pct"] = frame["mispricing"] / actual_all
    return frame, pd.DataFrame(fold_rows), overall, importance_df
