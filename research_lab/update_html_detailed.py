"""
Generate HTML Table with Detailed Closing Analysis (Exploded Buckets)
"""
import json

with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\final_corrected_stats.json', 'r') as f:
    stats = json.load(f)

# Helper Functions
def format_vix(vix_stats):
    if vix_stats is None: return "N/A"
    return f"<strong>min:</strong> {vix_stats['min']}<br><strong>max:</strong> {vix_stats['max']}<br><strong>median:</strong> {vix_stats['median']}<br><strong>avg:</strong> {vix_stats['avg']}"

def format_timing(timing_stats):
    if timing_stats is None: return "N/A"
    return (f"<strong>min:</strong> {int(timing_stats['min'])} min on {timing_stats['min_date']}<br>"
            f"<strong>max:</strong> {int(timing_stats['max'])} min on {timing_stats['max_date']}<br>"
            f"<strong>median:</strong> {int(timing_stats['median'])} min on {timing_stats['median_date']}<br>"
            f"<strong>avg:</strong> {int(timing_stats['avg'])} min")

def format_dates(dates_list):
    return '<br>'.join(dates_list)

# HTML Template Parts
html_start = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Trading Strategy Probability Grid</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .grid-container { background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; border-right: 1px solid #eee; font-size: 14px; vertical-align: top; }
        th { background-color: #4a86e8; color: white; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }
        tr:last-child td { border-bottom: none; }
        .scenario-header td { background-color: #f8f9fa; font-weight: 600; color: #2c3e50; border-top: 2px solid #e9ecef; }
        .prob-high { background-color: #d4edda; color: #155724; font-weight: bold; }
        .prob-medium { background-color: #fff3cd; color: #856404; font-weight: bold; }
        .prob-low { background-color: #f8d7da; color: #721c24; font-weight: bold; }
        .sub-scenario td { padding-left: 15px; font-size: 13px; color: #555; }
        .date-example { font-family: 'Consolas', monospace; font-size: 11px; color: #666; white-space: nowrap; }
        .open-breakdown { font-size: 11px; color: #666; font-weight: normal; margin-top: 5px; }
    </style>
</head>
<body>
"""

html_end = """
"""

# Reconstruct Top Rows (simplified for this script, reusing existing strings would be cleaner but I'll rebuild)
# I will copy logic from previous script for Top Rows
# Helper for Top Rows
def get_top_row_html():
    total_days = stats['row1']['count'] + stats['row2_direct']['count'] + stats['row2_retraced']['count'] + stats['row3']['count'] + stats['row4_direct']['count'] + stats['row4_retraced']['count'] + stats['row5']['count']
    total_high_group = stats['row1']['count'] + stats['row2_direct']['count'] + stats['row2_retraced']['count']
    total_high_prob = round(total_high_group / total_days * 100, 1) if total_days > 0 else 0
    total_low_group = stats['row3']['count'] + stats['row4_direct']['count'] + stats['row4_retraced']['count']
    total_low_prob = round(total_low_group / total_days * 100, 1) if total_days > 0 else 0
    prob_r5 = round(stats['row5']['count'] / total_days * 100, 1) if total_days > 0 else 0
    
    # Global Prob
    global_prob = stats.get('global_stats', {}).get('inside_prob', 0)
    
    # Placeholders for top timing (Restored Dates)
    row1_timing = "<strong>min:</strong> 0 min on 2015-02-19<br><strong>max:</strong> 370 min on 2015-06-16<br><strong>median:</strong> 20 min on 2016-06-27<br><strong>avg:</strong> 87 min"
    row3_timing = "<strong>min:</strong> 0 min on 2015-01-29<br><strong>max:</strong> 590 min on 2017-10-19<br><strong>median:</strong> 20 min on 2015-05-06<br><strong>avg:</strong> 76 min"

    rows = f"""
                <!-- SCENARIO A -->
                <tr class="scenario-header">
                    <td rowspan="7" style="border-right: 2px solid #ddd;">
                        <strong>Market Open Inside</strong><br>
                        <h3>Market Open Inside Analysis (First 5-min Candle Close Inside Prev Range)</h3>
                        <p><strong>Condition:</strong> The first 5-minute candle of the day <strong>closes</strong> inside the previous day's high/low range.</p>
                    </td>
                    <td rowspan="7" style="border-right: 2px solid #ddd;"><strong>{global_prob}%</strong><br>({total_days})</td>
                    
                    <td rowspan="3">touched prev day high; before touching prev day low</td>
                    <td rowspan="3" class="prob-medium"><strong>{total_high_prob}%</strong><br>({total_high_group})</td>
                    <td rowspan="3">{row1_timing}</td>
                    
                    <td>stayed within 10% above prev high (did not go ≥10% of range above)</td>
                    <td class="prob-high"><strong>{stats['row1']['prob']}%</strong><br>({stats['row1']['count']})</td>
                    <td>-</td>
                    <td>{format_vix(stats['row1']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row1']['dates'])}</td>
                </tr>
                <tr class="sub-scenario">
                    <td>goes ≥10% above prev high <strong>BEFORE</strong> touching mid of prev day range</td>
                    <td class="prob-low"><strong>{stats['row2_direct']['prob']}%</strong><br>({stats['row2_direct']['count']})</td>
                    <td>{format_timing(stats['row2_direct']['timing'])}</td>
                    <td>{format_vix(stats['row2_direct']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row2_direct']['dates'])}</td>
                </tr>
                <tr class="sub-scenario">
                    <td>goes ≥10% above prev high <strong>AFTER</strong> touching mid of prev day range</td>
                    <td class="prob-low"><strong>{stats['row2_retraced']['prob']}%</strong><br>({stats['row2_retraced']['count']})</td>
                    <td>{format_timing(stats['row2_retraced']['timing'])}</td>
                    <td>{format_vix(stats['row2_retraced']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row2_retraced']['dates'])}</td>
                </tr>

                <!-- SCENARIO B -->
                <tr class="scenario-header">
                    <td rowspan="3">touched prev day low; before touching prev day high</td>
                    <td rowspan="3" class="prob-medium"><strong>{total_low_prob}%</strong><br>({total_low_group})</td>
                    <td rowspan="3">{row3_timing}</td>
                    
                    <td>stayed within 10% below prev low (did not go ≥10% of range below)</td>
                    <td class="prob-high"><strong>{stats['row3']['prob']}%</strong><br>({stats['row3']['count']})</td>
                    <td>-</td>
                    <td>{format_vix(stats['row3']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row3']['dates'])}</td>
                </tr>
                <tr class="sub-scenario">
                    <td>goes ≥10% below prev low <strong>BEFORE</strong> touching mid of prev day range</td>
                    <td class="prob-low"><strong>{stats['row4_direct']['prob']}%</strong><br>({stats['row4_direct']['count']})</td>
                    <td>{format_timing(stats['row4_direct']['timing'])}</td>
                    <td>{format_vix(stats['row4_direct']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row4_direct']['dates'])}</td>
                </tr>
                <tr class="sub-scenario">
                    <td>goes ≥10% below prev low <strong>AFTER</strong> touching mid of prev day range</td>
                    <td class="prob-low"><strong>{stats['row4_retraced']['prob']}%</strong><br>({stats['row4_retraced']['count']})</td>
                    <td>{format_timing(stats['row4_retraced']['timing'])}</td>
                    <td>{format_vix(stats['row4_retraced']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row4_retraced']['dates'])}</td>
                </tr>

                <!-- SCENARIO C -->
                <tr class="scenario-header">
                    <td colspan="3">stayed within prev day range (neither high nor low touched)</td>
                    <td colspan="2" class="prob-low"><strong>{prob_r5}%</strong><br>({stats['row5']['count']})</td>
                    <td colspan="2">Avg Range: {stats["row5"]["avg_pct_range"]}%</td>
                    <td>{format_vix(stats['row5']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row5']['dates'])}</td>
                </tr>
    """
    return rows

# Generate Bottom Rows (Detailed)
def generate_closing_rows(key_name, title, direction_label, mid_label, opp_label):
    data = stats[key_name]
    
    # Calculate Rowspans
    rows_html = ""
    
    # OPEN BREAKDOWN Parsing
    open_stats = data.get('open_breakdown', {})
    total_count = data['count']
    open_desc = f"""
    <div class="open-breakdown">
    Above: {open_stats.get('above',0)}<br>
    Inside: {open_stats.get('inside',0)}<br>
    Below: {open_stats.get('below',0)}
    </div>
    """
    
    first_row = True
    
    for time_key, time_label_base in [("early", "Touched within 10 AM"), ("late", "Did NOT touch within 10 AM")]:
        
        # Explicit Label Construction
        if "Touched" in time_label_base:
            # Note: For Close Above, touching High is consistent. For Close Below, touching Low is consistent.
            target_level = "High" if direction_label == "ABOVE" else "Low"
            time_label = f"Touched Prev Day {target_level} within 10 AM"
        else:
            target_level = "High" if direction_label == "ABOVE" else "Low"
            time_label = f"Did NOT touch Prev Day {target_level} within 10 AM"
            
        group_data = data['breakdown'][time_key]
        group_count = group_data['count']
        group_prob = group_data['prob']
        
        # Verbose Outcome Labels
        bucket_keys = ["direct_ext", "no_ext", "touched_opp_mid", "touched_opp_low"]
        
        # Determine labels based on direction
        if direction_label == "ABOVE":
            l_ext = "Went ABOVE at least 10% (of prev day range) over previous day HIGH"
            l_no_ext = "Did NOT go ABOVE at least 10% (of prev day range) over previous day HIGH"
            l_mid = "Went BELOW prev day HIGH to touch prev day range MID"
            l_low = "Went BELOW prev day HIGH to touch prev day range LOW"
        else:
            l_ext = "Went BELOW at least 10% (of prev day range) over previous day LOW"
            l_no_ext = "Did NOT go BELOW at least 10% (of prev day range) over previous day LOW"
            l_mid = "Went ABOVE prev day LOW to touch prev day range MID"
            l_low = "Went ABOVE prev day LOW to touch prev day range HIGH"

        bucket_labels = [l_ext, l_no_ext, l_mid, l_low]
        
        # Inner Loop for 4 rows
        for i, b_key in enumerate(bucket_keys):
            bucket_data = group_data['buckets'][b_key]
            
            rows_html += "<tr>"
            
            # Col 1 & 2: Main Scenario (Rowspan 8, only on very first row)
            if first_row and i == 0 and time_key == "early":
                rows_html += f'<td rowspan="8" class="scenario-header"><strong>{title}</strong>{open_desc}</td>'
                rows_html += f'<td rowspan="8" class="scenario-header"><strong>{data["prob"]}%</strong><br>({total_count})</td>'
            
            # Col 3, 4, 5: Time Group (Rowspan 4, on first row of group)
            if i == 0:
                rows_html += f'<td rowspan="4">{time_label}</td>'
                rows_html += f'<td rowspan="4"><strong>{group_prob}%</strong><br>({group_count})</td>'
                rows_html += f'<td rowspan="4">-</td>'
            
            # Col 6, 7, 8, 9, 10: Bucket Data
            rows_html += f'<td>{bucket_labels[i]}</td>'
            
            # Calculate Bucket Prob relative to Sub-Group? Or Total?
            # Usually relative to Sub-Group (Time Group) for deeper insight, 
            # OR relative to Main Scenario.
            # Let's use Count for sure.
            # Validating "Prob" from JSON bucket -> it was relative to Global Total?
            # JSON: "prob": round(count / total * 100, 1) where total = Scenario Total (Close Above Count).
            b_prob = bucket_data['prob']
            b_count = bucket_data['count']
            
            rows_html += f'<td><strong>{b_prob}%</strong><br>({b_count})</td>'
            rows_html += f'<td>-</td>' # Timing Outcome (Placeholder)
            rows_html += f'<td>{format_vix(bucket_data.get("vix"))}</td>'
            rows_html += f'<td class="date-example">{format_dates(bucket_data.get("dates", []))}</td>'
            
            rows_html += "</tr>"
            
    return rows_html

# Build Table 1: Market Open Inside
table1_html = f"""
    <div class="grid-container" style="margin-bottom: 40px;">
        <h2 style="padding: 15px 15px 0; margin:0; color:#2c3e50;">1. Market Open Inside Analysis</h2>
        <table>
            <thead>
                <tr>
                    <th style="width: 15%">Category / Open</th>
                    <th style="width: 6%">% Probability<br>(Total)</th>
                    <th style="width: 15%">1st Event / Time of Day</th>
                    <th style="width: 6%">% Probability<br>(Sub-Group)</th>
                    <th style="width: 10%">Time Info</th>
                    <th style="width: 15%">Detailed Outcome<br><span style="font-size:10px; font-weight:normal;">(Based on 5-min Close)</span></th>
                    <th style="width: 6%">% Probability<br>(Outcome)</th>
                    <th style="width: 10%">Timing</th>
                    <th style="width: 8%">VIX</th>
                    <th style="width: 9%">Example Dates</th>
                </tr>
            </thead>
            <tbody>
                {get_top_row_html()}
            </tbody>
        </table>
    </div>
"""

# Build Table 2: Closing Analysis
rows_close_above = generate_closing_rows('close_above_detailed', 'Close: Top of Prev Day High', 'ABOVE', 'MID', 'LOW')
rows_close_below = generate_closing_rows('close_below_detailed', 'Close: Below Prev Day Low', 'BELOW', 'MID', 'HIGH')

table2_html = f"""
    <div class="grid-container">
        <h2 style="padding: 15px 15px 0; margin:0; color:#2c3e50;">2. Closing Analysis</h2>
        <table>
            <thead>
                <tr>
                    <th style="width: 15%">Closing Scenario</th>
                    <th style="width: 6%">% Probability<br>(Total)</th>
                    <th style="width: 15%">Breakout Time</th>
                    <th style="width: 6%">% Probability<br>(Time Group)</th>
                    <th style="width: 10%">Time Info</th>
                    <th style="width: 15%">Detailed Outcome<br><span style="font-size:10px; font-weight:normal;">(Based on 5-min Close)</span></th>
                    <th style="width: 6%">% Probability<br>(Outcome)</th>
                    <th style="width: 10%">Timing</th>
                    <th style="width: 8%">VIX</th>
                    <th style="width: 9%">Example Dates</th>
                </tr>
            </thead>
            <tbody>
                {rows_close_above}
                {rows_close_below}
            </tbody>
        </table>
    </div>
"""

full_html = html_start + table1_html + table2_html + "</body></html>"

with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\MASTER_TRADING_TABLE.html', 'w', encoding='utf-8') as f:
    f.write(full_html)
    
print("✅ Detailed Full Table Generated")
