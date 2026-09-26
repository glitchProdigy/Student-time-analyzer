"""
analysis.py
-----------
Statistics and analysis functions for time-use records.

All functions take a Pandas DataFrame (as produced by data_manager) and
return plain Python / NumPy values, so this module has no GUI dependency
and can be unit tested directly.
"""

import numpy as np
import pandas as pd


def category_totals_minutes(df: pd.DataFrame) -> pd.Series:
    """Total minutes spent per category, sorted descending."""
    if df.empty:
        return pd.Series(dtype=float)
    return df.groupby("category")["duration_minutes"].sum().sort_values(ascending=False)


def category_totals_hours(df: pd.DataFrame) -> pd.Series:
    """Same as category_totals_minutes but converted to hours (rounded to 2dp)."""
    totals = category_totals_minutes(df)
    return (totals / 60).round(2)


def category_percentages(df: pd.DataFrame) -> pd.Series:
    """Percentage of TOTAL RECORDED time that each category represents."""
    if df.empty:
        return pd.Series(dtype=float)
    totals = category_totals_minutes(df)
    grand_total = totals.sum()
    if grand_total == 0:
        return pd.Series(dtype=float)
    percentages = (totals / grand_total) * 100
    return percentages.round(2)


def most_time_consuming_category(df: pd.DataFrame):
    """Return (category_name, total_hours) for the top category, or (None, 0)."""
    totals = category_totals_hours(df)
    if totals.empty:
        return None, 0.0
    top_category = totals.idxmax()
    return top_category, float(totals.max())


def most_time_consuming_activities(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Top N individual activities by total time spent (activities may repeat
    across dates, so we group by activity name and sum)."""
    if df.empty:
        return pd.DataFrame(columns=["activity", "total_hours"])
    grouped = df.groupby("activity")["duration_minutes"].sum().sort_values(ascending=False)
    grouped_hours = (grouped / 60).round(2).head(top_n)
    result = grouped_hours.reset_index()
    result.columns = ["activity", "total_hours"]
    return result


def summary_statistics(df: pd.DataFrame) -> dict:
    """A dict of headline numbers used for the Dashboard 'summary cards'."""
    if df.empty:
        return {
            "total_records": 0,
            "total_hours": 0.0,
            "average_daily_hours": 0.0,
            "days_tracked": 0,
            "top_category": None,
            "top_category_hours": 0.0,
        }

    total_minutes = df["duration_minutes"].sum()
    days_tracked = df["date"].nunique()
    # NumPy used explicitly for the mean calculation
    daily_totals = df.groupby("date")["duration_minutes"].sum().values
    average_daily_minutes = float(np.mean(daily_totals)) if len(daily_totals) > 0 else 0.0

    top_cat, top_cat_hours = most_time_consuming_category(df)

    return {
        "total_records": int(len(df)),
        "total_hours": round(total_minutes / 60, 2),
        "average_daily_hours": round(average_daily_minutes / 60, 2),
        "days_tracked": int(days_tracked),
        "top_category": top_cat,
        "top_category_hours": top_cat_hours,
    }


def compare_periods(df: pd.DataFrame, start1, end1, start2, end2) -> dict:
    """Compare total hours per category between two date ranges (e.g. two weeks).
    Returns a dict: {"period1": Series, "period2": Series, "difference": Series}
    """
    if df.empty:
        empty = pd.Series(dtype=float)
        return {"period1": empty, "period2": empty, "difference": empty}

    p1 = df[(df["date"] >= start1) & (df["date"] <= end1)]
    p2 = df[(df["date"] >= start2) & (df["date"] <= end2)]

    p1_totals = category_totals_hours(p1)
    p2_totals = category_totals_hours(p2)

    all_categories = sorted(set(p1_totals.index) | set(p2_totals.index))
    p1_aligned = p1_totals.reindex(all_categories, fill_value=0.0)
    p2_aligned = p2_totals.reindex(all_categories, fill_value=0.0)
    # NumPy array subtraction for the difference
    difference = pd.Series(
        np.array(p2_aligned.values) - np.array(p1_aligned.values), index=all_categories
    ).round(2)

    return {"period1": p1_aligned, "period2": p2_aligned, "difference": difference}


def daily_totals_hours(df: pd.DataFrame) -> pd.Series:
    """Total hours logged per date, sorted chronologically (for trend line chart)."""
    if df.empty:
        return pd.Series(dtype=float)
    totals = df.groupby("date")["duration_minutes"].sum().sort_index()
    return (totals / 60).round(2)
