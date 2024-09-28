import sqlite3
import streamlit as st
import pandas as pd

from config import FIELDS

def initialize_database():
    conn = sqlite3.connect('local_data.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS facebook_data
                 (datasource TEXT, source TEXT, account_id TEXT, account_name TEXT, date TEXT, campaign TEXT, spend REAL, impressions INTEGER, outbound_clicks_outbound_click INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS google_ads_data
                 (datasource TEXT, source TEXT, account_id TEXT, account_name TEXT, date TEXT, campaign TEXT, spend REAL, impressions INTEGER, clicks INTEGER, keyword_text TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS googleanalytics4_data
                 (datasource TEXT, source TEXT, account_id TEXT, account_name TEXT, date TEXT, campaign TEXT, sessions INTEGER, engaged_sessions INTEGER, active_users INTEGER, page_path TEXT, user_engagement_duration REAL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS opp_data
                 (id TEXT, createdAt TEXT, lastStageChangeAt TEXT, monetaryValue REAL, stage TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS attribution_data
                 (id TEXT, createdAt TEXT, lastStageChangeAt TEXT, data_acquisizione TEXT, fonte TEXT, pipeline_stage_name TEXT, opportunity_monetary_value REAL)''')

    conn.commit()
    conn.close()

def save_to_database_api(df, table_name):
    conn = sqlite3.connect('local_data.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT date, campaign FROM {table_name}")
    existing_data = set(row[0] for row in cursor.fetchall())

    for _, row in df.iterrows():
        key = (row['date'], row['campaign'])
        if key in existing_data:
            update_query = f"UPDATE {table_name} SET "
            update_query += ", ".join([f"{col} = ?" for col in df.columns if col not in ['date', 'campaign']])
            update_query += " WHERE date = ? AND campaign = ?"
            cursor.execute(update_query, [row[col] for col in df.columns if col not in ['date', 'campaign']] + list(key))
        else:
            insert_query = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(['?' for _ in df.columns])})"
            cursor.execute(insert_query, row.tolist())

    conn.commit()
    conn.close()

def save_to_database_sql(df, table_name):
    conn = sqlite3.connect('local_data.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT id FROM {table_name}")
    existing_ids = set(row[0] for row in cursor.fetchall())

    for _, row in df.iterrows():
        if row['id'] in existing_ids:
            update_query = f"UPDATE {table_name} SET "
            update_query += ", ".join([f"{col} = ?" for col in df.columns if col != 'id'])
            update_query += " WHERE id = ?"
            cursor.execute(update_query, [row[col] for col in df.columns if col != 'id'] + [row['id']])
        else:
            insert_query = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(['?' for _ in df.columns])})"
            cursor.execute(insert_query, row.tolist())

    conn.commit()
    conn.close()

def get_data(table_name, start_date, end_date, custom_date_field='date'):
    conn = sqlite3.connect('local_data.db')

    query = f"SELECT * FROM {table_name} WHERE {custom_date_field} BETWEEN ? AND ?"
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    
    conn.close()
    
    return df