"""
Track 4 Demo - Generate Fresh Optimization Results
This script clears old data and runs a fresh optimization to show the expected Track 4 output
"""
import os
import shutil
from pathlib import Path

# Clear old data
data_dir = Path("data")
if data_dir.exists():
    print("Clearing old data...")
    for file in data_dir.glob("*.json"):
        file.unlink()
        print(f"  Removed {file.name}")

print("\n" + "="*70)
print("TRACK 4: COST-QUALITY OPTIMIZATION - FRESH DEMO")
print("="*70)
print("\nThis will generate fresh results showing:")
print('  "Switching from Model A to Model B reduces cost by X% with Y% quality impact"')
print("\nRunning optimization engine...\n")

# Run main.py
import main
