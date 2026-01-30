"""
Debug: Check if Jan 24 is in the row2_retraced dataset
"""
import pandas as pd
import json

# Load the generated stats
with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\final_corrected_stats.json', 'r') as f:
    stats = json.load(f)

# Check Row 2 retraced dates
row2_retr_dates = stats['row2_retraced']['dates']

print("Row 2 Retraced Example Dates:")
for d in row2_retr_dates:
    print(f"  {d}")
    if '2025-01-24' in d:
        print("  ^^^ JAN 24 FOUND HERE!")

# Also check all inside-related rows
print("\nChecking all INSIDE rows for Jan 24...")
for key in ['row1', 'row2_direct', 'row2_retraced', 'row3', 'row4_direct', 'row4_retraced', 'row5']:
    if '2025-01-24' in str(stats[key].get('dates', [])):
        print(f"  Found in {key}: {stats[key]['dates']}")
