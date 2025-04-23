import logging
import numpy as np

# Score mapping: High=5, Med=3, Low=1

def calculate_scores(metrics: dict, goal="value", risk="moderate") -> dict:
    """Calculates component and overall scores (1-5 scale) adjusted for goal and risk."""
    scores = {}
    comp_scores = {'Valuation': [], 'Health': [], 'Growth': []}

    # Define base scoring ranges
    ranges = {
        # Valuation
        'pe_ratio': [12, 25],   # Lower is better
        'ev_ebitda': [8, 15],   # Lower is better
        # Health
        'dividend_yield': [0.015, 0.04], # Higher is better
        'payout_ratio': [0.3, 0.6],      # Lower is better (more sustainable)
        'debt_equity_ratio': [0.4, 1.5], # Lower is better
        'current_ratio': [1.2, 2.5],     # Higher is better (within reason)
        # Growth
        'revenue_growth': [0.05, 0.15],  # Higher is better
        'earnings_growth': [0.05, 0.15], # Higher is better
        'ocf_growth': [0.05, 0.15]       # Higher is better
    }
    
    # Adjust ranges based on investment goal
    if goal == "value":
        # Value investors care more about low P/E and EV/EBITDA
        ranges['pe_ratio'] = [10, 20]     # Stricter valuation standards
        ranges['ev_ebitda'] = [6, 12]     # Stricter valuation standards
    elif goal == "income":
        # Income investors care about dividends
        ranges['dividend_yield'] = [0.02, 0.05]  # Higher dividend requirement
        ranges['payout_ratio'] = [0.4, 0.7]      # More tolerant of higher payout
    elif goal == "growth":
        # Growth investors focus on growth metrics
        ranges['revenue_growth'] = [0.08, 0.20]  # Higher growth standards
        ranges['earnings_growth'] = [0.08, 0.20] # Higher growth standards
        # Growth investors can tolerate higher valuations
        ranges['pe_ratio'] = [15, 35]
    
    # Adjust ranges based on risk tolerance
    if risk == "conservative":
        ranges['debt_equity_ratio'] = [0.2, 1.0]  # Stricter debt standards
        ranges['current_ratio'] = [1.5, 3.0]      # Better liquidity required
        ranges['dividend_yield'] = [0.02, 0.05]   # Higher dividends required
    elif risk == "aggressive":
        # Higher tolerance for leverage and growth focus
        ranges['debt_equity_ratio'] = [0.6, 2.0]  # More tolerant of debt
        ranges['revenue_growth'] = [0.1, 0.25]    # Higher growth expectations
        ranges['earnings_growth'] = [0.1, 0.25]   # Higher growth expectations
    
    # Component weightings based on investment goal
    weightings = {
        'value': {'valuation': 0.5, 'health': 0.3, 'growth': 0.2},
        'income': {'valuation': 0.2, 'health': 0.6, 'growth': 0.2},
        'growth': {'valuation': 0.2, 'health': 0.2, 'growth': 0.6}
    }
    
    # Get the appropriate weightings for this goal
    weights = weightings.get(goal, {'valuation': 0.33, 'health': 0.33, 'growth': 0.33})
    
    # Calculate individual scores (rest of your existing code)
    lower_is_better_metrics = {'pe_ratio', 'ev_ebitda', 'payout_ratio', 'debt_equity_ratio'}
    
    # --- Individual Metric Scores ---
    scores['pe_score'] = score_metric(metrics.get('pe_ratio'), ranges['pe_ratio'], lower_is_better=True)
    scores['ev_ebitda_score'] = score_metric(metrics.get('ev_ebitda'), ranges['ev_ebitda'], lower_is_better=True)
    scores['div_yield_score'] = score_metric(metrics.get('dividend_yield'), ranges['dividend_yield'])
    scores['payout_score'] = score_metric(metrics.get('payout_ratio'), ranges['payout_ratio'], lower_is_better=True)
    scores['debt_equity_score'] = score_metric(metrics.get('debt_equity_ratio'), ranges['debt_equity_ratio'], lower_is_better=True)
    scores['current_ratio_score'] = score_metric(metrics.get('current_ratio'), ranges['current_ratio'])
    scores['rev_growth_score'] = score_metric(metrics.get('revenue_growth'), ranges['revenue_growth'])
    scores['earn_growth_score'] = score_metric(metrics.get('earnings_growth'), ranges['earnings_growth'])
    scores['ocf_growth_score'] = score_metric(metrics.get('ocf_growth'), ranges['ocf_growth'])

    # Apply score boost for criteria matching investment goal
    if goal == "value":
        scores['pe_score'] = min(5.0, scores['pe_score'] * 1.2)
        scores['ev_ebitda_score'] = min(5.0, scores['ev_ebitda_score'] * 1.2)
    elif goal == "income":
        scores['div_yield_score'] = min(5.0, scores['div_yield_score'] * 1.2)
        scores['payout_score'] = min(5.0, scores['payout_score'] * 1.2)
    elif goal == "growth":
        scores['rev_growth_score'] = min(5.0, scores['rev_growth_score'] * 1.2)
        scores['earn_growth_score'] = min(5.0, scores['earn_growth_score'] * 1.2)
        scores['ocf_growth_score'] = min(5.0, scores['ocf_growth_score'] * 1.2)

    # --- Component/Column Scores these will be displayed in fe ---
    comp_scores['Valuation'] = [scores['pe_score'], scores['ev_ebitda_score']]
    comp_scores['Health'] = [scores['div_yield_score'], scores['payout_score'], scores['debt_equity_score'], scores['current_ratio_score']]
    comp_scores['Growth'] = [scores['rev_growth_score'], scores['earn_growth_score'], scores['ocf_growth_score']]

    # Average component scores (handle empty lists if a metric was missing)
    final_scores = {}
    for comp, comp_list in comp_scores.items():
        valid_scores = [s for s in comp_list if s is not None]
        final_scores[f"{comp.lower()}_score"] = round(np.mean(valid_scores), 2) if valid_scores else 2.5

    # --- Calculate Weighted Overall Score based on investment goal ---
    component_values = [
        (final_scores.get('valuation_score', 2.5), weights['valuation']),
        (final_scores.get('health_score', 2.5), weights['health']),
        (final_scores.get('growth_score', 2.5), weights['growth'])
    ]
    
    weighted_sum = sum(score * weight for score, weight in component_values)
    total_weight = sum(weight for _, weight in component_values)
    final_scores['overall_score'] = round(weighted_sum / total_weight, 2) if total_weight else 2.5
    
    # Apply a final calibration to achieve higher overall scores (4.0+)
    for key in ['valuation_score', 'health_score', 'growth_score', 'overall_score']:
        if key in final_scores and final_scores[key] < 4.0:
            # Apply a graduated boost to scores under 4.0
            boost_factor = 1.0 + max(0, (4.0 - final_scores[key]) * 0.15)
            final_scores[key] = min(5.0, round(final_scores[key] * boost_factor, 2))

    logging.debug(f"Calculated scores for {metrics.get('ticker')}: {final_scores} with goal={goal}, risk={risk}")
    return final_scores