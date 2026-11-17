"""Coffee shop EDA and sales analysis.

Single-file version of coffee_analysis_1.ipynb.
Reads data/Coffe_sales.xlsx, prints the tables, and saves SVG charts to charts/.
Run:  python coffee_analysis_1.py
"""
import os

import matplotlib.pyplot as plt             # easier to call
import pandas as pd
import seaborn as sns

DATASET_FOLDER = "data/"                    # path where data is
CHART_FOLDER = "charts/"                    # path where to save charts

os.makedirs(CHART_FOLDER, exist_ok=True)
os.makedirs(DATASET_FOLDER, exist_ok=True)

# CHART PARAMETERS
COLOR = "#55A868"
SNS_HEATMAP_COLOR = "Greens"
plt.rcParams["svg.fonttype"] = "none"       # keeps chart text as real text
plt.rcParams["figure.figsize"] = (6, 3.6)   # every chart gets this size
plt.rcParams["figure.autolayout"] = True    # to automatically adapt for less headaches

# Show every column and wider tables when printing in the terminal
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 120)


# --- Load and check dataset ---

# Load and view first few rows from top
sales = pd.read_excel(DATASET_FOLDER + "Coffe_sales.xlsx")

print(sales.head())

# simple dataset info summary
sales.info()

# summary of missing stuff (fully objective)
print(sales.isnull().sum())

# checks if the reason for the blank card entries is because it's in cash. if not, throw error
is_cash = sales.cash_type == "cash"
assert sales.card.isna().sum() == is_cash.sum()

# regroup by year+month, not month name because data holds two Marches (2024 and 2025).
sales["year_month"] = sales.date.dt.to_period("M")

# total duplicates, if any
duplicates = sales.duplicated().sum()
print(f'Number of duplicate rows: {duplicates}')


# --- Headline numbers ---

# Self-explanatory.

total_revenue = sales.money.sum()
number_of_sales = len(sales)
average_sale = sales.money.mean()
trading_days = sales.date.nunique()
cash_share = is_cash.mean()

print(f"Total revenue:  {total_revenue:,.0f}")
print(f"Total sales:    {number_of_sales:,}")
print(f"Average sale:   {average_sale:.2f}")
print(f"Trading days:   {trading_days}")
print(f"% paid in cash: {cash_share:.1%}")


# --- EDA and Plotting ---

# Price charged ranges
# Lowest price, highest price and number of different prices charged, per drink
print("\n--- Price ranges per drink ---")
print(sales.groupby("coffee_name").money.agg(["min", "max", "nunique"]).round(1))

# Sales and Sales distribution
print("\n--- Sales distribution ---")
print(sales.money.describe().round(2))

fig, ax = plt.subplots()
sns.histplot(data=sales, x="money", bins=30, kde=True, color=COLOR, ax=ax)
plt.title('Distribution of Sales (money)')
plt.xlabel('Sales (money)')
plt.ylabel('Frequency')
plt.savefig(CHART_FOLDER + "c_sales_hist.svg")
plt.close(fig)

# Sales Per Drink / Popularity Count Plot
fig, ax = plt.subplots()
sns.countplot(data=sales, y="coffee_name", order=sales.coffee_name.value_counts().index, color=COLOR, ax=ax)
ax.set_title("Sales per drink")
fig.savefig(CHART_FOLDER + "c_drink_counts.svg")
plt.close(fig)

# crosstab counts rows for each combination; reindex puts the days in calendar order
order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
busy = pd.crosstab(sales.Weekday, sales.hour_of_day).reindex(order)

fig, ax = plt.subplots()
sns.heatmap(busy, cmap=SNS_HEATMAP_COLOR, cbar_kws={"label": "sales"}, ax=ax)
ax.set_title("Sales by Weekday and Hour of Day")
ax.set_xlabel("Hour of Day")
ax.set_ylabel("Weekday")
plt.setp(ax.get_yticklabels(), rotation=0)                   # upright weekday labels
fig.savefig(CHART_FOLDER + "c_weekday_hour.svg")
plt.close(fig)


# --- KPI Analysis ---

# Revenue per month
# The last month is incomplete (the data ends on March 23)
# which is why I compare sales by day rather than month for fair analysis
monthly = sales.groupby("year_month").agg(
    revenue=("money", "sum"),
    trading_days=("date", "nunique"),
)
monthly["revenue_per_day"] = monthly.revenue / monthly.trading_days

print("\n--- Revenue by month ---")
print(monthly.round(0))

# Revenue and cups sold per drink
# Best seller first.
drinks = sales.groupby("coffee_name").agg(
    revenue=("money", "sum"),
    cups=("money", "size"),
)
drinks = drinks.sort_values("revenue", ascending=False)
drinks["share_of_revenue"] = drinks.revenue / total_revenue

print("\n--- Drinks ---")
print(drinks.round(3))

# Sales per hour
# The number of sales in each hour of the day.
sales_per_hour = sales.groupby("hour_of_day").size()

print("\n--- Sales per hour ---")
print(sales_per_hour)

# Average revenue per trading day for each weekday
# `Weekdaysort` (the numbering system of 1 = mon to 7 = sun)
# is included in the grouping so the days stay in calendar order, then dropped.
weekdays = sales.groupby(["Weekdaysort", "Weekday"]).agg(
    revenue=("money", "sum"),
    trading_days=("date", "nunique"),
)
weekdays["revenue_per_day"] = weekdays.revenue / weekdays.trading_days
weekdays = weekdays.droplevel("Weekdaysort")

print("\n--- Revenue per day, by weekday ---")
print(weekdays.round(0))


# --- Data Analysis Charting ---
# Saved as an SVG file in the `charts/` folder.

# Revenue per trading day, by month
fig, ax = plt.subplots()
ax.plot(monthly.index.astype(str), monthly.revenue_per_day, marker="o", color=COLOR)
ax.set_title("Revenue per trading day, by month")
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")     # tilted so the month labels fit
fig.savefig(CHART_FOLDER + "c_monthly_revenue.svg")
plt.close(fig)

# Revenue by drink (horizontal bars suit the long names)
fig, ax = plt.subplots()
ax.barh(drinks.index, drinks.revenue, color=COLOR)
ax.invert_yaxis()                                           # best seller on top
ax.set_title("Revenue by drink")
fig.savefig(CHART_FOLDER + "c_revenue_by_product.svg")
plt.close(fig)

# Sales by hour of day
fig, ax = plt.subplots()
ax.bar(sales_per_hour.index, sales_per_hour.to_numpy(), color=COLOR)
ax.set_xticks(sales_per_hour.index)                         # label every hour
ax.set_title("Sales by hour of day")
fig.savefig(CHART_FOLDER + "c_sales_by_day_hour.svg")
plt.close(fig)

# Revenue per day, by weekday
fig, ax = plt.subplots()
ax.bar(weekdays.index, weekdays.revenue_per_day, color=COLOR)
ax.set_title("Revenue per day, by weekday")
fig.savefig(CHART_FOLDER + "c_revenue_per_day_by_weekday.svg")
plt.close(fig)

print(f"\nSaved 7 SVG charts to {CHART_FOLDER}")
