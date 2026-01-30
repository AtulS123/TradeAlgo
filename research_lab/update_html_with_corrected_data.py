"""
Update HTML with corrected 2nd order data
"""

import json

# Load corrected data
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\corrected_data.json', 'r') as f:
    data = json.load(f)

# Read HTML
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\MASTER_TRADING_TABLE.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Prepare replacement values
row1_count = data['row1_stayed_within_10pct_above']['count']
row1_prob = data['row1_stayed_within_10pct_above']['probability']
row1_vix = data['row1_stayed_within_10pct_above']['vix']
row1_dates = '<br>'.join(data['row1_stayed_within_10pct_above']['dates'])

row2_count = data['row2_went_10pct_above']['count']
row2_prob = data['row2_went_10pct_above']['probability']
row2_vix = data['row2_went_10pct_above']['vix']
row2_dates = '<br>'.join(data['row2_went_10pct_above']['dates'])

row3_count = data['row3_stayed_within_10pct_below']['count']
row3_prob = data['row3_stayed_within_10pct_below']['probability']
row3_vix = data['row3_stayed_within_10pct_below']['vix']
row3_dates = '<br>'.join(data['row3_stayed_within_10pct_below']['dates'])

row4_count = data['row4_went_10pct_below']['count']
row4_prob = data['row4_went_10pct_below']['probability']
row4_vix = data['row4_went_10pct_below']['vix']
row4_dates = '<br>'.join(data['row4_went_10pct_below']['dates'])

row5_count = data['row5_stayed_inside']['count']
row5_prob = data['row5_stayed_inside']['probability']
row5_vix = data['row5_stayed_inside']['vix']
row5_avg_range = data['row5_stayed_inside']['avg_pct_range']
row5_gap_high = data['row5_stayed_inside']['avg_gap_from_high']
row5_gap_low = data['row5_stayed_inside']['avg_gap_from_low']
row5_dates = '<br>'.join(data['row5_stayed_inside']['dates'])

# Replace Row 1
html = html.replace(
    '<td>touches prev day low without going ≥10% (of prev range) over prev high</td>\n                    <td class="prob-high"><strong>86.8%</strong><br><strong>(512 days)</strong></td>',
    f'<td>stayed within 10% above prev high (did not go ≥10% of range above)</td>\n                    <td class="prob-high"><strong>{row1_prob}%</strong><br><strong>({row1_count} days)</strong></td>'
)

# Replace Row 2
html = html.replace(
    '<td>goes ≥10% (of prev range) above prev high</td>\n                    <td class="prob-low"><strong>13.2%</strong><br><strong>(78 days)</strong></td>',
    f'<td>goes ≥10% (of prev range) above prev high</td>\n                    <td class="prob-low"><strong>{row2_prob}%</strong><br><strong>({row2_count} days)</strong></td>'
)

# Replace Row 3
html = html.replace(
    '<td>touches prev day high without going ≥10% (of prev range) below prev low</td>\n                    <td class="prob-high"><strong>92.3%</strong><br><strong>(619 days)</strong></td>',
    f'<td>stayed within 10% below prev low (did not go ≥10% of range below)</td>\n                    <td class="prob-high"><strong>{row3_prob}%</strong><br><strong>({row3_count} days)</strong></td>'
)

# Replace Row 4
html = html.replace(
    '<td>goes ≥10% (of prev range) below prev low</td>\n                   <td class="prob-low"><strong>7.7%</strong><br><strong>(52 days)</strong></td>',
    f'<td>goes ≥10% (of prev range) below prev low</td>\n                    <td class="prob-low"><strong>{row4_prob}%</strong><br><strong>({row4_count} days)</strong></td>'
)

# Replace Row 5  
html = html.replace(
    '<td colspan="2">stayed within prev day range<br>(neither high nor low touched)</td>\n                    <td colspan="2" class="prob-low"><strong>16.3%</strong><br><strong>(245 days)</strong></td>\n                    <td colspan="2">No further moves</td>\n                    <td colspan="2" class="date-example">',
    f'<td colspan="2">stayed within prev day range<br>(neither high nor low touched)</td>\n                    <td colspan="2" class="prob-low"><strong>{row5_prob}%</strong><br><strong>({row5_count} days)</strong></td>\n                    <td colspan="2">Avg % range: {row5_avg_range}%<br>Gap from high: {row5_gap_high}%<br>Gap from low: {row5_gap_low}%</td>\n                    <td class="date-example">VIX: {row5_vix}</td>\n                    <td class="date-example">'
)

# Update VIX and dates
html = html.replace('<td>15.60</td>', f'<td>{row1_vix}</td>', 1)
html = html.replace(f'<td class="date-example">{row1_dates[:50]}', f'<td class="date-example">{row1_dates}', 1)

html = html.replace(f'<td>{row2_vix}</td>', f'<td>{row2_vix}</td>', 1)  
html = html.replace(f'<td class="date-example">{row2_dates[:20]}', f'<td class="date-example">{row2_dates}', 1)

html = html.replace('<td>15.36</td>', f'<td>{row3_vix}</td>', 1)
html = html.replace(f'<td class="date-example">{row3_dates[:50]}', f'<td class="date-example">{row3_dates}', 1)

html = html.replace(f'<td>{row4_vix}</td>', f'<td>{row4_vix}</td>', 1)
html = html.replace(f'<td class="date-example">{row4_dates[:20]}', f'<td class="date-example">{row4_dates}', 1)

html = html.replace(f'<td class="date-example">{row5_dates[:20]}', f'{row5_dates}', 1)

# Write updated HTML
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\MASTER_TRADING_TABLE.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ HTML updated with corrected data!")
print(f"\nRow 1: {row1_count} days ({row1_prob}%), VIX: {row1_vix}")
print(f"Row 2: {row2_count} days ({row2_prob}%), VIX: {row2_vix}")
print(f"Row 3: {row3_count} days ({row3_prob}%), VIX: {row3_vix}")
print(f"Row 4: {row4_count} days ({row4_prob}%), VIX: {row4_vix}")
print(f"Row 5: {row5_count} days ({row5_prob}%), VIX: {row5_vix}, Avg range: {row5_avg_range}%")
