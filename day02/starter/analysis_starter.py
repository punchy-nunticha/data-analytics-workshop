import pandas as pd

DATA_PATH = "day02/case02_marketing/data/marketing_performance.csv"
df = pd.read_csv(DATA_PATH)

# print(df.head())
# print(df.info())

# print(df.describe())

# print(df.isnull().sum())
# print("duplicates:", df.duplicated().sum())

# print(df["Channel"].value_counts())
# print(df["Customer_Segment"].value_counts())

# email = df.query("Channel == 'Display'")
# print(email.head())

channel_summary = (
    df.groupby("Channel", as_index=False)
      .agg(
          Spend=("Spend", "sum"),
          Revenue=("Revenue", "sum"),
          Conversions=("Conversions", "sum")
      )
)

print(channel_summary)
print(channel_summary.sort_values("Revenue", ascending=False))
channel_summary.to_csv("day02/output/channel_summary.csv", index=False)

def summarize_by(df, dimension):
    required_columns = {
        dimension,
        "Campaign",
        "Spend",
        "Revenue",
        "Clicks",
        "Conversions",
    }
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f"Missing columns: {sorted(missing_columns)}")

    summary = df.groupby(dimension, as_index=False).agg(
        Spend=("Spend", "sum"),
        Revenue=("Revenue", "sum"),
        Clicks=("Clicks", "sum"),
        Conversions=("Conversions", "sum"),
        Campaign_Rows=("Campaign", "count"),
    )
    summary["Conversion_Rate_calc"] = summary["Conversions"].div(
        summary["Clicks"].replace(0, pd.NA)
    )
    summary["ROAS_calc"] = summary["Revenue"].div(
        summary["Spend"].replace(0, pd.NA)
    )
    return summary


segment_summary = summarize_by(df, "Customer_Segment")
print("\nCustomer segment summary:")
print(segment_summary.sort_values("Revenue", ascending=False))


business_question = "Which channels and customer segments deserve more or less budget?"

# TODO 1: Data quality checks
# TODO 2: Compare Spend / Revenue / Conversion Rate / ROAS by Channel
# TODO 3: Compare by Customer_Segment
# TODO 4: Identify trade-offs rather than optimizing one metric
# TODO 5: Write evidence in day02/output/evidence.md
