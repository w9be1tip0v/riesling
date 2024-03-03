import streamlit as st
import streamlit_authenticator as sa
import pandas as pd
from datetime import datetime
from polygon_api import get_historical_data_as_df, get_financials_as_df, create_financials_dataframe, get_company_details, get_stock_splits, get_dividends_data, get_news
from chart import plot_candlestick_chart
from config.display_config import display_data_with_default_sort, escape_markdown


# Metadata
st.set_page_config(
    page_title='Polygon Data Viewer',
    page_icon=':hatched_chick:',
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "#### This is a Streamlit app to view financial data from the Polygon API.\n\nCopyright 2024, PyWeOp. All rights reserved.\n\n"
    }
)

# Read envinmnet for Development
API_KEY = st.secrets["API_KEY"]
if API_KEY is None:
    st.error("API_KEY is not set in .env file")
    st.stop()


### Streamlit UI ###
    
# Display the title of the app
st.title('Polygon Data Viewer')

# Set the app mode to 'Select' if it's not set
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = 'Select'

# Sidebar to select the market data to view
app_mode = st.sidebar.selectbox(
    'Choose the Market Data to View:',
    ['Select', 'Company Detail', 'Historical Stock Data', 'Company Financials Data', 'Stock Splits Data', 'Dividends Data']
)
st.session_state.app_mode = app_mode

# Top-level header
if st.session_state.app_mode == 'Select':
    st.header('Latest News')
    # Get news data and display it
    news_data = get_news()
    # Display news data
    for news in news_data:
        title = news.get('title', 'No Title Available')
        description = news.get('description', 'No Summary Available')
        author = news.get('author', 'Unknown Author')
        published_date = news.get('published_utc', 'Unknown Date')
        tickers = news.get('tickers', 'N/A')  # Tickers related to the news

        # Convert tickers to a comma-separated string
        if isinstance(tickers, list):
            tickers = ', '.join(tickers)

        article_url = news.get('article_url', '#')
        image_url = news.get('image_url')  # URL of the image

        # Escape $ in the description to avoid rendering as LaTeX
        escaped_description = escape_markdown(description)

        # Display news title, summary, author, published date, and tickers
        st.markdown(f"##### {title}")
        if image_url:  # If the news has an image, display it
            st.image(image_url, width=300)  # Image width is set to 300 pixels
            st.write(f"**Summary:**\n{escaped_description}")
            st.markdown(f"Author: {author}, Published on: {published_date}")
            st.write(f"Tickers: {tickers}")
        
        # Display a link to read more
        st.write(f"[Read more - external link]({article_url})")
        st.write("---")


