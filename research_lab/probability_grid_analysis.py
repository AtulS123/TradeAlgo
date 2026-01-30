"""
NIFTY 50 Probability Grid Analysis
===================================

Analyzes opening position relative to previous day's range and calculates:
1. First-order probabilities: State transitions throughout the day
2. Second-order probabilities: Conditional probabilities after state changes
3. Time-based insights: When breakouts/breakdowns typically occur

Author: Generated for Atul Singh
Date: 2026-01-29
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import json
from pathlib import Path
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')


class ProbabilityGridAnalyzer:
    """Analyzes NIFTY 50 opening positions and calculates probability grids"""
    
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.daily_data = None
        self.results = {}
        
    def load_and_prepare_data(self):
        """Load minute data and resample to 5-minute candles"""
        print("Loading data...")
        self.df = pd.read_csv(self.data_path)
        
        # Parse datetime
        self.df['datetime'] = pd.to_datetime(self.df['date'])
        self.df['date'] = self.df['datetime'].dt.date
        self.df['time'] = self.df['datetime'].dt.time
        
        # Sort by datetime
        self.df = self.df.sort_values('datetime').reset_index(drop=True)
        
        print(f"Loaded {len(self.df):,} minute candles")
        print(f"Date range: {self.df['datetime'].min()} to {self.df['datetime'].max()}")
        
        # Resample to 5-minute candles
        print("\nResampling to 5-minute candles...")
        self.df.set_index('datetime', inplace=True)
        
        df_5min = self.df.resample('5T').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        df_5min['date'] = df_5min.index.date
        df_5min['time'] = df_5min.index.time
        df_5min.reset_index(inplace=True)
        
        self.df = df_5min
        print(f"Resampled to {len(self.df):,} 5-minute candles")
        
    def calculate_daily_ranges(self):
        """Calculate daily high/low for each trading day"""
        print("\nCalculating daily ranges...")
        
        daily_agg = self.df.groupby('date').agg({
            'high': 'max',
            'low': 'min',
            'open': 'first',
            'close': 'last',
            'datetime': 'first'
        }).reset_index()
        
        daily_agg.columns = ['date', 'day_high', 'day_low', 'day_open', 'day_close', 'day_start']
        
        # Get first 5-min candle close for each day
        # Calculate minutes since 9:15
        self.df['minutes_since_915'] = self.df['datetime'].dt.hour * 60 + self.df['datetime'].dt.minute - (9*60 + 15)
        first_candles = self.df[self.df['minutes_since_915'] == 0][['date', 'close']].rename(columns={'close': 'first_5min_close'})
        daily_agg = daily_agg.merge(first_candles, on='date', how='left')
        
        # Add previous day's high and low
        daily_agg['prev_high'] = daily_agg['day_high'].shift(1)
        daily_agg['prev_low'] = daily_agg['day_low'].shift(1)
        daily_agg['prev_close'] = daily_agg['day_close'].shift(1)
        
        # Remove first day (no previous data)
        daily_agg = daily_agg.dropna()
        
        self.daily_data = daily_agg
        print(f"Calculated ranges for {len(self.daily_data)} trading days")
        
    def classify_opening_position(self):
        """Classify each day's opening position based on first 5-min candle CLOSE"""
        print("\nClassifying opening positions...")
        
        def classify(row):
            # Use first 5-min candle CLOSE for classification
            if row['first_5min_close'] > row['prev_high']:
                return 'ABOVE'
            elif row['first_5min_close'] < row['prev_low']:
                return 'BELOW'
            else:
                return 'INSIDE'
        
        self.daily_data['opening_position'] = self.daily_data.apply(classify, axis=1)
        
        # Count distributions
        counts = self.daily_data['opening_position'].value_counts()
        total = len(self.daily_data)
        
        print(f"\nOpening Position Distribution:")
        for pos in ['ABOVE', 'INSIDE', 'BELOW']:
            count = counts.get(pos, 0)
            pct = (count / total) * 100
            print(f"  {pos:6s}: {count:4d} days ({pct:5.2f}%)")
            
    def calculate_first_order_probabilities(self):
        """Calculate probabilities of staying in or moving to different states"""
        print("\n" + "="*70)
        print("CALCULATING FIRST-ORDER PROBABILITIES")
        print("="*70)
        
        results = defaultdict(lambda: defaultdict(int))
        
        for _, day in self.daily_data.iterrows():
            opening_pos = day['opening_position']
            prev_high = day['prev_high']
            prev_low = day['prev_low']
            day_high = day['day_high']
            day_low = day['day_low']
            
            # Determine end states
            stayed_in_range = (day_low >= prev_low) and (day_high <= prev_high)
            moved_above = day_high > prev_high
            moved_below = day_low < prev_low
            
            # Classify end state
            if opening_pos == 'INSIDE':
                if stayed_in_range:
                    results[opening_pos]['stayed_inside'] += 1
                elif moved_above and not moved_below:
                    results[opening_pos]['moved_above_only'] += 1
                elif moved_below and not moved_above:
                    results[opening_pos]['moved_below_only'] += 1
                else:  # Both above and below
                    results[opening_pos]['moved_both'] += 1
                    
            elif opening_pos == 'ABOVE':
                if day_low >= prev_high:
                    results[opening_pos]['stayed_above'] += 1
                elif day_low < prev_high and day_low >= prev_low:
                    results[opening_pos]['returned_to_range'] += 1
                else:  # Went below prev_low
                    results[opening_pos]['went_below_range'] += 1
                    
            elif opening_pos == 'BELOW':
                if day_high <= prev_low:
                    results[opening_pos]['stayed_below'] += 1
                elif day_high > prev_low and day_high <= prev_high:
                    results[opening_pos]['returned_to_range'] += 1
                else:  # Went above prev_high
                    results[opening_pos]['went_above_range'] += 1
        
        # Convert to probabilities
        prob_table = {}
        for opening_pos in ['ABOVE', 'INSIDE', 'BELOW']:
            total = sum(results[opening_pos].values())
            if total > 0:
                prob_table[opening_pos] = {
                    k: (v / total * 100) for k, v in results[opening_pos].items()
                }
                prob_table[opening_pos]['total_days'] = total
        
        self.results['first_order'] = prob_table
        self._print_first_order_results(prob_table)
        
    def _print_first_order_results(self, prob_table):
        """Print first-order probability results in a formatted table"""
        print("\n📊 FIRST-ORDER PROBABILITY TABLE")
        print("-" * 90)
        
        for opening_pos in ['INSIDE', 'ABOVE', 'BELOW']:
            if opening_pos not in prob_table:
                continue
                
            probs = prob_table[opening_pos]
            total_days = probs.pop('total_days', 0)
            
            print(f"\n🔹 Opening Position: {opening_pos} (Total: {total_days} days)")
            print("   " + "-" * 70)
            
            for outcome, prob in sorted(probs.items(), key=lambda x: -x[1]):
                outcome_display = outcome.replace('_', ' ').title()
                print(f"   {outcome_display:40s}: {prob:6.2f}%")
                
    def calculate_second_order_probabilities(self):
        """Calculate conditional probabilities (e.g., if moved lower from inside, what happens?)"""
        print("\n" + "="*70)
        print("CALCULATING SECOND-ORDER PROBABILITIES")
        print("="*70)
        
        second_order = defaultdict(lambda: defaultdict(int))
        
        # Merge daily data with minute data to track intraday movements
        for _, day in self.daily_data.iterrows():
            date = day['date']
            opening_pos = day['opening_position']
            prev_high = day['prev_high']
            prev_low = day['prev_low']
            
            # Get all 5-min candles for this day
            day_candles = self.df[self.df['date'] == date].copy()
            if len(day_candles) == 0:
                continue
                
            # Track state transitions
            if opening_pos == 'INSIDE':
                # Check if we moved outside the range during the day
                moved_above_time = None
                moved_below_time = None
                
                for idx, candle in day_candles.iterrows():
                    if candle['high'] > prev_high and moved_above_time is None:
                        moved_above_time = candle['time']
                    if candle['low'] < prev_low and moved_below_time is None:
                        moved_below_time = candle['time']
                
                # Scenario: Started inside, moved below
                if moved_below_time and not moved_above_time:
                    # Check if it returned to range after moving below
                    after_break = day_candles[day_candles['time'] > moved_below_time]
                    returned_to_range = any(after_break['high'] >= prev_low)
                    
                    if returned_to_range:
                        second_order['inside_then_below']['returned_to_range'] += 1
                    else:
                        second_order['inside_then_below']['stayed_below'] += 1
                        
                # Scenario: Started inside, moved above
                elif moved_above_time and not moved_below_time:
                    after_break = day_candles[day_candles['time'] > moved_above_time]
                    returned_to_range = any(after_break['low'] <= prev_high)
                    
                    if returned_to_range:
                        second_order['inside_then_above']['returned_to_range'] += 1
                    else:
                        second_order['inside_then_above']['stayed_above'] += 1
        
        # Convert to probabilities
        second_order_probs = {}
        for scenario, outcomes in second_order.items():
            total = sum(outcomes.values())
            if total > 0:
                second_order_probs[scenario] = {
                    k: (v / total * 100) for k, v in outcomes.items()
                }
                second_order_probs[scenario]['total_cases'] = total
        
        self.results['second_order'] = second_order_probs
        self._print_second_order_results(second_order_probs)
        
    def _print_second_order_results(self, probs):
        """Print second-order probability results"""
        print("\n📊 SECOND-ORDER CONDITIONAL PROBABILITIES")
        print("-" * 90)
        
        scenarios = {
            'inside_then_below': '📉 Started INSIDE → Moved BELOW prev day low',
            'inside_then_above': '📈 Started INSIDE → Moved ABOVE prev day high'
        }
        
        for scenario_key, scenario_desc in scenarios.items():
            if scenario_key not in probs:
                continue
                
            scenario_probs = probs[scenario_key].copy()
            total_cases = scenario_probs.pop('total_cases', 0)
            
            print(f"\n{scenario_desc}")
            print(f"   Total cases: {total_cases}")
            print("   " + "-" * 70)
            
            for outcome, prob in sorted(scenario_probs.items(), key=lambda x: -x[1]):
                outcome_display = outcome.replace('_', ' ').title()
                print(f"   {outcome_display:40s}: {prob:6.2f}%")
                
    def analyze_time_patterns(self):
        """Analyze when breakouts and breakdowns typically occur"""
        print("\n" + "="*70)
        print("ANALYZING TIME-BASED PATTERNS")
        print("="*70)
        
        breakout_times = []  # Moved above prev high
        breakdown_times = []  # Moved below prev low
        
        for _, day in self.daily_data.iterrows():
            date = day['date']
            opening_pos = day['opening_position']
            prev_high = day['prev_high']
            prev_low = day['prev_low']
            
            if opening_pos != 'INSIDE':
                continue
                
            day_candles = self.df[self.df['date'] == date].copy()
            
            # Find first breakout time
            for idx, candle in day_candles.iterrows():
                if candle['high'] > prev_high:
                    breakout_times.append(candle['time'])
                    break
                    
            # Find first breakdown time
            for idx, candle in day_candles.iterrows():
                if candle['low'] < prev_low:
                    breakdown_times.append(candle['time'])
                    break
        
        # Analyze time distribution
        time_insights = {
            'breakout_times': self._analyze_time_distribution(breakout_times, 'BREAKOUT (above prev high)'),
            'breakdown_times': self._analyze_time_distribution(breakdown_times, 'BREAKDOWN (below prev low)')
        }
        
        self.results['time_patterns'] = time_insights
        
    def _analyze_time_distribution(self, times, event_type):
        """Analyze distribution of times for a specific event"""
        if not times:
            print(f"\n⏰ {event_type}: No events found")
            return {}
            
        # Group by hour
        hour_counts = defaultdict(int)
        for t in times:
            hour = t.hour
            hour_counts[hour] += 1
        
        total = len(times)
        
        print(f"\n⏰ {event_type} Time Distribution")
        print(f"   Total events: {total}")
        print("   " + "-" * 70)
        
        # Sort by hour
        sorted_hours = sorted(hour_counts.items())
        for hour, count in sorted_hours:
            pct = (count / total) * 100
            bar = '█' * int(pct / 2)
            print(f"   {hour:02d}:00 - {hour:02d}:59  |{bar:30s} {count:4d} ({pct:5.2f}%)")
        
        # Find most common time window (30 min granularity)
        time_windows = defaultdict(int)
        for t in times:
            # Create 30-min windows
            window = f"{t.hour:02d}:{t.minute//30 * 30:02d}"
            time_windows[window] += 1
        
        most_common_window = max(time_windows.items(), key=lambda x: x[1])
        
        insight = {
            'total_events': total,
            'most_common_window': most_common_window[0],
            'most_common_count': most_common_window[1],
            'most_common_pct': (most_common_window[1] / total) * 100
        }
        
        print(f"\n   🔥 Most common time: {most_common_window[0]} ({most_common_window[1]} events, {insight['most_common_pct']:.2f}%)")
        
        return insight
        
    def save_results(self, output_dir='research_lab/results/probability_grid'):
        """Save all results to files"""
        print("\n" + "="*70)
        print("SAVING RESULTS")
        print("="*70)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save first-order probabilities
        first_order_df = pd.DataFrame(self.results['first_order']).T
        first_order_path = output_path / 'first_order_probabilities.csv'
        first_order_df.to_csv(first_order_path)
        print(f"✅ Saved: {first_order_path}")
        
        # Save second-order probabilities
        if self.results.get('second_order'):
            second_order_df = pd.DataFrame(self.results['second_order']).T
            second_order_path = output_path / 'second_order_probabilities.csv'
            second_order_df.to_csv(second_order_path)
            print(f"✅ Saved: {second_order_path}")
        
        # Save complete results as JSON
        results_json_path = output_path / 'complete_analysis.json'
        with open(results_json_path, 'w') as f:
            # Convert time objects to strings for JSON serialization
            json_results = json.dumps(self.results, indent=2, default=str)
            f.write(json_results)
        print(f"✅ Saved: {results_json_path}")
        
        # Save daily data with classifications
        daily_export_path = output_path / 'daily_classification.csv'
        self.daily_data.to_csv(daily_export_path, index=False)
        print(f"✅ Saved: {daily_export_path}")
        
        print(f"\n📁 All results saved to: {output_path.absolute()}")
        
        return output_path
        
    def generate_summary_insights(self):
        """Generate key insights from the analysis"""
        print("\n" + "="*70)
        print("🔍 KEY INSIGHTS & SUMMARY")
        print("="*70)
        
        insights = []
        
        # Insight 1: Most common opening position
        opening_dist = self.daily_data['opening_position'].value_counts()
        most_common = opening_dist.idxmax()
        most_common_pct = (opening_dist[most_common] / len(self.daily_data)) * 100
        insights.append(f"📌 Most common opening: {most_common} ({most_common_pct:.1f}% of days)")
        
        # Insight 2: Probability of staying in range when opened inside
        if 'INSIDE' in self.results['first_order']:
            inside_probs = self.results['first_order']['INSIDE']
            stayed_inside = inside_probs.get('stayed_inside', 0)
            insights.append(f"📌 When opening INSIDE: {stayed_inside:.1f}% chance of staying within previous day's range")
        
        # Insight 3: Time insights
        if 'time_patterns' in self.results:
            breakout = self.results['time_patterns'].get('breakout_times', {})
            if breakout.get('most_common_window'):
                insights.append(f"📌 Breakouts most common at: {breakout['most_common_window']} ({breakout['most_common_pct']:.1f}% of all breakouts)")
            
            breakdown = self.results['time_patterns'].get('breakdown_times', {})
            if breakdown.get('most_common_window'):
                insights.append(f"📌 Breakdowns most common at: {breakdown['most_common_window']} ({breakdown['most_common_pct']:.1f}% of all breakdowns)")
        
        # Print insights
        for insight in insights:
            print(f"\n  {insight}")
        
        print("\n" + "="*70)
        
        return insights
    
    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        print("\n" + "="*70)
        print("NIFTY 50 PROBABILITY GRID ANALYSIS")
        print("="*70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.load_and_prepare_data()
        self.calculate_daily_ranges()
        self.classify_opening_position()
        self.calculate_first_order_probabilities()
        self.calculate_second_order_probabilities()
        self.analyze_time_patterns()
        self.generate_summary_insights()
        output_path = self.save_results()
        
        print("\n" + "="*70)
        print("✅ ANALYSIS COMPLETE")
        print("="*70)
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return output_path


if __name__ == '__main__':
    # Path to NIFTY 50 minute data
    data_path = r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv'
    
    # Run analysis
    analyzer = ProbabilityGridAnalyzer(data_path)
    output_path = analyzer.run_full_analysis()
    
    print(f"\n📊 View results at: {output_path}")
