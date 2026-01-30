import zipfile
import os

def inspect_zip(zip_path):
    print(f"Inspecting {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            print(f"Files found: {len(z.namelist())}")
            print("First 10 files:")
            for name in z.namelist()[:10]:
                print(f" - {name}")
    except Exception as e:
        print(f"Error reading {zip_path}: {e}")

if __name__ == "__main__":
    base_dir = "kaggle_data"
    inspect_zip(os.path.join(base_dir, "minute.zip"))
    inspect_zip(os.path.join(base_dir, "archive.zip"))
