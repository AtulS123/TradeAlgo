"""
Generate HTML table for Market Open Above analysis
"""
import json

# Load stats
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\open_above_stats.json', 'r') as f:
    stats = json.load(f)

# Helper functions
def format_vix(vix_stats):
    if vix_stats is None:
        return "N/A"
    return f"min: {vix_stats['min']}<br>max: {vix_stats['max']}<br>median: {vix_stats['median']}<br>avg: {vix_stats['avg']}"

def format_timing(timing_stats):
    if timing_stats is None:
        return "N/A"
    return f"min: {timing_stats['min']}m<br>max: {timing_stats['max']}m<br>median: {timing_stats['median']}m<br>avg: {timing_stats['avg']}m"

def format_dates(dates_list):
    return '<br>'.join(dates_list) if dates_list else "N/A"

# HTML template
html_start = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Market Open Above Analysis</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .grid-container { background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; margin-bottom: 30px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; border-right: 1px solid #eee; font-size: 14px; vertical-align: top; }
        th { background-color: #e74c3c; color: white; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }
        tr:last-child td { border-bottom: none; }
        .scenario-header { background-color: #f8f9fa; font-weight: 600; color: #2c3e50; border-top: 2px solid #e9ecef; }
        .prob-high { background-color: #d4edda; color: #155724; font-weight: bold; }
        .prob-medium { background-color: #fff3cd; color: #856404; font-weight: bold; }
        .prob-low { background-color: #f8d7da; color: #721c24; font-weight: bold; }
        .date-example { font-family: 'Consolas', monospace; font-size: 11px; color: #666; white-space: nowrap; }
        h2 { padding: 15px; margin: 0; color: #2c3e50; }
        .indent-1 { padding-left: 30px; }
        .indent-2 { padding-left: 50px; }
        .indent-3 { padding-left: 70px; }
    </style>
</head>
<body>
"""

html_end = """
</body>
</html>
"""

# Build table
total = stats['total_above_days']
touched = stats['touched_by_10am']
not_touched = stats['not_touched_by_10am']

# Get breakdown counts
touched_breakdown = touched.get('breakdown', {})
stayed_above = touched_breakdown.get('stayed_above', {'count': 0, 'prob': 0})
below_not_mid = touched_breakdown.get('below_not_mid', {'count': 0, 'prob': 0})
touched_mid = touched_breakdown.get('touched_mid', {'count': 0, 'prob': 0})
touched_low = touched_breakdown.get('touched_low', {'count': 0, 'prob': 0})

# 4th order for below_not_mid - EOD touch
below_not_mid_eod = below_not_mid.get('eod_breakdown', {})
touched_eod_bnm = below_not_mid_eod.get('touched_eod', {'count': 0, 'prob': 0})
not_touched_eod_bnm = below_not_mid_eod.get('not_touched_eod', {'count': 0, 'prob': 0})

# Not touched by 10 AM breakdown - EOD touch
not_touched_breakdown = not_touched.get('breakdown', {})
touched_eod_nt = not_touched_breakdown.get('touched_eod', {'count': 0, 'prob': 0})
not_touched_eod_nt = not_touched_breakdown.get('not_touched_eod', {'count': 0, 'prob': 0})

table_html = f"""
    <div class="grid-container">
        <h2>Market Open Above Analysis (First 5-min Candle Close Above Prev High)</h2>
        <table>
            <thead>
                <tr>
                    <th style="width: 20%">Opening Position</th>
                    <th style="width: 15%">2nd Order Move</th>
                    <th style="width: 15%">% (Days)</th>
                    <th style="width: 15%">3rd Order Move</th>
                    <th style="width: 8%">% (Days)</th>
                    <th style="width: 10%">VIX Stats</th>
                    <th style="width: 10%">Timing</th>
                    <th style="width: 12%">Example Dates</th>
                </tr>
            </thead>
            <tbody>
                <!-- Main Row -->
                <tr class="scenario-header">
                    <td rowspan="10"><strong>Open: Above<br>(Close > Prev High)</strong><br><br>{total} days</td>
                    <td rowspan="6"><strong>Touched prev day high by 10 AM</strong></td>
                    <td rowspan="6" class="prob-medium"><strong>{touched['prob']}%</strong><br>({touched['count']})</td>
                    <td>Stayed above prev high</td>
                    <td class="prob-high">{stayed_above['prob']}%<br>({stayed_above['count']})</td>
                    <td>{format_vix(stayed_above.get('vix'))}</td>
                    <td>{format_timing(stayed_above.get('timing'))}</td>
                    <td class="date-example">{format_dates(stayed_above.get('dates', []))}</td>
                </tr>
                
                <!-- Below not mid with 4th order -->
                <tr>
                    <td rowspan="2" class="indent-1">Went below prev high but not to mid</td>
                    <td rowspan="2" class="prob-medium">{below_not_mid['prob']}%<br>({below_not_mid['count']})</td>
                    <td class="indent-2">Touched prev day high by EOD</td>
                    <td class="prob-low">{touched_eod_bnm['prob']}%<br>({touched_eod_bnm['count']})</td>
                    <td>{format_vix(touched_eod_bnm.get('vix'))}</td>
                    <td>{format_timing(touched_eod_bnm.get('timing'))}</td>
                    <td class="date-example">{format_dates(touched_eod_bnm.get('dates', []))}</td>
                </tr>
                <tr>
                    <td class="indent-2">Did not touch prev day high by EOD</td>
                    <td class="prob-high">{not_touched_eod_bnm['prob']}%<br>({not_touched_eod_bnm['count']})</td>
                    <td>{format_vix(not_touched_eod_bnm.get('vix'))}</td>
                    <td>{format_timing(not_touched_eod_bnm.get('timing'))}</td>
                    <td class="date-example">{format_dates(not_touched_eod_bnm.get('dates', []))}</td>
                </tr>
                
                <!-- Touched mid -->
                <tr>
                    <td>Went below to touch mid</td>
                    <td class="prob-medium">{touched_mid['prob']}%<br>({touched_mid['count']})</td>
                    <td>-</td>
                    <td>-</td>
                    <td>{format_vix(touched_mid.get('vix'))}</td>
                    <td>{format_timing(touched_mid.get('timing'))}</td>
                    <td class="date-example">{format_dates(touched_mid.get('dates', []))}</td>
                </tr>
                
                <!-- Touched low -->
                <tr>
                    <td>Went below to touch low</td>
                    <td class="prob-low">{touched_low['prob']}%<br>({touched_low['count']})</td>
                    <td>-</td>
                    <td>-</td>
                    <td>{format_vix(touched_low.get('vix'))}</td>
                    <td>{format_timing(touched_low.get('timing'))}</td>
                    <td class="date-example">{format_dates(touched_low.get('dates', []))}</td>
                </tr>
                
                <!-- Separator row -->
                <tr style="height: 10px; background-color: #f0f0f0;">
                    <td colspan="8"></td>
                </tr>
                
                <!-- Did NOT touch by 10 AM -->
                <tr class="scenario-header">
                    <td rowspan="2"><strong>Did NOT touch prev high by 10 AM</strong></td>
                    <td rowspan="2" class="prob-high"><strong>{not_touched['prob']}%</strong><br>({not_touched['count']})</td>
                    <td>Touched prev day high by EOD</td>
                    <td class="prob-medium">{touched_eod_nt['prob']}%<br>({touched_eod_nt['count']})</td>
                    <td>{format_vix(touched_eod_nt.get('vix'))}</td>
                    <td>{format_timing(touched_eod_nt.get('timing'))}</td>
                    <td class="date-example">{format_dates(touched_eod_nt.get('dates', []))}</td>
                </tr>
                <tr>
                    <td>Did not touch prev day high by EOD</td>
                    <td class="prob-high">{not_touched_eod_nt['prob']}%<br>({not_touched_eod_nt['count']})</td>
                    <td>{format_vix(not_touched_eod_nt.get('vix'))}</td>
                    <td>{format_timing(not_touched_eod_nt.get('timing'))}</td>
                    <td class="date-example">{format_dates(not_touched_eod_nt.get('dates', []))}</td>
                </tr>
            </tbody>
        </table>
    </div>
"""

# Generate full HTML
full_html = html_start + table_html + html_end

# Save
output_path = r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\MARKET_OPEN_ABOVE_TABLE.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(full_html)

print(f"✅ HTML table generated: {output_path}")
