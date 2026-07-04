import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import os

# =========================================================
# 1. LOAD DATA
# =========================================================
def load_data():
    print("Loading data...")

    df = pd.read_excel("data.xlsx")

    df["RecordedDate"] = pd.to_datetime(df["RecordedDate"], errors="coerce")
    df = df[df["RecordedDate"] >= pd.to_datetime("2026-06-30")]

    outlier_file = "listOfManuallyIdentifiedOutliers.txt"
    if os.path.exists(outlier_file):
        with open(outlier_file, "r") as f:
            outliers = [line.strip() for line in f if line.strip()]
        df = df[~df["ResponseId"].isin(outliers)]
        print(f"Outliers removed: {len(outliers)}")

    print("Final rows:", len(df))
    return df


# =========================================================
# 2. LONG FORMAT
# =========================================================
def transform_to_long(df):

    print("Transforming to long format (FIXED MATCHING)...")

    notification_map = {
        "1": "Earcon",
        "2": "Short Speech",
        "3": "Rich Speech"
    }

    scenario_map = {
        'A': {'Social': 'Alone', 'Task': 'High mental', 'CM': 'Quiet'},
        'B': {'Social': 'Interactive', 'Task': 'High mental', 'CM': 'Speech'},
        'C': {'Social': 'Alone', 'Task': 'Low', 'CM': 'Music'},
        'D': {'Social': 'Interactive', 'Task': 'High physical', 'CM': 'Music'},
        'E': {'Social': 'Passive', 'Task': 'High physical', 'CM': 'Quiet'},
        'F': {'Social': 'Passive', 'Task': 'Low', 'CM': 'Speech'},
        'G': {'Social': 'Alone', 'Task': 'High physical', 'CM': 'Speech'},
        'H': {'Social': 'Passive', 'Task': 'High mental', 'CM': 'Music'},
        'I': {'Social': 'Interactive', 'Task': 'Low', 'CM': 'Quiet'},
    }

    rows = []

    for _, row in df.iterrows():
        rid = row["ResponseId"]

        for sc in scenario_map.keys():
            for t in ["1", "2", "3"]:

                # FIX: direct structured matching instead of string guessing
                d_col = f"{sc}_{t}_Detectability"
                dis_col = f"{sc}_{t}_Disruption"
                soc_col = f"{sc}_{t}_SocialAcceptability"

                if d_col not in df.columns and dis_col not in df.columns and soc_col not in df.columns:
                    continue

                rows.append({
                    "ResponseId": rid,
                    "Notification_Type": notification_map[t],
                    "Scenario": sc,
                    "Asocial": scenario_map[sc]["Social"],
                    "Task": scenario_map[sc]["Task"],
                    "CM": scenario_map[sc]["CM"],

                    "Detectability": row.get(d_col),
                    "Disruption": row.get(dis_col),
                    "SocialAcceptability": row.get(soc_col),
                })

    long_df = pd.DataFrame(rows)

    print("Long shape:", long_df.shape)

    # CRITICAL DEBUG
    print("\nNaN check:")
    print(long_df[["Detectability","Disruption","SocialAcceptability"]].isna().sum())

    return long_df


# =========================================================
# 3. CLEAN DV VALUES (CRITICAL FIX)
# =========================================================
def clean_dv(df):

    dv_cols = ["Detectability", "Disruption", "SocialAcceptability"]

    for col in dv_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.extract(r"(\d+\.?\d*)")[0]
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# =========================================================
# 4. DATA CHECKS
# =========================================================
def data_checks(df):
    print("\n========== DATA CHECKS ==========")
    print("Participants:", df["ResponseId"].nunique())

    print("\nMissing values:")
    print(df[["Detectability", "Disruption", "SocialAcceptability"]].isna().sum())

# =========================================================
# 5. MODEL (ROBUST OLS)
# =========================================================
def run_model(df, dv):

    print(f"\n========== MODEL: {dv} ==========")

    df_clean = df.dropna(subset=[dv]).copy()

    if len(df_clean) < 10:
        print("Not enough data for", dv)
        return None

    formula = f"{dv} ~ C(Notification_Type) + C(Asocial) + C(Task) + C(CM)"

    model = smf.ols(formula, data=df_clean)
    result = model.fit(cov_type="cluster", cov_kwds={"groups": df_clean["ResponseId"]})

    print(result.summary())

    return result


# =========================================================
# 6. PIPELINE
# =========================================================
def run_analysis():

    df = load_data()
    long_df = transform_to_long(df)

    long_df = clean_dv(long_df)

    print("\nMissing after cleaning:")
    print(long_df.isna().sum())

    m1 = run_model(long_df, "Disruption")
    m2 = run_model(long_df, "Detectability")
    m3 = run_model(long_df, "SocialAcceptability")

    return m1, m2, m3


# =========================================================
# RUN
# =========================================================
run_analysis()