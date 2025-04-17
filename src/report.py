import requests
import json
import pandas as pd
import yfinance as yf
from datetime import datetime

class ReportAnalyser:
    def __init__(self):
        self.base_url = "https://virtserver.swaggerhub.com/Z5488280/BRAVO/1.0.0"
    
    def get_company_data(self, company_name, time_range='last_30_days', limit=100):
        """Get company data from the Bravo API"""
        api_url = f"{self.base_url}/v1/retreive/{company_name}?time_range={time_range}&limit={limit}"
        
        response = requests.get(api_url, headers={"accept": "application/json"})
        response.raise_for_status()
        return response.json()
    
    def get_stock_data(self, ticker_symbol, period="1mo"):
        """Get stock market data using yfinance"""
        stock_data = yf.download(ticker_symbol, period=period)
        return stock_data
    
    def generate_report(self, company_name, chat_history=None):
        """Generate comprehensive investment report using Bravo API"""
        # Create request body for the report endpoint
        if not chat_history:
            chat_history = [
                {"role": "user", "content": f"Analyse {company_name} as an investment opportunity"},
                {"role": "user", "content": f"What are the key strengths and weaknesses of {company_name}?"},
                {"role": "user", "content": f"Summarise market sentiment for {company_name}"}
            ]
        
        # Convert chat history to JSON string
        chat_history_str = json.dumps(chat_history)
        
        # Call Bravo's report endpoint
        url = f"{self.base_url}/v1/analysis/report"
        
        response = requests.post(
            url,
            params={"chat_history": chat_history_str},
            headers={"accept": "application/json"}
        )
        response.raise_for_status()
        
        # Get the report data
        report_data = response.json()
        
        # Enhance the report with additional financial data if possible
        try:
            # Try to map company name to ticker
            ticker_mappings = {
                "tesla": "TSLA",
                "apple": "AAPL",
                "microsoft": "MSFT",
                "google": "GOOGL",
                "amazon": "AMZN"
            }
            
            ticker = ticker_mappings.get(company_name.lower(), company_name.upper())
            stock_data = self.get_stock_data(ticker)
            
            if not stock_data.empty:
                # Calculate key metrics
                current_price = stock_data['Close'].iloc[-1]
                previous_price = stock_data['Close'].iloc[0]
                percent_change = ((current_price - previous_price) / previous_price) * 100
                
                # Add financial metrics to the report
                financial_data = {
                    "ticker": ticker,
                    "current_price": current_price,
                    "percent_change_1mo": percent_change,
                    "trading_volume": stock_data['Volume'].mean(),
                    "price_high": stock_data['High'].max(),
                    "price_low": stock_data['Low'].min(),
                    "analysis_date": datetime.now().strftime("%Y-%m-%d")
                }
                
                # Add financial data to the report
                if "response" in report_data:
                    report_data["financial_data"] = financial_data
        except Exception as e:
            print(f"Could not enhance report with financial data: {str(e)}")
        
        return report_data