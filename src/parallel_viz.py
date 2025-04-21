import base64
import io
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

def generate_parallel_chart(ranked_companies, goal, risk, dark_theme=True):
    """Generate a parallel coordinates chart for comparing top companies"""
    try:
        # Take top companies
        top_companies = ranked_companies[:5]
        
        # Define metrics to display based on investment goal
        if goal == 'growth':
            metrics = ['pe_ratio', 'revenue_growth', 'earnings_growth', 'return_on_equity', 'debt_to_equity']
            metric_labels = ['P/E Ratio', 'Revenue Growth', 'Earnings Growth', 'ROE', 'Debt/Equity']
            higher_better = [False, True, True, True, False]
        elif goal == 'value':
            metrics = ['pe_ratio', 'price_to_intrinsic', 'return_on_assets', 'debt_to_equity', 'dividend_yield']
            metric_labels = ['P/E Ratio', 'Price/Value', 'ROA', 'Debt/Equity', 'Dividend Yield']
            higher_better = [False, False, True, False, True]
        elif goal == 'income':
            metrics = ['dividend_yield', 'payout_ratio', 'debt_to_equity', 'pe_ratio', 'free_cash_flow_yield']
            metric_labels = ['Dividend Yield', 'Payout Ratio', 'Debt/Equity', 'P/E Ratio', 'FCF Yield']
            higher_better = [True, False, False, False, True]
        else:
            # Default metrics
            metrics = ['pe_ratio', 'dividend_yield', 'debt_to_equity', 'return_on_equity', 'return_on_assets']
            metric_labels = ['P/E Ratio', 'Dividend Yield', 'Debt/Equity', 'ROE', 'ROA']
            higher_better = [False, True, False, True, True]
        
        # Setup chart theme
        if dark_theme:
            plt.style.use('dark_background')
            colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0']
            text_color = 'white'
            grid_color = '#555555'
        else:
            plt.style.use('default')
            colors = ['#ff6666', '#3399ff', '#66cc66', '#ff9933', '#9966ff']
            text_color = 'black'
            grid_color = '#cccccc'
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Bar positions
        x = np.arange(len(metrics))
        
        # Get data ranges for each metric
        ranges = {}
        for i, metric in enumerate(metrics):
            values = [company['metrics'].get(metric, 0) for company in top_companies]
            # Flip range if lower is better
            if higher_better[i]:
                ranges[metric] = (min(values), max(values))
            else:
                ranges[metric] = (max(values), min(values))
        
        # Plot each company
        for i, company in enumerate(top_companies):
            # Get values for this company
            values = []
            for metric in metrics:
                value = company['metrics'].get(metric, 0)
                values.append(value)
            
            # Normalize values to y-position
            ys = []
            for j, (metric, value) in enumerate(zip(metrics, values)):
                min_val, max_val = ranges[metric]
                if min_val == max_val:
                    y = 0.5  # Middle position if all values are the same
                else:
                    y = (value - min_val) / (max_val - min_val)
                ys.append(y)
            
            # Plot line for this company
            ax.plot(x, ys, 'o-', color=colors[i % len(colors)], 
                   label=f"{company['ticker']} ({company['score']:.0f}%)")
            
            # Add company ticker at the start of the line
            ax.text(x[0]-0.1, ys[0], company['ticker'], 
                   ha='right', va='center', fontsize=10)
        
        # Set up the axes
        ax.set_xticks(x)
        ax.set_xticklabels(metric_labels)
        
        # Set y-axis labels (empty to keep it clean)
        ax.set_yticks([])
        
        # Add vertical lines for each metric
        for x_pos in x:
            ax.axvline(x_pos, color='gray', linestyle='-', alpha=0.3)
        
        # Add legend
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), 
                 ncol=3, frameon=False)
        
        # Add title
        goal_name = goal.capitalize()
        risk_name = risk.capitalize()
        ax.set_title(f"Top Companies for {goal_name} Investors with {risk_name} Risk Tolerance", 
                    fontsize=16, y=1.02)
        
        # Set axis limits
        ax.set_xlim(-0.5, len(metrics) - 0.5)
        ax.set_ylim(-0.05, 1.05)
        
        # Add metric labels at top and bottom
        for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
            min_val, max_val = ranges[metric]
            
            # Format values appropriately
            if metric in ['pe_ratio', 'debt_to_equity']:
                min_label = f"{min_val:.1f}x"
                max_label = f"{max_val:.1f}x"
            elif metric in ['dividend_yield', 'free_cash_flow_yield', 'revenue_growth', 
                           'earnings_growth', 'return_on_equity', 'return_on_assets',
                           'payout_ratio']:
                min_label = f"{min_val*100:.1f}%"
                max_label = f"{max_val*100:.1f}%"
            elif metric == 'price_to_intrinsic':
                min_label = f"{min_val:.1f}x" 
                max_label = f"{max_val:.1f}x"
            else:
                min_label = f"{min_val:.1f}"
                max_label = f"{max_val:.1f}"
            
            # Add labels
            if higher_better[i]:
                ax.text(i, 1.02, max_label, ha='center', va='bottom', fontsize=9)
                ax.text(i, -0.02, min_label, ha='center', va='top', fontsize=9)
            else:
                ax.text(i, 1.02, min_label, ha='center', va='bottom', fontsize=9)
                ax.text(i, -0.02, max_label, ha='center', va='top', fontsize=9)
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # Convert to base64
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        
        return img_str
    
    except Exception as e:
        print(f"Error generating parallel coordinates chart: {e}")
        import traceback
        traceback.print_exc()
        return None