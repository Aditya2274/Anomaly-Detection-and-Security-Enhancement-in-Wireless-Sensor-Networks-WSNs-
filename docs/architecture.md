# TERF Architecture: Trust-Enhanced Random Forest for WSN Intrusion Detection

This document provides a concise architectural overview of the **Trust-Enhanced Random Forest (TERF)** intrusion detection system for Wireless Sensor Networks (WSNs), designed around the **WSN-DS** benchmark dataset.

---

## 1. Project Motivation & Problem Statement
* Wireless Sensor Networks (WSNs) rely on cooperative multi-hop forwarding under resource-constrained conditions.
* Malicious compromised nodes exploit this trust to launch severe routing and Denial-of-Service (DoS) attacks: **Blackhole**, **Grayhole (Selective Forwarding)**, **Flooding**, and **Scheduling (TDMA interference)**.
* Standard machine learning classifiers rely solely on instantaneous network packet counts, often failing to detect stealthy attacks (like Grayhole) or generating high false alarms during legitimate wireless channel congestion.

---

## 2. The WSN-DS Benchmark & Protocol Environment
* The system is modeled on the **WSN-DS** dataset (*Almomani et al., 2016*, Journal of Sensors).
* Simulated in **NS-2** using the **LEACH (Low-Energy Adaptive Clustering Hierarchy)** routing protocol with 100 sensor nodes.
* Captures 15 fundamental protocol features across cluster formation and steady-state transmission:
  * Clustering & Topology: `Is_CH`, `who_CH`, `Dist_To_CH`, `Rank`
  * Control Packets: `ADV_S`, `ADV_R`, `JOIN_S`, `JOIN_R`, `SCH_S`, `SCH_R`
  * Data Packets: `DATA_S`, `DATA_R`, `DATA_F` (Forwarded), `DATA_D` (Dropped)
  * Energy: `Energy` (Residual battery in Joules)

---

## 3. Dynamic Multi-Factor Trust Modeling (The Core Novelty)
To overcome the limitations of raw packet counters, TERF continuously calculates **dynamic behavioral trust scores**:

```text
                  DATA_F
1. Direct Trust = ──────────────   (Exposes Blackhole and Grayhole packet dropping)
                  DATA_R + ε

2. Energy Trust = Energy / E_max   (Exposes energy-depletion DoS and Flooding)

                       ⎛ Control Packets ⎞
3. Control Trust = 1 - ⎜ ─────────────── ⎟ (Exposes ADV/JOIN broadcast storms)
                       ⎝  Total Packets  ⎠

4. Composite Trust = 0.50 × Direct + 0.30 × Control + 0.20 × Energy
```

* **Stealth Disambiguation:** While a standard classifier cannot easily differentiate between a 30% channel collision drop and a 30% Grayhole drop, the persistent Direct Trust tracking immediately isolates the selective dropping pattern.

---

## 4. Model Hierarchy & Decision Layer
The architecture implements a comparative multi-model evaluation hierarchy:
1. **Logistic Regression:** Linear decision baseline for tabular network records.
2. **Decision Tree:** Interpretable tree-based baseline.
3. **Standard Random Forest:** Ensemble of decision trees trained strictly on raw network features (15 features).
4. **Trust-Enhanced Random Forest (TERF):** Ensemble of decision trees trained on raw network features + dynamic multi-factor trust features (19 features total).

---

## 5. Automated Defense & Quarantine Policy
The classification output drives an automated network security policy:
* **Trust > 0.75:** Node is authorized for normal packet routing toward the Base Station.
* **Trust 0.50 – 0.75:** Node flagged as **Suspicious**; transit traffic is rerouted through verified alternate paths.
* **Trust 0.38 – 0.50:** Multi-hop neighbor challenge & verification probes triggered.
* **Trust < 0.38 / Attack Confirmed:** Revoke cryptographic keys and **isolate the malicious node** from the network topology.
