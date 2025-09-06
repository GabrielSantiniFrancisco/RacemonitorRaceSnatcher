import threading, websocket, traceback
import pandas as pd
from typing import Dict
from dataclasses import dataclass, field
from enum import Enum
from CustomLogger import CustomLogger 
from EnvManager import EnvManager 

class SortMode(Enum):
    RACE = 0
    QUALIFYING = 1

@dataclass
class Competitor:
    racer_id: str = ""
    number: str = ""
    transponder: str = ""
    first_name: str = ""
    last_name: str = ""
    nationality: str = ""
    additional_data: str = ""
    category: str = ""
    category_description: str = ""
    position: str = ""
    laps: str = ""
    total_time: str = ""
    total_time_milliseconds: int = 0
    best_position: str = ""
    best_lap: str = ""
    best_time: str = ""
    best_time_milliseconds: int = 0
    last_lap_time: str = ""
    last_split_time: str = ""
    data_updated: bool = False
    calculated_diff: str = ""  
    calculated_gap: str = ""   
    display_position: str = ""
    sort_mode: int = 0

    def set_total_time(self, time_str: str, logger:CustomLogger):
        if time_str and time_str != "00:59:59.999":
            self.total_time = time_str
            self.total_time_milliseconds = self.convert_time_to_milliseconds(time_str, logger)
        else:
            self.total_time = time_str
            self.total_time_milliseconds = 0

    def set_best_time(self, time_str: str, logger:CustomLogger):
        if time_str and time_str != "00:59:59.999":
            self.best_time = time_str
            self.best_time_milliseconds = self.convert_time_to_milliseconds(time_str, logger)
        else:
            self.best_time = time_str
            self.best_time_milliseconds = 0

    @staticmethod
    def convert_time_to_milliseconds(time_str: str, logger:CustomLogger) -> int:
        try:
            if not time_str or time_str == "00:59:59.999": return 0

            if '.' in time_str:
                time_part, ms_part = time_str.split('.')
                milliseconds = int(ms_part)
            else:
                time_part = time_str
                milliseconds = 0

            parts = [int(p) for p in time_part.split(':')]
            while len(parts) < 3: parts.insert(0, 0) 

            hours, minutes, seconds = parts
            total_ms = (
                hours * 60 * 60 * 1000 +
                minutes * 60 * 1000 +
                seconds * 1000 +
                milliseconds
            )
            return total_ms
        except Exception as e:
            logger.error(f"Error converting time '{time_str}': {e}")
            logger.debug(f'\n{traceback.format_exc()}')
            return 0

@dataclass
class RaceClass:
    class_id: str = ""
    description: str = ""

