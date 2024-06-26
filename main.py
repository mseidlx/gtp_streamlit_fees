import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px

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
    df['origin_key'] = df['origin_key'].replace('polygon_zkevm', 'Polygon zkEVM')
    df['origin_key'] = df['origin_key'].replace('scroll', 'Scroll')

    return df

def plot_data(df):
    ## rename column datetime to "Date" and value to "Median Transaction Costs in USD"
    df = df.copy()
    df = df[(df['metric_key'] == 'txcosts_median_usd')]
    df.rename(columns={'datetime': 'Date', 'value': 'Median Transaction Costs', 'origin_key' : 'Chain'}, inplace=True)
    df.reset_index(drop=True, inplace=True)

    st.line_chart(df, x='Date', y='Median Transaction Costs', color='Chain', height=450, width=1200)

def plot_plotly(df):
    df = df.copy()
    df = df[(df['metric_key'] == 'txcosts_median_usd')]
    df.rename(columns={'datetime': 'Date', 'value': 'Median Transaction Costs', 'origin_key' : 'Chain'}, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df = df.sort_values(by=['Date', 'Chain'])

    fig = px.line(df, x='Date', y='Median Transaction Costs', color='Chain')

    for i, trace in enumerate(fig.data):
        trace.hovertemplate = '%{fullData.name}<br>$%{y:.4f}<extra></extra>'

    fig.update_layout(
        yaxis_title=None,
        xaxis_title=None,
        legend_title=None,
        hovermode='x unified',
        legend=dict(
            orientation="h",  # Horizontal orientation
            yanchor="bottom",
            y=-0.25,  # Negative y positions the legend below the chart
            xanchor="center",
            x=0.5
        )
    )
    st.plotly_chart(fig, use_container_width=True)

def create_df_clean(df):
    ## order by unix desc and only keep latest value per origin_key
    df = df.pivot_table(index=['origin_key', 'granularity', 'unix', 'datetime'], columns='metric_key', values='value').reset_index()
    df = df.sort_values('unix', ascending=False).drop_duplicates('origin_key')
    df = df[['origin_key', 'txcosts_avg_usd', 'txcosts_median_usd', 'txcosts_native_median_usd', 'datetime']]
    df.set_index('origin_key', inplace=True)

    #order by value ascending
    df = df.sort_values('txcosts_avg_usd', ascending=True)

    ##value column in USD
    df['txcosts_avg_usd'] = df['txcosts_avg_usd'].apply(lambda x: f"${x:,.4f}")
    df['txcosts_median_usd'] = df['txcosts_median_usd'].apply(lambda x: f"${x:,.4f}")
    df['txcosts_native_median_usd'] = df['txcosts_native_median_usd'].apply(lambda x: f"${x:,.4f}")

    ## rename column value to "Median Transaction Costs in USD" and datetime to "Last Updated"
    df.rename(columns={'datetime': 'Last Updated (UTC)', 'txcosts_median_usd': 'Median Tx Costs', 'txcosts_avg_usd': 'Avg Tx Costs', 'txcosts_native_median_usd': 'Native Transfer'}, inplace=True)

    ##reorder columns
    df = df[['Avg Tx Costs', 'Median Tx Costs', 'Native Transfer', 'Last Updated (UTC)']]

    ## replace values "$nan" with "-"
    df = df.replace('$nan', '-')

    df.reset_index(inplace=True)
    return df

def create_df_list(df, metric_key):
    ## filter df to metric_key == txcosts_median_usd put these values in list per origin_key
    df = df[df['metric_key'] == metric_key]
    df = df.sort_values('unix', ascending=True)
    df = df.groupby('origin_key')['value'].apply(list).reset_index()
    return df

def create_dataframe(df, metric_key):
    df_clean = create_df_clean(df)
    df_list = create_df_list(df, metric_key)

    ## join df_clean and df_median on origin_key
    df_clean = df_clean.merge(df_list, on='origin_key', how='left')
    df_clean.rename(columns={'value': 'Median Tx Costs Over Time'}, inplace=True)

    # ## drop column Native Transfer
    # df_clean = df_clean.drop(columns='Native Transfer')

    st.dataframe(
        df_clean,
        column_config={
            "origin_key": "Chain",
            "Median Tx Costs Over Time": st.column_config.LineChartColumn(
                "Median Tx Costs Over Time"
            ),
            # "Avg Tx Costs": st.column_config.ProgressColumn(
            #     "Avg Tx Costs",
            #     help="The average cost of a transaction in USD",
            #     format="$%f",
            # ),
            "Native Transfer": None,
        },
        hide_index=True,
        width=1000
    )


def main():
    st.set_page_config(page_title="growthepie - EIP4844 Tracker", page_icon= "https://i.ibb.co/RbSqMg2/Logo-with-Whitespace.png")
    #st.image('gtp-logo-on-white.png', width=300)

    st.info("This page will slowly be deprecated as we created a better, more integrated fees page. Please visit [fees.growthepie.xyz](https://fees.growthepie.xyz) for the latest data and features.")

    url = "https://fees.growthepie.xyz"
    image_url = "https://i.ibb.co/2YrQDMM/Screenshot-2024-04-24-120919.png" 
    st.markdown(f"[![Alt Text]({image_url})]({url})", unsafe_allow_html=True)


    st.divider()
    st.divider()
    st.divider()

    df = fetch_data()

    st.header("EIP 4844 Tracker (outdated - see info above)")
    
    options = st.multiselect(
        'Chains',
        ['OP Mainnet', 'Arbitrum', 'Base', 'Zora', 'Starknet', 'Linea', 'zkSync Era', 'Polygon zkEVM', 'Scroll'],
        ['OP Mainnet', 'Arbitrum', 'Base', 'Zora', 'Starknet', 'Linea', 'zkSync Era'])
    
    df = df[df['origin_key'].isin(options)]

    st.subheader("Median Transaction Costs in USD")
    st.text("Data is updated in 10 minute intervals. Cheap Tx here we come!")
    plot_plotly(df)
    #plot_data(df)
    create_dataframe(df, 'txcosts_median_usd')

    link_text = "Data from growthepie.xyz"
    st.markdown(f'<a href="{url}" target="_blank">{link_text}</a>', unsafe_allow_html=True)

    link_text = "Twitter Profile"
    st.markdown(f'<a href="https://twitter.com/growthepie_eth" target="_blank">{link_text}</a>', unsafe_allow_html=True)

    

if __name__ == "__main__":
    main()
