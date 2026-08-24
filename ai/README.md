# AI Logistics Intelligence

This module adds ML/AI capabilities without turning the project into an unnecessary collection of models.

## Components

- **ETA prediction:** XGBoost regressor (`model/eta_xgb.pkl`)
- **Late-delivery risk:** XGBoost classifier (`model/late_risk_xgb.pkl`)
- **Demand forecasting:** dependency-light trend baseline in `logistics_intelligence.py`, ready to replace with LightGBM/XGBoost when sufficient history is available
- **Vehicle assignment:** interpretable scoring function combining distance, utilization and traffic
- **AI Copilot context:** converts route results into structured facts suitable for an LLM explanation layer

## Training

Provide historical delivery data and run:

```bash
python model/train_logistics_models.py --csv data/deliveries.csv
```

The training script reports MAE/R² for ETA and accuracy for late-risk classification. Models are saved locally and should not be committed if they are large.

## Design principle

OR-Tools remains responsible for hard routing constraints. ML predicts uncertain outcomes such as ETA and late-delivery risk. The two layers are intentionally separated so predictions do not silently violate vehicle capacity or routing constraints.