@dataclass
class Session:
    session_id: str = ""
    session_name: str = ""
    track_name: str = ""
    track_length: str = ""
    current_time: str = ""
    session_time: str = ""
    time_to_go: str = ""
    laps_to_go: str = ""
    flag_status: str = ""
    sort_mode: SortMode = SortMode.RACE
    classes: Dict[str, RaceClass] = field(default_factory=dict)
    competitors: Dict[str, Competitor] = field(default_factory=dict)
    sorted_competitors: list = field(default_factory=list)

    def get_competitor(self, racer_id: str) -> Competitor:
        if racer_id not in self.competitors:
            self.competitors[racer_id] = Competitor(racer_id=racer_id)
        return self.competitors[racer_id]

    def sort_competitors(self):
        competitors_list = list(self.competitors.values())
        
        if self.sort_mode == SortMode.QUALIFYING:
            # Sort by best time (fastest first)
            competitors_list.sort(key=lambda x: (
                x.best_time_milliseconds if x.best_time_milliseconds > 0 else float('inf'),
                self.get_position_number(x.best_position)
            ))
        else:
            # Sort by position, then by laps (descending), then by total time
            competitors_list.sort(key=lambda x: (
                self.get_position_number(x.position),
                -int(x.laps) if x.laps.isdigit() else 0,
                x.total_time_milliseconds if x.total_time_milliseconds > 0 else float('inf')
            ))
        
        self.sorted_competitors = competitors_list

    def get_position_number(self, position: str) -> int:
        try:
            value = int(position) if position and position.isdigit() else 9999
            return value
        except Exception as e:
            return 9999

    def reset_session(self):
        self.classes.clear()
        self.competitors.clear()
        self.session_id = ""
        self.session_name = ""
        self.track_name = ""
        self.current_time = ""
        self.session_time = ""
        self.time_to_go = ""
        self.laps_to_go = ""
        self.flag_status = ""
        self.sorted_competitors.clear()

    def calculate_gaps_and_diffs(self):
        """Calculate gap and diff for all competitors based on their sorted positions"""
        if not self.sorted_competitors:
            return
        
        # Leader gets no gap/diff
        if len(self.sorted_competitors) > 0:
            self.sorted_competitors[0].calculated_gap = ""
            self.sorted_competitors[0].calculated_diff = ""
        
        for i in range(1, len(self.sorted_competitors)):
            current = self.sorted_competitors[i]
            previous = self.sorted_competitors[i-1]
            leader = self.sorted_competitors[0]
            
            # Skip calculation if current competitor has no valid time
            if current.total_time_milliseconds == 0:
                current.calculated_gap = ""
                current.calculated_diff = ""
                continue
            
            # Calculate gap (to previous competitor)
            current.calculated_gap = self._calculate_time_difference(
                current, previous, current.best_time_milliseconds
            )
            
            # Calculate diff (to leader)
            current.calculated_diff = self._calculate_time_difference(
                current, leader, current.best_time_milliseconds
            )

    def _calculate_time_difference(self, slower_competitor: 'Competitor', faster_competitor: 'Competitor', slower_best_lap_ms: int) -> str:
        """Calculate time difference between two competitors"""
        if faster_competitor.total_time_milliseconds == 0:
            return ""
        
        # Check lap difference
        slower_laps = int(slower_competitor.laps) if slower_competitor.laps.isdigit() else 0
        faster_laps = int(faster_competitor.laps) if faster_competitor.laps.isdigit() else 0
        lap_diff = faster_laps - slower_laps
        
        # If lap difference exists and time difference > slower's best lap, show +X LAP
        if lap_diff > 0:
            time_diff_ms = slower_competitor.total_time_milliseconds - faster_competitor.total_time_milliseconds
            if slower_best_lap_ms > 0 and time_diff_ms > slower_best_lap_ms:
                return f"+{lap_diff} LAP" if lap_diff == 1 else f"+{lap_diff} LAPS"
        
        # Calculate time difference
        time_diff_ms = abs(slower_competitor.total_time_milliseconds - faster_competitor.total_time_milliseconds)
        return self._format_time_difference(time_diff_ms)

    def _format_time_difference(self, time_diff_ms: int) -> str:
        """Format time difference in milliseconds to readable format"""
        if time_diff_ms == 0:
            return ""
        
        hours = time_diff_ms // (60 * 60 * 1000)
        minutes = (time_diff_ms % (60 * 60 * 1000)) // (60 * 1000)
        seconds = (time_diff_ms % (60 * 1000)) // 1000
        milliseconds = time_diff_ms % 1000
        
        if hours > 0:
            return f"+{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        elif minutes > 0:
            return f"+{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        else:
            return f"+{seconds:02d}.{milliseconds:03d}"

