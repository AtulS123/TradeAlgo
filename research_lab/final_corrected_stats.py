"""
Final Corrected VIX & Timing Statistics Calculation
Fixes:
1. Calculates Prev Day Levels on FULL dataset (including Special Trading Days)
2. Filters for Normal Trading Days (9:15 start) for analysis
3. Uses Full Day High/Low for classification
4. Splits Row 2 and Row 4 into Direct vs Retraced moves
5. Implements Detailed Closing Analysis (Close Above/Below) with 10AM logic
"""
import pandas as pd
import numpy as np
import json
from datetime import time

# 0. Load Data
vix = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\INDIA VIX_minute.csv')

# Preprocess
df_raw = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv')
df_raw['datetime'] = pd.to_datetime(df_raw['date'])
df_raw = df_raw.set_index('datetime')

# Resample to 5-min
# Market starts 9:15. 5T bins usually align to 9:15.
# closed='left', label='left' -> 9:15:00 includes 9:15 data and labeled 9:15.
df_5min_full = df_raw.resample('5T', closed='left', label='left').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last'
}).dropna()

df_5min_full = df_5min_full.reset_index()
df_5min_full['date'] = df_5min_full['datetime'].dt.date
df_5min_full['time'] = df_5min_full['datetime'].dt.time
# Minutes from 9:15 (0, 5, 10...)
df_5min_full['minutes_since_915'] = (df_5min_full['datetime'].dt.hour * 60 + df_5min_full['datetime'].dt.minute) - (9 * 60 + 15)

# Filter out empty or non-market hours if any (though dropna usually handles empty)
# Ensure we only keep rows where minutes_since_915 >= 0
df_5min_full = df_5min_full[df_5min_full['minutes_since_915'] >= 0]


# 1. Daily Aggregation on FULL dataset
daily_full = df_5min_full.groupby('date').agg({
    'high': 'max',
    'low': 'min',
    'open': 'first',
    'close': 'last'
}).reset_index()
daily_full.columns = ['date', 'day_high', 'day_low', 'day_open', 'day_close']

# Calculate Previous Day Levels
daily_full['prev_high'] = daily_full['day_high'].shift(1)
daily_full['prev_low'] = daily_full['day_low'].shift(1)
daily_full['prev_mid'] = (daily_full['prev_high'] + daily_full['prev_low']) / 2
daily_full['prev_range'] = daily_full['prev_high'] - daily_full['prev_low']
daily_full['day_range'] = daily_full['day_high'] - daily_full['day_low']
daily_full = daily_full.dropna() # Drop first day which has no prev

# Load VIX
vix['datetime'] = pd.to_datetime(vix['date'])
vix['date'] = vix['datetime'].dt.date
vix_daily = vix.groupby('date').agg({'close': 'last'}).reset_index()
vix_daily = vix_daily.rename(columns={'close': 'vix'})
daily_full = daily_full.merge(vix_daily, on='date', how='left')

# 2. Identify Normal Days
first_candle = df_5min_full.groupby('date').first()
normal_start_1 = time(9, 15)
normal_start_2 = time(9, 20)
normal_days_index = first_candle[
    (first_candle['time'] == normal_start_1) | 
    (first_candle['time'] == normal_start_2)
].index

# Filter Daily data to only keep Normal Days for analysis
daily_analysis = daily_full[daily_full['date'].isin(normal_days_index)].copy()
# Add first_5min_close for use in classification
daily_analysis['first_5min_close'] = daily_analysis['date'].map(first_candle['close'])

print(f"Total Daily Rows: {len(daily_full)}")
print(f"Analysis Rows (Normal Days): {len(daily_analysis)}")

# Initialize timing columns
daily_analysis['time_to_high'] = np.nan
daily_analysis['time_to_low'] = np.nan
daily_analysis['time_to_10pct_above'] = np.nan
daily_analysis['time_to_10pct_below'] = np.nan
daily_analysis['retraced_to_mid_after_high'] = False
daily_analysis['retraced_to_mid_after_low'] = False

