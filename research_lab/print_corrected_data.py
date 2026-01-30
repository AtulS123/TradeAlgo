import json

with open(r'C:\Users\atuls\Startup\TradeAlgo\research_lab\results\probability_grid\corrected_data.json', 'r') as f:
    data = json.load(f)

print("ROW 1: Stayed within 10% above")
print(f"  Count: {data['row1_stayed_within_10pct_above']['count']}")
print(f"  Prob: {data['row1_stayed_within_10pct_above']['probability']}%")
print(f"  VIX: {data['row1_stayed_within_10pct_above']['vix']}")
print(f"  Dates: {', '.join(data['row1_stayed_within_10pct_above']['dates'])}")

print("\nROW 2: Went >=10% above")
print(f"  Count: {data['row2_went_10pct_above']['count']}")
print(f"  Prob: {data['row2_went_10pct_above']['probability']}%")
print(f"  VIX: {data['row2_went_10pct_above']['vix']}")
print(f"  Dates: {', '.join(data['row2_went_10pct_above']['dates'])}")

print("\nROW 3: Stayed within 10% below")
print(f"  Count: {data['row3_stayed_within_10pct_below']['count']}")
print(f"  Prob: {data['row3_stayed_within_10pct_below']['probability']}%")
print(f"  VIX: {data['row3_stayed_within_10pct_below']['vix']}")
print(f"  Dates: {', '.join(data['row3_stayed_within_10pct_below']['dates'])}")

print("\nROW 4: Went >=10% below")
print(f"  Count: {data['row4_went_10pct_below']['count']}")
print(f"  Prob: {data['row4_went_10pct_below']['probability']}%")
print(f"  VIX: {data['row4_went_10pct_below']['vix']}")
print(f"  Dates: {', '.join(data['row4_went_10pct_below']['dates'])}")

print("\nROW 5: Stayed inside")
print(f"  Count: {data['row5_stayed_inside']['count']}")
print(f"  Prob: {data['row5_stayed_inside']['probability']}%")
print(f"  VIX: {data['row5_stayed_inside']['vix']}")
print(f"  Avg % range: {data['row5_stayed_inside']['avg_pct_range']}%")
print(f"  Avg gap from high: {data['row5_stayed_inside']['avg_gap_from_high']}%")
print(f"  Avg gap from low: {data['row5_stayed_inside']['avg_gap_from_low']}%")
print(f"  Dates: {', '.join(data['row5_stayed_inside']['dates'])}")
