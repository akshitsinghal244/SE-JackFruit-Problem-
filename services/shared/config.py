"""Constants shared by all three model services.

Everything that must be IDENTICAL between training and serving lives here,
so the three services can never silently disagree about it.
"""

# Class order is fixed everywhere: index 0 = Low, 1 = Medium, 2 = High.
CLASSES = ["Low", "Medium", "High"]

# Number of past days the user sends (prev_sales has exactly this many values).
WINDOW = 7

# SADS 2.6: "Accuracy values are computed offline on the held-out last 3 months".
HOLDOUT_MONTHS = 3

# Used only for model selection / early stopping (the 3 months before the holdout).
VALIDATION_MONTHS = 3

# prev_sales ORDER CONTRACT (write this into the API spec!):
#   prev_sales[0] = sales 7 days before `date`  (oldest)
#   prev_sales[6] = sales 1 day  before `date`  (newest)  -> this is lag_1
PREV_SALES_ORDER = "oldest_to_newest"

# Feature names for the ML row of the table:
# store, item, day-of-week, month, 7 lags, rolling mean  -> 12 features
LAG_NAMES = [f"lag_{k}" for k in range(1, WINDOW + 1)]
TABULAR_FEATURES = ["store", "item", "dow", "month", *LAG_NAMES, "roll_mean"]

# Upper bound for a single day's sales value accepted by the API.
MAX_DAILY_SALES = 100_000
