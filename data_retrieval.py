import streamlit as st
import json
from urllib.request import urlopen
import pandas as pd
import mysql.connector

from db import save_to_database

def api_retrieving(data_source, fields, start_date, end_date):
    url = f"{st.secrets.source}{data_source}?api_key={st.secrets.api_key}&date_from={start_date}&date_to={end_date}&fields={fields}&_renderer=json"
    
    with urlopen(url) as response:
        data_json = json.load(response)
    
    df_raw = pd.json_normalize(data_json, record_path=["data"])
    df_raw["date"] = pd.to_datetime(df_raw["date"]).dt.date
    
    return df_raw

def api_retrieve_data(source, fields, start_date, end_date):
    try:
        df = api_retrieving(source, fields, start_date, end_date)
        
        try:
            save_to_database(df, f"{source}_data", is_api=True)
            st.success(f"Dati da {source} salvati correttamente")
        except Exception as e:
            st.error(f"Errore nel salvare i dati da {source}: {str(e)}")
    except Exception as e:
        st.error(f"Errore nel recupero dei dati da {source}: {str(e)}")

def opp_retrieving(pool, update_type, start_date, end_date):
    conn = pool.get_connection()
    cursor = conn.cursor()
    
    query = f"""
                SELECT
                    o.id AS id,
                    o.createdAt,
                    o.lastStageChangeAt,
                    o.monetaryValue,
                    ops.name AS stage
                FROM
                    opportunities o
                JOIN opportunity_pipeline_stages ops ON o.pipelineStageId=ops.id
                WHERE
                    o.locationId='{st.secrets.id_cliente}'
                    AND ops.pipelineId='{st.secrets.pipeline_vendita}'
                    AND o.{update_type} >= '{start_date}T00:00:00.000Z'
                    AND o.{update_type} <= '{end_date}T23:59:59.999Z'
                ORDER BY
                    o.{update_type};
            """
    
    cursor.execute(query)

    df_raw = cursor.fetchall()

    cursor.close()
    conn.close()

    df_raw = pd.DataFrame(df_raw, columns=cursor.column_names)
    df_raw['createdAt'] = pd.to_datetime(df_raw['createdAt']).dt.date
    df_raw['lastStageChangeAt'] = pd.to_datetime(df_raw['lastStageChangeAt']).dt.date

    try:
        save_to_database(df_raw, "opp_data", is_api=False)
        st.success(f"Dati da opportunità salvati correttamente")
    except Exception as e:
        st.error(f"Errore nel salvare i dati da opportunità: {str(e)}")

def attribution_retrieving(pool, update_type, start_date, end_date):
    conn = pool.get_connection()
    cursor = conn.cursor()
    
    if update_type == "data_acquisizione":
        filter_update = f"FROM_UNIXTIME(ccf_data.value / 1000, '%Y-%m-%d')"
    elif update_type == "createdAt":
        filter_update = f"DATE(o.createdAt)"
    else:
        filter_update = f"DATE(o.lastStageChangeAt)"
    
    query = f"""
                SELECT
                    o.id AS id,
                    o.createdAt AS createdAt,
                    o.lastStageChangeAt AS lastStageChangeAt,
                    ccf_data.value AS data_acquisizione,
                    COALESCE(ccf_fonte.value, 'Non specificato') AS fonte,
                    ops.name AS pipeline_stage_name,
                    o.monetaryValue AS opportunity_monetary_value
                FROM
                    opportunities o
                    INNER JOIN opportunity_pipeline_stages ops ON o.pipelineStageId = ops.id
                    LEFT JOIN contacts c ON o.contactId = c.id
                    LEFT JOIN contact_custom_fields ccf_data ON c.id = ccf_data.contactId AND ccf_data.id = 'ok7yK4uSS6wh0S2DnZrz'
                    LEFT JOIN contact_custom_fields ccf_fonte ON c.id = ccf_fonte.contactId AND ccf_fonte.id = 'UiALy82OthZAitbSZTOU'
                WHERE
                    o.locationId = '{st.secrets.id_cliente}'
                    AND ops.pipelineId = '{st.secrets.pipeline_vendita}'
                    AND {filter_update} BETWEEN '{start_date}' AND '{end_date}';
            """
    
    cursor.execute(query)

    df_raw = cursor.fetchall()
    
    cursor.close()
    conn.close()

    df_raw = pd.DataFrame(df_raw, columns=cursor.column_names)
    df_raw['createdAt'] = pd.to_datetime(df_raw['createdAt']).dt.date
    df_raw['lastStageChangeAt'] = pd.to_datetime(df_raw['lastStageChangeAt']).dt.date
    df_raw['lastStageChangeAt'] = df_raw['lastStageChangeAt'].fillna(df_raw['createdAt'])
    df_raw['data_acquisizione'] = pd.to_datetime(pd.to_numeric(df_raw['data_acquisizione'], errors='coerce'), unit='ms', errors='coerce')
    df_raw['data_acquisizione'] = df_raw['data_acquisizione'].dt.strftime('%Y-%m-%d').fillna('N/A')
    df_raw['data_acquisizione'] = df_raw['data_acquisizione'].replace('NaT', 'N/A')

    try:
        save_to_database(df_raw, "attribution_data", is_api=False)
        st.success(f"Dati da attribuzione salvati correttamente")
    except Exception as e:
        st.error(f"Errore nel salvare i dati da attribuzione: {str(e)}")

def order_retrieving(pool, start_date, end_date):
    conn = pool.get_connection()
    cursor = conn.cursor()
    
    query = f"""
                SELECT
                    pay.contactId AS id,
                    pay.createdAt AS date,
                    pay.entitySourceName AS product_name,
                    pay.entitySourceMeta AS product_meta,
                    pay.amount AS total,
                    pay.currency AS currency,
                    pay.status AS status
                FROM
                    payment_transactions pay
                WHERE
                    pay.altId = '{st.secrets.id_cliente}'
                    AND pay.createdAt BETWEEN '{start_date}' AND '{end_date}';
            """
    
    cursor.execute(query)

    df_raw = cursor.fetchall()
    
    cursor.close()
    conn.close()

    df_raw = pd.DataFrame(df_raw, columns=cursor.column_names)
    df_raw['date'] = pd.to_datetime(df_raw['date']).dt.date

    try:
        save_to_database(df_raw, "payment_orders", is_api=False)
        st.success(f"Dati da transazioni salvati correttamente")
    except Exception as e:
        st.error(f"Errore nel salvare i dati da transazioni: {str(e)}")