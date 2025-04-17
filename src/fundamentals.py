import json
import requests
import logging
from tabulate import tabulate
from colorama import Fore, Style, init
from config import FMP_API_KEY

init()

BASE_URL = "https://financialmodelingprep.com/api/v3/"
BASE_URL_V4 = "https://financialmodelingprep.com/api/v4/"

def fetch_first_item(url, error_message, default=None):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"{response.status_code} {response.reason}")
        data = response.json()
        if not data:
            raise ValueError("Empty response returned")
        return data[0]
    except (requests.exceptions.HTTPError, ValueError) as e:
        print(f"Warning: {error_message}: {e}")
        if default is None:
            raise requests.exceptions.RequestException(f"{error_message}: {e}")
        return default
    except Exception as e:
        print(f"Warning: {error_message}: {e}")
        if default is None:
            raise requests.exceptions.RequestException(f"{error_message}: {e}")
        return default

def get_ratios(ticker):
    url = f"{BASE_URL}ratios/{ticker}?period=annual&apikey={FMP_API_KEY}"
    return fetch_first_item(url, "Error fetching ratios data")

def get_key_metrics(ticker):
    url = f"{BASE_URL}key-metrics/{ticker}?period=annual&apikey={FMP_API_KEY}"
    return fetch_first_item(url, "Error fetching key metrics data", default={})

def get_growth(ticker):
    url = f"{BASE_URL}financial-growth/{ticker}?period=annual&apikey={FMP_API_KEY}"
    return fetch_first_item(url, "Error fetching growth data", default={})

def get_profile(ticker):
    url = f"{BASE_URL}profile/{ticker}?apikey={FMP_API_KEY}"
    data = fetch_first_item(url, "Error fetching profile data")
    if data is None:
        raise ValueError("Error fetching profile data")
    return data

def get_financial_ratios(ticker):
    url = f"{BASE_URL}ratios-ttm/{ticker}?apikey={FMP_API_KEY}"
    return fetch_first_item(url, "Error fetching TTM ratios data", default={})

def get_industry_pe(industry, annual_date, exchange="NYSE"):
    industry_pe_url = (
        f"{BASE_URL_V4}industry_price_earning_ratio?date={annual_date}"
        f"&exchange={exchange}&apikey={FMP_API_KEY}"
    )
    response = requests.get(industry_pe_url)
    response.raise_for_status()
    industry_list = response.json()
    for item in industry_list:
        if item.get("industry") == industry:
            return float(item.get("pe"))
    return None

def get_complete_metrics(ticker):
    # Get ratios data
    ratios_data = get_ratios(ticker)
    reporting_period = ratios_data.get("date")
    
    # Get key metrics and growth data
    metrics_data = get_key_metrics(ticker)
    growth_data = get_growth(ticker)
    
    # Get company profile for industry info
    profile_data = get_profile(ticker)
    industry = profile_data.get("industry")
    industry_pe = None
    if industry:
        try:
            industry_pe = get_industry_pe(industry, reporting_period)
        except Exception as e:
            print(f"Warning: Couldn't fetch industry PE: {e}")
    
    # Get TTM financial ratios for more up-to-date metrics
    ttm_ratios = get_financial_ratios(ticker)
    
    # Create a comprehensive metrics dictionary
    metrics = {
        # Valuation Metrics
        "pe_ratio": ratios_data.get("priceEarningsRatio"),
        "industry_pe": industry_pe,
        "peg_ratio": ratios_data.get("priceEarningsToGrowthRatio"),
        "ps_ratio": ratios_data.get("priceToSalesRatio"),
        "ev_to_ebitda": ratios_data.get("enterpriseValueMultiple"),
        "price_to_fcf": ratios_data.get("priceToFreeCashFlowsRatio"),
        "earnings_yield": ratios_data.get("earningsYield"),
        "fcf_yield": metrics_data.get("freeCashFlowYield"),
        
        # Profitability Metrics
        "roe": ratios_data.get("returnOnEquity"),
        "roa": ratios_data.get("returnOnAssets"),
        "roic": ratios_data.get("returnOnInvestedCapital"),
        # "net_profit_margin": ratios_data.get("netProfitMargin"),
        "gross_profit_margin": ratios_data.get("grossProfitMargin"),
        "operating_profit_margin": ratios_data.get("operatingProfitMargin"),
        
        # Solvency/Leverage Metrics
        "debt_to_equity": ratios_data.get("debtToEquity"),
        "debt_ratio": ratios_data.get("debtRatio"),
        "current_ratio": ratios_data.get("currentRatio"),
        "interest_coverage": ratios_data.get("interestCoverage"),
        
        # Growth Metrics
        "revenue_growth": growth_data.get("revenueGrowth"),
        "eps_growth": growth_data.get("epsgrowth"),
        "operating_cash_flow_growth": growth_data.get("operatingCashFlowGrowth"),
        "fcf_growth": growth_data.get("freeCashFlowGrowth"),
        "capex_growth": growth_data.get("capitalExpenditureGrowth"),
        
        # Additional Information
        "enterprise_value": metrics_data.get("enterpriseValue"),
        "company_name": profile_data.get("companyName"),
        "industry": industry,
        "sector": profile_data.get("sector"),
        "market_cap": profile_data.get("mktCap"),
        "beta": profile_data.get("beta"),
        "ticker": ticker
    }
    
    return metrics

