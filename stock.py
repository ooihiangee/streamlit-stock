import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
import yfinance as yf
from streamlit_option_menu import option_menu
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import regex as re
import json

def get_dividend():
    """
    Scrapes I3investor's Stock Dividends by Announcement Date table to get stock data.

    Returns:
        A DATAFRAME that contains 'stock_name', 'dividend', 'ex_date' keys, etc.
    """
    url = "https://klse.i3investor.com/web/entitlement/dividend/latest"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    headers = {"User-Agent": user_agent}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      content = response.text
      pattern = r'var dtdata = (\[.*?\])\];'
      match = re.search(pattern, content, re.DOTALL)
      if match:
        extracted_text = match.group(1) + ']'
        data = json.loads(extracted_text)
        df = pd.DataFrame(data, columns = ['Announcement Date', 'Stock Name', 'Opening Price', 'Current Price', 'Dividend', 'Ex Date', 'Stock Code', 'Blank', 'URL'])
        df = df.drop(columns=['Blank'])
        df['Stock Code'] = df['Stock Code'].str.replace('/web/stock/entitlement/', '')
        df['URL'] = 'https://klse.i3investor.com/' + df['URL']
        df.index = range(1, len(df) + 1)
        df['Announcement Date'] = pd.to_datetime(df['Announcement Date'], format='%d-%b-%Y').dt.date
        df['Ex Date'] = pd.to_datetime(df['Ex Date'], format='%d-%b-%Y').dt.date
        return df
      else:
        print("No match found.")
    else:
      print("Failed to access the website. Status code:", response.status_code)

def get_ipo():
    """
    Scrapes Bursa Malaysia's IPOs Listing by Announcement Date table to get IPO data.

    Returns:
        A DATAFRAME that contains 'company name', 'offer period', 'date of listing', etc.
    """
    url = "https://www.bursamalaysia.com/listing/listing_resources/ipo/ipo_summary"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    headers = {"User-Agent": user_agent}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      content = response.text
      soup = BeautifulSoup(content, 'html.parser')
      table = soup.find('table')

      # Get table headers
      headers = []
      for th in table.find_all('th'):
          headers.append(th.get_text(strip=True).replace('\n', ' '))

      # Get table rows
      rows = []
      for tr in table.find('tbody').find_all('tr'):
          cells = tr.find_all('td')
          row = [cell.get_text(strip=True).replace('\n', ' ') for cell in cells]
          rows.append(row)

      ipo_df = pd.DataFrame(rows, 
                            columns=['Name of Company', 'Application Opened', 'Application Closed', 'Issue Price', 'Public Issue', 'Offer for Sale', 'Private Placement', 'Issue House', 'List Sought', 'Date of Listing'])
      ipo_df.index = range(1, len(ipo_df) + 1)
      ipo_df['Application Opened'] = pd.to_datetime(ipo_df['Application Opened'], format='%d %b %Y').dt.date
      ipo_df['Application Closed'] = ipo_df['Application Closed'].replace('-', np.nan)
      ipo_df['Application Closed'] = pd.to_datetime(ipo_df['Application Closed'], errors='coerce').dt.date
      ipo_df['Date of Listing'] = pd.to_datetime(ipo_df['Date of Listing'], format='%d %b %Y').dt.date
      return ipo_df
    else:
      print("Failed to access the website. Status code:", response.status_code)

# https://icons.getbootstrap.com/ for icons

def streamlit_menu(example=1, options=["Home", "Contact"], icons=["coin", "bar-chart"]):
    if example == 1:
        # 1. as sidebar menu
        with st.sidebar:
            selected = option_menu(
                menu_title="Main Menu",  # required
                options=options,  # required
                icons=icons,  # optional
                menu_icon="cast",  # optional
                default_index=0,  # optional
            )
        return selected

    if example == 2:
        # 2. horizontal menu w/o custom style
        selected = option_menu(
            menu_title=None,  # required
            options=options,  # required
            icons=icons,  # optional
            menu_icon="cast",  # optional
            default_index=0,  # optional
            orientation="horizontal",
        )
        return selected

    if example == 3:
        # 3. horizontal menu with custom style
        selected = option_menu(
            menu_title=None,  # required
            options=options,  # required
            icons=icons,  # optional
            menu_icon="cast",  # optional
            default_index=0,  # optional
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {
                    "font-size": "25px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "green"},
            },
        )
        return selected

# Streamlit application
def main():
    
    # Set page configuration to wide mode
    st.set_page_config(layout="wide")

    # 1 = sidebar menu, 2 = horizontal menu, 3 = horizontal menu w/ custom menu
    selected = streamlit_menu(example = 2, 
                            options=["Homepage", "Dashboard", "Analysis", "Resources"],
                            icons=["house", "bar-chart-fill", "bar-chart-steps", "file-earmark-medical-fill"])

    if selected == "Homepage":
        st.title("Malaysian Stock Market Data")

        # User inputs for stock ticker and date range
        stock_ticker = st.text_input("Enter stock ticker (e.g., 5158.KL for Tenaga Nasional Berhad):", "5158.KL")
        start_date = st.date_input("Start date", datetime(2020, 1, 1))
        end_date = st.date_input("End date", datetime(2023, 12, 31))

        if st.button("Get Stock Data"):
            # Download historical data
            try:
                stock_data = yf.download(stock_ticker, start=start_date, end=end_date)
                if stock_data.empty:
                    st.error("No data found for the given stock ticker and date range.")
                else:
                    st.success(f"Data retrieved successfully for {stock_ticker}.")
                    st.dataframe(stock_data)

                    # CSV download button
                    csv = stock_data.to_csv().encode('utf-8')
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f'{stock_ticker}_historical_data.csv',
                        mime='text/csv',
                    )
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if selected == "Dashboard":
        st.title("To be constructed")
        stock = yf.Ticker('AAPL')
        stock.recommendations
        stock.calendar
        stock.info
        ticker_df = stock.history(period='1d',start='2020-01-01',end='2024-06-10')
        st.line_chart(ticker_df.Close)

    if selected == "Analysis":
        st.title("To be constructed")

    if selected == "Resources":

        st.title("IPO")
        st.write('https://www.bursamalaysia.com/listing/listing_resources/ipo/ipo_summary')
        ipo_df = get_ipo()
        st.dataframe(ipo_df)

        # CSV download button
        csv = ipo_df.to_csv().encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f'ipo.csv',
            mime='text/csv',
        )

        st.title("Dividend")
        st.write('https://klse.i3investor.com/web/entitlement/dividend/latest')
        dividend_df = get_dividend()
        st.dataframe(dividend_df)

        # CSV download button
        csv = dividend_df.to_csv().encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f'dividend.csv',
            mime='text/csv',
        )

if __name__ == "__main__":
    main()