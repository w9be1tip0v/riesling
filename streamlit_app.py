import streamlit as st
import requests
import requests_cache
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import os

# Streamlit app configuration
st.set_page_config(page_title='Polygon Data Viewer', layout="wide")
st.title('Polygon Data Viewer')

# Read environment secret for Streamlit App
API_KEY = st.secrets["API_KEY"]
if API_KEY is None:
    st.error("API_KEY is not set in .env file")
    st.stop()

### Configure the Streamlit app ###
    
# Apply default sort and display the data
def display_data_with_default_sort(df, sort_column):
    if not df.empty:
        df_sorted = df.sort_values(by=sort_column, ascending=False)
        st.dataframe(df_sorted)
    else:
        st.error("No data found.")

# Escape Markdown special characters
def escape_markdown(text):
    # Special characters in Markdown
    markdown_special_chars = ["\\", "`", "*", "_", "{", "}", "[", "]", "(", ")", "#", "+", "-", ".", "!", "|", ":", "$", ">"]
    for char in markdown_special_chars:
        text = text.replace(char, f"\\{char}")
    
    return text

# Configure logging
def setup_logging():
    # Set the root directory path
    root_dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))     # Get the parent directory of the current file

    # Path to the .log directory 
    log_directory = os.path.join(root_dir_path, '.log')

    # Create the .log directory if it does not exist
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Log file name with the current date
    log_filename = os.path.join(log_directory, f"polygon_api_{datetime.now().strftime('%Y-%m-%d')}.log")

    # Set up logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Set up a TimedRotatingFileHandler
    handler = TimedRotatingFileHandler(
    log_filename,  # Log file name
    when='midnight',  # Split the log file at midnight
    interval=1,  # Split the log file every day
    backupCount=30,  # Keep 30 log files
    encoding='utf-8',  # Set the encoding to UTF-8
    delay=False,  # Write log messages immediately
    utc=False,  # Use local time
    )

    # Set the log message format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # Set the log message format
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger


#### Define the Streamlit app mode ####

# Initialize the logger
logger = setup_logging()

# Creat .cache directory if it doesn't exist 
cache_dir = '.cache'
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

# Enable requests_cache to cache API responses
requests_cache.install_cache('.cache/polygon_api_cache', expire_after=1800)  # 30 minutes

# Apply comma formatting to the entire DataFrame
def format_with_comma(df):
    for col in df.select_dtypes(include=['float', 'int']).columns:
        df[col] = df[col].apply(lambda x: f"{x:,.2f}")
    return df

# Get historical stock data from Polygon API
def get_historical_data_as_df(ticker, from_date, to_date, adjusted, timespan, api_key):
    adjusted_param = 'true' if adjusted else 'false'
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/{timespan}/{from_date}/{to_date}?adjusted={adjusted_param}&apiKey={api_key}"
    logger.info(f"Requesting historical data for {ticker} from {from_date} to {to_date} with adjusted={adjusted_param} and timespan={timespan}") # Log the request
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get('results', [])
        if data:
            df = pd.DataFrame(data)
            df['t'] = pd.to_datetime(df['t'], unit='ms').dt.date
            df.rename(columns={'t': 'Date', 'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close', 'v': 'Volume'}, inplace=True)
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            df = format_with_comma(df)  # Apply comma formatting
            return df
        else:
            logger.warning(f"No data found for {ticker} from {from_date} to {to_date}")
            return pd.DataFrame()  # Return empty dataframe if no data found
    else:
        logger.error(f"API request failed for {ticker} with status code {response.status_code}: {response.text}")
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")


# Get financials data from Polygon API
def get_financials_as_df(ticker, limit, api_key, timeframe=None):
    url = f"https://api.polygon.io/vX/reference/financials?ticker={ticker}&limit={limit}&apiKey={api_key}"
    if timeframe:
        url += f"&timeframe={timeframe}"
    logger.info(f"Requesting financials data for {ticker} with limit {limit} and timeframe {timeframe}")
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()['results']
        logger.info(f"Successfully retrieved financials data for {ticker}. Number of records: {len(data)}")
        return data
    else:
        logger.error(f"Failed to retrieve financials data for {ticker}. Status code: {response.status_code}, Response: {response.text}")
        return []



# Create a dataframe from the financials data
def create_financials_dataframe(data):
    logger.info(f"Starting to create dataframe from financials data. Number of records: {len(data)}")
    records = []

    for item in data:
        record = {
            "CIK": item.get("cik"),
            "Company Name": item.get("company_name"),
            "Fiscal Year": item.get("fiscal_year"),
            "Fiscal Period": item.get("fiscal_period"),
            "Start Date": item.get("start_date"),
            "End Date": item.get("end_date"),
            "Filing Date": item.get("filing_date"),
        }
        
        financials = item.get('financials', {})
        for section, section_data in financials.items():
            for key, value in section_data.items():
                label = value.get("label")
                if label:
                    record[label] = value.get("value")

        # Free Cash Flow calculation
        net_cash_flow_op = record.get("Net Cash Flow From Operating Activities", 0)
        net_cash_flow_inv = record.get("Net Cash Flow From Investing Activities", 0)
        record["Free Cash Flow"] = net_cash_flow_op + net_cash_flow_inv
        
        records.append(record)

    if records:
        logger.info("Successfully created records for dataframe.")
    else:
        logger.warning("No records were created for the dataframe.")

    df = pd.DataFrame(records)
    df = format_with_comma(df)  # Apply comma formatting for entire DataFrame
    columns_order = [
        "CIK", "Company Name", "Fiscal Year", "Fiscal Period", "Start Date", "End Date", "Filing Date",
        "Revenues", "Gross Profit", "Operating Income/Loss", "Income/Loss From Continuing Operations Before Tax",
        "Net Income/Loss", "Basic Earnings Per Share", "Diluted Earnings Per Share", "Assets",
        "Current Assets", "Noncurrent Assets", "Liabilities", "Current Liabilities", "Noncurrent Liabilities",
        "Equity", "Net Cash Flow From Operating Activities", "Net Cash Flow From Investing Activities", 
        "Net Cash Flow From Financing Activities", "Free Cash Flow"
    ]
    df = df[[col for col in columns_order if col in df.columns]]

    logger.info(f"Dataframe creation completed. Number of rows: {df.shape[0]}")
    return df