def define_metrics_importance(risk_tolerance, investment_goal):
    metrics = {
        "primary": [],     # Most important metrics (🔑)
        "secondary": [],   # Somewhat important metrics (🔹)
        "additional": []   # Less important but still relevant metrics (ℹ️)
    }
    
    # Conservative + Income
    if risk_tolerance == "Conservative" and investment_goal == "Income":
        metrics["primary"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Lower P/E suggests better value"},
            {"key": "debt_ratio", "label": "Debt Ratio", "description": "Lower debt reduces risk"},
            {"key": "current_ratio", "label": "Current Ratio", "description": "Higher liquidity is safer"}
        ]
        metrics["secondary"] = [
            {"key": "fcf_yield", "label": "Free Cash Flow Yield", "description": "Higher FCF yield is preferred"},
        ]
    
    # Conservative + Balanced
    elif risk_tolerance == "Conservative" and investment_goal == "Balanced":
        metrics["primary"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Lower P/E suggests better value"},
            {"key": "debt_ratio", "label": "Debt Ratio", "description": "Lower debt reduces risk"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Steady growth is preferred"}
        ]
        metrics["secondary"] = [
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "Lower PEG indicates better value for growth"},
            {"key": "current_ratio", "label": "Current Ratio", "description": "Higher indicates financial stability"},
            {"key": "roe", "label": "Return on Equity", "description": "Shows management effectiveness"}
        ]
        metrics["additional"] = [
            {"key": "gross_profit_margin", "label": "Gross Profit Margin", "description": "Higher margins indicate pricing power"},
        ]
    
    # Conservative + Growth
    elif risk_tolerance == "Conservative" and investment_goal == "Growth":
        metrics["primary"] = [
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "Lower PEG indicates better value for growth"},
            {"key": "debt_ratio", "label": "Debt Ratio", "description": "Lower debt reduces risk while pursuing growth"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Consistent growth without excessive volatility"}
        ]
        metrics["secondary"] = [
            {"key": "eps_growth", "label": "EPS Growth", "description": "Steady earnings growth with less volatility"},
            {"key": "roe", "label": "Return on Equity", "description": "Higher ROE suggests efficient growth"},
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Reasonable valuation for growth stocks"}
        ]
        metrics["additional"] = [
            {"key": "gross_profit_margin", "label": "Gross Profit Margin", "description": "Margin stability indicates sustainable growth"},
            {"key": "operating_cash_flow_growth", "label": "Operating Cash Flow Growth", "description": "Cash-backed growth is more reliable"}
        ]
    
    # Moderate + Income
    elif risk_tolerance == "Moderate" and investment_goal == "Income":
        metrics["primary"] = [
            {"key": "payout_ratio", "label": "Payout Ratio", "description": "Sustainable payout ratio ensures dividend longevity"},
            {"key": "fcf_yield", "label": "Free Cash Flow Yield", "description": "Higher indicates better dividend coverage"},
        ]
        metrics["secondary"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Value indicator relative to income potential"},
            {"key": "debt_to_equity", "label": "Debt to Equity", "description": "Lower ratios indicate financial stability"},
            {"key": "current_ratio", "label": "Current Ratio", "description": "Higher indicates better short-term liquidity"}
        ]
        metrics["additional"] = [
            {"key": "roe", "label": "Return on Equity", "description": "Efficiency in generating profit from equity"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Moderate growth supports income increases"}
        ]
    
    # Moderate + Balanced
    elif risk_tolerance == "Moderate" and investment_goal == "Balanced":
        metrics["primary"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Reasonable valuation relative to earnings"},
            {"key": "roe", "label": "Return on Equity", "description": "Shows management effectiveness"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Consistent top-line growth"},
            {"key": "debt_to_equity", "label": "Debt to Equity", "description": "Reasonable leverage for growth and stability"}
        ]
        metrics["secondary"] = [
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "Value indicator accounting for growth"},
            {"key": "fcf_yield", "label": "Free Cash Flow Yield", "description": "Higher indicates value creation"}
        ]
        metrics["additional"] = [
            {"key": "operating_profit_margin", "label": "Operating Profit Margin", "description": "Operational efficiency"},
            {"key": "eps_growth", "label": "EPS Growth", "description": "Growth in shareholder earnings"}
        ]
    
    # Moderate + Growth
    elif risk_tolerance == "Moderate" and investment_goal == "Growth":
        metrics["primary"] = [
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Strong top-line growth potential"},
            {"key": "eps_growth", "label": "EPS Growth", "description": "Earnings growth translates to shareholder returns"},
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "Lower indicates better value relative to growth"},
            {"key": "roic", "label": "Return on Invested Capital", "description": "Higher ROIC suggests effective growth investments"}
        ]
        metrics["secondary"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Current valuation perspective"},
            {"key": "gross_profit_margin", "label": "Gross Profit Margin", "description": "Margin for reinvestment in growth"},
            {"key": "debt_to_equity", "label": "Debt to Equity", "description": "Reasonable leverage for growth opportunities"}
        ]
        metrics["additional"] = [
            {"key": "operating_cash_flow_growth", "label": "Operating Cash Flow Growth", "description": "Cash generation supports sustainable growth"},
            {"key": "fcf_growth", "label": "Free Cash Flow Growth", "description": "Growing ability to fund future expansion"}
        ]
    
    # Aggressive + Income
    elif risk_tolerance == "Aggressive" and investment_goal == "Income":
        metrics["primary"] = [
            {"key": "fcf_yield", "label": "Free Cash Flow Yield", "description": "Strong cash generation for dividends"},
            {"key": "earnings_yield", "label": "Earnings Yield", "description": "Higher indicates better income potential"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Growth supports dividend increases"},
            {"key": "roe", "label": "Return on Equity", "description": "Higher returns support income growth"}
        ]
        metrics["secondary"] = [
            {"key": "payout_ratio", "label": "Payout Ratio", "description": "Higher payout may provide more immediate income"},
            {"key": "net_profit_margin", "label": "Net Profit Margin", "description": "Higher margins support sustainable income"},
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Lower values indicate better income value"}
        ]
        metrics["additional"] = [
            {"key": "debt_to_equity", "label": "Debt to Equity", "description": "Leverage can amplify returns if managed well"},
            {"key": "eps_growth", "label": "EPS Growth", "description": "Growth in earnings supports dividend growth"}
        ]
    
    # Aggressive + Balanced
    elif risk_tolerance == "Aggressive" and investment_goal == "Balanced":
        metrics["primary"] = [
            {"key": "roe", "label": "Return on Equity", "description": "Strong returns on shareholder capital"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Significant growth for appreciation potential"},
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Valuation context for potential returns"},
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "Growth-adjusted valuation"}
        ]
        metrics["secondary"] = [
            {"key": "roic", "label": "Return on Invested Capital", "description": "Effectiveness of capital allocation"},
            {"key": "eps_growth", "label": "EPS Growth", "description": "Bottom-line growth potential"},
            {"key": "fcf_yield", "label": "Free Cash Flow Yield", "description": "Higher FCF yield typically indicates value"}
        ]
        metrics["additional"] = [
            {"key": "operating_profit_margin", "label": "Operating Profit Margin", "description": "Efficiency in operations"},
            {"key": "debt_to_equity", "label": "Debt to Equity", "description": "Leverage amplifies returns in good times"}
        ]
    
    # Aggressive + Growth
    elif risk_tolerance == "Aggressive" and investment_goal == "Growth":
        metrics["primary"] = [
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "High growth potential is key"},
            {"key": "eps_growth", "label": "EPS Growth", "description": "Earnings growth driving shareholder returns"},
            {"key": "roic", "label": "Return on Invested Capital", "description": "Efficiency in generating growth from investments"},
            {"key": "gross_profit_margin", "label": "Gross Profit Margin", "description": "Margin for reinvestment in growth"}
        ]
        metrics["secondary"] = [
            {"key": "operating_cash_flow_growth", "label": "Operating Cash Flow Growth", "description": "Cash generation supports growth initiatives"},
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "Growth-adjusted valuation metric"},
            {"key": "roe", "label": "Return on Equity", "description": "Efficiency in using shareholder capital"}
        ]
        metrics["additional"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Context for current valuation"},
            {"key": "fcf_growth", "label": "Free Cash Flow Growth", "description": "Ability to self-fund future growth"}
        ]
    
    # Default case
    else:
        metrics["primary"] = [
            {"key": "pe_ratio", "label": "P/E Ratio", "description": "Price to Earnings ratio"},
            {"key": "roe", "label": "Return on Equity", "description": "Profitability relative to equity"},
            {"key": "revenue_growth", "label": "Revenue Growth", "description": "Top-line growth rate"},
            {"key": "debt_ratio", "label": "Debt Ratio", "description": "Lower values indicate less financial risk"}
        ]
        metrics["secondary"] = [
            {"key": "peg_ratio", "label": "PEG Ratio", "description": "P/E ratio adjusted for growth"},
            {"key": "debt_to_equity", "label": "Debt to Equity", "description": "Leverage ratio"},
            {"key": "fcf_yield", "label": "Free Cash Flow Yield", "description": "Indicates value and sustainability"}
        ]
        metrics["additional"] = [
            {"key": "operating_profit_margin", "label": "Operating Profit Margin", "description": "Operational efficiency"},
            {"key": "current_ratio", "label": "Current Ratio", "description": "Short-term liquidity"},
        ]
    
    return metrics

