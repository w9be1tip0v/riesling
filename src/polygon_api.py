import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv
import config.log_config

# Read the API_KEY from .env file
load_dotenv()
API_KEY = os.getenv('API_KEY')

# Initialize the logger
logger = config.log_config.setup_logging()

# Apply comma formatting to the entire DataFrame
def format_with_comma(df):
    for col in df.select_dtypes(include=['float', 'int']).columns:
        df[col] = df[col].apply(lambda x: f"{x:,.2f}")
    return df

# Get historical stock data from Polygon API
@st.cache_data(ttl=1800, max_entries=100, show_spinner='Fetching data from API...')
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
@st.cache_data(ttl=1800, max_entries=100, show_spinner='Fetching data from API...')
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
@st.cache_data(ttl=1800, max_entries=100, show_spinner=True)
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
@st.cache_data(ttl=1800, max_entries=100, show_spinner='Fetching data from API...')
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
@st.cache_data(ttl=1800, max_entries=100, show_spinner='Fetching data from API...')
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
@st.cache_data(ttl=1800, max_entries=100, show_spinner='Fetching data from API...')
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
@st.cache_data(ttl=1800, max_entries=100, show_spinner='Fetching data from API...')
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
