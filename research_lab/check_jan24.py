import pandas as pd
from datetime import date

df = pd.read_csv(r'C:\Users\atuls\Startup\TradeAlgo\kaggle_data\archive\NIFTY 50_minute.csv', encoding='utf-8')
df['datetime'] = pd.to_datetime(df['date'])
df.set_index('datetime', inplace=True)

df_5min = df.resample('5min').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna()
df_5min['date'] = df_5min.index.date
df_5min['min'] = df_5min.index.hour * 60 + df_5min.index.minute - 555
df_5min.reset_index(inplace=True)

jan24 = df_5min[df_5min['date'] == date(2025, 1, 24)].copy()
jan23 = df_5min[df_5min['date'] == date(2025, 1, 23)].copy()

ph = jan23['high'].max()
pl = jan23['low'].min()
pm = (ph + pl) / 2
pr = ph - pl

fc = jan24[jan24['min'] == 0].iloc[0]

print("="*60)
print("JANUARY 24, 2025")
print("="*60)
print(f"Previous: H={ph:.2f} M={pm:.2f} L={pl:.2f} R={pr:.2f}")
print(f"First5min: O={fc['open']:.2f} H={fc['high']:.2f} L={fc['low']:.2f} C={fc['close']:.2f}")

# Classification
if fc['close'] > ph:
    cls = "ABOVE"
elif fc['close'] < pl:
    cls = "BELOW"
else:
    cls = "INSIDE"

print(f"\nOPENING: {cls}")

if cls == "INSIDE":
    th = jan24[jan24['high'] >= ph]
    tl = jan24[jan24['low'] <= pl]
    
    if len(th) > 0 and (len(tl) == 0 or th.iloc[0]['min'] < tl.iloc[0]['min']):
        print("Touched HIGH first")
        tm = th.iloc[0]['min']
        
        thresh = ph + 0.1 * pr
        after = jan24[jan24['min'] >= tm]
        ext = after[after['close'] >= thresh]
        
        if len(ext) > 0:
            te = ext.iloc[0]['min']
            print(f"Extended 10%: YES at {te} min (thresh={thresh:.2f})")
            
            bet = after[after['min'] <= te]
            mtch = bet[bet['low'] <= pm]
            
            if len(mtch) > 0:
                print(f"Touched mid BEFORE ext: YES at {mtch.iloc[0]['min']} min")
                print("CATEGORY: ROW 2 RETRACED")
            else:
                print("Touched mid BEFORE ext: NO")
                print("CATEGORY: ROW 2 DIRECT")
        else:
            print("Extended 10%: NO")
            print("CATEGORY: ROW 1")

dh = jan24['high'].max()
dl = jan24['low'].min()
dc = jan24['close'].iloc[-1]

print(f"\nDay stats: H={dh:.2f} L={dl:.2f} C={dc:.2f}")
if dc > ph:
    print(f"CLOSE: ABOVE")
elif dc < pl:
    print(f"CLOSE: BELOW")
else:
    print(f"CLOSE: INSIDE")