def format_metric_value(key, value):
    if value is None:
        return "N/A"
    
    # Format percentages
    if key in ["roe", "roa", "roic", "net_profit_margin", "gross_profit_margin", 
               "operating_profit_margin", "revenue_growth", "eps_growth", 
               "operating_cash_flow_growth", "fcf_growth", "capex_growth"]:
        return f"{value * 100:.2f}%" if isinstance(value, (int, float)) else "N/A"
    
    # Format ratios
    elif key in ["pe_ratio", "peg_ratio", "ps_ratio", "ev_to_ebitda", "price_to_fcf", 
                "debt_to_equity", "debt_ratio", "current_ratio", "interest_coverage"]:
        return f"{value:.2f}x" if isinstance(value, (int, float)) else "N/A"
    
    # Format monetary values
    elif key in ["enterprise_value", "market_cap"]:
        if isinstance(value, (int, float)):
            if value >= 1e9:
                return f"${value / 1e9:.2f}B"
            elif value >= 1e6:
                return f"${value / 1e6:.2f}M"
            else:
                return f"${value:.2f}"
        else:
            return "N/A"
    
    
    # Format beta
    elif key == "beta" and isinstance(value, (int, float)):
        if value < 0.8:
            return f"{value:.2f} (Low)"
        elif value < 1.2:
            return f"{value:.2f} (Average)"
        else:
            return f"{value:.2f} (High)"
    
    # Default formatting
    else:
        return f"{value:.2f}" if isinstance(value, (int, float)) else "N/A"

