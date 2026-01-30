"""
Generate HTML table for Market Open Below analysis
"""
import json

# Load stats
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\open_below_stats.json', 'r') as f:
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

# Build table
total = stats['total_below_days']
touched = stats['touched_by_10am']
not_touched = stats['not_touched_by_10am']

# Get breakdown counts
touched_breakdown = touched.get('breakdown', {})
stayed_below = touched_breakdown.get('stayed_below', {'count': 0, 'prob': 0})
above_not_mid = touched_breakdown.get('above_not_mid', {'count': 0, 'prob': 0})
touched_mid = touched_breakdown.get('touched_mid', {'count': 0, 'prob': 0})
touched_high = touched_breakdown.get('touched_high', {'count': 0, 'prob': 0})

# 4th order for above_not_mid - EOD Retest
above_not_mid_eod = above_not_mid.get('eod_breakdown', {})
retested_low = above_not_mid_eod.get('retested', {'count': 0, 'prob': 0})
not_retested_low = above_not_mid_eod.get('not_retested', {'count': 0, 'prob': 0})

# Not touched by 10 AM breakdown - EOD touch
not_touched_breakdown = not_touched.get('breakdown', {})
touched_eod_nt = not_touched_breakdown.get('touched_eod', {'count': 0, 'prob': 0})
not_touched_eod_nt = not_touched_breakdown.get('not_touched_eod', {'count': 0, 'prob': 0})

table_html = f"""
    <!-- Market Open Below Table -->
    <div class="grid-container" style="margin-bottom: 40px;">
        <h2 style="padding: 15px 15px 0; margin:0; color:#2c3e50;">3. Market Open Below Analysis</h2>
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
                    <td rowspan="10"><strong>Open: Below<br>(Close < Prev Low)</strong><br><br>{total} days</td>
                    <td rowspan="6"><strong>Touched prev day low by 10 AM</strong></td>
                    <td rowspan="6" class="prob-medium"><strong>{touched['prob']}%</strong><br>({touched['count']})</td>
                    <td>Stayed below prev low</td>
                    <td class="prob-high">{stayed_below['prob']}%<br>({stayed_below['count']})</td>
                    <td>{format_vix(stayed_below.get('vix'))}</td>
                    <td>{format_timing(stayed_below.get('timing'))}</td>
                    <td class="date-example">{format_dates(stayed_below.get('dates', []))}</td>
                </tr>
                
                <!-- Above not mid with 4th order -->
                <tr>
                    <td rowspan="2" class="indent-1">Went above prev low but not to mid</td>
                    <td rowspan="2" class="prob-medium">{above_not_mid['prob']}%<br>({above_not_mid['count']})</td>
                    <td class="indent-2">Touched prev day low by EOD</td>
                    <td class="prob-low">{retested_low['prob']}%<br>({retested_low['count']})</td>
                    <td>{format_vix(retested_low.get('vix'))}</td>
                    <td>{format_timing(retested_low.get('timing'))}</td>
                    <td class="date-example">{format_dates(retested_low.get('dates', []))}</td>
                </tr>
                <tr>
                    <td class="indent-2">Did not touch prev day low by EOD</td>
                    <td class="prob-high">{not_retested_low['prob']}%<br>({not_retested_low['count']})</td>
                    <td>{format_vix(not_retested_low.get('vix'))}</td>
                    <td>{format_timing(not_retested_low.get('timing'))}</td>
                    <td class="date-example">{format_dates(not_retested_low.get('dates', []))}</td>
                </tr>
                
                <!-- Touched mid -->
                <tr>
                    <td>Went above to touch mid</td>
                    <td class="prob-medium">{touched_mid['prob']}%<br>({touched_mid['count']})</td>
                    <td>-</td>
                    <td>-</td>
                    <td>{format_vix(touched_mid.get('vix'))}</td>
                    <td>{format_timing(touched_mid.get('timing'))}</td>
                    <td class="date-example">{format_dates(touched_mid.get('dates', []))}</td>
                </tr>
                
                <!-- Touched high -->
                <tr>
                    <td>Went above to touch high</td>
                    <td class="prob-low">{touched_high['prob']}%<br>({touched_high['count']})</td>
                    <td>-</td>
                    <td>-</td>
                    <td>{format_vix(touched_high.get('vix'))}</td>
                    <td>{format_timing(touched_high.get('timing'))}</td>
                    <td class="date-example">{format_dates(touched_high.get('dates', []))}</td>
                </tr>
                
                <!-- Separator row -->
                <tr style="height: 10px; background-color: #f0f0f0;">
                    <td colspan="8"></td>
                </tr>
                
                <!-- Did NOT touch by 10 AM -->
                <tr class="scenario-header">
                    <td rowspan="2"><strong>Did NOT touch prev low by 10 AM</strong></td>
                    <td rowspan="2" class="prob-high"><strong>{not_touched['prob']}%</strong><br>({not_touched['count']})</td>
                    <td>Touched prev day low by EOD</td>
                    <td class="prob-medium">{touched_eod_nt['prob']}%<br>({touched_eod_nt['count']})</td>
                    <td>{format_vix(touched_eod_nt.get('vix'))}</td>
                    <td>{format_timing(touched_eod_nt.get('timing'))}</td>
                    <td class="date-example">{format_dates(touched_eod_nt.get('dates', []))}</td>
                </tr>
                <tr>
                    <td>Did not touch prev day low by EOD</td>
                    <td class="prob-high">{not_touched_eod_nt['prob']}%<br>({not_touched_eod_nt['count']})</td>
                    <td>{format_vix(not_touched_eod_nt.get('vix'))}</td>
                    <td>{format_timing(not_touched_eod_nt.get('timing'))}</td>
                    <td class="date-example">{format_dates(not_touched_eod_nt.get('dates', []))}</td>
                </tr>
            </tbody>
        </table>
    </div>
"""

# Save to file
with open(r'results\probability_grid\MARKET_OPEN_BELOW_TABLE.html', 'w', encoding='utf-8') as f:
    f.write(table_html)
    print("Market Open Below table generated in results/probability_grid/MARKET_OPEN_BELOW_TABLE.html")
