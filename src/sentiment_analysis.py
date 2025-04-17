import numpy as np
import requests
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io

base_url = "https://virtserver.swaggerhub.com/Z5488280/BRAVO/1.0.0"
def get_sentiment_data(company_name, time_range='last_30_days', limit=100):
    api_url = f"{base_url}/v1/retreive/{company_name}?time_range={time_range}&limit={limit}"

    response = requests.get(api_url, headers={"accept": "application/json"})
    response.raise_for_status()

    data = response.json()
    print(f"Received {len(data.get('events', []))} events from API")
    
    return data

    return response.json()

def count_sentiments(data):
    # Have to aggregate positve, negative first
    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}

    for event in data.get('events', []):
        sentiment = event.get('attribute', {}).get('sentiment', 'Neutral')

        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
        else:
            sentiment_counts["Neutral"] += 1
    return sentiment_counts

def create_sentiment_chart(company_name, sentiment_counts, exclude_neutral=False):
    # Havve toggle option for neutral button
    total_count = sum(sentiment_counts.values())

    fig = Figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='polar')

    colour_spectrum = {"Positive": "#4CAF50", "Neutral": "#9E9E9E", "Negative": "#F44336"}

    if exclude_neutral:
        non_neutral_count = sentiment_counts["Positive"] + sentiment_counts["Negative"]

        if non_neutral_count == 0:  # Handle case with no non-neutral data
            positive = 50  # Default to 50-50 split if no data
            negative = 50
        else:
            positive = round((sentiment_counts["Positive"] / non_neutral_count * 100), 1)
            negative = round((sentiment_counts["Negative"] / non_neutral_count * 100), 1)

        # semicircle
        pos_end = np.pi * (positive / 100)

        # filling secitons
        ax.fill_between(np.linspace(0, pos_end, 50), 0.7, 0.9, color=colour_spectrum["Positive"], alpha=0.8)
        ax.fill_between(np.linspace(pos_end, np.pi, 50), 0.7, 0.9, color=colour_spectrum["Negative"], alpha=0.8)

        p_label = f"Positive: {positive}% ({sentiment_counts['Positive']})"
        n_label = f"Negative: {negative}% ({sentiment_counts['Negative']})"

        ax.text(pos_end/2, 1.0, p_label, ha='center', va='center',
                bbox=dict(facecolor='#E8F5E9', alpha=0.8, boxstyle='round'))
        ax.text((pos_end + np.pi)/2, 1.0, n_label, ha='center', va='center',
                bbox=dict(facecolor='#FFEBEE', alpha=0.8, boxstyle='round'))

    else:
        # neutral toggle button
        percentages = {s: round((c / total_count * 100), 1) for s, c in sentiment_counts.items()}
        pos_end = np.pi * (percentages["Positive"] / 100)
        neu_end = pos_end + np.pi * (percentages["Neutral"] / 100)

        # Draw sections
        ax.fill_between(np.linspace(0, pos_end, 50), 0.7, 0.9, color=colour_spectrum["Positive"], alpha=0.8)
        ax.fill_between(np.linspace(pos_end, neu_end, 50), 0.7, 0.9, color=colour_spectrum["Neutral"], alpha=0.8)
        ax.fill_between(np.linspace(neu_end, np.pi, 50), 0.7, 0.9, color=colour_spectrum["Negative"], alpha=0.8)

        positive_label = f"Positive: {percentages['Positive']}% ({sentiment_counts['Positive']})"
        neutral_label = f"Neutral: {percentages['Neutral']}% ({sentiment_counts['Neutral']})"
        negative_label = f"Negative: {percentages['Negative']}% ({sentiment_counts['Negative']})"

        ax.text(pos_end/2, 1.0, positive_label, ha='center', va='center',
                bbox=dict(facecolor='#E8F5E9', alpha=0.8, boxstyle='round'))
        ax.text((pos_end + neu_end)/2, 1.0, neutral_label, ha='center', va='center',
                bbox=dict(facecolor='#F5F5F5', alpha=0.8, boxstyle='round'))
        ax.text((neu_end + np.pi)/2, 1.0, negative_label, ha='center', va='center',
                bbox=dict(facecolor='#FFEBEE', alpha=0.8, boxstyle='round'))


    #
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.grid(False)
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # Set title
    ax.set_title(f'Sentiment breakdown for {company_name}', fontsize=18, pad=20)

    # Add toggle indicator text
    toggle_status = "Exclude neutral: ON" if exclude_neutral else "Include neutral"
    fig.text(0.15, 0.15, toggle_status, fontsize=12)

    # Convert to PNG bytes
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    output.seek(0)

    return output