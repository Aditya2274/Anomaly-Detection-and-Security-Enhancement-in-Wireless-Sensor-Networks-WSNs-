"""WSN Cyberattack Simulator & Dataset Generator
Generates realistic Wireless Sensor Network (WSN) network-layer traffic data
with simulated routing and MAC attacks:
1. Normal (expected operation with realistic wireless packet loss & channel collisions)
2. Blackhole (complete traffic attraction and transit packet drop)
3. Grayhole (stealthy selective packet drop designed to mimic noisy channels)
4. Flooding (excessive control packet broadcast + battery drain)
5. Scheduling/TDMA (slot collision + MAC desynchronization)

Computes dynamic trust metrics (Direct Trust, Energy Trust, Control Trust, Composite Trust)
for Trust-Enhanced Random Forest (TERF).
"""

import os
import numpy as np
import pandas as pd

def generate_wsn_attack_dataset(n_samples=80_000, random_seed=42):
    rng = np.random.default_rng(random_seed)
    
    # Class distribution (realistic WSN-DS distribution)
    n_normal = int(n_samples * 0.70)
    n_blackhole = int(n_samples * 0.08)
    n_grayhole = int(n_samples * 0.08)
    n_flooding = int(n_samples * 0.08)
    n_scheduling = n_samples - (n_normal + n_blackhole + n_grayhole + n_flooding)
    
    counts = {
        'Normal': n_normal,
        'Blackhole': n_blackhole,
        'Grayhole': n_grayhole,
        'Flooding': n_flooding,
        'Scheduling': n_scheduling
    }
    
    rows = []
    eps = 1e-4
    
    for attack_type, count in counts.items():
        # Node & topology attributes
        node_ids = rng.integers(1, 101, size=count)
        time_steps = rng.uniform(1.0, 3600.0, size=count)
        is_ch = rng.choice([0, 1], size=count, p=[0.85, 0.15])
        who_ch = rng.integers(1, 15, size=count)
        dist_to_ch = rng.uniform(5.0, 90.0, size=count)
        rank = rng.integers(1, 6, size=count)
        
        # Base network packet traffic
        data_s = rng.integers(10, 80, size=count)
        data_r = rng.integers(30, 220, size=count)
        adv_s = rng.integers(1, 6, size=count)
        adv_r = rng.integers(4, 28, size=count)
        join_s = rng.integers(1, 5, size=count)
        join_r = rng.integers(2, 12, size=count)
        sch_s = rng.integers(1, 6, size=count)
        sch_r = rng.integers(1, 6, size=count)
        energy_base = rng.uniform(0.7, 2.0, size=count)
        
        if attack_type == 'Normal':
            # In realistic WSNs, channel noise, collisions and distance cause 2% to 15% packet loss
            loss_ratio = rng.beta(a=1.5, b=20.0, size=count)  # Mean ~ 7% loss, occasionally up to 18%
            data_d = np.round(data_r * loss_ratio).astype(int)
            data_f = np.maximum(0, data_r - data_d)
            energy = np.clip(energy_base - rng.uniform(0.04, 0.18, size=count), 0.1, 2.0)
            
        elif attack_type == 'Blackhole':
            # Attracts traffic, drops virtually all transit packets (92% - 100%)
            data_r = rng.integers(100, 400, size=count)
            drop_ratio = rng.uniform(0.92, 1.00, size=count)
            data_d = np.round(data_r * drop_ratio).astype(int)
            data_f = np.maximum(0, data_r - data_d)
            energy = np.clip(energy_base - rng.uniform(0.08, 0.24, size=count), 0.1, 2.0)
            
        elif attack_type == 'Grayhole':
            # Stealthy: selectively drops 28% to 62% of packets to blend with congested channels
            drop_ratio = rng.uniform(0.28, 0.62, size=count)
            data_d = np.round(data_r * drop_ratio).astype(int)
            data_f = np.maximum(0, data_r - data_d)
            energy = np.clip(energy_base - rng.uniform(0.05, 0.20, size=count), 0.1, 2.0)
            
        elif attack_type == 'Flooding':
            # Broadcast flood of control packets (ADV/JOIN/RREQ), exhausts battery & buffers
            adv_s = rng.integers(45, 200, size=count)
            join_s = rng.integers(30, 150, size=count)
            sch_s = rng.integers(20, 90, size=count)
            # Channel saturation causes collateral drops (18% - 42%)
            loss_ratio = rng.uniform(0.18, 0.42, size=count)
            data_d = np.round(data_r * loss_ratio).astype(int)
            data_f = np.maximum(0, data_r - data_d)
            energy = np.clip(energy_base - rng.uniform(0.40, 0.85, size=count), 0.02, 2.0)
            
        elif attack_type == 'Scheduling':
            # Out-of-slot transmissions, causing TDMA slot contention and collisions
            sch_s = rng.integers(12, 50, size=count)
            sch_r = rng.integers(10, 40, size=count)
            loss_ratio = rng.uniform(0.16, 0.38, size=count)
            data_d = np.round(data_r * loss_ratio).astype(int)
            data_f = np.maximum(0, data_r - data_d)
            energy = np.clip(energy_base - rng.uniform(0.10, 0.32, size=count), 0.05, 2.0)
            
        df_group = pd.DataFrame({
            'Node_ID': node_ids,
            'Time': np.round(time_steps, 1),
            'Is_CH': is_ch,
            'who_CH': who_ch,
            'Dist_To_CH': np.round(dist_to_ch, 2),
            'Rank': rank,
            'ADV_S': adv_s,
            'ADV_R': adv_r,
            'JOIN_S': join_s,
            'JOIN_R': join_r,
            'SCH_S': sch_s,
            'SCH_R': sch_r,
            'DATA_S': data_s,
            'DATA_R': data_r,
            'DATA_F': data_f,
            'DATA_D': data_d,
            'Energy': np.round(energy, 4),
            'Attack_Type': attack_type
        })
        rows.append(df_group)
        
    df = pd.concat(rows, ignore_index=True)
    df = df.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)
    
    # ================= Trust Score Engineering (TERF Features) =================
    # 1. Direct Trust: Observed packet forwarding reliability
    # Forwarded / (Received + epsilon)
    direct_trust_raw = df['DATA_F'] / (df['DATA_R'] + eps)
    df['Direct_Trust'] = np.clip(direct_trust_raw, 0.0, 1.0)
    
    # 2. Energy Trust: Energy conservation relative to active load
    df['Energy_Trust'] = np.clip(df['Energy'] / 2.0, 0.0, 1.0)
    
    # 3. Control Trust: Control packet ratio compared to expected communication quota
    total_control = df['ADV_S'] + df['JOIN_S'] + df['SCH_S']
    total_packets = df['DATA_S'] + df['DATA_R'] + total_control + eps
    control_ratio = total_control / total_packets
    df['Control_Trust'] = np.clip(1.0 - (control_ratio * 1.6), 0.0, 1.0)
    
    # 4. Composite Trust: Multi-dimensional trust fusion
    # Direct forwarding trust (50%), Control integrity (30%), Energy conservation (20%)
    df['Composite_Trust'] = np.round(
        0.50 * df['Direct_Trust'] + 
        0.30 * df['Control_Trust'] + 
        0.20 * df['Energy_Trust'], 
        4
    )
    
    df['Direct_Trust'] = np.round(df['Direct_Trust'], 4)
    df['Energy_Trust'] = np.round(df['Energy_Trust'], 4)
    df['Control_Trust'] = np.round(df['Control_Trust'], 4)
    df['Is_Attack'] = (df['Attack_Type'] != 'Normal').astype(int)
    
    return df

if __name__ == '__main__':
    print("[1/2] Simulating WSN network traffic with realistic channel noise & cyberattacks...")
    df = generate_wsn_attack_dataset(n_samples=80_000, random_seed=42)
    
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))
    os.makedirs(out_dir, exist_ok=True)
    out_csv = os.path.join(out_dir, 'wsn_attack_simulation.csv')
    df.to_csv(out_csv, index=False)
    
    print(f"[2/2] Saved simulated cyberattack dataset ({len(df):,} rows) to:\n  {out_csv}")
    print("\nClass Distribution:")
    print(df['Attack_Type'].value_counts())
    print("\nSample Average Composite Trust by Attack:")
    print(df.groupby('Attack_Type')[['Direct_Trust', 'Control_Trust', 'Energy_Trust', 'Composite_Trust']].mean().round(3))
