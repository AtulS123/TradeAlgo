"""
Update HTML Table with Split Rows (Row 2 Direct/Retraced and Row 4 Direct/Retraced)
"""
import json
import re

# Load Stats
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\final_corrected_stats.json', 'r') as f:
    stats = json.load(f)

# Read HTML
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\MASTER_TRADING_TABLE.html', 'r', encoding='utf-8') as f:
    html = f.read()

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

def get_percent(row, total):
    if total == 0: return 0.0
    return round((row['count'] / total) * 100, 1)

# Totals for Prob calc
total_high_group = stats['row1']['count'] + stats['row2_direct']['count'] + stats['row2_retraced']['count']
total_low_group = stats['row3']['count'] + stats['row4_direct']['count'] + stats['row4_retraced']['count']

# --------------------------------------------------------------------------------
# CONSTRUCT SCENARIO A BLOCK (High First)
# --------------------------------------------------------------------------------
# Row 1 (Top part of rowspan)
# Row 2a (Direct)
# Row 2b (Retraced)

scenario_a_html = f"""
                <tr class="scenario-header">
                    <td rowspan="3">touched prev day high; before touching prev day low</td>
                    <td rowspan="3" class="prob-medium"><strong>39.2%</strong><br><strong>({total_high_group} days)</strong></td>
                    <td rowspan="3"><strong>min:</strong> 0 on 2015-02-19<br><strong>max:</strong> 370 on
                        2015-06-16<br><strong>median:</strong> 20 on 2016-06-27<br><strong>avg:</strong> 87 min</td>
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

# --------------------------------------------------------------------------------
# CONSTRUCT SCENARIO B BLOCK (Low First)
# --------------------------------------------------------------------------------
# Row 3
# Row 4a
# Row 4b

scenario_b_html = f"""
                <tr class="scenario-header">
                    <td rowspan="3">touched prev day low; before touching prev day high</td>
                    <td rowspan="3" class="prob-medium"><strong>44.6%</strong><br><strong>({total_low_group} days)</strong></td>
                    <td rowspan="3"><strong>min:</strong> 0 on 2015-01-29<br><strong>max:</strong> 590 on 2017-10-19
                        ⚠️<br><strong>(valid max: 370)</strong><br><strong>median:</strong> 20 on
                        2015-05-06<br><strong>avg:</strong> 76 min</td>
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

# Replace in HTML
# Regex approach to find the blocks
# Scenario A starts with <tr class="scenario-header"> and contains "touched prev day high"
# It ends at </tr> which is followed by <tr class="scenario-header"> (next block) OR <tr class="scenario-header"> for low first

# Strategy: Find strict markers
start_marker_A = '<tr class="scenario-header">\n                    <td rowspan="2">touched prev day high; before touching prev day low</td>'
# But rowspan might be different in actual file if I didn't update it? No, it IS rowspan="2" currently.

# Finding END of Scenario A
# It ends after the 2nd row (sub-scenario).
# Look for the start of Scenario B
start_marker_B = '<tr class="scenario-header">\n                    <td rowspan="2">touched prev day low; before touching prev day high</td>'

# Finding END of Scenario B
# Look for start of Stayed Inside
start_marker_C = '<!-- STAYED INSIDE -->'

# Get indices
idx_A = html.find('touched prev day high; before touching prev day low')
# Backtrack to <tr
idx_A_start = html.rfind('<tr', 0, idx_A)

idx_B = html.find('touched prev day low; before touching prev day high')
idx_B_start = html.rfind('<tr', 0, idx_B)

idx_C = html.find('stayed within prev day range')
idx_C_start = html.rfind('<!-- STAYED INSIDE -->', 0, idx_C)
if idx_C_start == -1: # Fallback
    idx_C_start = html.rfind('<tr', 0, idx_C)

# Replace Block A
# Removing from A_start to B_start (minus whitespace maybe?)
# Let's clean up whitespace in my generated strings too?
# Nah, HTML doesn't care much.

# Construct New HTML
new_html = html[:idx_A_start] + scenario_a_html + html[idx_B_start:idx_C_start] 
# Wait, I need to replace Block B too.
# The `html[idx_B_start:idx_C_start]` is the OLD Block B. I want to replace it.

# So:
new_html = html[:idx_A_start] + scenario_a_html + "\n\n" + scenario_b_html + "\n\n" + html[idx_C_start:]

with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\MASTER_TRADING_TABLE.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("✅ HTML Updated with SPLIT rows structure")