# --------------------------------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------------------------------
def get_vix_stats(df):
    valid = df['vix'].dropna()
    if len(valid) == 0: return None
    return {
        "min": round(valid.min(), 2),
        "max": round(valid.max(), 2),
        "avg": round(valid.mean(), 2),
        "median": round(valid.median(), 2)
    }

def get_timing_stats(df):
    if 'time_to_2nd_order' not in df.columns: return None
    valid = df.dropna(subset=['time_to_2nd_order'])
    if len(valid) == 0: return None
    
    min_idx = valid['time_to_2nd_order'].idxmin()
    max_idx = valid['time_to_2nd_order'].idxmax()
    median_val = valid['time_to_2nd_order'].median()
    median_idx = (valid['time_to_2nd_order'] - median_val).abs().idxmin()
    
    return {
        "min": int(valid.loc[min_idx, 'time_to_2nd_order']),
        "min_date": str(valid.loc[min_idx, 'date']),
        "max": int(valid.loc[max_idx, 'time_to_2nd_order']),
        "max_date": str(valid.loc[max_idx, 'date']),
        "avg": int(valid['time_to_2nd_order'].mean()),
        "median": int(valid['time_to_2nd_order'].median()),
        "median_date": str(valid.loc[median_idx, 'date']),
        "avg_raw": float(valid['time_to_2nd_order'].mean())
    }

def get_recent_dates(df, limit=5):
    if len(df) == 0: return []
    return [str(d) for d in df.sort_values('date', ascending=False).head(limit)['date'].tolist()]

# --------------------------------------------------------------------------------
# MAIN ANALYSIS LOOPS
# --------------------------------------------------------------------------------

# 3. Calculate 5-min Timing Logic for Analysis Days
for idx, day in daily_analysis.iterrows():
    # Use full 5-min data for that day
    day_data = df_5min_full[df_5min_full['date'] == day['date']].copy()
    
    # EXCLUDE first 5-min candle (9:15-9:20) for more actionable post-opening data
    # Start timing analysis from second candle (minute 5 onwards)
    after_first_candle = day_data[day_data['minutes_since_915'] >= 5]
    
    # Time to touch high (starting from second candle)
    touched_high = after_first_candle[after_first_candle['high'] >= day['prev_high']]
    if len(touched_high) > 0:
        daily_analysis.at[idx, 'time_to_high'] = touched_high.iloc[0]['minutes_since_915']
    
    # Time to touch low (starting from second candle)
    touched_low = after_first_candle[after_first_candle['low'] <= day['prev_low']]
    if len(touched_low) > 0:
        daily_analysis.at[idx, 'time_to_low'] = touched_low.iloc[0]['minutes_since_915']
        
    # Time to 10% extension ABOVE (Based on CLOSE)
    if pd.notna(daily_analysis.at[idx, 'time_to_high']):
        time_high = daily_analysis.at[idx, 'time_to_high']
        after_high = day_data[day_data['minutes_since_915'] >= time_high]
        threshold_above = day['prev_high'] + 0.1 * day['prev_range']
        # User Change: Look at CLOSE of candle, not high
        went_above = after_high[after_high['close'] >= threshold_above]
        if len(went_above) > 0:
            time_ext = went_above.iloc[0]['minutes_since_915']
            daily_analysis.at[idx, 'time_to_10pct_above'] = time_ext
            
            # Check Mid Retracement (Retracement logic typically touches, so Low/High is okay for retrace? 
            # "Before touching mid". Touching is usually wicking?
            # User said "same logic for every subrow". 
            # Row 2 is "goes > 10%...". 
            # Does "Retraced to mid" logic change? "Before touching mid".
            # Touching a level usually implies High/Low. 
            # Using Close for EXTENSION is explicit. 
            # I will keep Retracement as Low/High unless specified, as "touch" usually means price traded there. 
            # "Goes > 10% above" implies sustaining/closing?
            # I'll stick to changing the Extension check to Close only.
            
            between = after_high[after_high['minutes_since_915'] <= time_ext]
            touched_mid = between[between['low'] <= day['prev_mid']]
            if len(touched_mid) > 0:
                daily_analysis.at[idx, 'retraced_to_mid_after_high'] = True

    # Time to 10% extension BELOW (Based on CLOSE)
    if pd.notna(daily_analysis.at[idx, 'time_to_low']):
        time_low = daily_analysis.at[idx, 'time_to_low']
        after_low = day_data[day_data['minutes_since_915'] >= time_low]
        threshold_below = day['prev_low'] - 0.1 * day['prev_range']
        # User Change: Look at CLOSE of candle, not low
        went_below = after_low[after_low['close'] <= threshold_below]
        if len(went_below) > 0:
            time_ext = went_below.iloc[0]['minutes_since_915']
            daily_analysis.at[idx, 'time_to_10pct_below'] = time_ext
            
            # Check Mid Retracement
            between = after_low[after_low['minutes_since_915'] <= time_ext]
            touched_mid = between[between['high'] >= day['prev_mid']]
            if len(touched_mid) > 0:
                daily_analysis.at[idx, 'retraced_to_mid_after_low'] = True

