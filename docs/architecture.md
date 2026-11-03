# TERF Architecture — Explained (5 points, 3 lines each)

## 1. What this project is
Trust-enhanced anomaly detection for wireless sensor networks.
A dense autoencoder reconstructs the 4 sensor channels (temp, humidity, light, voltage); high
reconstruction error flags deviation from normal. No single model is trusted on its own.

## 2. The autoencoder baseline (the "ML brain")
A small dense neural net learns the expected pattern of each channel; anomaly score = MSE.
Threshold set at the 99th percentile of validation scores — above it = AE evidence.
Catches spikes and drift, but is weak on stuck-at and missing values (constant/NaN looks normal).

## 3. The sensor-health rules (the "expert" signals)
Stuck-at rule: rolling standard deviation of the light channel flags near-constant readings.
Missingness rule: direct NaN check, recorded before imputation, because "no data" is a strong fault.
Structural and not learned — strong precisely where the autoencoder fails.

## 4. The decision layer (evidence fusion — NOT naive OR)
Each frame is scored by strength: structural rules = strong (weight 2); autoencoder = weak (weight 1).
A persistence counter gates escalation: persistent >=1 Watch, >=2 Verify, >=4 Alert; structural any -> Alert.
Prevents a single noisy frame from causing a panic response.

## 5. The 4 states and end-to-end flow
sensor data -> autoencoder score + temporal checks + missingness -> decision layer -> Normal/Watch/Verify/Alert.
No anomaly score is treated as a confirmed fault by itself — persistence and context reduce false alarms.
All results are synthetic-demo: validation on verified, fault-labelled real data is still required.
