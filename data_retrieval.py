import streamlit as st
import json
from urllib.request import urlopen
import pandas as pd
import mysql.connector

from db import save_to_database, save_to_database_debug

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
        filter_update = f"FROM_UNIXTIME(contact_custom_fields.value / 1000, '%Y-%m-%d')"
    elif update_type == "createdAt":
        filter_update = f"DATE(opportunities.createdAt)"
    else:
        filter_update = f"DATE(opportunities.lastStageChangeAt)"
    
    query = f"""
                SELECT
                    opportunities.id AS id,
                    opportunities.createdAt AS createdAt,
                    opportunities.lastStageChangeAt AS lastStageChangeAt,
                    contact_custom_fields.value AS data_acquisizione,
                    COALESCE(additional_custom_field.value, 'Non specificato') AS fonte,
                    opportunity_pipeline_stages.name AS pipeline_stage_name,
                    opportunities.monetaryValue AS opportunity_monetary_value
                FROM
                    opportunities
                    LEFT JOIN contacts ON opportunities.contactId = contacts.id
                    LEFT JOIN contact_custom_fields AS additional_custom_field 
                        ON contacts.id = additional_custom_field.contactId
                        AND additional_custom_field.id = 'UiALy82OthZAitbSZTOU'
                    LEFT JOIN opportunity_pipeline_stages 
                        ON opportunities.pipelineStageId = opportunity_pipeline_stages.id
                    LEFT JOIN contact_custom_fields 
                        ON contacts.id = contact_custom_fields.contactId
                    LEFT JOIN sub_account_custom_fields 
                        ON contact_custom_fields.id = sub_account_custom_fields.id
                WHERE
                    sub_account_custom_fields.locationId = '{st.secrets.id_cliente}'
                    AND opportunity_pipeline_stages.pipelineId='{st.secrets.pipeline_vendita}'
                    AND sub_account_custom_fields.id = 'ok7yK4uSS6wh0S2DnZrz'
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
    df_raw['data_acquisizione'] = pd.to_datetime(df_raw['data_acquisizione'], unit='ms', errors='coerce')
    df_raw['data_acquisizione'] = df_raw['data_acquisizione'].dt.strftime('%Y-%m-%d').fillna('N/A')
    df_raw['data_acquisizione'] = df_raw['data_acquisizione'].replace('NaT', 'N/A')

    try:
        save_to_database(df_raw, "attribution_data", is_api=False)
        st.success(f"Dati da attribuzione salvati correttamente")
    except Exception as e:
        st.error(f"Errore nel salvare i dati da attribuzione: {str(e)}")