class RaceTimingHandler:
    def __init__(self, caller_script: str, config_file_path: str, transaction_id: str = None):
        self.session = Session()
        self.websocket = None
        self.running = False
        self.listen_thread = None

        self.competitors_df = pd.DataFrame()
        self.session_df = pd.DataFrame()

        self.env = EnvManager(config_file_path)
        logging_config = self.env.config.get('logging_config', {})
        self.logger = CustomLogger(config=logging_config, logger_name=caller_script, transaction_id=transaction_id)
        formatted_config = "\n".join([f"{key}: {value}" for key, value in self.env.config.items() if 'API_KEY' not in key])
        self.logger.info("Environment variables and logger initialized successfully")
        self.logger.debug(f"Configuration values set:\n{formatted_config}")

    def connect(self, ws_url: str):
        """Connect to the WebSocket and start handling data in a background thread"""

        self.logger.info(f"Connecting to WebSocket URL: {ws_url}")
        try:
            self.websocket = websocket.WebSocketApp(ws_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close)
            self.running = True

            # Start listening in a thread
            self.listen_thread = threading.Thread(target=self.websocket.run_forever)
            self.listen_thread.start()
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            self.logger.debug(f'\n{traceback.format_exc()}') 
            self.running = False

    def disconnect(self):
        """Disconnect from WebSocket"""
        self.running = False
        if self.websocket: self.websocket.close()
        if self.listen_thread and self.listen_thread.is_alive(): self.listen_thread.join()
        self.logger.info("WebSocket connection closed")

    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        self.logger.debug(f"Received message:\n{message}")
        self.process_data(message)

    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        self.logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        self.logger.warning("WebSocket connection closed")
        self.running = False

    def process_data(self, data: str):
        """Process incoming data messages"""
        data_updated = False
        lines = data.strip().split('\n')
        
        for line in lines:
            if not line.strip(): continue
            try:
                elements = [element.replace('"', '') for element in line.split(',')]
                if not elements: continue
                command = elements[0]
                match command:
                    case "$F":      self.handle_race_progress_data(elements)
                    case "$A":      self.handle_driver_data(elements)
                    case "$B":      self.handle_race_session_data(elements)
                    case "$C":      self.handle_race_class_data(elements)
                    case "$COMP":   self.handle_extended_driver_data(elements)
                    case "$E":      self.handle_track_data(elements)
                    case "$G":      self.handle_race_position_data(elements)
                    case "$H":      self.handle_best_lap_time_data(elements)
                    case "$I":      self.handle_reset_data()
                    case "$J":      self.handle_last_lap_time_data(elements)
                    case "$RMS":    self.handle_sort_mode_data(elements)
                data_updated = True
            except Exception as e:
                self.logger.error(f"Error processing line '{line}': {str(e)}")
                continue
        
        if data_updated: self.handle_session_update()

    def handle_race_progress_data(self, elements: list):
        """Handle flag/timing information ($F)"""
        if len(elements) >= 6:
            self.session.laps_to_go = elements[1]
            self.session.time_to_go = elements[2]
            self.session.current_time = elements[3]
            self.session.session_time = elements[4]
            self.session.flag_status = elements[5].strip()

    def handle_driver_data(self, elements: list):
        """Handle competitor information ($A)"""
        if len(elements) >= 8:
            competitor = self.session.get_competitor(elements[1])
            competitor.number = elements[2]
            competitor.transponder = elements[3]
            competitor.first_name = elements[4]
            competitor.last_name = elements[5]
            competitor.nationality = elements[6]
            competitor.category = elements[7]

    def handle_race_session_data(self, elements: list):
        """Handle session information ($B)"""
        if len(elements) >= 3:
            self.session.session_id = elements[1]
            self.session.session_name = elements[2]

    def handle_race_class_data(self, elements: list):
        """Handle class information ($C)"""
        if len(elements) >= 3:
            race_class = RaceClass()
            race_class.class_id = elements[1]
            race_class.description = elements[2]
            self.session.classes[race_class.class_id] = race_class

    def handle_extended_driver_data(self, elements: list):
        """Handle extended competitor information ($COMP)"""
        if len(elements) >= 8:
            competitor = self.session.get_competitor(elements[1])
            competitor.number = elements[2]
            competitor.category = elements[3]
            competitor.first_name = elements[4]
            competitor.last_name = elements[5]
            competitor.nationality = elements[6]
            competitor.additional_data = elements[7]

    def handle_track_data(self, elements: list):
        """Handle track information ($E)"""
        if len(elements) >= 3:
            if elements[1] == "TRACKNAME":
                self.session.track_name = elements[2]
            elif elements[1] == "TRACKLENGTH":
                self.session.track_length = elements[2]

    def handle_race_position_data(self, elements: list):
        """Handle position/timing data ($G)"""
        if len(elements) >= 5:
            competitor = self.session.get_competitor(elements[2])
            new_position = elements[1]
            new_laps = elements[3]
            new_total_time = elements[4]
            
            if (competitor.position != new_position or 
                competitor.laps != new_laps or 
                competitor.total_time != new_total_time):
                competitor.data_updated = True
                
            competitor.position = new_position
            competitor.laps = new_laps
            competitor.set_total_time(new_total_time, self.logger)

    def handle_best_lap_time_data(self, elements: list):
        """Handle best lap data ($H)"""
        if len(elements) >= 5:
            competitor = self.session.get_competitor(elements[2])
            new_best_position = elements[1]
            new_best_lap = elements[3]
            new_best_time = elements[4]
            
            if (competitor.best_position != new_best_position or 
                competitor.best_lap != new_best_lap or 
                competitor.best_time != new_best_time):
                competitor.data_updated = True
                
            competitor.best_position = new_best_position
            competitor.best_lap = new_best_lap
            competitor.set_best_time(new_best_time, self.logger)

    def handle_reset_data(self):
        """Handle reset session ($I)"""
        self.session.reset_session()

    def handle_last_lap_time_data(self, elements: list):
        """Handle lap time data ($J)"""
        if len(elements) >= 4:
            competitor = self.session.get_competitor(elements[1])
            competitor.last_lap_time = elements[2]
            competitor.set_total_time(elements[3], self.logger)
            competitor.data_updated = True

    def handle_sort_mode_data(self, elements: list):
        """Handle sort mode ($RMS)"""
        if len(elements) >= 2:
            if elements[1] == "qualifying":
                self.session.sort_mode = SortMode.QUALIFYING
            else:
                self.session.sort_mode = SortMode.RACE

    def handle_session_update(self):
        """Handle session updates - sort competitors and process changes, return session and competitors as pandas DataFrames"""

        self.session.sort_competitors()
        self.session.calculate_gaps_and_diffs()

        # Competitors DataFrame
        competitors_data = []
        for i, competitor in enumerate(self.session.sorted_competitors):
            pos = competitor.position if competitor.position else str(i + 1)
            name = f"{competitor.first_name} {competitor.last_name}".strip()
            if not name:
                name = f"Driver {competitor.racer_id}"

            competitors_data.append({
                "Pos": pos,
                "#": competitor.number,
                "Name": name,
                "Laps": competitor.laps,
                "Time": competitor.total_time if competitor.total_time else "-",
                "Best": competitor.best_time if competitor.best_time else "-",
                "Diff": competitor.calculated_diff if competitor.calculated_diff else "-",
                "Gap": competitor.calculated_gap if competitor.calculated_gap else "-",
                "RacerID": competitor.racer_id,
                "Transponder": competitor.transponder,
                "Category": competitor.category,
                "CategoryDesc": competitor.category_description,
                "BestLap": competitor.best_lap,
                "LastLap": competitor.last_lap_time,
            })

            competitor.data_updated = False

        self.competitors_df = pd.DataFrame(competitors_data)

        # Session DataFrame (single row)
        session_data = {
            "SessionID": self.session.session_id,
            "SessionName": self.session.session_name,
            "TrackName": self.session.track_name,
            "TrackLength": self.session.track_length,
            "CurrentTime": self.session.current_time,
            "SessionTime": self.session.session_time,
            "TimeToGo": self.session.time_to_go,
            "LapsToGo": self.session.laps_to_go,
            "FlagStatus": self.session.flag_status,
            "SortMode": self.session.sort_mode.name,
        }
        self.session_df = pd.DataFrame([session_data])

    def get_competitors(self) -> Dict[str, Competitor]:
        """Retrieve all competitors"""
        return self.session.competitors

    def get_session_info(self) -> Dict:
        """Retrieve session information"""
        return {
            "session_id": self.session.session_id,
            "session_name": self.session.session_name,
            "track_name": self.session.track_name,
            "track_length": self.session.track_length,
            "current_time": self.session.current_time,
            "session_time": self.session.session_time,
            "time_to_go": self.session.time_to_go,
            "laps_to_go": self.session.laps_to_go,
            "flag_status": self.session.flag_status,
            "sort_mode": self.session.sort_mode.name,
        }