# scripts/load_data.py — Phase 1: Data Loading and Cleaning
#
# PURPOSE: Load CICIDS2017 CSV files, clean them, handle class imbalance,
# simulate IPs if missing, and save a clean dataset ready for Phase 2.
#
# RUN: python scripts/load_data.py

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import os
import pandas as pd
import numpy as np
import config

# ── Feature columns we care about ─────────────────────────────────────────────
# These are the numeric network-flow statistics present in CICIDS2017.
# We define them here (not in config.py) so Phase 1 can validate them.
FEATURE_COLUMNS = [
    "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Total Length of Fwd Packets", "Total Length of Bwd Packets",
    "Fwd Packet Length Max", "Fwd Packet Length Min",
    "Fwd Packet Length Mean", "Fwd Packet Length Std",
    "Bwd Packet Length Max", "Bwd Packet Length Min",
    "Bwd Packet Length Mean", "Bwd Packet Length Std",
    "Flow Bytes/s", "Flow Packets/s",
    "Flow IAT Mean", "Flow IAT Std", "Flow IAT Max", "Flow IAT Min",
    "Fwd IAT Total", "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min",
    "Bwd IAT Total", "Bwd IAT Mean", "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min",
    "Fwd PSH Flags", "Bwd PSH Flags", "Fwd URG Flags", "Bwd URG Flags",
    "Fwd Header Length", "Bwd Header Length",
    "Fwd Packets/s", "Bwd Packets/s",
    "Min Packet Length", "Max Packet Length",
    "Packet Length Mean", "Packet Length Std", "Packet Length Variance",
    "FIN Flag Count", "SYN Flag Count", "RST Flag Count",
    "PSH Flag Count", "ACK Flag Count", "URG Flag Count",
    "CWE Flag Count", "ECE Flag Count",
    "Down/Up Ratio", "Average Packet Size",
    "Avg Fwd Segment Size", "Avg Bwd Segment Size",
    "Fwd Avg Bytes/Bulk", "Fwd Avg Packets/Bulk", "Fwd Avg Bulk Rate",
    "Bwd Avg Bytes/Bulk", "Bwd Avg Packets/Bulk", "Bwd Avg Bulk Rate",
    "Subflow Fwd Packets", "Subflow Fwd Bytes",
    "Subflow Bwd Packets", "Subflow Bwd Bytes",
    "Init_Win_bytes_forward", "Init_Win_bytes_backward",
    "act_data_pkt_fwd", "min_seg_size_forward",
    "Active Mean", "Active Std", "Active Max", "Active Min",
    "Idle Mean", "Idle Std", "Idle Max", "Idle Min",
    "Destination Port",
]

# Maps raw CICIDS2017 label strings → our 5-class system
LABEL_MAP = {
    "BENIGN":                       "BENIGN",
    "DDoS":                         "DDoS",
    "PortScan":                     "PortScan",
    "FTP-Patator":                  "BruteForce",
    "SSH-Patator":                  "BruteForce",
    "Bot":                          "Other",
    "Web Attack \x96 Brute Force":  "BruteForce",
    "Web Attack \u2013 Brute Force":"BruteForce",
    "Web Attack \x96 XSS":          "Other",
    "Web Attack \u2013 XSS":        "Other",
    "Web Attack \x96 Sql Injection":"Other",
    "Web Attack \u2013 Sql Injection":"Other",
    "Infiltration":                 "Other",
    "Heartbleed":                   "Other",
    "DoS Hulk":                     "DDoS",
    "DoS GoldenEye":                "DDoS",
    "DoS slowloris":                "DDoS",
    "DoS Slowhttptest":             "DDoS",
}

BENIGN_DOWNSAMPLE_RATIO = 3.0
RANDOM_SEED = 42
SAMPLE_SIZE = 50_000


def simulate_ip(role: str, idx: int) -> str:
    if role == "src":
        return f"10.0.{(idx // 254) % 254}.{idx % 254 + 1}"
    return f"192.168.{(idx // 254) % 10}.{idx % 254 + 1}"


