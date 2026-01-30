import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
from jugaad_data.nse import bhavcopy_fo_save
from requests.exceptions import ConnectionError

class HistoricalHarvester:
    def __init__(self, start_date=None, end_year=2016, base_dir="data_archive"):
        self.base_dir = base_dir
        self.end_year = end_year
        # Start from yesterday if not specified
        if start_date:
            self.current_date = start_date
        else:
            self.current_date = (datetime.now() - timedelta(days=1)).date()
        
        self.session = requests.Session()
        self.setup_session()
        
        # Create base directory
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def setup_session(self):
        """Initialize or re-initialize the session with headers."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        })
        # Visit NSE homepage to get cookies
        try:
            self.session.get("https://www.nseindia.com", timeout=10)
        except Exception as e:
            print(f"Warning: Could not initialize NSE session: {e}")

    def get_target_path(self, date_obj):
        """Create directory structure and return target file path."""
        year = str(date_obj.year)
        month = date_obj.strftime("%b").upper() # JAN, FEB, etc.
        
        dir_path = os.path.join(self.base_dir, year, month)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        return os.path.join(dir_path, f"fo_{date_obj.strftime('%d%m%Y')}.csv")

    def download_legacy(self, date_obj, output_path):
        """Fallback method for older data using direct requests to archives."""
        # Format: https://archives.nseindia.com/content/historical/DERIVATIVES/2016/JAN/fo01JAN2016bhav.csv.zip
        # Or csv directly depending on the era. 
        # Note: NSE archives often provide zip files for older data.
        
        year = date_obj.strftime("%Y")
        month = date_obj.strftime("%b").upper()
        date_str = date_obj.strftime("%d%b%Y").upper()
        
        # Try CSV first, then ZIP
        filenames = [
            f"fo{date_str}bhav.csv",
            f"fo{date_str}bhav.csv.zip"
        ]
        
        base_url = f"https://archives.nseindia.com/content/historical/DERIVATIVES/{year}/{month}/"
        
        for filename in filenames:
            url = base_url + filename
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    # If zip, we might need to unzip, but for now let's save what we get
                    # If the user wants strictly CSV, we might need to unzip.
                    # jugaad-data handles unzip automatically.
                    
                    # For simplicity in this fallback, if it's a zip, we save it as zip, 
                    # but the requirement says "fo_{date}.csv". 
                    # Let's try to handle zip extraction if needed, or just save content.
                    
                    if filename.endswith('.zip'):
                        import zipfile
                        import io
                        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                            # Assume the csv is inside with the same name pattern
                            csv_name = z.namelist()[0]
                            with z.open(csv_name) as f:
                                content = f.read()
                                with open(output_path, 'wb') as out_f:
                                    out_f.write(content)
                    else:
                        with open(output_path, 'wb') as f:
                            f.write(response.content)
                    return True
                elif response.status_code == 404:
                    continue # Try next filename or return False
            except Exception as e:
                print(f"Legacy download error for {date_obj}: {e}")
        
        return False

    def run(self):
        consecutive_failures = 0
        requests_count = 0
        
        print(f"Starting harvest from {self.current_date} backwards to {self.end_year}...")
        
        # Create a progress bar roughly estimating days
        days_total = (self.current_date - datetime(self.end_year, 1, 1).date()).days
        pbar = tqdm(total=days_total)
        
        while self.current_date.year >= self.end_year:
            if consecutive_failures >= 10:
                print("Too many consecutive failures. Stopping.")
                break
                
            target_path = self.get_target_path(self.current_date)
            
            # Skip if already exists
            if os.path.exists(target_path):
                # print(f"Skipping {self.current_date}, already exists.")
                self.current_date -= timedelta(days=1)
                pbar.update(1)
                consecutive_failures = 0 # Reset on existing file? Or keep counting? 
                # Usually if it exists, it's a success.
                continue
            
            success = False
            try:
                # 1. Try jugaad-data first
                # bhavcopy_fo_save returns the path of the saved file
                # It saves to the directory provided.
                output_dir = os.path.dirname(target_path)
                
                # jugaad-data saves with a specific name, we might need to rename it
                # or just let it save and then rename.
                # It usually saves as fo<dd><MMM><yyyy>bhav.csv
                
                try:
                    saved_path = bhavcopy_fo_save(self.current_date, output_dir)
                    
                    # Rename to our standard fo_{date}.csv
                    if os.path.exists(saved_path):
                        # If saved_path is not target_path, rename
                        # But wait, we want to control the filename.
                        # jugaad-data doesn't let us control filename easily in the function call,
                        # it returns the path it saved to.
                        
                        # We can read it and write to our target path, or move it.
                        # Let's move it.
                        os.replace(saved_path, target_path)
                        success = True
                        
                except Exception as e:
                    # jugaad-data failed, maybe 404 or other error
                    # If it's a holiday, it might raise an error or just print.
                    # We'll assume failure and try fallback if appropriate
                    # But for recent years, jugaad-data is best.
                    pass

                # 2. Fallback to legacy if jugaad failed
                if not success:
                    success = self.download_legacy(self.current_date, target_path)

                if success:
                    consecutive_failures = 0
                else:
                    # Likely a holiday or weekend
                    # print(f"No Data (Holiday/Fail) for {self.current_date}")
                    consecutive_failures += 1
            
            except Exception as e:
                print(f"Error processing {self.current_date}: {e}")
                consecutive_failures += 1
            
            # Rate limiting and Session Management
            requests_count += 1
            if requests_count >= 100:
                self.setup_session()
                requests_count = 0
                time.sleep(1) # Extra pause on re-init
            
            time.sleep(0.2)
            
            self.current_date -= timedelta(days=1)
            pbar.update(1)
            
        pbar.close()
        print("Harvest complete.")

if __name__ == "__main__":
    harvester = HistoricalHarvester()
    harvester.run()
