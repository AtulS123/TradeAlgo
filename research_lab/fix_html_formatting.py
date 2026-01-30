"""
Fix Row 3 Description and verify timing stats display
"""

with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\MASTER_TRADING_TABLE.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Fix Row 3 Description (Cell 4)
# Current broken state: <td><strong>min:</strong> 10.35<br><strong>max:</strong> 76.95<br><strong>median:</strong> 15.4<br><strong>avg:</strong> 16.52</td>
# Expected: <td>stayed within 10% below prev low (did not go ≥10% of range below)</td>

# I need to match the context to be sure I'm changing Row 3
# Row 3 starts after "touched prev day high" block ends.
# It starts with "touched prev day low; before touching prev day high"

# Find start of Row 3 scenarios
idx_row3 = html.find('touched prev day low; before touching prev day high')
if idx_row3 == -1:
    print("Error: Could not find Row 3 start")
else:
    # Find the broken cell after the "Time to 1st Order" cell
    # Sequence: 
    # 1. Touched Low (rowspan)
    # 2. Prob (rowspan)
    # 3. Time 1st (rowspan) -> ends with 87 min or similar?
    #    Actually Time 1st ends with 'avg:</strong> 76 min</td>'
    
    idx_time1 = html.find('avg:</strong> 76 min</td>', idx_row3)
    if idx_time1 != -1:
        # The next cell is the broken one
        start_cell = html.find('<td>', idx_time1)
        end_cell = html.find('</td>', start_cell) + 5
        
        current_content = html[start_cell:end_cell]
        print(f"Found content to replace: {current_content}")
        
        if "min:" in current_content and "max:" in current_content:
            new_content = '<td>stayed within 10% below prev low (did not go ≥10% of range below)</td>'
            html = html[:start_cell] + new_content + html[end_cell:]
            print("Fixed Row 3 Description")
        else:
            print("Content didn't look broken as expected?")

# Also check if VIX column got duplicated or lost?
# The broken content "min: 10.35..." looks like VIX stats.
# Row 3 VIX stats should be in column 7.
# Let's check further down in Row 3.
# After Description -> Prob (10.9%) -> Time 2nd (N/A) -> VIX -> Dates

# Since I shifted the VIX stats to Description column, the VIX column might have OLD stats or something else.
# I should re-apply the correct VIX stats to the VIX column for Row 3 just to be safe.
# Row 3 VIX: min 10.39, max 59.77, median 15.29, avg 15.36 (from Step 366/410)
# Wait, "min 10.35" in the broken cell matches Row 2 VIX min (or Row 4?)?
# Step 366: Row 3 min 10.39. Row 1 min 10.35.
# So I pasted ROW 1 VIX into ROW 3 Desc? Or Row 4 VIX?
# Anyway, I'll update the VIX column with correct Row 3 values.

import json
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\final_corrected_stats.json', 'r') as f:
    stats = json.load(f)

def format_vix(vix_stats):
    if vix_stats is None: return "N/A"
    return f"<strong>min:</strong> {vix_stats['min']}<br><strong>max:</strong> {vix_stats['max']}<br><strong>median:</strong> {vix_stats['median']}<br><strong>avg:</strong> {vix_stats['avg']}"

# Update Row 3 VIX column
# Find "stayed within 10% below" -> Prob -> N/A -> VIX
# Since I just fixed the description, I can search for it now (if I do it sequentially in string)
# But avoiding complexity, I will just find "N/A (stayed within)" that comes AFTER the Row 3 start marker
idx_na = html.find('<td>N/A (stayed within)</td>', idx_row3)
if idx_na != -1:
    vix_start = html.find('<td>', idx_na + len('<td>N/A (stayed within)</td>'))
    vix_end = html.find('</td>', vix_start) + 5
    new_vix = f"<td>{format_vix(stats['row3']['vix'])}</td>"
    html = html[:vix_start] + new_vix + html[vix_end:]
    print("Updated Row 3 VIX")

with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\MASTER_TRADING_TABLE.html', 'w', encoding='utf-8') as f:
    f.write(html)