def generate_synthetic_dataset() -> pd.DataFrame:
    """Fallback synthetic dataset when no CSV is found."""
    print("\n" + "=" * 60)
    print("WARNING: No CSV files found in data/raw/")
    print("Generating SYNTHETIC demo dataset (NOT real traffic).")
    print("Download real data: https://www.unb.ca/cic/datasets/ids-2017.html")
    print("=" * 60 + "\n")

    rng = np.random.default_rng(42)
    n = 2000

    def block(n_rows, label, flow_scale=1.0, pkt_scale=1.0):
        d = {col: rng.uniform(0, 1000, n_rows) for col in FEATURE_COLUMNS}
        d["Flow Duration"] = rng.integers(0, 120_000_000, n_rows)
        d["Flow Bytes/s"] = rng.uniform(0, 2_000_000, n_rows) * flow_scale
        d["Flow Packets/s"] = rng.uniform(0, 10_000, n_rows) * pkt_scale
        d["SYN Flag Count"] = rng.integers(0, 5, n_rows)
        d["Destination Port"] = rng.integers(0, 65535, n_rows)
        d["Label"] = [label] * n_rows
        d["Source IP"] = [f"10.0.0.{i % 254 + 1}" for i in range(n_rows)]
        d["Destination IP"] = [f"192.168.1.{i % 254 + 1}" for i in range(n_rows)]
        d["synthetic"] = [True] * n_rows
        return pd.DataFrame(d)

    parts = [
        block(800, "BENIGN"),
        block(400, "DDoS",      flow_scale=50.0, pkt_scale=20.0),
        block(400, "PortScan",  pkt_scale=5.0),
        block(200, "BruteForce"),
        block(200, "Other"),
    ]
    return pd.concat(parts, ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)


def main():
    print("=" * 60)
    print("SentinelAI — Phase 1: Data Loading and Cleaning")
    print("=" * 60)

    os.makedirs(config.PROCESSED_DATA_DIR, exist_ok=True)

    # 1. Try real CSVs
    raw_dir = Path(config.RAW_DATA_DIR)
    csv_files = list(raw_dir.glob("*.csv"))
    synthetic = False

    if csv_files:
        frames = []
        for fp in csv_files:
            print(f"Loading: {fp.name} ...")
            df = pd.read_csv(fp, nrows=SAMPLE_SIZE, encoding="latin-1")
            df.columns = df.columns.str.strip()
            frames.append(df)
        df = pd.concat(frames, ignore_index=True)
    else:
        df = generate_synthetic_dataset()
        synthetic = True

    # 2. Normalise label column name
    df.columns = df.columns.str.strip()
    if "Label" not in df.columns and " Label" in df.columns:
        df.rename(columns={" Label": "Label"}, inplace=True)

    # 3. Replace inf with NaN, then drop NaN rows
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    before = len(df)
    feat_present = [c for c in FEATURE_COLUMNS if c in df.columns]
    df = df.dropna(subset=feat_present + ["Label"])
    after = len(df)
    print(f"Dropped {before - after:,} rows with NaN/Inf  ({before:,} -> {after:,})")

    # 4. Drop duplicates
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    print(f"Dropped {before - after:,} duplicate rows  ({before:,} -> {after:,})")

    # 5. Map labels
    if not synthetic:
        df["Label"] = df["Label"].str.strip().map(LABEL_MAP).fillna("Other")

    # 6. Simulate IPs if missing
    if "Source IP" not in df.columns:
        print("[IP Simulation] No Source IP found — assigning SIMULATED IPs (NOT real).")
        df["Source IP"] = [simulate_ip("src", i) for i in range(len(df))]
        df["Destination IP"] = [simulate_ip("dst", i) for i in range(len(df))]

    # 7. Downsample BENIGN to fix class imbalance
    attack_df = df[df["Label"] != "BENIGN"]
    benign_df = df[df["Label"] == "BENIGN"]
    max_attack = attack_df["Label"].value_counts().max()
    keep = min(int(max_attack * BENIGN_DOWNSAMPLE_RATIO), len(benign_df))
    benign_sampled = benign_df.sample(n=keep, random_state=RANDOM_SEED)
    df = pd.concat([benign_sampled, attack_df], ignore_index=True)
    df = df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    print(f"[Downsample] Kept {keep:,} BENIGN rows (ratio {BENIGN_DOWNSAMPLE_RATIO}x)")

    # 8. Summary
    print(f"\nFinal shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print("Label distribution:")
    for label, count in df["Label"].value_counts().items():
        print(f"  {label:<15} {count:>7,}  ({count/len(df)*100:.1f}%)")

    # 9. Save
    out = Path(config.PROCESSED_DATA_DIR) / "cleaned_data.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved: {out}")
    print("\nPhase 1 complete. Run Phase 2: python scripts/feature_engineering.py")
    return df


if __name__ == "__main__":
    main()
