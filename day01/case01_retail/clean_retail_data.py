from pathlib import Path

import pandas as pd

source = Path(__file__).parent / "data" / "retail_sales_dirty.csv"
output = source.with_name("retail_sales_cleaned.csv")
log_output = source.with_name("retail_sales_quality_log.csv")

df = pd.read_csv(source)
log = []

# Standardize categorical text without changing the raw source file.
for column in ["Region", "Branch", "Product", "Category", "Customer_Segment"]:
    original = df[column].copy()
    df[column] = df[column].astype("string").str.strip()
    if column == "Region":
        df[column] = df[column].str.title()
    changed = original.fillna("<NA>") != df[column].fillna("<NA>")
    if changed.any():
        log.append({
            "issue_type": "Consistency",
            "field_or_row": column,
            "action": "Standardized whitespace/case",
            "status": "Corrected",
            "reason": f"Standardized {int(changed.sum())} value(s) without changing their apparent meaning.",
        })

# Use the dominant product-category relationship to resolve the single P-A typo.
p_a_mask = df["Product"].eq("P-A") & df["Category"].eq("Electronic")
if p_a_mask.any():
    df.loc[p_a_mask, "Category"] = "Home"
    log.append({
        "issue_type": "Mapping",
        "field_or_row": "P-A / Category",
        "action": "Changed Electronic to Home",
        "status": "Corrected with documented assumption",
        "reason": "All other P-A records use Home; Electronic is a single inconsistent value.",
    })

# Reconstruct only the two missing financial values using the documented formula.
missing_sales = df["Sales"].isna() & df["Profit"].notna() & df["Cost"].notna()
if missing_sales.any():
    df.loc[missing_sales, "Sales"] = df.loc[missing_sales, "Cost"] + df.loc[missing_sales, "Profit"]
    log.append({
        "issue_type": "Missing",
        "field_or_row": "Sales / source row 33",
        "action": "Derived Sales = Cost + Profit",
        "status": "Corrected with documented assumption",
        "reason": "Uses the dataset's stated Profit = Sales - Cost relationship.",
    })

missing_profit = df["Profit"].isna() & df["Sales"].notna() & df["Cost"].notna()
if missing_profit.any():
    df.loc[missing_profit, "Profit"] = df.loc[missing_profit, "Sales"] - df.loc[missing_profit, "Cost"]
    log.append({
        "issue_type": "Missing",
        "field_or_row": "Profit / source row 34",
        "action": "Derived Profit = Sales - Cost",
        "status": "Corrected with documented assumption",
        "reason": "Uses the dataset's stated Profit = Sales - Cost relationship.",
    })

# Remove the second copy only when every field is identical.
duplicate_mask = df.duplicated(keep="first")
if duplicate_mask.any():
    removed_rows = (df.index[duplicate_mask] + 2).tolist()
    df = df.loc[~duplicate_mask].copy()
    log.append({
        "issue_type": "Duplicate",
        "field_or_row": str(removed_rows),
        "action": "Removed exact duplicate row(s), retaining the first occurrence",
        "status": "Corrected",
        "reason": "The duplicate matched every field and no transaction ID was available.",
    })

# Apply the requested business-rule corrections using the dominant data pattern.
negative_quantity = df["Quantity"] < 0
if negative_quantity.any():
    df.loc[negative_quantity, "Quantity"] = df.loc[negative_quantity, "Quantity"].abs()
    log.append({
        "issue_type": "Business-rule check",
        "field_or_row": "Quantity / source row 78",
        "action": "Converted negative quantity to absolute value",
        "status": "Corrected with documented assumption",
        "reason": "All other quantities are positive; no return indicator exists in the source.",
    })

invalid_discount = ~df["Discount"].between(0, 1)
if invalid_discount.any():
    df.loc[invalid_discount, "Discount"] = df.loc[invalid_discount, "Discount"] / 10
    log.append({
        "issue_type": "Business-rule check",
        "field_or_row": "Discount / source row 56",
        "action": "Converted 2.5 to 0.25",
        "status": "Corrected with documented assumption",
        "reason": "The dataset uses decimal rates from 0 to 0.30; 2.5 is treated as a misplaced decimal.",
    })

loss_mask = df["Sales"] < df["Cost"]
if loss_mask.any():
    log.append({
        "issue_type": "Business-rule check",
        "field_or_row": "Sales and Cost",
        "action": "Left loss-making rows unchanged and flagged",
        "status": "Needs verification",
        "reason": "Negative profit can be a valid business outcome; confirm with business context.",
    })

df.to_csv(output, index=False, float_format="%.3f")
pd.DataFrame(log).to_csv(log_output, index=False)
print(f"Wrote {output}")
print(f"Wrote {log_output}")