# 4. Classification
def classify_open(row):
    # Use first_5min_close for the classification as per user request
    if row['first_5min_close'] > row['prev_high']:
        return 'ABOVE'
    elif row['first_5min_close'] < row['prev_low']:
        return 'BELOW'
    else:
        return 'INSIDE'

daily_analysis['opening_position'] = daily_analysis.apply(classify_open, axis=1)
inside_days = daily_analysis[daily_analysis['opening_position'] == 'INSIDE'].copy()

# Groups
# A. Touched High First (Inside Open)
touched_high_first = inside_days[
    (inside_days['time_to_high'].notna()) &
    ((inside_days['time_to_low'].isna()) | (inside_days['time_to_high'] < inside_days['time_to_low']))
].copy()

# Row 1 (Stayed Within - Did NOT extend based on CLOSE)
row1 = touched_high_first[touched_high_first['time_to_10pct_above'].isna()].copy()

# Row 2 (Parent - Extended based on CLOSE)
row2_base = touched_high_first[touched_high_first['time_to_10pct_above'].notna()].copy()
row2_base['time_to_2nd_order'] = row2_base['time_to_10pct_above'] - row2_base['time_to_high']

# Split Row 2
row2_direct = row2_base[row2_base['retraced_to_mid_after_high'] == False].copy()
row2_retraced = row2_base[row2_base['retraced_to_mid_after_high'] == True].copy()

# B. Touched Low First (Inside Open)
touched_low_first = inside_days[
    (inside_days['time_to_low'].notna()) &
    ((inside_days['time_to_high'].isna()) | (inside_days['time_to_low'] < inside_days['time_to_high']))
].copy()

# Row 3 (Stayed Within - Did NOT extend below based on CLOSE)
row3 = touched_low_first[touched_low_first['time_to_10pct_below'].isna()].copy()

# Row 4 (Parent - Extended below based on CLOSE)
row4_base = touched_low_first[touched_low_first['time_to_10pct_below'].notna()].copy()
row4_base['time_to_2nd_order'] = row4_base['time_to_10pct_below'] - row4_base['time_to_low']

# Split Row 4
row4_direct = row4_base[row4_base['retraced_to_mid_after_low'] == False].copy()
row4_retraced = row4_base[row4_base['retraced_to_mid_after_low'] == True].copy()

# C. Stayed Inside (Row 5)
row5 = inside_days[
    (inside_days['day_high'] < inside_days['prev_high']) &
    (inside_days['day_low'] > inside_days['prev_low'])
].copy()
row5['pct_range'] = (row5['day_range'] / row5['prev_range']) * 100
row5['gap_from_high'] = ((row5['prev_high'] - row5['day_high']) / row5['prev_range']) * 100
row5['gap_from_low'] = ((row5['day_low'] - row5['prev_low']) / row5['prev_range']) * 100

