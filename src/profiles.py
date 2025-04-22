from enum import Enum

class InvestmentGoal(str, Enum):
    GROWTH = "growth"
    VALUE = "value"
    INCOME = "income"

class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

def get_profile_metrics(goal:InvestmentGoal, risk:RiskTolerance):
    """Get the important metrics for a specific investment profile"""
    metrics = {}
    
    # Base metrics by goal
    if goal == InvestmentGoal.GROWTH:
        metrics = {
            'revenue_growth': {'weight': 0.3, 'higher_better': True},
            'earnings_growth': {'weight': 0.25, 'higher_better': True},
            'return_on_equity': {'weight': 0.2, 'higher_better': True},
            'pe_ratio': {'weight': 0.15, 'higher_better': False},
            'debt_to_equity': {'weight': 0.10, 'higher_better': False},
        }
    elif goal == InvestmentGoal.VALUE:
        metrics = {
            'pe_ratio': {'weight': 0.4, 'higher_better': False},
            'debt_to_equity': {'weight': 0.20, 'higher_better': False},
            'return_on_equity': {'weight': 0.20, 'higher_better': True},
            'dividend_yield': {'weight': 0.20, 'higher_better': True},
        }
    elif goal == InvestmentGoal.INCOME:
        metrics = {
            'dividend_yield': {'weight': 0.50, 'higher_better': True},
            'debt_to_equity': {'weight': 0.2, 'higher_better': False},
            'pe_ratio': {'weight': 0.15, 'higher_better': False},
            'earnings_growth': {'weight': 0.15, 'higher_better': True},
        }
    else: # Default Balanced
        metrics = {
            'roe': {'weight': 0.25, 'higher_better': True},
            'pe_ratio': {'weight': 0.25, 'higher_better': False},
            'dividend_yield': {'weight': 0.25, 'higher_better': True},
            'revenue_growth': {'weight': 0.15, 'higher_better': True},
            'debt_equity_ratio': {'weight': 0.10, 'higher_better': False},
         }
    
    # Adjust weights based on risk tolerance
    if risk == RiskTolerance.CONSERVATIVE:
        if 'debt_equity_ratio' in metrics: metrics['debt_equity_ratio']['weight'] *= 1.5
        if 'revenue_growth' in metrics: metrics['revenue_growth']['weight'] *= 0.5
        if 'earnings_growth' in metrics: metrics['earnings_growth']['weight'] *= 0.5
    elif risk == RiskTolerance.AGGRESSIVE:
        if 'debt_equity_ratio' in metrics: metrics['debt_equity_ratio']['weight'] *= 0.5
        if 'revenue_growth' in metrics: metrics['revenue_growth']['weight'] *= 1.5
        if 'earnings_growth' in metrics: metrics['earnings_growth']['weight'] *= 1.5
    

    
    # Normalise weights to sum to 1
    total_weight = sum(m['weight'] for m in metrics.values())
    for metric in metrics:
        metrics[metric]['weight'] /= total_weight
    
    return metrics

def get_profile_description(goal, risk):
    """Get description of investment profile"""
    descriptions = {
        'growth': {
            'conservative': "Growth investors seeking steady, reliable expansion with lower volatility",
            'moderate': "Growth investors balancing capital appreciation with reasonable risk",
            'aggressive': "Growth investors pursuing maximum capital appreciation, willing to accept higher volatility"
        },
        'value': {
            'conservative': "Value investors focusing on capital preservation with stable undervalued companies",
            'moderate': "Value investors seeking undervalued opportunities with reasonable margins of safety",
            'aggressive': "Value investors looking for deeply discounted opportunities, including turnaround situations"
        },
        'income': {
            'conservative': "Income investors prioritising dividend stability and preservation of capital",
            'moderate': "Income investors balancing current yield with dividend growth potential",
            'aggressive': "Income investors seeking maximum yield, accepting higher risk to dividend sustainability"
        }
    }
    return descriptions.get(goal, {}).get(risk, "Custom investment profile")