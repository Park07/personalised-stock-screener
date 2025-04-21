from enum import Enum

class InvestmentGoal(str, Enum):
    GROWTH = "growth"
    VALUE = "value"
    INCOME = "income"

class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

def get_profile_metrics(goal, risk):
    """Get the important metrics for a specific investment profile"""
    metrics = {}
    
    # Base metrics by goal
    if goal == InvestmentGoal.GROWTH:
        metrics = {
            'revenue_growth': {'weight': 0.25, 'higher_better': True},
            'earnings_growth': {'weight': 0.20, 'higher_better': True},
            'return_on_equity': {'weight': 0.15, 'higher_better': True},
            'pe_ratio': {'weight': 0.15, 'higher_better': False},
            'debt_to_equity': {'weight': 0.10, 'higher_better': False},
            'market_cap': {'weight': 0.15, 'higher_better': True}
        }
    elif goal == InvestmentGoal.VALUE:
        metrics = {
            'pe_ratio': {'weight': 0.25, 'higher_better': False},
            'free_cash_flow_yield': {'weight': 0.20, 'higher_better': True},
            'debt_to_equity': {'weight': 0.15, 'higher_better': False},
            'return_on_equity': {'weight': 0.10, 'higher_better': True},
            'dividend_yield': {'weight': 0.10, 'higher_better': True},
            'return_on_assets': {'weight': 0.20, 'higher_better': True}
        }
    elif goal == InvestmentGoal.INCOME:
        metrics = {
            'dividend_yield': {'weight': 0.30, 'higher_better': True},
            'free_cash_flow_yield': {'weight': 0.20, 'higher_better': True},
            'debt_to_equity': {'weight': 0.15, 'higher_better': False},
            'pe_ratio': {'weight': 0.10, 'higher_better': False},
            'earnings_growth': {'weight': 0.15, 'higher_better': True},
            'return_on_equity': {'weight': 0.10, 'higher_better': True}
        }
    
    # Adjust weights based on risk tolerance
    if risk == RiskTolerance.CONSERVATIVE:
        # Increase weight of safety metrics
        for metric in ['debt_to_equity', 'free_cash_flow_yield']:
            if metric in metrics:
                metrics[metric]['weight'] *= 1.3
        # Decrease weight of growth metrics
        for metric in ['revenue_growth', 'earnings_growth']:
            if metric in metrics:
                metrics[metric]['weight'] *= 0.7
    elif risk == RiskTolerance.AGGRESSIVE:
        # Decrease weight of safety metrics
        for metric in ['debt_to_equity', 'free_cash_flow_yield']:
            if metric in metrics:
                metrics[metric]['weight'] *= 0.7
        # Increase weight of growth metrics
        for metric in ['revenue_growth', 'earnings_growth', 'return_on_equity']:
            if metric in metrics:
                metrics[metric]['weight'] *= 1.3
    
    # Normalise weights to sum to 1
    total_weight = sum(m['weight'] for m in metrics.values())
    for metric in metrics:
        metrics[metric]['weight'] /= total_weight
    
    return metrics

def get_profile_description(goal, risk):
    """Get human-readable description of investment profile"""
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