# D. Detailed Closing Analysis
cutoff_minutes = 45 # 9:15 to 10:00 is 45 minutes

def analyze_closing_scenario(df_subset, direction='ABOVE'):
    total = len(df_subset)
    if total == 0: return {}
    
    results = {
        "total_count": total,
        "early": {"count": 0, "buckets": {}},
        "late": {"count": 0, "buckets": {}}
    }
    for key in ["early", "late"]:
        results[key]["buckets"] = {
            "touched_opp_low": [], 
            "touched_opp_mid": [], 
            "direct_ext": [],      
            "no_ext": []           
        }

    for idx, day in df_subset.iterrows():
        touch_time = day['time_to_high'] if direction == 'ABOVE' else day['time_to_low']
        
        if pd.isna(touch_time): 
            results["late"]["buckets"]["no_ext"].append(day['date'])
            continue
            
        is_early = touch_time <= cutoff_minutes
        category = "early" if is_early else "late"
        
        day_5min = df_5min_full[df_5min_full['date'] == day['date']].copy()
        post_touch = day_5min[day_5min['minutes_since_915'] >= touch_time]
        
        if len(post_touch) == 0: 
            results[category]["buckets"]["no_ext"].append(day['date'])
            continue

        if direction == 'ABOVE':
            if (post_touch['low'] <= day['prev_low']).any():
                results[category]["buckets"]["touched_opp_low"].append(day['date'])
            elif (post_touch['low'] <= day['prev_mid']).any():
                results[category]["buckets"]["touched_opp_mid"].append(day['date'])
            else:
                threshold = day['prev_high'] + 0.1 * day['prev_range']
                if (post_touch['high'] >= threshold).any():
                    results[category]["buckets"]["direct_ext"].append(day['date'])
                else:
                    results[category]["buckets"]["no_ext"].append(day['date'])
        else:
            if (post_touch['high'] >= day['prev_high']).any():
                results[category]["buckets"]["touched_opp_low"].append(day['date']) 
            elif (post_touch['high'] >= day['prev_mid']).any():
                results[category]["buckets"]["touched_opp_mid"].append(day['date'])
            else:
                threshold = day['prev_low'] - 0.1 * day['prev_range']
                if (post_touch['low'] <= threshold).any():
                    results[category]["buckets"]["direct_ext"].append(day['date'])
                else:
                    results[category]["buckets"]["no_ext"].append(day['date'])

    def summarize_bucket(dates_list):
        count = len(dates_list)
        if count == 0: return {"count": 0, "prob": 0, "vix": None, "timing": None}
        subset = daily_analysis[daily_analysis['date'].isin(dates_list)]
        return {
            "count": count,
            "prob": round(count / total * 100, 1), 
            "vix": get_vix_stats(subset),
            "dates": get_recent_dates(subset)
        }

    final_struct = {
        "count": total,
        "prob": round(total / len(daily_analysis) * 100, 1),
        "breakdown": {
            "early": {
                "count": sum(len(results["early"]["buckets"][k]) for k in results["early"]["buckets"]),
                "buckets": {k: summarize_bucket(v) for k, v in results["early"]["buckets"].items()}
            },
            "late": {
                "count": sum(len(results["late"]["buckets"][k]) for k in results["late"]["buckets"]),
                "buckets": {k: summarize_bucket(v) for k, v in results["late"]["buckets"].items()}
            }
        }
    }
    final_struct["breakdown"]["early"]["prob"] = round(final_struct["breakdown"]["early"]["count"] / total * 100, 1) if total > 0 else 0
    final_struct["breakdown"]["late"]["prob"] = round(final_struct["breakdown"]["late"]["count"] / total * 100, 1) if total > 0 else 0
    return final_struct

# Close Above Prev High
close_above = daily_analysis[daily_analysis['day_close'] > daily_analysis['prev_high']].copy()
close_above_stats = analyze_closing_scenario(close_above, direction='ABOVE')