# Get company details from Polygon API
def get_company_details(ticker, api_key):
    logger.info(f"Requesting company details for ticker: {ticker}")
    url = f"https://api.polygon.io/v3/reference/tickers/{ticker}?apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get('results', {})
        if data:
            logger.info(f"Successfully retrieved company details for {ticker}.")
        else:
            logger.warning(f"Company details for {ticker} were found, but no data was returned.")
        # Convert the data to a dataframe
        details_df = pd.DataFrame([data])
        return details_df.transpose()
    else:
        logger.error(f"Failed to retrieve company details for {ticker}: HTTP {response.status_code}")
        raise Exception(f"Failed to retrieve company details: {response.status_code}")
    
# Get stock splits data from Polygon API
def get_stock_splits(ticker=None, limit=50, **date_filters):
    logger.info(f"Requesting stock splits data for ticker: {ticker if ticker else 'All Tickers'} with limit: {limit}")
    # Base URL
    base_url = f'https://api.polygon.io/v3/reference/splits?limit={limit}&apiKey={API_KEY}'
    
    # Add ticker to the URL if provided
    if ticker:
        base_url += f'&ticker={ticker}'
    
    # Add date filters to the URL
    for key, value in date_filters.items():
        if value:  # Only add the filter if the value is not None
            base_url += f'&execution_date.{key}={value}'

    response = requests.get(base_url)
    if response.status_code == 200:
        data = response.json().get('results', [])
        if data:
            logger.info(f"Successfully retrieved stock splits data for {ticker if ticker else 'All Tickers'}.")
            df = pd.DataFrame(data)[['ticker', 'execution_date', 'split_from', 'split_to']]
            df.columns = ['Ticker', 'Execution Date', 'Split From', 'Split To']
            df['Adjustment Factor'] = df['Split From'] / df['Split To']
            df['Adjustment Factor'] = df['Adjustment Factor'].apply(lambda x: f"{x:.10f}")
            return df
        else:
            logger.warning(f"Stock splits data for {ticker if ticker else 'All Tickers'} was found, but no data was returned.")
            return pd.DataFrame(columns=['Ticker', 'Execution Date', 'Split From', 'Split To', 'Adjustment Factor'])
    else:
        logger.error(f"Failed to retrieve stock splits data for {ticker if ticker else 'All Tickers'}: HTTP {response.status_code}")
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

# Get dividends data from Polygon API
def get_dividends_data(ticker, limit, api_key):
    logger.info(f"Requesting dividends data for ticker: {ticker} with limit: {limit}")
    url = f"https://api.polygon.io/v3/reference/dividends?ticker={ticker}&limit={limit}&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get('results', [])
        if data:
            logger.info(f"Successfully retrieved dividends data for {ticker}.")
            return data
        else:
            logger.warning(f"Dividends data for {ticker} was found, but no data was returned.")
            return []
    else:
        logger.error(f"Failed to retrieve dividends data for {ticker}: HTTP {response.status_code}")
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
    

# Get news from Polygon API    
def get_news(ticker=None, limit=5, api_key=API_KEY):
    # Use the ticker-specific news URL if ticker is provided
    if ticker:
        url = f"https://api.polygon.io/v2/reference/news?ticker={ticker}&limit={limit}&apiKey={api_key}"
    else:
        # Use the general news URL if no ticker is provided
        url = f"https://api.polygon.io/v2/reference/news?limit={limit}&apiKey={api_key}"
    
    response = requests.get(url)
    if response.status_code == 200:
        news_data = response.json().get('results', [])
        return news_data
    else:
        logger.error(f"Failed to retrieve news: {response.status_code}")
        return []


# Plot a Candlestick Chart
def plot_candlestick_chart(df):
    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'])])

    fig.update_layout(title='Candlestick Chart', xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)




# Sidebar
app_mode = st.sidebar.selectbox(
    'Choose the data type',
    ['Select', 'Company Detail', 'Historical Stock Data', 'Financials Data', 'Stock Splits Data', 'Dividends Data']
)

# Top-level header
if app_mode == 'Select':
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
elif app_mode == 'Historical Stock Data':
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
elif app_mode == 'Financials Data':
    st.header("Financials Data")
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
elif app_mode == 'Company Detail':
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
elif app_mode == 'Stock Splits Data':
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
elif app_mode == 'Dividends Data':
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


