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

def save_to_database(df, table_name, is_api=True):
    conn = sqlite3.connect('local_data.db')
    cursor = conn.cursor()

    if is_api:
        key_columns = ['date', 'campaign']
        cursor.execute(f"SELECT {', '.join(key_columns)} FROM {table_name}")
    else:
        key_columns = ['id']
        cursor.execute(f"SELECT id FROM {table_name}")

    existing_data = set(tuple(row) for row in cursor.fetchall())

    for _, row in df.iterrows():
        key = tuple(row[col] for col in key_columns)
        key_str = tuple(str(k) for k in key)
        if key_str in existing_data:
            update_query = f"UPDATE {table_name} SET "
            update_query += ", ".join([f"{col} = ?" for col in df.columns if col not in key_columns])
            update_query += f" WHERE {' AND '.join([f'{col} = ?' for col in key_columns])}"
            update_values = [row[col] for col in df.columns if col not in key_columns] + list(key)
            cursor.execute(update_query, update_values)
        else:
            insert_query = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(['?' for _ in df.columns])})"
            cursor.execute(insert_query, row.tolist())
        
        existing_data.add(key_str)

    conn.commit()
    conn.close()

def save_to_database_debug(df, table_name, is_api=True):
    st.write(f"save_to_database {table_name}")
    conn = sqlite3.connect('local_data.db')
    cursor = conn.cursor()

    if is_api:
        st.write("is_api")
        key_columns = ['date', 'campaign']
        cursor.execute(f"SELECT {', '.join(key_columns)} FROM {table_name}")
    else:
        st.write("not is_api")
        key_columns = ['id']
        cursor.execute(f"SELECT id FROM {table_name}")

    st.write(key_columns)

    existing_data = set(tuple(row) for row in cursor.fetchall())
    st.write(existing_data)

    for _, row in df.iterrows():
        st.write(row)
        key = tuple(row[col] for col in key_columns)
        st.write(key)
        key_str = tuple(str(k) for k in key)
        st.write(key_str)
        if key_str in existing_data:
            st.write("update")
            update_query = f"UPDATE {table_name} SET "
            update_query += ", ".join([f"{col} = ?" for col in df.columns if col not in key_columns])
            update_query += f" WHERE {' AND '.join([f'{col} = ?' for col in key_columns])}"
            st.write(update_query)
            update_values = [row[col] for col in df.columns if col not in key_columns] + list(key)
            st.write(update_values)
            cursor.execute(update_query, update_values)
        else:
            st.write("insert")
            insert_query = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(['?' for _ in df.columns])})"
            st.write(insert_query)
            cursor.execute(insert_query, row.tolist())
        
        existing_data.add(key_str)
        st.write(existing_data)
    conn.commit()
    conn.close()

def get_data(table_name, start_date, end_date, custom_date_field='date'):
    conn = sqlite3.connect('local_data.db')

    query = f"SELECT * FROM {table_name} WHERE {custom_date_field} BETWEEN ? AND ?"
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    
    conn.close()
    
    return df