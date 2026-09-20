import pandas as pd

DATA_PATH = "day02/case02_marketing/data/marketing_performance.csv"
df = pd.read_csv(DATA_PATH)

df["Month"] = pd.to_datetime(df["Month"])

monthly_channel = (
    df.groupby(["Month", "Channel"], as_index=False)
      .agg(Spend=("Spend", "sum"), Revenue=("Revenue", "sum"))
)
monthly_channel["ROAS_calc"] = monthly_channel["Revenue"] / monthly_channel["Spend"]
print(monthly_channel.sort_values("Revenue", ascending=False).head(10))
print(monthly_channel.sort_values("ROAS_calc", ascending=False).head(10))

# Check whether channel performance is consistent across months and campaigns.
channel_month_stability = (
  monthly_channel.groupby("Channel", as_index=False)
  .agg(
    Avg_ROAS=("ROAS_calc", "mean"),
    ROAS_std=("ROAS_calc", "std"),
    Min_ROAS=("ROAS_calc", "min"),
    Max_ROAS=("ROAS_calc", "max"),
    Months=("Month", "nunique")
  )
)

campaign_channel = (
  df.groupby(["Channel", "Campaign"], as_index=False)
  .agg(Spend=("Spend", "sum"), Revenue=("Revenue", "sum"))
)
campaign_channel["ROAS_calc"] = (
  campaign_channel["Revenue"] / campaign_channel["Spend"]
)

channel_campaign_stability = (
  campaign_channel.groupby("Channel", as_index=False)
  .agg(
    Avg_ROAS=("ROAS_calc", "mean"),
    ROAS_std=("ROAS_calc", "std"),
    Min_ROAS=("ROAS_calc", "min"),
    Max_ROAS=("ROAS_calc", "max"),
    Campaigns=("Campaign", "nunique")
  )
)

print(channel_month_stability.sort_values("Avg_ROAS", ascending=False))
print(channel_campaign_stability.sort_values("Avg_ROAS", ascending=False))



# TODO 1: Data quality checks
# TODO 2: Compare Spend / Revenue / Conversion Rate / ROAS by Channel
# TODO 3: Compare by Customer_Segment
# TODO 4: Identify trade-offs rather than optimizing one metric
# TODO 5: Write evidence in day02/output/evidence.md