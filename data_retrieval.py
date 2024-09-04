import streamlit as st
import json
from urllib.request import urlopen
import pandas as pd
import mysql.connector

def api_retrieving(data_source, fields, start_date, end_date):
    url = f"{st.secrets.source}{data_source}?api_key={st.secrets.api_key}&date_from={start_date}&date_to={end_date}&fields={fields}&_renderer=json"
    
    with urlopen(url) as response:
        data_json = json.load(response)
    
    df_raw = pd.json_normalize(data_json, record_path=["data"])
    df_raw["date"] = pd.to_datetime(df_raw["date"]).dt.date
    
    return df_raw

def api_retrieve_data(source, fields, start_date, end_date):
    try:
        if source == 'opportunities':
            return opp_created_retrieving(pool, start_date, end_date)
        else:
            return api_retrieving(source, fields, start_date, end_date)
    except Exception as e:
        st.warning(f"Errore nel recupero dei dati da {source}: {str(e)}")
        return pd.DataFrame()

def opp_retrieving(pool, start_date, end_date):
    conn = pool.get_connection()
    cursor = conn.cursor()
    
    query = f"""
                SELECT
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
                    AND o.createdAt >= '{start_date}T00:00:00.000Z'
                    AND o.createdAt <= '{end_date}T23:59:59.999Z'
                ORDER BY
                    o.createdAt;
            """

    cursor.execute(query)

    df_raw = cursor.fetchall()

    cursor.close()
    conn.close()

    df_raw = pd.DataFrame(df_raw, columns=cursor.column_names)
    df_raw['createdAt'] = pd.to_datetime(df_raw['createdAt']).dt.date
    df_raw['lastStageChangeAt'] = pd.to_datetime(df_raw['lastStageChangeAt']).dt.date

    return df_raw

def lead_retrieving(pool, start_date, end_date):
    conn = pool.get_connection()
    cursor = conn.cursor()
    
    query = f"""
                SELECT
                    contacts.email,
                    sub_account_custom_fields.name AS custom_field_name,
                    FROM_UNIXTIME(contact_custom_fields.value / 1000, '%d/%m/%Y') AS custom_field_value,
                    additional_custom_field.value AS additional_custom_field_value,
                    opportunity_pipeline_stages.name AS pipeline_stage_name
                FROM
                    contacts
                    JOIN contact_custom_fields ON contacts.id = contact_custom_fields.contactId
                    JOIN sub_account_custom_fields ON contact_custom_fields.id = sub_account_custom_fields.id
                    LEFT JOIN contact_custom_fields AS additional_custom_field
                        ON contacts.id = additional_custom_field.contactId
                        AND additional_custom_field.id = 'UiALy82OthZAitbSZTOU'
                    LEFT JOIN opportunities ON contacts.id = opportunities.contactId
                    LEFT JOIN opportunity_pipeline_stages ON opportunities.pipelineStageId = opportunity_pipeline_stages.id
                WHERE
                    sub_account_custom_fields.locationId = '{st.secrets.id_cliente}'
                    AND sub_account_custom_fields.id = 'ok7yK4uSS6wh0S2DnZrz'
                    AND FROM_UNIXTIME(contact_custom_fields.value / 1000, '%Y-%m-%d') BETWEEN {start_date} AND {end_date};
            """

    cursor.execute(query)

    df_raw = cursor.fetchall()

    cursor.close()
    conn.close()

    return pd.DataFrame(df_raw, columns=cursor.column_names)
