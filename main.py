import streamlit as st
import pandas as pd
import requests
import time

# Initialize or get the last run timestamp
if 'last_run' not in st.session_state:
    st.session_state['last_run'] = time.time()

def fetch_data():
    # API endpoint
    url = "https://api.growthepie.xyz/v1/fees_dict.json"
    response = requests.get(url)
    data = response.json()
    
    # Convert JSON to DataFrame
    df = pd.DataFrame(data)
    
    # Filter based on conditions
    filtered_df = df[(df['metric_key'] == 'txcosts_median_usd') & (df['granularity'] == 'hourly')]
    
    # Convert unix timestamp to datetime for better readability on plot
    df['datetime'] = pd.to_datetime(df['unix'], unit='ms')

    return filtered_df

def plot_data(df):
    st.line_chart(df, x='datetime', y='value', color='origin_key')

def create_table(df):
    ## order by unix desc and only keep latest value per origin_key
    df = df.sort_values('unix', ascending=False).drop_duplicates('origin_key')
    df = df[['origin_key', 'value', 'datetime']]
    st.table(df)

def main():
    # Check if 5 minutes have passed since the last API call
    current_time = time.time()
    if current_time - st.session_state['last_run'] > 300:  # 5 minutes in seconds
        df = fetch_data()
        st.session_state['last_run'] = current_time
        st.experimental_rerun()
    else:
        df = fetch_data()  # Assuming you want to load the existing data even if not updating

    plot_data(df)
    create_table(df)

if __name__ == "__main__":
    main()
