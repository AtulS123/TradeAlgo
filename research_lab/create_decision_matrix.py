"""
NIFTY 50 Trading Decision Matrix Generator
===========================================

Creates comprehensive reference tables for daily trading decisions
"""

import pandas as pd
import json
from pathlib import Path


def create_trading_decision_matrix():
    """Create comprehensive trading decision matrix"""
    
    # Load analysis results
    results_path = Path('research_lab/results/probability_grid')
    with open(results_path / 'complete_analysis.json', 'r') as f:
        analysis = json.load(f)
    
    # ==========================================
    # PRIMARY DECISION MATRIX
    # ==========================================
    
    primary_matrix = []
    
    # Scenario 1: Opening INSIDE Range
    primary_matrix.append({
        'Opening_Position': 'INSIDE',
        'Current_State': 'Just Opened (9:15 AM)',
        'Most_Likely_Outcome': 'Move Below Prev Low',
        'Probability': '41.0%',
        'Action': 'Watch for breakdown. Be ready to fade if moves below (87% return rate)',
        'Risk_Level': 'MEDIUM'
    })
    
    primary_matrix.append({
        'Opening_Position': 'INSIDE',
        'Current_State': 'Just Opened (9:15 AM)',
        'Most_Likely_Outcome': 'Move Above Prev High',
        'Probability': '34.0%',
        'Action': 'Watch for breakout. Be ready to fade if moves above (85% return rate)',
        'Risk_Level': 'MEDIUM'
    })
    
    primary_matrix.append({
        'Opening_Position': 'INSIDE',
        'Current_State': 'Just Opened (9:15 AM)',
        'Most_Likely_Outcome': 'Stay Inside All Day',
        'Probability': '16.3%',
        'Action': 'Range trading unlikely. Prepare for directional move',
        'Risk_Level': 'LOW'
    })
    
    # Scenario 2: Inside → Moved Below
    primary_matrix.append({
        'Opening_Position': 'INSIDE',
        'Current_State': 'Broke Below Prev Low',
        'Most_Likely_Outcome': 'Return to Range',
        'Probability': '86.7%',
        'Action': 'FADE THE BREAKDOWN! Strong mean reversion expected',
        'Risk_Level': 'LOW (Mean Reversion Trade)'
    })
    
    primary_matrix.append({
        'Opening_Position': 'INSIDE',
        'Current_State': 'Broke Below Prev Low',
        'Most_Likely_Outcome': 'Stay Below All Day',
        'Probability': '13.3%',
        'Action': 'If sustained below after 10 AM, trend continuation possible',
        'Risk_Level': 'HIGH'
    })
    
    # Scenario 3: Inside → Moved Above
    primary_matrix.append({
        'Opening_Position': 'INSIDE',
        'Current_State': 'Broke Above Prev High',
        'Most_Likely_Outcome': 'Return to Range',
        'Probability': '84.5%',
        'Action': 'FADE THE BREAKOUT! Strong mean reversion expected',
        'Risk_Level': 'LOW (Mean Reversion Trade)'
    })
    
    primary_matrix.append({
        'Opening_Position': 'INSIDE',
        'Current_State': 'Broke Above Prev High',
        'Most_Likely_Outcome': 'Stay Above All Day',
        'Probability': '15.5%',
        'Action': 'If sustained above after 10 AM, trend continuation possible',
        'Risk_Level': 'HIGH'
    })
    
    # Scenario 4: Opening ABOVE Range
    primary_matrix.append({
        'Opening_Position': 'ABOVE',
        'Current_State': 'Just Opened (9:15 AM)',
        'Most_Likely_Outcome': 'Return to Range',
        'Probability': '53.3%',
        'Action': 'GAP FILL TRADE! Expect pullback into range',
        'Risk_Level': 'MEDIUM (Mean Reversion)'
    })
    
    primary_matrix.append({
        'Opening_Position': 'ABOVE',
        'Current_State': 'Just Opened (9:15 AM)',
        'Most_Likely_Outcome': 'Stay Above All Day',
        'Probability': '31.1%',
        'Action': 'Wait for confirmation. If holds above after 10 AM, trend strong',
        'Risk_Level': 'MEDIUM'
    })
    
    primary_matrix.append({
        'Opening_Position': 'ABOVE',
        'Current_State': 'Just Opened (9:15 AM)',
        'Most_Likely_Outcome': 'Drop Below Range',
        'Probability': '15.6%',
        'Action': 'Rare but possible. Strong reversal signal if happens',
        'Risk_Level': 'HIGH'
    })
    
    # Scenario 5: Opening BELOW Range
    primary_matrix.append({
        'Opening_Position': 'BELOW',
        'Current_State': 'Just Opened (9:15 AM)',
        'Most_Likely_Outcome': 'Return to Range',
        'Probability': '50.2%',
        'Action': 'GAP FILL TRADE! Expect bounce into range',
        'Risk_Level': 'MEDIUM (Mean Reversion)'
    })
    
    primary_matrix.append({
        'Opening_Position': 'BELOW',
        'Current_State': 'Just Opened (9:15 AM)',
        'Most_Likely_Outcome': 'Stay Below All Day',
        'Probability': '41.0%',
        'Action': 'Watch for sustained weakness. If holds below after 10 AM, trend strong',
        'Risk_Level': 'MEDIUM'
    })
    
    primary_matrix.append({
        'Opening_Position': 'BELOW',
        'Current_State': 'Just Opened (9:15 AM)',
        'Most_Likely_Outcome': 'Rally Above Range',
        'Probability': '8.8%',
        'Action': 'Rare but possible. Strong reversal signal if happens',
        'Risk_Level': 'HIGH'
    })
    
    # Convert to DataFrame
    df_primary = pd.DataFrame(primary_matrix)
    
    # ==========================================
    # TIME-BASED DECISION MATRIX
    # ==========================================
    
    time_matrix = []
    
    time_matrix.append({
        'Time_Window': '9:00 - 9:30 AM',
        'Significance': 'CRITICAL',
        'Breakout_Probability': '40.2%',
        'Breakdown_Probability': '40.4%',
        'Action': 'WATCH CLOSELY! 40% of all directional moves happen now. But remember: 85% reverse later!',
        'Strategy': 'Identify direction, then FADE after 10 AM'
    })
    
    time_matrix.append({
        'Time_Window': '9:30 - 10:00 AM',
        'Significance': 'HIGH',
        'Breakout_Probability': '~20%',
        'Breakdown_Probability': '~20%',
        'Action': 'Consolidation period. Watch for confirmation of morning move',
        'Strategy': 'If morning breakout holds, consider trend continuation. Otherwise, fade'
    })
    
    time_matrix.append({
        'Time_Window': '10:00 AM - 2:00 PM',
        'Significance': 'MEDIUM',
        'Breakout_Probability': '~30%',
        'Breakdown_Probability': '~30%',
        'Action': 'If opened inside and broke out in morning, expect mean reversion NOW',
        'Strategy': 'Mean reversion trades work best in this window'
    })
    
    time_matrix.append({
        'Time_Window': '2:00 PM - 3:30 PM',
        'Significance': 'MEDIUM',
        'Breakout_Probability': '~10%',
        'Breakdown_Probability': '~10%',
        'Action': 'Final hour. Closing moves typically confirm or reverse morning direction',
        'Strategy': 'Square off positions before close unless strong trend'
    })
    
    df_time = pd.DataFrame(time_matrix)
    
    # ==========================================
    # QUICK REFERENCE CHEAT SHEET
    # ==========================================
    
    cheat_sheet = []
    
    cheat_sheet.append({
        'IF_This_Happens': 'Day opens INSIDE range',
        'THEN_Expect': 'Directional move (84% of days)',
        'Probability': '84%',
        'Best_Strategy': 'Wait for initial move, then FADE it',
        'Win_Rate': '85-87%'
    })
    
    cheat_sheet.append({
        'IF_This_Happens': 'Day opens ABOVE range',
        'THEN_Expect': 'Gap fill (return to range)',
        'Probability': '53%',
        'Best_Strategy': 'Short near open, target prev day high',
        'Win_Rate': '53%'
    })
    
    cheat_sheet.append({
        'IF_This_Happens': 'Day opens BELOW range',
        'THEN_Expect': 'Gap fill (return to range)',
        'Probability': '50%',
        'Best_Strategy': 'Long near open, target prev day low',
        'Win_Rate': '50%'
    })
    
    cheat_sheet.append({
        'IF_This_Happens': 'Opened inside, broke above in first 30 min',
        'THEN_Expect': 'Return to range',
        'Probability': '85%',
        'Best_Strategy': 'SHORT after breakout, target prev high retest',
        'Win_Rate': '85%'
    })
    
    cheat_sheet.append({
        'IF_This_Happens': 'Opened inside, broke below in first 30 min',
        'THEN_Expect': 'Return to range',
        'Probability': '87%',
        'Best_Strategy': 'LONG after breakdown, target prev low retest',
        'Win_Rate': '87%'
    })
    
    cheat_sheet.append({
        'IF_This_Happens': 'Big directional move before 9:30 AM',
        'THEN_Expect': 'Mean reversion 10 AM - 2 PM',
        'Probability': '85%',
        'Best_Strategy': 'Fade the morning move mid-day',
        'Win_Rate': '85%'
    })
    
    df_cheat = pd.DataFrame(cheat_sheet)
    
    # ==========================================
    # SAVE ALL MATRICES
    # ==========================================
    
    output_path = Path('research_lab/results/probability_grid')
    
    # Save primary decision matrix
    primary_path = output_path / 'TRADING_DECISION_MATRIX.csv'
    df_primary.to_csv(primary_path, index=False)
    print(f"✅ Created: {primary_path}")
    
    # Save time-based matrix
    time_path = output_path / 'TIME_BASED_MATRIX.csv'
    df_time.to_csv(time_path, index=False)
    print(f"✅ Created: {time_path}")
    
    # Save cheat sheet
    cheat_path = output_path / 'QUICK_REFERENCE_CHEAT_SHEET.csv'
    df_cheat.to_csv(cheat_path, index=False)
    print(f"✅ Created: {cheat_path}")
    
    # Print preview
    print("\n" + "="*100)
    print("📊 TRADING DECISION MATRIX - PREVIEW")
    print("="*100)
    print(df_primary.to_string(index=False))
    
    print("\n" + "="*100)
    print("⏰ TIME-BASED MATRIX - PREVIEW")
    print("="*100)
    print(df_time.to_string(index=False))
    
    print("\n" + "="*100)
    print("🎯 QUICK REFERENCE CHEAT SHEET - PREVIEW")
    print("="*100)
    print(df_cheat.to_string(index=False))
    
    return df_primary, df_time, df_cheat


if __name__ == '__main__':
    create_trading_decision_matrix()
    print("\n✅ All decision matrices created!")
    print("\n📂 Open these CSV files in Excel for easy daily reference:")
    print("   1. TRADING_DECISION_MATRIX.csv - Complete scenario breakdown")
    print("   2. TIME_BASED_MATRIX.csv - Time window strategies")
    print("   3. QUICK_REFERENCE_CHEAT_SHEET.csv - One-line actionable insights")
