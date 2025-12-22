# 🏎️ RacemonitorRaceSnatcher

_"Pay for data? Nah fam, we boost the browser's keys and slide into the WSS like it's our own pit lane — just to drop clean race data on stream and make it look like we shelled out for the VIP package."_

---

## ⚡ What's This?

RacemonitorRaceSnatcher is a scrappy little pit-crew script that:

- 🔑 **Boosts** the API key straight outta your browser (no shame).
- 📡 **Slides** into the RaceMonitor websocket feed like it owns the joint.
- 📺 **Pipes** that sweet, sweet live telemetry into your own broadcast stream.

In short: it's the sketchy middleman that makes your stream look pro without burning a hole in your wallet.

---

## 📋 Requirements

- **Python 3.10+**
- **Google Chrome** (for Selenium headless browser)
- **ChromeDriver** (auto-managed by Selenium 4.6+)

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/RacemonitorRaceSnatcher.git
cd RacemonitorRaceSnatcher
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🏁 Usage

The project has **two main modules** that work together:

### Step 1: Get WebSocket Credentials (`GetRaceMonitorKeyModule.py`)

This module extracts the WebSocket URL and authentication key from RaceMonitor.

```python
import sys
sys.path.insert(0, 'lib')

from GetRaceMonitorKeyModule import RaceMonitorKeyRetriever

# Initialize with config path
retriever = RaceMonitorKeyRetriever(
    caller_script='my_script',
    config_file_path='conf/GetRaceMonitorKeyModule.cfg'
)

# Get WSS link and key for a race ID
wss_link, wss_key = retriever.get_link_and_key('37820')

print(f"WSS Link: {wss_link}")
print(f"WSS Key: {wss_key}")
```

**Output example:**

```
WSS Link: wss://cluster1.race-monitor.com/instance/22/someid
WSS Key: <wsskey>
```

### Step 2: Connect and Receive Race Data (`RaceTimeHandlerModule.py`)

This module connects to the WebSocket and provides two DataFrames:

- **Competitors DataFrame**: Driver positions, lap times, gaps
- **Session DataFrame**: Track info, session time, flag status

```python
import sys
import time
sys.path.insert(0, 'lib')

from RaceTimeHandlerModule import RaceTimingHandler

# Initialize with config path
handler = RaceTimingHandler(
    caller_script='my_script',
    config_file_path='conf/RaceTimeHandlerModule.cfg'
)

# Connect using the WSS link from Step 1
handler.connect(wss_link)

# Listen for data
time.sleep(10)  # Wait for data to arrive

# Access the DataFrames
print("=== COMPETITORS ===")
print(handler.competitors_df)

print("\n=== SESSION ===")
print(handler.session_df)

# Disconnect when done
handler.disconnect()
```

---

## 🎯 Quick Start (All-in-One)

Use the `main.py` script for a complete workflow:

```bash
# Activate virtual environment
source venv/bin/activate

# Run with a Race ID
python main.py <RACE_ID>

# Examples:
python main.py 37820                      # Connect to race 37820
python main.py 37820 --duration 60        # Listen for 60 seconds
python main.py 37820 --output results     # Save CSV files
python main.py 37820 --no-display         # Silent mode (no terminal output)
```

### Command Line Options

| Option         | Description                    | Default |
| -------------- | ------------------------------ | ------- |
| `race_id`      | RaceMonitor Race ID (required) | -       |
| `--duration`   | Duration to listen in seconds  | 30      |
| `--output`     | Output folder for CSV files    | None    |
| `--no-display` | Disable live terminal display  | False   |

---

## 📁 Project Structure

```
RacemonitorRaceSnatcher/
├── main.py                          # All-in-one entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── conf/
│   ├── GetRaceMonitorKeyModule.cfg  # Config for key retrieval
│   └── RaceTimeHandlerModule.cfg    # Config for timing handler
├── lib/
│   ├── CustomLogger.py              # Structured logging utility
│   ├── EnvManager.py                # Configuration manager
│   ├── GetRaceMonitorKeyModule.py   # WebSocket credential extractor
│   └── RaceTimeHandlerModule.py     # Race timing data handler
└── logs/                            # Log files (auto-created)
```

