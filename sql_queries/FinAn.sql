-- CREATE DATASET
--CREATE DATABASE finance;

-- FACT TABLE
CREATE TABLE fact_transaction(
id BIGINT PRIMARY KEY,
date_key INT,
transaction_date DATETIME,
client_id int,
card_id int,
merchant_id int,
mcc int,
amount  decimal(18,2),
use_chip varchar(50),
errors BIT,
fraud_label bit -- train_fraud_label.json
);

-- DIMENSION TABLE
-- describe the customer
create table dim_customer(
id int PRIMARY KEY,
current_age int,
retirement_age int,
birth_year int,
birth_month int,
gender varchar(10),
latitude decimal(9,6),
longitude decimal(9,6),
per_capita_income decimal(18,2),
yearly_income decimal(18,2),
total_debt decimal(18,2),
credit_score smallint,
);

-- attributes of a card.
CREATE TABLE dim_card(
id INT PRIMARY KEY,
client_id INT,
card_brand VARCHAR(20),
card_type VARCHAR(20),
expires VARCHAR(20),
has_chip VARCHAR(5),
num_cards_issued INT,
credit_limit DECIMAL(18,2),
acct_open_date VARCHAR(20),
year_pin_last_changed INT
);

-- Why Separate Merchant Dimension? Because merchant info repeats millions of times.

create table dim_merchant(
merchant_id int PRIMARY KEY,
merchant_city varchar(50)
);

create table dim_mcc(
mcc int primary key,
mcc_description varchar(255)
);

-- create date dimension table
CREATE TABLE dim_date (
    date_key       INT         NOT NULL PRIMARY KEY,  -- YYYYMMDD
    full_date      DATE        NOT NULL,
    day            TINYINT     NOT NULL,
    month          TINYINT     NOT NULL,
    month_name     VARCHAR(20) NOT NULL,
    quarter        VARCHAR(5)     NOT NULL,
    year           SMALLINT    NOT NULL,
    weekday        VARCHAR(20) NOT NULL,
    weekend_flag   VARCHAR(3)     NOT NULL  -- 'Yes' or 'No'
);


-- Apply indexing in SQL Server because it directly affects how fast Power BI can query your tables
-- Your fact table (fact_transaction) will grow very large (millions of rows)
-- Your dimension tables (dim_date, dim_customer, etc.) are joined to the fact table in queries
-- Power BI generates SQL queries under the hood when you drag fields into visuals

-- FACT : Indexes here speed up joins and filters since this table will be the largest

-- Primary key already is already indexed
-- Foreign key indexes for joins
CREATE NONCLUSTERED INDEX idx_fact_date ON fact_transaction(date_key);
CREATE NONCLUSTERED INDEX idx_fact_client ON fact_transaction(client_id);
CREATE NONCLUSTERED INDEX idx_fact_card ON fact_transaction(card_id);
CREATE NONCLUSTERED INDEX idx_fact_merchant ON fact_transaction(merchant_id);
CREATE NONCLUSTERED INDEX idx_fact_mcc ON fact_transaction(mcc);

-- index for frequent filters
CREATE NONCLUSTERED INDEX idx_fact_fraud ON fact_transaction(fraud_label);

--    Dimension Table
-- This table is small but heavily used for slicing/filtering in dashboards

CREATE NONCLUSTERED INDEX idx_dimdate_year ON dim_date(year);
CREATE NONCLUSTERED INDEX idx_dimdate_month ON dim_date(month);
CREATE NONCLUSTERED INDEX idx_dimdate_quarter ON dim_date(quarter);

--  index for frequent filters
CREATE NONCLUSTERED INDEX idx_customer_credit ON dim_customer(credit_score);
CREATE NONCLUSTERED INDEX idx_customer_income ON dim_customer(yearly_income);

CREATE NONCLUSTERED INDEX idx_card_client ON dim_card(client_id);
CREATE NONCLUSTERED INDEX idx_card_brand ON dim_card(card_brand);

CREATE NONCLUSTERED INDEX idx_merchant_city ON dim_merchant(merchant_city);

-- Adding Primary key 
ALTER TABLE dim_mcc ADD CONSTRAINT PK_dim_mcc PRIMARY KEY (mcc);





