"""
Continuous Monitoring Mode
Run the optimization system continuously
"""
from continuous_monitor import ContinuousMonitor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
    """Run continuous monitoring"""
    monitor = ContinuousMonitor()
    
    print("\n" + "="*70)
    print("CONTINUOUS MONITORING MODE")
    print("="*70)
    print("\nThe system will continuously monitor for new prompts and")
    print("optimize model usage based on cost-quality trade-offs.")
    print("\nPress Ctrl+C to stop\n")
    print("="*70 + "\n")
    
    try:
        monitor.start_continuous_monitoring()
    except KeyboardInterrupt:
        print("\n\nStopping...")
        monitor.stop()


if __name__ == "__main__":
    main()