def generate_terminal_table(metrics, metrics_importance, ticker):
    # Setup importance indicators with colors
    indicators = {
        "primary": f"{Fore.GREEN}🔑 MOST IMPORTANT{Style.RESET_ALL}",
        "secondary": f"{Fore.BLUE}🔹 IMPORTANT{Style.RESET_ALL}",
        "additional": f"{Fore.YELLOW}ℹ️  SUPPLEMENTARY{Style.RESET_ALL}"
    }
    
    # Company header
    output = f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n"
    output += f"{Fore.CYAN}FUNDAMENTAL ANALYSIS FOR: {metrics.get('company_name', 'Unknown')} ({ticker}){Style.RESET_ALL}\n"
    output += f"{Fore.CYAN}Industry: {metrics.get('industry', 'N/A')} | Sector: {metrics.get('sector', 'N/A')}{Style.RESET_ALL}\n"
    output += f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n\n"
    
    # Create tables for each importance category
    for category in ["primary", "secondary", "additional"]:
        if not metrics_importance[category]:
            continue
            
        output += f"{indicators[category]}\n\n"
        
        table_data = []
        headers = ["Metric", "Value", "Description"]
        
        for metric_def in metrics_importance[category]:
            key = metric_def["key"]
            value = metrics.get(key)
            formatted_value = format_metric_value(key, value)
            
            # Add benchmark comparison for PE ratio
            if key == "pe_ratio" and metrics.get("industry_pe"):
                industry_pe = metrics.get("industry_pe")
                industry_pe_formatted = format_metric_value("pe_ratio", industry_pe)
                formatted_value = f"{formatted_value} (Industry: {industry_pe_formatted})"
            
            # Add row to table
            table_data.append([
                metric_def["label"],
                formatted_value,
                metric_def["description"]
            ])
        
        # Generate and add table to output
        table = tabulate(table_data, headers=headers, tablefmt="grid")
        output += f"{table}\n\n"
    
    return output

