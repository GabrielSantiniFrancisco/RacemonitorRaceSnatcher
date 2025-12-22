#!/usr/bin/env python3
"""
RacemonitorRaceSnatcher - Main Entry Point

Connects to RaceMonitor's WebSocket to receive live race timing data.
"""

import os
import sys
import time
import argparse

# Add lib folder to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from GetRaceMonitorKeyModule import RaceMonitorKeyRetriever
from RaceTimeHandlerModule import RaceTimingHandler


def main():
    parser = argparse.ArgumentParser(
        description='🏎️ RacemonitorRaceSnatcher - Live Race Timing Data Extractor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py 12345                    # Connect to race ID 12345 (runs until Ctrl+C)
  python main.py 12345 --duration 60      # Run for 60 seconds only
  python main.py 12345 --output results   # Save results to results/ folder on exit
  python main.py 12345 --debug            # Enable verbose debug logging
        """
    )
    
    parser.add_argument('race_id', type=str, help='RaceMonitor Race ID (numeric)')
    parser.add_argument('--duration', type=int, default=None, 
                        help='Duration to listen for data in seconds (default: unlimited)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output folder for CSV files (optional)')
    parser.add_argument('--no-display', action='store_true',
                        help='Disable live display of race data')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging (verbose output)')
    
    args = parser.parse_args()
    
    # Validate race_id
    if not args.race_id.isdigit():
        print(f"❌ Error: Race ID must be numeric. Got: {args.race_id}")
        sys.exit(1)
    
    # Paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    key_config = os.path.join(project_root, 'conf', 'GetRaceMonitorKeyModule.cfg')
    handler_config = os.path.join(project_root, 'conf', 'RaceTimeHandlerModule.cfg')
    
    print("=" * 60)
    print("🏎️  RacemonitorRaceSnatcher")
    print("=" * 60)
    print(f"📋 Race ID: {args.race_id}")
    print(f"⏱️  Duration: {'Unlimited (Ctrl+C to stop)' if args.duration is None else f'{args.duration} seconds'}")
    print()
    
    # Set log level based on debug flag
    log_level = 'DEBUG' if args.debug else 'WARNING'
    
    # Step 1: Get WebSocket credentials
    print("🔑 Step 1: Extracting WebSocket credentials from RaceMonitor...")
    try:
        key_retriever = RaceMonitorKeyRetriever(
            caller_script='main',
            config_file_path=key_config,
            log_level=log_level
        )
        ws_url, ws_key = key_retriever.get_link_and_key(args.race_id)
        print(f"✅ WebSocket URL obtained: {ws_url[:50]}...")
        print(f"✅ WebSocket Key obtained: {ws_key[:10]}...")
    except Exception as e:
        print(f"❌ Failed to retrieve WebSocket credentials: {e}")
        sys.exit(1)
    
    print()
    
    # Step 2: Connect to WebSocket and receive data
    print("📡 Step 2: Connecting to WebSocket...")
    try:
        handler = RaceTimingHandler(
            caller_script='main',
            config_file_path=handler_config,
            log_level=log_level
        )
        handler.connect(ws_url)
        print("✅ Connected to WebSocket!")
    except Exception as e:
        print(f"❌ Failed to connect to WebSocket: {e}")
        sys.exit(1)
    
    print()
    if args.duration:
        print(f"📺 Listening for race data for {args.duration} seconds...")
    else:
        print("📺 Listening for race data (Press Ctrl+C to stop)...")
    print("-" * 60)
    
    # Step 3: Listen and display data
    start_time = time.time()
    last_display = 0
    display_interval = 2  # Update display every 2 seconds
    
    def should_continue():
        """Check if we should continue listening"""
        if not handler.running:
            return False
        if args.duration is None:
            return True  # Unlimited duration
        return time.time() - start_time < args.duration
    
    try:
        while should_continue():
            time.sleep(0.5)
            
            # Display updates periodically
            if not args.no_display and time.time() - last_display >= display_interval:
                last_display = time.time()
                
                if not handler.competitors_df.empty:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("=" * 80)
                    print("🏎️  LIVE RACE TIMING")
                    print("=" * 80)
                    
                    # Session info
                    if not handler.session_df.empty:
                        session = handler.session_df.iloc[0]
                        print(f"🏁 {session.get('SessionName', 'N/A')} | "
                              f"🏟️ {session.get('TrackName', 'N/A')} | "
                              f"🚩 {session.get('FlagStatus', 'N/A')}")
                        print(f"⏱️ Session: {session.get('SessionTime', 'N/A')} | "
                              f"To Go: {session.get('TimeToGo', 'N/A')} | "
                              f"Laps: {session.get('LapsToGo', 'N/A')}")
                    
                    print("-" * 80)
                    
                    # Competitors table
                    display_cols = ['Pos', '#', 'Name', 'Laps', 'Best', 'Gap']
                    available_cols = [c for c in display_cols if c in handler.competitors_df.columns]
                    if available_cols:
                        df_display = handler.competitors_df[available_cols].head(20)
                        print(df_display.to_string(index=False))
                    
                    print("-" * 80)
                    elapsed = int(time.time() - start_time)
                    if args.duration:
                        remaining = args.duration - elapsed
                        print(f"⏳ Time remaining: {remaining}s | Press Ctrl+C to stop")
                    else:
                        print(f"⏳ Running for {elapsed}s | Press Ctrl+C to stop")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    
    finally:
        # Disconnect
        print("\n🔌 Disconnecting from WebSocket...")
        handler.disconnect()
        
        # Save output if requested
        if args.output:
            output_folder = os.path.join(project_root, args.output)
            os.makedirs(output_folder, exist_ok=True)
            
            if not handler.competitors_df.empty:
                competitors_file = os.path.join(output_folder, f'race_{args.race_id}_competitors.csv')
                handler.competitors_df.to_csv(competitors_file, index=False)
                print(f"💾 Saved competitors to: {competitors_file}")
            
            if not handler.session_df.empty:
                session_file = os.path.join(output_folder, f'race_{args.race_id}_session.csv')
                handler.session_df.to_csv(session_file, index=False)
                print(f"💾 Saved session to: {session_file}")
        
        print("\n✅ Done!")


if __name__ == '__main__':
    main()

