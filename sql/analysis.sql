-- Financial data quality analysis. SYNTHETIC DATA ONLY.
-- Run against a table named transactions with the same columns as
-- data/transactions.csv. Demonstrates CTEs and window functions.

-- 1. Daily totals by department, with a 7-day rolling average (window function).
WITH daily AS (
    SELECT date, department, SUM(amount) AS daily_total, COUNT(*) AS n_tx
    FROM transactions
    WHERE amount IS NOT NULL
    GROUP BY date, department
)
SELECT date, department, daily_total, n_tx,
       AVG(daily_total) OVER (
           PARTITION BY department ORDER BY date
           ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
       ) AS rolling_7d_avg
FROM daily
ORDER BY department, date;

-- 2. Duplicate transaction IDs.
SELECT transaction_id, COUNT(*) AS occurrences
FROM transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1
ORDER BY occurrences DESC;

-- 3. Largest transaction per department, ranked (window function).
WITH ranked AS (
    SELECT *, RANK() OVER (PARTITION BY department ORDER BY amount DESC) AS rnk
    FROM transactions
    WHERE amount IS NOT NULL
)
SELECT transaction_id, date, department, amount
FROM ranked
WHERE rnk <= 3
ORDER BY department, rnk;

-- 4. Department share of total, using a window total.
SELECT department, SUM(amount) AS dept_total,
       SUM(amount) * 100.0 / SUM(SUM(amount)) OVER () AS pct_of_total
FROM transactions
WHERE amount IS NOT NULL
GROUP BY department
ORDER BY dept_total DESC;
