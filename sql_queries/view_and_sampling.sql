CREATE VIEW vw_ml_transactions AS
SELECT 
	ft.amount, ft.use_chip, 
    ft.errors, ft.fraud_label,
	ft.card_id, ft.transaction_date,
    dc.current_age, dc.retirement_age, 
    dc.gender, dc.per_capita_income,
    dc.yearly_income, dc.total_debt, 
    dc.credit_score, dc.latitude, 
    dc.longitude, cd.card_brand,
    cd.card_type, cd.num_cards_issued, 
    cd.credit_limit, cd.acct_open_date,
    mc.mcc_description,
	dd.day, dd.month, 
	dd.quarter,dd.weekend_flag,dd.year
FROM fact_transaction ft
JOIN dim_customer dc
    ON ft.card_id = dc.id
JOIN dim_card cd 
    ON ft.card_id = cd.id
JOIN dim_mcc mc
    ON ft.mcc = mc.mcc
JOIN dim_date dd
	ON ft.date_key = dd.date_key



-- SQL Sampling Query

SELECT *
FROM vw_ml_transactions
WHERE fraud_label = 1

UNION ALL

SELECT *
FROM (
    SELECT TOP 500000 *
    FROM vw_ml_transactions
    WHERE fraud_label = 0
    ORDER BY NEWID()
) AS sampled_nonfraud;