def generate_preference_analysis_report(ticker, risk_tolerance, investment_goal):
    try:
        # Get all metrics
        all_metrics = get_complete_metrics(ticker)
        
        # Determine which metrics to emphasize
        metrics_importance = define_metrics_importance(risk_tolerance, investment_goal)
        
        # Generate the terminal table
        report = generate_terminal_table(all_metrics, metrics_importance, ticker)
        
        # Add summary
        report += f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n"
        report += f"{Fore.CYAN}PREFERENCE SUMMARY{Style.RESET_ALL}\n"
        report += f"{Fore.CYAN}Risk Tolerance: {risk_tolerance} | Investment Goal: {investment_goal}{Style.RESET_ALL}\n"
        report += f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n\n"
        
        # Create a custom summary based on user preferences
        summary = generate_custom_summary(all_metrics, risk_tolerance, investment_goal)
        report += summary
        
        return report
        
    except Exception as e:
        return f"Error generating report: {str(e)}"

def generate_custom_summary(metrics, risk_tolerance, investment_goal):
    company_name = metrics.get("company_name", "This company")
    summary = ""
    
    # Add risk profile assessment
    if risk_tolerance == "Conservative":
        if metrics.get("debt_ratio", 0) and metrics.get("debt_ratio", 0) > 0.5 and metrics.get("debt_ratio", 0) is not None:
            summary += f"{Fore.RED}⚠️ WARNING: {company_name} has a high debt ratio ({format_metric_value('debt_ratio', metrics.get('debt_ratio'))}) which may not align with your conservative risk profile.{Style.RESET_ALL}\n\n"
        if metrics.get("beta", 0) is not None and metrics.get("beta", 0) > 1.2 and metrics.get("beta", 0) is not None:
            summary += f"{Fore.RED}⚠️ WARNING: {company_name} has high volatility (Beta: {format_metric_value('beta', metrics.get('beta'))}) which may not align with your conservative risk profile.{Style.RESET_ALL}\n\n"
    
    # Add investment goal assessment
    if investment_goal == "Growth":
        if metrics.get("revenue_growth", 0) < 0.05 and metrics.get("revenue_growth", 0) is not None:
            summary += f"{Fore.YELLOW}📊 NOTE: {company_name} shows limited revenue growth ({format_metric_value('revenue_growth', metrics.get('revenue_growth'))}) which may not fully support your growth goal.{Style.RESET_ALL}\n\n"
        elif metrics.get("revenue_growth", 0) > 0.15 and metrics.get("revenue_growth", 0) is not None:
            summary += f"{Fore.GREEN}✅ POSITIVE: {company_name} demonstrates strong revenue growth ({format_metric_value('revenue_growth', metrics.get('revenue_growth'))}) which aligns with your growth goal.{Style.RESET_ALL}\n\n"
    
    # Add valuation assessment
    industry_pe = metrics.get("industry_pe")
    pe_ratio = metrics.get("pe_ratio")
    if pe_ratio and industry_pe:
        if pe_ratio < industry_pe * 0.7:
            summary += f"{Fore.GREEN}✅ VALUATION: {company_name} appears potentially undervalued with a P/E ratio ({format_metric_value('pe_ratio', pe_ratio)}) well below the industry average ({format_metric_value('pe_ratio', industry_pe)}).{Style.RESET_ALL}\n\n"
        elif pe_ratio > industry_pe * 1.3:
            summary += f"{Fore.YELLOW}📊 VALUATION: {company_name} trades at a premium with a P/E ratio ({format_metric_value('pe_ratio', pe_ratio)}) above the industry average ({format_metric_value('pe_ratio', industry_pe)}).{Style.RESET_ALL}\n\n"
    
    # If no specific comments were added, provide a general statement
    if not summary:
        summary = f"Based on your {risk_tolerance.lower()} risk tolerance and {investment_goal.lower()} investment goal, review the metrics above to assess if {company_name} aligns with your investment strategy.\n\n"
    
    # Add final recommendation based on overall alignment
    alignment_score = calculate_alignment_score(metrics, risk_tolerance, investment_goal)
    if alignment_score > 75:
        summary += f"{Fore.GREEN}🌟 OVERALL: {company_name} appears to be well-aligned with your {risk_tolerance.lower()} risk tolerance and {investment_goal.lower()} investment goal.{Style.RESET_ALL}\n"
    elif alignment_score > 50:
        summary += f"{Fore.BLUE}🔹 OVERALL: {company_name} is moderately aligned with your {risk_tolerance.lower()} risk tolerance and {investment_goal.lower()} investment goal.{Style.RESET_ALL}\n"
    else:
        summary += f"{Fore.YELLOW}⚠️ OVERALL: {company_name} may not strongly align with your {risk_tolerance.lower()} risk tolerance and {investment_goal.lower()} investment goal. Consider the highlighted concerns.{Style.RESET_ALL}\n"
    
    return summary

