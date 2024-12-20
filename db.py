import sqlite3
import streamlit as st
import pandas as pd
import environ

from config import FIELDS

def initialize_database():
    conn = sqlite3.connect('local_data.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS facebook_data
                (datasource TEXT, 
                source TEXT, 
                account_id TEXT, 
                account_name TEXT, 
                date TEXT, 
                campaign TEXT, 
                adset_name TEXT,
                adset_status TEXT,
                ad_name TEXT,
                status TEXT,
                link TEXT,
                age TEXT,
                gender TEXT,
                spend REAL, 
                impressions INTEGER, 
                outbound_clicks_outbound_click INTEGER, 
                actions_lead INTEGER, 
                actions_purchase INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS facebook_geo_data
                (datasource TEXT, 
                source TEXT, 
                account_id TEXT, 
                account_name TEXT, 
                date TEXT, 
                campaign TEXT, 
                adset_name TEXT,
                ad_name TEXT,
                country TEXT,
                region TEXT,
                spend REAL, 
                impressions INTEGER, 
                outbound_clicks_outbound_click INTEGER, 
                actions_lead INTEGER, 
                actions_purchase INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS google_ads_data
                (datasource TEXT, 
                source TEXT, 
                account_id TEXT, 
                account_name TEXT, 
                date TEXT, 
                campaign TEXT, 
                spend REAL, 
                impressions INTEGER, 
                clicks INTEGER, 
                keyword_text TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tiktok_data
                (datasource TEXT, 
                source TEXT, 
                account_id TEXT, 
                account_name TEXT, 
                date TEXT, 
                campaign TEXT, 
                ad_group_name TEXT,
                ad_group_operation_status TEXT,
                ad_name TEXT,
                ad_operation_status TEXT,
                spend REAL, 
                impressions INTEGER, 
                clicks INTEGER, 
                total_sales_lead INTEGER, 
                total_purchase INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS googleanalytics4_data
                (datasource TEXT, 
                source TEXT, 
                account_id TEXT, 
                account_name TEXT, 
                date TEXT, 
                campaign TEXT, 
                sessions INTEGER, 
                engaged_sessions INTEGER, 
                active_users INTEGER, 
                page_path TEXT, 
                user_engagement_duration REAL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS opp_data
                (id TEXT, 
                createdAt TEXT, 
                lastStageChangeAt TEXT, 
                monetaryValue REAL, 
                venditore TEXT, 
                stage TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS attribution_data
                (id TEXT, 
                createdAt TEXT, 
                lastStageChangeAt TEXT, 
                data_acquisizione TEXT, 
                fonte TEXT, 
                pipeline_stage_name TEXT, 
                opportunity_monetary_value REAL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS transaction_data
                (id TEXT, 
                date TEXT, 
                product_name TEXT, 
                product_meta JSON, 
                total REAL, 
                currency TEXT, 
                status TEXT)''')

    conn.commit()
    conn.close()

def add_column(table_name, column_name, column_type):
    conn = sqlite3.connect('local_data.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        st.success(f"Colonna {column_name} aggiunta correttamente")
    except sqlite3.OperationalError as e:
        st.error(f"Errore durante l'aggiunta della colonna {column_name}: {e}")

    conn.commit()
    conn.close()

def delete_column(table_name, column_name):
    conn = sqlite3.connect('local_data.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
        st.success(f"Colonna {column_name} eliminata correttamente")
    except sqlite3.OperationalError as e:
        st.error(f"Errore durante l'eliminazione della colonna {column_name}: {e}")

    conn.commit()
    conn.close()

def delete_table(table_name):
    conn = sqlite3.connect('local_data.db')
    cursor = conn.cursor()

    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        st.success(f"Tabella {table_name} eliminata correttamente")
    except sqlite3.OperationalError as e:
        st.error(f"Errore durante l'eliminazione della tabella {table_name}: {e}")
    
    conn.commit()
    conn.close()

def delete_table_data(table_name):
    conn = sqlite3.connect('local_data.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"DELETE FROM {table_name}")
        st.success(f"Dati della tabella {table_name} eliminati correttamente")
    except sqlite3.OperationalError as e:
        st.error(f"Errore durante l'eliminazione dei dati della tabella {table_name}: {e}")

    conn.commit()
    conn.close()

def save_to_database(df, table_name, is_api=True):
    conn = sqlite3.connect('local_data.db')
    cursor = conn.cursor()
    
    if is_api:
        if table_name == 'facebook_data':
            key_columns = ['date', 'campaign', 'adset_name', 'ad_name', 'age', 'gender']
        elif table_name == 'google_ads_data':
            key_columns = ['date', 'campaign']
        elif table_name == 'tiktok_data':
            key_columns = ['date', 'campaign', 'ad_group_name', 'ad_name']
        elif table_name == 'googleanalytics4_data':
            key_columns = ['date', 'campaign']
        else:
            st.warning(f"Tabella {table_name} non supportata nella funzione save_to_database. I dati potrebbero non essere salvati correttamente.")
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

def get_data(table_name, start_date, end_date, custom_date_field='date'):
    conn = sqlite3.connect('local_data.db')

    query = f"SELECT * FROM {table_name} WHERE {custom_date_field} BETWEEN ? AND ?"
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    
    conn.close()
    
    return df

def show_table_data(table_name, start_date, end_date, custom_date_field='date'):
    env = environ.Env()
    environ.Env.read_env()
    
    source = table_name.removesuffix("_data")
    if custom_date_field == 'date':
        account_id_key = f"{source}_account_id"
        account_id = env(account_id_key)
    else:
        account_id = None

    conn = sqlite3.connect('local_data.db')
    
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    
    schema_info = cursor.fetchall()
    schema_df = pd.DataFrame(schema_info, columns=['id', 'nome', 'tipo', 'notnull', 'dflt_value', 'pk'])

    if account_id:
        data_df = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE account_id = ? AND {custom_date_field} BETWEEN ? AND ?", conn, params=(account_id, start_date, end_date))
    else:
        data_df = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE {custom_date_field} BETWEEN ? AND ?", conn, params=(start_date, end_date))
    
    conn.close()
    
    st.subheader("Struttura della tabella")
    st.dataframe(schema_df, column_order=['id', 'nome', 'tipo'], use_container_width=True, hide_index=True)

    st.subheader("Dati della tabella")
    st.dataframe(data_df, use_container_width=True, hide_index=True)