# Breakdown Open Stats for Parent Row
close_above_breakdown = close_above['opening_position'].value_counts()
close_above_stats['open_breakdown'] = {
    "above": int(close_above_breakdown.get('ABOVE', 0)),
    "inside": int(close_above_breakdown.get('INSIDE', 0)),
    "below": int(close_above_breakdown.get('BELOW', 0))
}

# Close Below Prev Low
close_below = daily_analysis[daily_analysis['day_close'] < daily_analysis['prev_low']].copy()
close_below_stats = analyze_closing_scenario(close_below, direction='BELOW')
close_below_breakdown = close_below['opening_position'].value_counts()
close_below_stats['open_breakdown'] = {
    "above": int(close_below_breakdown.get('ABOVE', 0)),
    "inside": int(close_below_breakdown.get('INSIDE', 0)),
    "below": int(close_below_breakdown.get('BELOW', 0))
}

# --------------------------------------------------------------------------------
# JSON OUTPUT
# --------------------------------------------------------------------------------
output = {
    "global_stats": {
        "total_days": len(daily_analysis),
        "inside_days": len(inside_days),
        "inside_prob": round(len(inside_days)/len(daily_analysis)*100, 1) if len(daily_analysis) > 0 else 0
    },
    "row1": {
        "count": len(row1),
        "prob": round(len(row1)/len(touched_high_first)*100, 1) if len(touched_high_first) > 0 else 0,
        "vix": get_vix_stats(row1),
        "timing": None,
        "dates": get_recent_dates(row1)
    },
    "row2_direct": {
        "count": len(row2_direct),
        "prob": round(len(row2_direct)/len(touched_high_first)*100, 1) if len(touched_high_first) > 0 else 0,
        "vix": get_vix_stats(row2_direct),
        "timing": get_timing_stats(row2_direct),
        "dates": get_recent_dates(row2_direct)
    },
    "row2_retraced": {
        "count": len(row2_retraced),
        "prob": round(len(row2_retraced)/len(touched_high_first)*100, 1) if len(touched_high_first) > 0 else 0,
        "vix": get_vix_stats(row2_retraced),
        "timing": get_timing_stats(row2_retraced),
        "dates": get_recent_dates(row2_retraced)
    },
    "row3": {
        "count": len(row3),
        "prob": round(len(row3)/len(touched_low_first)*100, 1) if len(touched_low_first) > 0 else 0,
        "vix": get_vix_stats(row3),
        "timing": None,
        "dates": get_recent_dates(row3)
    },
    "row4_direct": {
        "count": len(row4_direct),
        "prob": round(len(row4_direct)/len(touched_low_first)*100, 1) if len(touched_low_first) > 0 else 0,
        "vix": get_vix_stats(row4_direct),
        "timing": get_timing_stats(row4_direct),
        "dates": get_recent_dates(row4_direct)
    },
    "row4_retraced": {
        "count": len(row4_retraced),
        "prob": round(len(row4_retraced)/len(touched_low_first)*100, 1) if len(touched_low_first) > 0 else 0,
        "vix": get_vix_stats(row4_retraced),
        "timing": get_timing_stats(row4_retraced),
        "dates": get_recent_dates(row4_retraced)
    },
    "row5": {
        "count": len(row5),
        "prob": round(len(row5)/len(inside_days)*100, 1) if len(inside_days) > 0 else 0,
        "vix": get_vix_stats(row5),
        "avg_pct_range": round(row5['pct_range'].mean(), 1),
        "avg_gap_high": round(row5['gap_from_high'].mean(), 1),
        "avg_gap_low": round(row5['gap_from_low'].mean(), 1),
        "dates": get_recent_dates(row5)
    },
    "close_above_detailed": close_above_stats,
    "close_below_detailed": close_below_stats
}

with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\final_corrected_stats.json', 'w') as f:
    json.dump(output, f, indent=4)
print("JSON Updated")