def calculate_alignment_score(metrics, risk_tolerance, investment_goal):
    score = 50  # Start with neutral score
    
    # Adjust score based on risk tolerance
    if risk_tolerance == "Conservative":
        # Lower debt is better for conservative investors
        debt_ratio = metrics.get("debt_ratio")
        if debt_ratio is not None and debt_ratio < 0.3:
            score += 10
        elif debt_ratio is not None and debt_ratio > 0.5:
            score -= 10
            
        # Lower beta is better for conservative investors
        beta = metrics.get("beta")
        if beta is not None and beta < 0.8:
            score += 10
        elif beta is not None and beta > 1.2:
            score -= 10
            
    
    elif risk_tolerance == "Aggressive":
        # More growth-oriented metrics for aggressive investors
        rev_growth = metrics.get("revenue_growth")
        if rev_growth is not None and rev_growth > 0.15:
            score += 10
        elif rev_growth is not None and rev_growth < 0.05:
            score -= 5
            
        # Higher ROE is better for aggressive investors
        roe = metrics.get("roe")
        if roe is not None and roe > 0.20:
            score += 10
        elif roe is not None and roe < 0.1:
            score -= 5
    
    # Adjust score based on investment goal
    if investment_goal == "Income":
        # Higher FCF yield is better for income
        fcf_yield = metrics.get("fcf_yield")
        if fcf_yield is not None and fcf_yield > 0.05:
            score += 10
        elif fcf_yield is not None and fcf_yield < 0.02:
            score -= 10
            
        # Lower payout ratio is more sustainable
        payout_ratio = metrics.get("payoutRatio")
        if payout_ratio is not None and payout_ratio < 0.7 and payout_ratio > 0:
            score += 5
        elif payout_ratio is not None and (payout_ratio > 0.9 or payout_ratio < 0):
            score -= 10
    
    elif investment_goal == "Growth":
        # Higher growth rates are better
        rev_growth = metrics.get("revenue_growth")
        if rev_growth is not None and rev_growth > 0.15:
            score += 15
        elif rev_growth is not None and rev_growth < 0.05:
            score -= 15
            
        # Higher EPS growth is important
        eps_growth = metrics.get("eps_growth")
        if eps_growth is not None and eps_growth > 0.15:
            score += 10
        elif eps_growth is not None and eps_growth < 0.05:
            score -= 10
    
    # Ensure score stays within bounds
    return max(0, min(100, score))
