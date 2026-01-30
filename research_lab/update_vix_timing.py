"""
Update HTML with VIX and timing statistics
"""

import json

# Load stats
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\vix_timing_stats.json', 'r') as f:
    stats = json.load(f)

# Read HTML
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\MASTER_TRADING_TABLE.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Format VIX stats
def format_vix(vix_stats):
    if vix_stats['min'] is None:
        return "N/A"
    return f"<strong>min:</strong> {vix_stats['min']}<br><strong>max:</strong> {vix_stats['max']}<br><strong>median:</strong> {vix_stats['median']}<br><strong>avg:</strong> {vix_stats['avg']}"

# Format timing stats
def format_timing(timing_stats):
    if timing_stats is None:
        return "N/A (stayed within)"
    return (f"<strong>min:</strong> {int(timing_stats['min'])} min on {timing_stats['min_date']}<br>"
            f"<strong>max:</strong> {int(timing_stats['max'])} min on {timing_stats['max_date']}<br>"
            f"<strong>median:</strong> {int(timing_stats['median'])} min on {timing_stats['median_date']}<br>"
            f"<strong>avg:</strong> {int(timing_stats['avg'])} min")

# Update Row 1
html = html.replace(
    '<td>15.59</td>',
    f'<td>{format_vix(stats["row1_stayed_within_10pct_above"]["vix_stats"])}</td>',
    1
)

# Replace the [pending calc] with timing for Row 1 (stayed within, so no 2nd order timing)
# Actually for rows 1, 3, 5 there's no "2nd order move" since they stayed within, so keep as N/A

# Update Row 2
html = html.replace(
    '<td>15.78</td>',
    f'<td>{format_vix(stats["row2_went_10pct_above"]["vix_stats"])}</td>',
    1
)

# Find and replace the [pending calc] for Row 2 with timing stats
# Need to find the right occurrence
lines =html.split('\n')
row2_timing_line = -1
row4_timing_line = -1
pending_count = 0

for i, line in enumerate(lines):
    if '[pending calc]' in line and 'stayed within 10% above' in lines[max(0, i-5):i+1]:
        row2_timing_line = i
    elif '[pending calc]' in line and 'goes ≥10% (of prev range) above' in lines[max(0, i-5):i+1]:
        # This is row 2's timing
        if row2_timing_line == -1:
            row2_timing_line = i
            
# Actually, let me do this more carefully with targeted replacements

# Row 2 - update VIX and add timing (replace [pending calc])
# The structure is: ...prob...</td><td>[pending calc]</td><td>15.78</td>...

# Let me use a different approach - find each row block and replace

# Row 1
html = html.replace(
    'stayed within 10% above prev high (did not go ≥10% of range above)</td>\n                    <td class="prob-high"><strong>89.7%</strong><br><strong>(529 days)</strong></td>\n                    <td>[pending calc]</td>\n                    <td>15.59</td>',
    f'stayed within 10% above prev high (did not go ≥10% of range above)</td>\n                    <td class="prob-high"><strong>89.7%</strong><br><strong>(529 days)</strong></td>\n                    <td>N/A (stayed within)</td>\n                    <td>{format_vix(stats["row1_stayed_within_10pct_above"]["vix_stats"])}</td>'
)

# Row 2
html = html.replace(
    'goes ≥10% (of prev range) above prev high</td>\n                    <td class="prob-low"><strong>10.3%</strong><br><strong>(61 days)</strong></td>\n                    <td>[pending calc]</td>\n                    <td>15.78</td>',
    f'goes ≥10% (of prev range) above prev high</td>\n                    <td class="prob-low"><strong>10.3%</strong><br><strong>(61 days)</strong></td>\n                    <td>{format_timing(stats["row2_went_10pct_above"]["timing_stats"])}</td>\n                    <td>{format_vix(stats["row2_went_10pct_above"]["vix_stats"])}</td>'
)

# Row 3
html = html.replace(
    'stayed within 10% below prev low (did not go ≥10% of range below)</td>\n                    <td class="prob-high"><strong>89.0%</strong><br><strong>(597 days)</strong></td>\n                    <td>[pending calc]</td>\n                    <td>15.31</td>',
    f'stayed within 10% below prev low (did not go ≥10% of range below)</td>\n                    <td class="prob-high"><strong>89.0%</strong><br><strong>(597 days)</strong></td>\n                    <td>N/A (stayed within)</td>\n                    <td>{format_vix(stats["row3_stayed_within_10pct_below"]["vix_stats"])}</td>'
)

# Row 4
html = html.replace(
    'goes ≥10% (of prev range) below prev low</td>\n                    <td class="prob-low"><strong>11.0%</strong><br><strong>(74 days)</strong></td>\n                    <td>[pending calc]</td>\n                    <td>16.22</td>',
    f'goes ≥10% (of prev range) below prev low</td>\n                    <td class="prob-low"><strong>11.0%</strong><br><strong>(74 days)</strong></td>\n                    <td>{format_timing(stats["row4_went_10pct_below"]["timing_stats"])}</td>\n                    <td>{format_vix(stats["row4_went_10pct_below"]["vix_stats"])}</td>'
)

# Row 5 - just update VIX
html = html.replace(
    '<td>15.78</td>\n                    <td class="date-example">',
    f'<td>{format_vix(stats["row5_stayed_inside"]["vix_stats"])}</td>\n                    <td class="date-example">'
)

# Write updated HTML
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\MASTER_TRADING_TABLE.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ HTML updated with VIX and timing statistics!")
print("\nRow 1 (stayed within 10% above):")
print(f"  VIX: {stats['row1_stayed_within_10pct_above']['vix_stats']}")
print("\nRow 2 (went ≥10% above):")
print(f"  VIX: {stats['row2_went_10pct_above']['vix_stats']}")
print(f"  Timing: {stats['row2_went_10pct_above']['timing_stats']}")
print("\nRow 3 (stayed within 10% below):")
print(f"  VIX: {stats['row3_stayed_within_10pct_below']['vix_stats']}")
print("\nRow 4 (went ≥10% below):")
print(f"  VIX: {stats['row4_went_10pct_below']['vix_stats']}")
print(f"  Timing: {stats['row4_went_10pct_below']['timing_stats']}")
print("\nRow 5 (stayed inside):")
print(f"  VIX: {stats['row5_stayed_inside']['vix_stats']}")
