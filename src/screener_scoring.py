import logging
import numpy as np

# Score mapping: High=5, Med=3, Low=1

def score_metric(value, ranges, lower_is_better=False):
    """Scores a metric 1-5 based on simple ranges."""
    if value is None or np.isnan(value): return 2.5 # Neutral for missing data
    try:
        value = float(value)
        low_threshold, high_threshold = ranges
        score = 2.5 # Default neutral

        if lower_is_better:
            if value <= low_threshold: score = 5.0
            elif value < high_threshold: score = 3.0
            else: score = 1.0
        else: # Higher is better
            if value >= high_threshold: score = 5.0
            elif value > low_threshold: score = 3.0
            else: score = 1.0
        return score
    except (ValueError, TypeError):
        return 2.5 # Neutral if cannot convert

def calculate_scores(metrics: dict) -> dict:
    """Calculates component and overall scores (1-5 scale) from raw metrics."""
    scores = {}
    comp_scores = {'Valuation': [], 'Health': [], 'Growth': []}

    # Define scoring ranges
    # Format: [Lower Threshold, Upper Threshold] for Score 3 (Medium)
    # Values below Lower get 1 (if higher_better) or 5 (if lower_better)
    # Values above Upper get 5 (if higher_better) or 1 (if lower_better)
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

    # --- Component/Column Scores these will be displayed in fe ---
    comp_scores['Valuation'] = [scores['pe_score'], scores['ev_ebitda_score']]
    comp_scores['Health'] = [scores['div_yield_score'], scores['payout_score'], scores['debt_equity_score'], scores['current_ratio_score']]
    comp_scores['Growth'] = [scores['rev_growth_score'], scores['earn_growth_score'], scores['ocf_growth_score']]

    # Average component scores (handle empty lists if a metric was missing)
    final_scores = {}
    for comp, comp_list in comp_scores.items():
        valid_scores = [s for s in comp_list if s is not None]
        final_scores[f"{comp.lower()}_score"] = round(np.mean(valid_scores), 2) if valid_scores else 2.5

    # --- Calculate Overall Score ---
    component_values = [s for s in final_scores.values() if s is not None]
    final_scores['overall_score'] = round(np.mean(component_values), 2) if component_values else 2.5

    logging.debug(f"Calculated scores for {metrics.get('ticker')}: {final_scores}")
    return final_scores
