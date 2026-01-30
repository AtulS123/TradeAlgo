from research_lab.backtest_pipeline import WalkForwardOptimizer
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

if __name__ == "__main__":
    # Select a stock that exists in the data
    # Based on file list, we have many. Let's try a major one.
    symbol = "RELIANCE" 
    
    print(f"Initializing Lab for {symbol}...")
    try:
        optimizer = WalkForwardOptimizer(symbol)
        stats = optimizer.run_pipeline()
        print("\nDetailed Stats:")
        print(stats)
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
