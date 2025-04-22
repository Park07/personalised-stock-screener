import logging
import pandas as pd
# Assumes profiles.py is in the same core/ directory
from .profiles import get_profile_metrics, InvestmentGoal, RiskTolerance

def normalise_metric(value, all_values, higher_better=True):
    """Normalises a metric value between 0 and 1 based on its peers."""
    if value is None or pd.isna(value): return 0.5
    valid_values = [v for v in all_values if v is not None and pd.notna(v)]
    if not valid_values: return 0.5
    min_val, max_val = min(valid_values), max(valid_values)
    if min_val == max_val: return 0.5
    try:
        normalised = (value - min_val) / (max_val - min_val)
    except ZeroDivisionError: return 0.5
    if not higher_better: normalised = 1.0 - normalised
    return max(0.0, min(1.0, normalised))

def generate_recommendation_summary(metrics: dict, profile_config: dict) -> str:
    """Generates a 1-2 sentence summary based on key profile metrics."""
    sorted_metrics = sorted(
        [item for item in profile_config.items() if item[0] in metrics],
        key=lambda item: item[1]['weight'], reverse=True
    )
    top_metrics = sorted_metrics[:3]
    strengths = []
    cautions = []

    for key, config in top_metrics:
        value = metrics.get(key)
        if value is None: continue
        label = key.replace('_',' ').title()
        norm_score_guess = 0.5
        # Basic thresholds - refine these!
        if key == 'pe_ratio' and not config['higher_better']:
            if value < 15: norm_score_guess = 0.8
            elif value > 35: norm_score_guess = 0.2
        elif key == 'roe' and config['higher_better']:
            if value > 0.20: norm_score_guess = 0.8
            elif value < 0.08: norm_score_guess = 0.2
        elif key == 'revenue_growth' and config['higher_better']:
             if value > 0.15: norm_score_guess = 0.8
             elif value < 0.03: norm_score_guess = 0.2
        # Add others like dividend_yield, debt_equity_ratio

        if norm_score_guess >= 0.7:
            fmt_val = f"{value*100:.0f}%" if ('growth' in key or 'yield' in key or 'roe' in key) else f"{value:.1f}"
            strengths.append(f"{label.lower()} ({fmt_val})")
        elif norm_score_guess <= 0.3:
            fmt_val = f"{value*100:.0f}%" if ('growth' in key or 'yield' in key or 'roe' in key) else f"{value:.1f}"
            cautions.append(f"{label.lower()} ({fmt_val})")

    summary = ""
    if strengths: summary += f"Strengths: {', '.join(strengths[:2])}. "
    if cautions: summary += f"Cautions: {', '.join(cautions[:1])}. " # Maybe only 1 caution
    if not summary: summary = "Overall profile appears neutral based on key metrics."
    return summary.strip()

def rank_companies(goal: InvestmentGoal, risk: RiskTolerance, company_data_list: list, sector: str = None):
    """Calculates dynamic scores, adds summary, and ranks companies."""
    if not company_data_list: return []
    logging.info(f"Ranking {len(company_data_list)} companies: Goal={goal.value}, Risk={risk.value}, Sector={sector or 'All'}")
    try:
        profile_metrics_config = get_profile_metrics(goal, risk)
        if not profile_metrics_config: return []

        df = pd.DataFrame(company_data_list)
        if df.empty: return []

        if sector and sector.lower() != 'all' and 'sector' in df.columns:
            df = df[df['sector'].str.lower() == sector.lower()].copy()
            if df.empty: return []

        # Ensure metrics used for scoring are numeric
        metrics_to_score = list(profile_metrics_config.keys())
        for metric in metrics_to_score:
            if metric in df.columns:
                df[metric] = pd.to_numeric(df[metric], errors='coerce')
            else:
                logging.warning(f"Metric '{metric}' needed for scoring not in data, ignoring.")
                profile_metrics_config.pop(metric, None) # Remove from config if not available

        if not profile_metrics_config: # Check if any metrics are left after filtering
             logging.error("No valid metrics found in data for selected profile.")
             return []

        # Recalculate value ranges based on filtered data
        metric_value_ranges = {metric: df[metric].dropna().tolist() for metric in profile_metrics_config if metric in df.columns}

        df['profile_score'] = 0.0
        total_weight_applied = 0.0
        for metric, config in profile_metrics_config.items():
            if metric in df.columns:
                weight = config['weight']
                higher_better = config['higher_better']
                all_vals = metric_value_ranges.get(metric, [])
                norm_scores = df[metric].apply(lambda x: normalise_metric(x, all_vals, higher_better))
                df['profile_score'] += norm_scores.fillna(0.5) * weight
                total_weight_applied += weight

        if total_weight_applied > 0:
            df['profile_score'] = (df['profile_score'] / total_weight_applied) * 100.0
        else: df['profile_score'] = 50.0

        df['recommendation_summary'] = df.apply(
            lambda row: generate_recommendation_summary(row.to_dict(), profile_metrics_config), axis=1
        )

        ranked_df = df.sort_values(by='profile_score', ascending=False, na_position='last')
        return ranked_df.to_dict('records')

    except Exception as e:
        logging.exception(f"Ranking calculation failed")
        return []
