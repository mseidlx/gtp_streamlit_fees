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
    df = df[(df['granularity'] == '10_min')]
    # Convert unix timestamp to datetime for better readability on plot
    df['datetime'] = pd.to_datetime(df['unix'], unit='ms')

    ##replace origin_key values with cleaner names, i.e. optimsim with OP mainnet
    df['origin_key'] = df['origin_key'].replace('optimism', 'OP Mainnet')
    df['origin_key'] = df['origin_key'].replace('arbitrum', 'Arbitrum')
    df['origin_key'] = df['origin_key'].replace('zksync_era', 'zkSync Era')
    df['origin_key'] = df['origin_key'].replace('base', 'Base')
    df['origin_key'] = df['origin_key'].replace('zora', 'Zora')
    df['origin_key'] = df['origin_key'].replace('starknet', 'Starknet')
    df['origin_key'] = df['origin_key'].replace('linea', 'Linea')

    return df

def plot_data(df):
    ## rename column datetime to "Date" and value to "Median Transaction Costs in USD"
    df = df.copy()
    df = df[(df['metric_key'] == 'txcosts_median_usd')]
    df.rename(columns={'datetime': 'Date', 'value': 'Median Transaction Costs', 'origin_key' : 'Chain'}, inplace=True)
    df.reset_index(drop=True, inplace=True)

    print(df.head())

    st.line_chart(df, x='Date', y='Median Transaction Costs', color='Chain')

def create_table(df):
    ## order by unix desc and only keep latest value per origin_key
    df = df.pivot_table(index=['origin_key', 'granularity', 'unix', 'datetime'], columns='metric_key', values='value').reset_index()
    df = df.sort_values('unix', ascending=False).drop_duplicates('origin_key')
    df = df[['origin_key', 'txcosts_avg_usd', 'txcosts_median_usd', 'txcosts_native_median_usd', 'datetime']]
    df.set_index('origin_key', inplace=True)

    #order by value ascending
    df = df.sort_values('txcosts_avg_usd', ascending=True)

    ##value column in USD
    df['txcosts_avg_usd'] = df['txcosts_avg_usd'].apply(lambda x: f"${x:,.3f}")
    df['txcosts_median_usd'] = df['txcosts_median_usd'].apply(lambda x: f"${x:,.3f}")
    df['txcosts_native_median_usd'] = df['txcosts_native_median_usd'].apply(lambda x: f"${x:,.3f}")

    ## rename column value to "Median Transaction Costs in USD" and datetime to "Last Updated"
    df.rename(columns={'datetime': 'Last Updated (UTC)', 'txcosts_median_usd': 'Median Tx Costs', 'txcosts_avg_usd': 'Avg Tx Costs', 'txcosts_native_median_usd': 'Native Transfer'}, inplace=True)

    ##reorder columns
    df = df[['Avg Tx Costs', 'Median Tx Costs', 'Native Transfer', 'Last Updated (UTC)']]

    ## replace values "$nan" with "-"
    df = df.replace('$nan', '-')

    st.table(df)

def main():
    st.image('gtp-logo-on-white.png')
    # Check if 5 minutes have passed since the last API call
    current_time = time.time()
    if current_time - st.session_state['last_run'] > 300:  # 5 minutes in seconds
        df = fetch_data()
        st.session_state['last_run'] = current_time
        st.rerun()
    else:
        df = fetch_data()  # Assuming you want to load the existing data even if not updating

    st.header("Median Transaction Costs in USD")
    # Example hyperlink
    url = "https://www.growthepie.xyz"
    link_text = "Data from growthepie.xyz"
    st.markdown(f'<a href="{url}" target="_blank">{link_text}</a>', unsafe_allow_html=True)

    # st.subheader("Data from growthepie.xyz")
    plot_data(df)
    create_table(df)

if __name__ == "__main__":
    main()
