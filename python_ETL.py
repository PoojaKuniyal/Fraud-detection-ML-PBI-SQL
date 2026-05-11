###         SQL Schema  (done in sqlserver)
# Building fact (Main business table) and dimension tables from the Financial transaction dataset and then pushing them into SQL Server.

###         Data Pipeline (Python ETL)

import pandas as pd
import json

##      LOAD DATA   
cards_data = pd.read_csv(r'raw_data\cards_data.csv')
transactions_data = pd.read_csv(r'raw_data\transactions_data.csv')
users_data = pd.read_csv(r'raw_data\users_data.csv')

with open (r'raw_data\mcc_codes.json') as f:
    mcc_data = json.load(f)
mcc_codes = pd.DataFrame(list(mcc_data.items()), columns=["mcc", "mcc_description"])

with open(r'raw_data\train_fraud_labels.json') as f:
    fraud_data = json.load(f)
fraud_labels = pd.DataFrame(list(fraud_data['target'].items()), columns=["id", "fraud_label"])

#  Merge transaction data with fraud label / target

# Ensure both are of same data type
fraud_labels['id'] = fraud_labels['id'].astype(int)
transactions_data['id'] = transactions_data['id'].astype(int)

df = transactions_data.merge(fraud_labels, on='id',how='inner') # only transactions that have fraud labels - No null targets → Only keeps rows where a fraud label exists

df['fraud_label'] = df['fraud_label'].map({
    'Yes':1,
    'No':0
})

######  Data Cleaning

# Remove duplicates
cards_data.drop_duplicates(inplace=True)
df.drop_duplicates(inplace=True)
users_data.drop_duplicates(inplace=True)

#  check missing values, info, shape
print(cards_data.isnull().sum())
print(cards_data.head())
print(cards_data.info())
print(cards_data.shape)

print(df.isnull().sum())
print(df.head())
print(df.info())
print(df.shape)

print(users_data.isnull().sum())
print(users_data.head())
print(users_data.info())
print(users_data.shape)

# Clean money
def clean_money(col):
    return(
        col.astype(str)
        .str.replace('$','',regex=False)
        .str.replace(',','',regex=False)
        .str.replace('(', '-', regex=False)
        .str.replace(')', '', regex=False)
        .str.strip()
        .astype(float)
    )

cards_data['credit_limit'] = clean_money(cards_data['credit_limit'])
print("credit_limit cleaned value ", cards_data['credit_limit'].iloc[0])
df['amount'] = clean_money(df['amount'])
print("amount cleaned value ", df['amount'].iloc[0])

users_data['per_capita_income'] = clean_money(users_data['per_capita_income'])
print("per capita income cleaned value ", users_data['per_capita_income'].iloc[0])
users_data['yearly_income'] = clean_money(users_data['yearly_income'])
print("yearly income cleaned value ", users_data['yearly_income'].iloc[0])
users_data['total_debt'] = clean_money(users_data['total_debt'])
print("total_debt cleaned value ", users_data['total_debt'].iloc[0])


df['errors'] = df['errors'].notna().astype(int)
df.drop(columns=['merchant_state','zip'], inplace=True) # high missing values


print("-------- number of unique cards on dark web",cards_data['card_on_dark_web'].unique()) 
cards_data.drop(columns=['card_on_dark_web'], inplace=True) # low-information and zero-variance features as all values are 'NO'

###### Select fact table columns

# Convert to datetime
df['date'] = pd.to_datetime(df['date'], errors='coerce') 

df['date_key'] = df['date'].dt.strftime('%Y%m%d').astype(int)

print(" --- data type of date column ", df['date'].dtype)
print(df['date'].head())
print(df['date'].isnull().sum())

fact_transaction = df[['id','date_key','date','client_id','card_id','merchant_id',
                     'mcc','amount','use_chip','errors','fraud_label']]

fact_transaction = fact_transaction.rename(
    columns={'date':'transaction_date'}
)

###### Dimension tables (dimensional modeling)

dim_customer = users_data[['id','current_age','retirement_age','birth_year',
                           'birth_month','gender','latitude','longitude',
                           'per_capita_income','yearly_income','total_debt',
                           'credit_score']]
dim_customer = dim_customer.drop_duplicates(subset=['id'])
# Fill missing credit scores with 0 or a default, then ensure it's an integer
dim_customer['credit_score'] = dim_customer['credit_score'].fillna(0).astype(int)

dim_card = cards_data[['id', 'client_id', 'card_brand', 'card_type', 
                       'expires', 'has_chip', 'num_cards_issued', 
                       'credit_limit', 'acct_open_date', 'year_pin_last_changed']]

dim_card = dim_card.drop_duplicates(subset=['id'])

dim_merchant = df[['merchant_id','merchant_city']]

dim_merchant = dim_merchant.drop_duplicates(subset=['merchant_id'])

print(" --- duplication of merchant id ",dim_merchant['merchant_id'].duplicated().sum())

dim_mcc = mcc_codes[['mcc','mcc_description']].drop_duplicates()
dim_mcc = dim_mcc.drop_duplicates(subset=['mcc'])

dim_date = pd.DataFrame({
    'date_key': df['date'].dt.strftime('%Y%m%d').astype(int),
    'full_date': df['date'].dt.date,
    'day': df['date'].dt.day,
    'month': df['date'].dt.month,
    'month_name': df['date'].dt.month_name(),
    'quarter': 'Q' + df['date'].dt.quarter.astype(str),
    'year': df['date'].dt.year,
    'weekday': df['date'].dt.day_name(),
    'weekend_flag': df['date'].dt.dayofweek.isin([5,6]).map({True:'Yes',False:'No'})
})
dim_date = dim_date.drop_duplicates(subset=['date_key']) 

# make sure ODBC Driver 17 for SQL Server is installed.
import pyodbc
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=finance;Trusted_Connection=yes;"
)
print("Connected successfully")


######### Load into SQL (Connect & upload)

# 1. Connect -> SQLAlchemy connection string

from sqlalchemy import create_engine

# 1. Create engine with fast_executemany
engine = create_engine(
    "mssql+pyodbc://localhost\\SQLEXPRESS/finance?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server",
     fast_executemany=True
)

# 2. Upload tables / Inserting into tables created in sql from cleaned raw csv
# (Removed method='multi' to bypass 2100 parameter limit)
# Note: fast_executemany=True makes these very fast without needing method='multi'

print("Loading fact transaction...")
fact_transaction.to_sql('fact_transaction', engine, if_exists='append',index=False, chunksize=5000)
print("Loading dim_customer...")
dim_customer.to_sql('dim_customer', engine, if_exists='append', index=False)

print("Loading dim_date...")
dim_date.to_sql('dim_date', engine, if_exists='append', index=False)

print("Loading dim_card...")
dim_card.to_sql('dim_card', engine, if_exists='append', index=False)

print("Loading dim_mcc...")
dim_mcc.to_sql('dim_mcc', engine, if_exists='append', index=False)

print("Loading dim_merchant...")
dim_merchant.to_sql('dim_merchant', engine, if_exists='append', index=False)


print("All data loaded successfully.")
# replace DROPS your SQL tables and recreates them automatically -> SQL datatypes are lost, primary keys vanish, schema design becomes useless so append

# Dimension tables must contain unique entities , Fact tables contain : repeated events