# Historical Stock Data
elif st.session_state.app_mode == 'Historical Stock Data':
    st.header("Historical Stock Data")
    ticker = st.text_input('Enter ticker symbol', 'AAPL')
    timespan = st.selectbox('Select timespan', options=['minute', 'hour', 'day', 'month', 'year'], index=2)  # Default to 'day'
    from_date = st.date_input('From date', datetime(2022, 1, 1))
    to_date = st.date_input('To date', datetime.today())
    adjusted = st.checkbox('Adjust for stock splits', value=True)  # checkbox default value is True for adjusted

    if st.button('Get Historical Data'):
        df = get_historical_data_as_df(ticker, from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d"), adjusted, timespan, API_KEY)
        if not df.empty:
            # Plot candlestick chart
            plot_candlestick_chart(df)
            display_data_with_default_sort(df, 'Date')
        else:
            st.error("No historical data found.")


# Financials Data
elif st.session_state.app_mode == 'Company Financials Data':
    st.header("Company Financials Data")
    ticker = st.text_input('Enter ticker symbol', 'AAPL')
    limit = st.number_input('Enter the number of financial records to retrieve (min=1, max=100)', min_value=1, max_value=100, value=30) # Default to 30
    # Dropdown for timeframe
    timeframe = st.selectbox('Select timeframe', options=['', 'annual', 'quarterly', 'ttm'], index=0)

    if st.button('Get Financials'):
        # Pass None if the selected option is 'None'
        timeframe_to_pass = None if timeframe == '' else timeframe
        financials_data = get_financials_as_df(ticker, limit, API_KEY, timeframe=timeframe_to_pass)
        df_financials = create_financials_dataframe(financials_data)
        display_data_with_default_sort(df_financials, 'End Date')


# Company Detail
elif st.session_state.app_mode == 'Company Detail':
    st.header("Company Detail")
    ticker = st.text_input('Enter ticker symbol', 'AAPL').upper()
    
    if st.button('Get Company Details'):
        try:
            company_details_df = get_company_details(ticker, API_KEY)
            if not company_details_df.empty:
                # Display company logos
                if 'branding' in company_details_df.index:
                    branding_info = company_details_df.loc['branding', 0]
                    if isinstance(branding_info, dict) and 'logo_url' in branding_info:
                        logo_url = branding_info['logo_url']
                        # Add API key to the logo URL
                        logo_url_with_key = f"{logo_url}?apiKey={API_KEY}"
                        st.markdown(f"<div style='text-align: center'><img src='{logo_url_with_key}' height='100'></div>", unsafe_allow_html=True)

                # Remove branding from the details
                company_details_df = company_details_df.drop('branding', errors='ignore')
                
                # Convert homepage_url to clickable link
                if 'homepage_url' in company_details_df.index:
                    homepage_url = company_details_df.loc['homepage_url', 0]
                    homepage_link = f"<a href='{homepage_url}' target='_blank'>{homepage_url}</a>"
                    company_details_df.loc['homepage_url', 0] = homepage_link

                # Format address
                if 'address' in company_details_df.index:
                    address_info = company_details_df.loc['address', 0]
                    if isinstance(address_info, dict):
                        formatted_address = ', '.join([address_info.get(k, '') for k in ['address1', 'city', 'state', 'postal_code']])
                        company_details_df.loc['address', 0] = formatted_address

                # Display company details in a table
                company_details_df = company_details_df.reset_index().rename(columns={'index': 'Key', 0: 'Value'})
                st.markdown("""
                    <style>
                        .dataframe th, .dataframe td {
                            text-align: center;
                        }
                        .dataframe td {
                            max-width: 800px;
                            word-wrap: break-word;
                        }
                    </style>
                    """, unsafe_allow_html=True)
                st.write(company_details_df.to_html(escape=False, index=False), unsafe_allow_html=True)

                # Fetch and display related news
                related_news = get_news(ticker=ticker)
                st.subheader(f"Related News for {ticker}")
                for news_item in related_news[:3]:  # Display only the first 3 related news items
                    title = news_item.get('title', 'No Title Available')
                    description = news_item.get('description', 'No Summary Available')
                    author = news_item.get('author', 'Unknown Author')
                    published_date = news_item.get('published_utc', 'Unknown Date')
                    article_url = news_item.get('article_url', '#')
                    image_url = news_item.get('image_url')

                    # Escape $ in the description to avoid rendering as LaTeX
                    escaped_description = escape_markdown(description)
                    
                    st.markdown(f"##### [{title}]({article_url})")
                    if image_url:
                        st.image(image_url, width=300)
                        st.markdown(f"**Summary:** {escaped_description}")
                        st.markdown(f"Author: {author}, Published on: {published_date}")
                        st.write("---")                
            else:
                st.error("No company details found.")
        except Exception as e:
            st.error(str(e))

# Stock Splits Data
elif st.session_state.app_mode == 'Stock Splits Data':
    st.header("Stock Splits Data")
    ticker = st.text_input('Enter ticker symbol (optional)')

    # execution_date filters
    with st.expander("Execution Date Filters", expanded=False):  # expanded=False to collapse the expander by default
        # date_input returns a datetime.date object
        gt_date = st.date_input('Execution Date Greater Than (optional)', value=None, key='gt')
        gte_date = st.date_input('Execution Date Greater Than Or Equal To (optional)', value=None, key='gte')
        lt_date = st.date_input('Execution Date Less Than (optional)', value=None, key='lt')
        lte_date = st.date_input('Execution Date Less Than Or Equal To (optional)', value=None, key='lte')

        # Convert datetime.date to string in 'YYYY-MM-DD' format
        gt = gt_date.strftime('%Y-%m-%d') if gt_date else ''
        gte = gte_date.strftime('%Y-%m-%d') if gte_date else ''
        lt = lt_date.strftime('%Y-%m-%d') if lt_date else ''
        lte = lte_date.strftime('%Y-%m-%d') if lte_date else ''

    limit = st.number_input('Limit', min_value=1, max_value=1000, value=50, step=1)

    if st.button('Get Stock Splits'):
        # Create a dictionary of date filters
        date_filters = {'gt': gt, 'gte': gte, 'lt': lt, 'lte': lte}
        df_splits = get_stock_splits(ticker, limit, **date_filters)
        display_data_with_default_sort(df_splits, 'Execution Date')

# Dividends Data
elif st.session_state.app_mode == 'Dividends Data':
    st.header("Dividends Data")
    ticker = st.text_input('Enter ticker symbol', 'AAPL').upper()
    limit = st.number_input('Limit', min_value=1, max_value=1000, value=50, step=1)

    if st.button('Get Dividends'):
        dividends_data = get_dividends_data(ticker, limit, API_KEY)
        if dividends_data:
            # Convert the list of dictionaries to a DataFrame
            df_dividends = pd.DataFrame(dividends_data)

            # Rename columns
            df_dividends.rename(columns={
                'ticker': 'Ticker',
                'declaration_date': 'Declaration Date',
                'ex_dividend_date': 'Ex Dividend Date',
                'record_date': 'Record Date',
                'pay_date': 'Pay Date',
                'frequency': 'Frequency',
                'dividend_type': 'Type',
                'cash_amount': 'Amount'
            }, inplace=True)

            # Reorder columns
            columns_order = ['Ticker', 'Declaration Date', 'Ex Dividend Date', 'Record Date', 'Pay Date', 'Frequency', 'Type', 'Amount']
            df_dividends = df_dividends[columns_order]

            # Use the display_data_with_default_sort function to display the DataFrame sorted by 'Declaration Date'
            display_data_with_default_sort(df_dividends, 'Declaration Date')
        else:
            st.error("No dividends data found.")
