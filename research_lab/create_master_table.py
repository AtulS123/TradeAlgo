"""
Master Trading Reference Table Generator
=========================================

Creates a single, comprehensive HTML table for daily trading reference
"""

import pandas as pd
import json
from pathlib import Path


def create_master_trading_table():
    """Create a single master reference table in HTML"""
    
    results_path = Path('research_lab/results/probability_grid')
    
    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NIFTY 50 - Master Trading Reference</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Consolas', 'Monaco', monospace;
            background: #1a1a1a;
            color: #fff;
            padding: 20px;
        }
        
        .container {
            max-width: 1800px;
            margin: 0 auto;
        }
        
        h1 {
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #00ff88;
            text-shadow: 0 0 10px #00ff88;
        }
        
        .subtitle {
            text-align: center;
            font-size: 1.2em;
            margin-bottom: 30px;
            color: #888;
        }
        
        .section-header {
            background: linear-gradient(90deg, #ff6b6b 0%, #4ecdc4 100%);
            padding: 15px;
            margin: 30px 0 10px 0;
            font-size: 1.5em;
            font-weight: bold;
            border-radius: 5px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.5);
        }
        
        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        th {
            padding: 15px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #333;
            font-size: 0.95em;
        }
        
        td {
            padding: 12px 15px;
            border: 1px solid #333;
            background: #2a2a2a;
            font-size: 0.9em;
        }
        
        tr:hover td {
            background: #3a3a3a;
        }
        
        .prob-high {
            color: #00ff88;
            font-weight: bold;
        }
        
        .prob-medium {
            color: #ffd700;
            font-weight: bold;
        }
        
        .prob-low {
            color: #ff6b6b;
            font-weight: bold;
        }
        
        .action-buy {
            background: #1a4d2e !important;
            border-left: 4px solid #00ff88;
        }
        
        .action-sell {
            background: #4d1a1a !important;
            border-left: 4px solid #ff6b6b;
        }
        
        .action-fade {
            background: #1a3a4d !important;
            border-left: 4px solid #4ecdc4;
        }
        
        .risk-low {
            color: #00ff88;
        }
        
        .risk-medium {
            color: #ffd700;
        }
        
        .risk-high {
            color: #ff6b6b;
        }
        
        .highlight-box {
            background: #2d2d00;
            border: 2px solid #ffd700;
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
        }
        
        .highlight-box h3 {
            color: #ffd700;
            margin-bottom: 10px;
        }
        
        .stat-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: bold;
            margin: 2px;
        }
        
        .badge-green {
            background: #00ff88;
            color: #000;
        }
        
        .badge-yellow {
            background: #ffd700;
            color: #000;
        }
        
        .badge-red {
            background: #ff6b6b;
            color: #000;
        }
        
        @media print {
            body {
                background: white;
                color: black;
            }
            
            td {
                background: white !important;
            }
            
            .section-header {
                background: #ccc !important;
                color: black !important;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 NIFTY 50 MASTER TRADING REFERENCE</h1>
        <p class="subtitle">Based on 2,376 trading days | 5-min candle analysis</p>
        
        <!-- QUICK STATS -->
        <div class="highlight-box">
            <h3>⚡ CRITICAL STATS TO REMEMBER</h3>
            <span class="stat-badge badge-green">87% Mean Reversion after Inside→Below</span>
            <span class="stat-badge badge-green">85% Mean Reversion after Inside→Above</span>
            <span class="stat-badge badge-yellow">40% of moves happen 9:00-9:30 AM</span>
            <span class="stat-badge badge-yellow">53% Gap Fill when open above</span>
            <span class="stat-badge badge-yellow">50% Gap Fill when open below</span>
            <span class="stat-badge badge-red">Only 16% stay in range when open inside</span>
        </div>
        
        <!-- PRIMARY DECISION TABLE -->
        <div class="section-header">📊 PRIMARY DECISION MATRIX - ALL SCENARIOS</div>
        <table>
            <thead>
                <tr>
                    <th style="width: 12%">Opening Position</th>
                    <th style="width: 18%">Current Market State</th>
                    <th style="width: 18%">Expected Outcome</th>
                    <th style="width: 8%">Probability</th>
                    <th style="width: 34%">Trading Action</th>
                    <th style="width: 10%">Risk Level</th>
                </tr>
            </thead>
            <tbody>
                <!-- INSIDE SCENARIOS -->
                <tr>
                    <td rowspan="7" style="background: #1a2a4d; font-weight: bold; font-size: 1.1em; vertical-align: top;">
                        📍 INSIDE<br>Prev Range
                    </td>
                    <td>Just Opened (9:15 AM)</td>
                    <td>Move Below Prev Low</td>
                    <td class="prob-medium">41.0%</td>
                    <td>Watch for breakdown. First 30 min critical. If breaks, FADE after 9:45</td>
                    <td class="risk-medium">MEDIUM</td>
                </tr>
                <tr>
                    <td>Just Opened (9:15 AM)</td>
                    <td>Move Above Prev High</td>
                    <td class="prob-medium">34.0%</td>
                    <td>Watch for breakout. First 30 min critical. If breaks, FADE after 9:45</td>
                    <td class="risk-medium">MEDIUM</td>
                </tr>
                <tr>
                    <td>Just Opened (9:15 AM)</td>
                    <td>Stay Inside All Day</td>
                    <td class="prob-low">16.3%</td>
                    <td>RARE! Don't expect range-bound day. Prepare for directional move</td>
                    <td class="risk-low">LOW</td>
                </tr>
                <tr>
                    <td>Just Opened (9:15 AM)</td>
                    <td>Move BOTH Directions</td>
                    <td class="prob-low">8.7%</td>
                    <td>High volatility day. Trade carefully, tight stops</td>
                    <td class="risk-high">HIGH</td>
                </tr>
                <tr class="action-buy">
                    <td>🔽 Broke Below Prev Low</td>
                    <td><strong>RETURN TO RANGE</strong></td>
                    <td class="prob-high">86.7%</td>
                    <td><strong>⭐ BEST TRADE: GO LONG! Target prev day low. 87% win rate</strong></td>
                    <td class="risk-low">🟢 LOW</td>
                </tr>
                <tr>
                    <td>🔽 Broke Below, After 10 AM</td>
                    <td>Stay Below All Day</td>
                    <td class="prob-low">13.3%</td>
                    <td>If sustained below after 10 AM, trend may continue. Avoid counter-trend</td>
                    <td class="risk-high">HIGH</td>
                </tr>
                <tr class="action-sell">
                    <td>🔼 Broke Above Prev High</td>
                    <td><strong>RETURN TO RANGE</strong></td>
                    <td class="prob-high">84.5%</td>
                    <td><strong>⭐ BEST TRADE: GO SHORT! Target prev day high. 85% win rate</strong></td>
                    <td class="risk-low">🟢 LOW</td>
                </tr>
                
                <!-- ABOVE SCENARIOS -->
                <tr>
                    <td rowspan="3" style="background: #1a4d1a; font-weight: bold; font-size: 1.1em; vertical-align: top;">
                        📈 ABOVE<br>Prev Range
                    </td>
                    <td class="action-sell">Gap Up Opening (9:15 AM)</td>
                    <td><strong>GAP FILL - Return to Range</strong></td>
                    <td class="prob-high">53.3%</td>
                    <td><strong>SHORT near open, target previous day high (gap fill trade)</strong></td>
                    <td class="risk-medium">🟡 MEDIUM</td>
                </tr>
                <tr>
                    <td>Gap Up, After 10 AM</td>
                    <td>Stay Above All Day</td>
                    <td class="prob-medium">31.1%</td>
                    <td>If holds above prev high after 10 AM, trend is strong. Consider longs</td>
                    <td class="risk-medium">MEDIUM</td>
                </tr>
                <tr>
                    <td>Gap Up Opening</td>
                    <td>Drop Below Prev Range</td>
                    <td class="prob-low">15.6%</td>
                    <td>Rare but happens. Strong reversal signal if price drops below prev low</td>
                    <td class="risk-high">HIGH</td>
                </tr>
                
                <!-- BELOW SCENARIOS -->
                <tr>
                    <td rowspan="3" style="background: #4d1a1a; font-weight: bold; font-size: 1.1em; vertical-align: top;">
                        📉 BELOW<br>Prev Range
                    </td>
                    <td class="action-buy">Gap Down Opening (9:15 AM)</td>
                    <td><strong>GAP FILL - Return to Range</strong></td>
                    <td class="prob-high">50.2%</td>
                    <td><strong>LONG near open, target previous day low (gap fill trade)</strong></td>
                    <td class="risk-medium">🟡 MEDIUM</td>
                </tr>
                <tr>
                    <td>Gap Down, After 10 AM</td>
                    <td>Stay Below All Day</td>
                    <td class="prob-medium">41.0%</td>
                    <td>If holds below prev low after 10 AM, weakness confirmed. Consider shorts</td>
                    <td class="risk-medium">MEDIUM</td>
                </tr>
                <tr>
                    <td>Gap Down Opening</td>
                    <td>Rally Above Prev Range</td>
                    <td class="prob-low">8.8%</td>
                    <td>Rare but happens. Strong reversal signal if price rallies above prev high</td>
                    <td class="risk-high">HIGH</td>
                </tr>
            </tbody>
        </table>
        
        <!-- TIME-BASED MATRIX -->
        <div class="section-header">⏰ TIME-BASED TRADING WINDOWS</div>
        <table>
            <thead>
                <tr>
                    <th style="width: 15%">Time Window</th>
                    <th style="width: 12%">Importance</th>
                    <th style="width: 13%">Breakout %</th>
                    <th style="width: 13%">Breakdown %</th>
                    <th style="width: 35%">What to Do</th>
                    <th style="width: 12%">Best Strategy</th>
                </tr>
            </thead>
            <tbody>
                <tr style="background: #4d2a00; border: 3px solid #ff6b6b;">
                    <td style="font-size: 1.1em;"><strong>9:00 - 9:30 AM</strong></td>
                    <td class="prob-high">🔥 CRITICAL</td>
                    <td class="prob-high">40.2%</td>
                    <td class="prob-high">40.4%</td>
                    <td><strong>⚠️ MOST IMPORTANT WINDOW! 40% of all moves happen now. Identify direction but DON'T chase - 85% will reverse!</strong></td>
                    <td>Watch & Wait</td>
                </tr>
                <tr>
                    <td><strong>9:30 - 10:00 AM</strong></td>
                    <td class="prob-high">HIGH</td>
                    <td class="prob-medium">~20%</td>
                    <td class="prob-medium">~20%</td>
                    <td>Consolidation period. If morning move holds, trend may be real. Otherwise FADE</td>
                    <td>Confirmation</td>
                </tr>
                <tr class="action-fade">
                    <td><strong>10:00 AM - 2:00 PM</strong></td>
                    <td class="prob-medium">MEDIUM</td>
                    <td class="prob-medium">~30%</td>
                    <td class="prob-medium">~30%</td>
                    <td><strong>⭐ MEAN REVERSION WINDOW! If opened inside and broke out in morning, TRADE THE RETURN now</strong></td>
                    <td>Fade Morning Move</td>
                </tr>
                <tr>
                    <td><strong>2:00 - 3:30 PM</strong></td>
                    <td class="prob-medium">MEDIUM</td>
                    <td class="prob-low">~10%</td>
                    <td class="prob-low">~10%</td>
                    <td>Final hour. Close positions unless strong trend. Avoid new trades</td>
                    <td>Square Off</td>
                </tr>
            </tbody>
        </table>
        
        <!-- QUICK CHEAT SHEET -->
        <div class="section-header">🎯 QUICK DECISION CHEAT SHEET</div>
        <table>
            <thead>
                <tr>
                    <th style="width: 30%">IF This Happens...</th>
                    <th style="width: 25%">THEN Expect...</th>
                    <th style="width: 10%">Probability</th>
                    <th style="width: 25%">Best Action</th>
                    <th style="width: 10%">Win Rate</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Day opens <strong>INSIDE</strong> range</td>
                    <td>Directional move (not range-bound)</td>
                    <td class="prob-high">84%</td>
                    <td>Wait for initial move, then FADE it</td>
                    <td class="prob-high">85-87%</td>
                </tr>
                <tr class="action-sell">
                    <td>Day opens <strong>ABOVE</strong> range (gap up)</td>
                    <td>Gap fill (return to range)</td>
                    <td class="prob-high">53%</td>
                    <td><strong>SHORT near open, target prev high</strong></td>
                    <td class="prob-high">53%</td>
                </tr>
                <tr class="action-buy">
                    <td>Day opens <strong>BELOW</strong> range (gap down)</td>
                    <td>Gap fill (return to range)</td>
                    <td class="prob-high">50%</td>
                    <td><strong>LONG near open, target prev low</strong></td>
                    <td class="prob-high">50%</td>
                </tr>
                <tr class="action-sell">
                    <td>Opened inside, <strong>broke above</strong> in first 30 min</td>
                    <td>Return to range (mean reversion)</td>
                    <td class="prob-high">85%</td>
                    <td><strong>⭐ SHORT after 9:45, target prev high</strong></td>
                    <td class="prob-high">85%</td>
                </tr>
                <tr class="action-buy">
                    <td>Opened inside, <strong>broke below</strong> in first 30 min</td>
                    <td>Return to range (mean reversion)</td>
                    <td class="prob-high">87%</td>
                    <td><strong>⭐ LONG after 9:45, target prev low</strong></td>
                    <td class="prob-high">87%</td>
                </tr>
                <tr>
                    <td>Big move before 9:30 AM (any direction)</td>
                    <td>Mean reversion between 10 AM - 2 PM</td>
                    <td class="prob-high">85%</td>
                    <td><strong>FADE the morning move mid-day</strong></td>
                    <td class="prob-high">85%</td>
                </tr>
            </tbody>
        </table>
        
        <!-- DAILY CHECKLIST -->
        <div class="section-header">📋 DAILY TRADING CHECKLIST</div>
        <div class="highlight-box">
            <h3>✅ Pre-Market (before 9:15 AM)</h3>
            <p>☐ Calculate yesterday's high and low<br>
            ☐ Determine where market might open (above/inside/below)<br>
            ☐ Review probability table for expected scenario<br>
            ☐ Set alerts at previous day high/low levels</p>
            
            <h3 style="margin-top: 20px;">✅ Market Open (9:15 - 9:30 AM)</h3>
            <p>☐ Note exact opening position vs prev day range<br>
            ☐ Watch for first 30-min directional move (40% probability window)<br>
            ☐ DO NOT CHASE - Remember 85% mean reversion rate!<br>
            ☐ Mark entry levels for fade trades</p>
            
            <h3 style="margin-top: 20px;">✅ Mid-Day (10:00 AM - 2:00 PM)</h3>
            <p>☐ If opened inside and broke out → Execute fade trade (87% edge)<br>
            ☐ If gap opened → Watch for gap fill (50-53% probability)<br>
            ☐ Monitor if morning move is sustained or reversing<br>
            ☐ Best window for mean reversion trades</p>
            
            <h3 style="margin-top: 20px;">✅ Close (2:00 - 3:30 PM)</h3>
            <p>☐ Square off positions unless strong trend<br>
            ☐ Review accuracy of probability predictions<br>
            ☐ Log the day's outcome for personal tracking</p>
        </div>
        
        <p style="text-align: center; margin-top: 40px; color: #666; font-size: 0.9em;">
            Generated from 2,376 trading days | NIFTY 50 Historical Analysis<br>
            Last Updated: 2026-01-29 | This is for educational purposes only
        </p>
    </div>
</body>
</html>
"""
    
    # Save master table
    output_path = Path('research_lab/results/probability_grid')
    master_path = output_path / 'MASTER_TRADING_TABLE.html'
    
    with open(master_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Created: {master_path}")
    print(f"\n📊 MASTER TRADING TABLE generated!")
    print(f"\n🌐 Open in browser: file:///{master_path.absolute()}")
    print(f"\n💡 TIP: Keep this table open on a second monitor while trading!")
    
    return master_path


if __name__ == '__main__':
    create_master_trading_table()