---

## 🔧 How It Works

### Module 1: GetRaceMonitorKeyModule

1. Launches a **headless Chrome browser** using Selenium
2. Navigates to `https://api.race-monitor.com/Timing/?raceid=<RACE_ID>`
3. Captures **browser performance logs**
4. Extracts the **WebSocket URL** and **Sec-WebSocket-Key** from network requests
5. Returns both values for use with RaceTimeHandlerModule

### Module 2: RaceTimeHandlerModule

1. **Connects** to the WebSocket URL obtained from Module 1
2. **Receives and parses** real-time race timing messages
3. **Updates two DataFrames** with the latest data:
   - `competitors_df`: All driver/competitor data
   - `session_df`: Session/track information

#### Protocol Messages Decoded

| Command | Description          | Example Data               |
| ------- | -------------------- | -------------------------- |
| `$F`    | Race progress        | Time, laps, flag status    |
| `$A`    | Driver info          | Number, name, nationality  |
| `$B`    | Session info         | Session ID, name           |
| `$C`    | Class info           | Class ID, description      |
| `$COMP` | Extended driver data | Additional competitor info |
| `$E`    | Track info           | Track name, length         |
| `$G`    | Position data        | Position, laps, total time |
| `$H`    | Best lap data        | Best position, lap, time   |
| `$I`    | Reset session        | Clears all data            |
| `$J`    | Last lap time        | Lap time, total time       |
| `$RMS`  | Sort mode            | Race or Qualifying         |

---

## 📊 Output DataFrames

### Competitors DataFrame (`handler.competitors_df`)

| Column       | Description          |
| ------------ | -------------------- |
| Pos          | Current position     |
| #            | Car number           |
| Name         | Driver name          |
| Laps         | Laps completed       |
| Time         | Total race time      |
| Best         | Best lap time        |
| Diff         | Difference to leader |
| Gap          | Gap to car ahead     |
| RacerID      | Unique racer ID      |
| Transponder  | Transponder ID       |
| Category     | Race category        |
| CategoryDesc | Category description |
| BestLap      | Best lap number      |
| LastLap      | Last lap time        |

### Session DataFrame (`handler.session_df`)

| Column      | Description                         |
| ----------- | ----------------------------------- |
| SessionID   | Session identifier                  |
| SessionName | Name of session                     |
| TrackName   | Track name                          |
| TrackLength | Track length                        |
| CurrentTime | Current time                        |
| SessionTime | Session elapsed time                |
| TimeToGo    | Time remaining                      |
| LapsToGo    | Laps remaining                      |
| FlagStatus  | Current flag (Green/Yellow/Red/etc) |
| SortMode    | RACE or QUALIFYING                  |

---

## 🔍 Finding a Race ID

1. Go to [Race-Monitor.com/Live](https://www.race-monitor.com/Live)
2. Click on any live race
3. Copy the race ID from the URL: `race-monitor.com/Live/Race/37820` → ID is **37820**

---

## 🐛 Troubleshooting

### Chrome/ChromeDriver Issues

```bash
pip install --upgrade selenium
```

Selenium 4.6+ automatically manages ChromeDriver.

### WebSocket Connection Failed

- Verify the race ID is valid and the race is currently live
- Check your internet connection
- Some races may have additional protection

### No Data Displayed

- The race might not be active
- Wait a few seconds for data to arrive
- Check the logs in `logs/` folder for errors

---

## ⚠️ Disclaimer

This is a _for-educational-purposes-only_ hackjob.  
If you run it on an actual event, don’t @ us when the pit wall lawyers start calling.

---

## :exclamation: Don't panic kiddo, this is under construction
