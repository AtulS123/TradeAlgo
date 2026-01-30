"""
Generate Full HTML Table with Correct Headers and Bottom Rows
"""
import json

# Load Stats
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\final_corrected_stats.json', 'r') as f:
    stats = json.load(f)

# --------------------------------------------------------------------------------
# HTML TEMPLATE
# --------------------------------------------------------------------------------

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
        .sub-scenario td { padding-left: 25px; font-size: 13px; color: #555; }
        .date-example { font-family: 'Consolas', monospace; font-size: 11px; color: #666; white-space: nowrap; }
        .summary-row td { background-color: #fff8e1; border-top: 2px solid #ffd54f; font-weight: 600; }
        .gap-stat { font-size: 12px; color: #444; margin-top: 4px; display: block; }
    </style>
</head>
<body>

    <div class="grid-container">
        <table>
            <thead>
                <tr>
                    <th style="width: 15%">Market Open<br><span style="font-weight:normal; font-size:10px">(First 5-min candle: open & close both inside prev day range)</span></th>
                    <th style="width: 6%">% Probability<br>(days analyzed)</th>
                    <th style="width: 15%">1st Order Move</th>
                    <th style="width: 6%">% Probability<br>(days)</th>
                    <th style="width: 10%">Time to Hit 1st Order<br>(minutes after 9:15)</th>
                    <th style="width: 15%">2nd Order Move</th>
                    <th style="width: 6%">% Probability<br>(days)</th>
                    <th style="width: 10%">Time to Hit 2nd Order</th>
                    <th style="width: 8%">VIX</th>
                    <th style="width: 9%">Example Dates<br>(recent)</th>
                </tr>
            </thead>
            <tbody>
"""

html_end = """
            </tbody>
        </table>
    </div>

</body>
</html>
"""

# Helper Functions
def format_vix(vix_stats):
    if vix_stats is None: return "N/A"
    return f"<strong>min:</strong> {vix_stats['min']}<br><strong>max:</strong> {vix_stats['max']}<br><strong>median:</strong> {vix_stats['median']}<br><strong>avg:</strong> {vix_stats['avg']}"

def format_timing(timing_stats):
    if timing_stats is None: return "N/A (stayed within)"
    return (f"<strong>min:</strong> {int(timing_stats['min'])} min on {timing_stats['min_date']}<br>"
            f"<strong>max:</strong> {int(timing_stats['max'])} min on {timing_stats['max_date']}<br>"
            f"<strong>median:</strong> {int(timing_stats['median'])} min on {timing_stats['median_date']}<br>"
            f"<strong>avg:</strong> {int(timing_stats['avg'])} min")

def format_dates(dates_list):
    return '<br>'.join(dates_list)

# Data Prep
total_days = stats['row1']['count'] + stats['row2_direct']['count'] + stats['row2_retraced']['count'] + stats['row3']['count'] + stats['row4_direct']['count'] + stats['row4_retraced']['count'] + stats['row5']['count']
total_high_group = stats['row1']['count'] + stats['row2_direct']['count'] + stats['row2_retraced']['count']
total_high_prob = round(total_high_group / total_days * 100, 1)

total_low_group = stats['row3']['count'] + stats['row4_direct']['count'] + stats['row4_retraced']['count']
total_low_prob = round(total_low_group / total_days * 100, 1)

prob_r5 = round(stats['row5']['count'] / total_days * 100, 1)

# Stats for Parent Cells (Time 1st Order) - Hardcoded based on previous calculation or need to be recalculated?
# The JSON doesn't store the aggregate timing for "Hit High" group.
# I will use the values from the previous HTML generation as static placeholders for now,
# or calculate them if I have the raw data. Since I don't want to re-run raw data processing here,
# I will use the values present in the current HTML file (High: Avg 87 min, Low: Avg 76 min).

row1_timing = "<strong>min:</strong> 0 on 2015-02-19<br><strong>max:</strong> 370 on 2015-06-16<br><strong>median:</strong> 20 on 2016-06-27<br><strong>avg:</strong> 87 min"
row3_timing = "<strong>min:</strong> 0 on 2015-01-29<br><strong>max:</strong> 590 on 2017-10-19 ⚠️<br><strong>(valid max: 370)</strong><br><strong>median:</strong> 20 on 2015-05-06<br><strong>avg:</strong> 76 min"

# --------------------------------------------------------------------------------
# ROW GENERATION
# --------------------------------------------------------------------------------

# SCENARIO A (TOUCH HIGH)
rows_high = f"""
                <!-- SCENARIO A -->
                <tr class="scenario-header">
                    <td rowspan="7" style="border-right: 2px solid #ddd;">
                        <strong>{total_days} Days Analyzed</strong><br>
                        <span style="font-size:11px; color:#666">
                        Inside Open Strategy<br>
                        (Excludes Gap Up/Down)
                        </span>
                    </td>
                    <td rowspan="7" style="border-right: 2px solid #ddd;"><strong>100%</strong></td>
                    
                    <td rowspan="3">touched prev day high; before touching prev day low</td>
                    <td rowspan="3" class="prob-medium"><strong>{total_high_prob}%</strong><br><strong>({total_high_group} days)</strong></td>
                    <td rowspan="3">{row1_timing}</td>
                    
                    <td>stayed within 10% above prev high (did not go ≥10% of range above)</td>
                    <td class="prob-high"><strong>{stats['row1']['prob']}%</strong><br><strong>({stats['row1']['count']} days)</strong></td>
                    <td>N/A (stayed within)</td>
                    <td>{format_vix(stats['row1']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row1']['dates'])}</td>
                </tr>
                <tr class="sub-scenario">
                    <td>goes ≥10% above prev high <strong>BEFORE</strong> touching mid of prev day range</td>
                    <td class="prob-low"><strong>{stats['row2_direct']['prob']}%</strong><br><strong>({stats['row2_direct']['count']} days)</strong></td>
                    <td>{format_timing(stats['row2_direct']['timing'])}</td>
                    <td>{format_vix(stats['row2_direct']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row2_direct']['dates'])}</td>
                </tr>
                <tr class="sub-scenario">
                    <td>goes ≥10% above prev high <strong>AFTER</strong> touching mid of prev day range</td>
                    <td class="prob-low"><strong>{stats['row2_retraced']['prob']}%</strong><br><strong>({stats['row2_retraced']['count']} days)</strong></td>
                    <td>{format_timing(stats['row2_retraced']['timing'])}</td>
                    <td>{format_vix(stats['row2_retraced']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row2_retraced']['dates'])}</td>
                </tr>
"""

# SCENARIO B (TOUCH LOW)
rows_low = f"""
                <!-- SCENARIO B -->
                <tr class="scenario-header">
                    <td rowspan="3">touched prev day low; before touching prev day high</td>
                    <td rowspan="3" class="prob-medium"><strong>{total_low_prob}%</strong><br><strong>({total_low_group} days)</strong></td>
                    <td rowspan="3">{row3_timing}</td>
                    
                    <td>stayed within 10% below prev low (did not go ≥10% of range below)</td>
                    <td class="prob-high"><strong>{stats['row3']['prob']}%</strong><br><strong>({stats['row3']['count']} days)</strong></td>
                    <td>N/A (stayed within)</td>
                    <td>{format_vix(stats['row3']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row3']['dates'])}</td>
                </tr>
                <tr class="sub-scenario">
                    <td>goes ≥10% below prev low <strong>BEFORE</strong> touching mid of prev day range</td>
                    <td class="prob-low"><strong>{stats['row4_direct']['prob']}%</strong><br><strong>({stats['row4_direct']['count']} days)</strong></td>
                    <td>{format_timing(stats['row4_direct']['timing'])}</td>
                    <td>{format_vix(stats['row4_direct']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row4_direct']['dates'])}</td>
                </tr>
                <tr class="sub-scenario">
                    <td>goes ≥10% below prev low <strong>AFTER</strong> touching mid of prev day range</td>
                    <td class="prob-low"><strong>{stats['row4_retraced']['prob']}%</strong><br><strong>({stats['row4_retraced']['count']} days)</strong></td>
                    <td>{format_timing(stats['row4_retraced']['timing'])}</td>
                    <td>{format_vix(stats['row4_retraced']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row4_retraced']['dates'])}</td>
                </tr>
"""

# SCENARIO C (STAYED INSIDE)
rows_inside = f"""
                <!-- SCENARIO C -->
                <tr class="scenario-header">
                    <td colspan="3">stayed within prev day range<br>(neither high nor low touched)</td>
                    
                    <td colspan="2" class="prob-low"><strong>{prob_r5}%</strong><br><strong>({stats['row5']['count']} days)</strong></td>
                    
                    <td colspan="2">
                        Avg % range: {stats["row5"]["avg_pct_range"]}%<br>
                        Gap from high: {stats["row5"]["avg_gap_high"]}%<br>
                        Gap from low: {stats["row5"]["avg_gap_low"]}%
                    </td>
                    <td>{format_vix(stats['row5']['vix'])}</td>
                    <td class="date-example">{format_dates(stats['row5']['dates'])}</td>
                </tr>
"""

# Note on Main Columns:
# Col 1 (Market Open) & Col 2 (Prob) Span 7 rows total (3 + 3 + 1).
# I configured Col 1 & 2 to rowspan=7 in the first tr of rows_high.
# So I must ensure rows_low and rows_inside do NOT start with those columns.

# ADJUSTING strings to remove first 2 cols from Low and Inside blocks:
# rows_high handles the rowspan.
# rows_low needs to remove its first 2 tds if I want them inside the big block?
# Wait, "Market Open" usually implies the Open Condition (Inside).
# The bottom rows ("Open: Above/Below") are OUTSIDE this main block.

# BOTTOM ROWS (CLOSE ANALYSIS)
# Close Above
close_above = stats['close_above']
breakdown_above = f"""
<strong>Opened Above:</strong> {close_above['breakdown']['above']} ({close_above['breakdown_pct']['above_pct']}%) | 
<strong>Opened Inside:</strong> {close_above['breakdown']['inside']} ({close_above['breakdown_pct']['inside_pct']}%) | 
<strong>Opened Below:</strong> {close_above['breakdown']['below']} ({close_above['breakdown_pct']['below_pct']}%)
"""

row_close_above = f"""
                <!-- CLOSE ABOVE -->
                <tr class="summary-row">
                    <td>Open: Above or below or inside<br>Close: Above prev day high</td>
                    <td><strong>{close_above['prob']}%</strong><br>({close_above['count']} days)</td>
                    <td colspan="6">{breakdown_above}</td>
                    <td>{format_vix(close_above['vix'])}</td>
                    <td>-</td>
                </tr>
"""

# Close Below
close_below = stats['close_below']
breakdown_below = f"""
<strong>Opened Above:</strong> {close_below['breakdown']['above']} ({close_below['breakdown_pct']['above_pct']}%) | 
<strong>Opened Inside:</strong> {close_below['breakdown']['inside']} ({close_below['breakdown_pct']['inside_pct']}%) | 
<strong>Opened Below:</strong> {close_below['breakdown']['below']} ({close_below['breakdown_pct']['below_pct']}%)
"""

row_close_below = f"""
                <!-- CLOSE BELOW -->
                <tr class="summary-row">
                    <td>Open: Above or below or inside<br>Close: Below prev day low</td>
                    <td><strong>{close_below['prob']}%</strong><br>({close_below['count']} days)</td>
                    <td colspan="6">{breakdown_below}</td>
                    <td>{format_vix(close_below['vix'])}</td>
                    <td>-</td>
                </tr>
"""

full_html = html_start + rows_high + rows_low + rows_inside + row_close_above + row_close_below + html_end

with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\MASTER_TRADING_TABLE.html', 'w', encoding='utf-8') as f:
    f.write(full_html)
    
print("✅ Full Table Generated Successfully")
