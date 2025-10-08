"""
Data export utilities for test results
"""

import csv
import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class DataExporter:
    """Export test data to various formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def export_to_csv(self, export_data: Dict[str, Any], output_path: str) -> bool:
        """Export session data to CSV format"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            base_name = os.path.splitext(output_path)[0]
            
            # Export session summary
            summary_path = f"{base_name}_summary.csv"
            self._export_summary_csv(export_data['session_info'], summary_path)
            
            # Export latency data
            if export_data['latency_data']:
                latency_path = f"{base_name}_latency.csv"
                self._export_timeseries_csv(export_data['latency_data'], latency_path, 'Latency (s)')
            
            # Export bandwidth data
            if export_data['bandwidth_data']:
                bandwidth_path = f"{base_name}_bandwidth.csv"
                self._export_timeseries_csv(export_data['bandwidth_data'], bandwidth_path, 'Bandwidth (bytes/s)')
            
            # Export error logs
            if export_data['error_logs']:
                errors_path = f"{base_name}_errors.csv"
                self._export_errors_csv(export_data['error_logs'], errors_path)
            
            self.logger.info(f"Data exported to CSV: {base_name}_*.csv")
            return True
            
        except Exception as e:
            self.logger.error(f"CSV export failed: {e}")
            return False
    
    def export_to_json(self, export_data: Dict[str, Any], output_path: str) -> bool:
        """Export session data to JSON format"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Add export metadata
            export_data['export_metadata'] = {
                'export_timestamp': datetime.now().isoformat(),
                'export_format': 'json',
                'exporter_version': '1.0.0'
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Data exported to JSON: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"JSON export failed: {e}")
            return False
    
    def _export_summary_csv(self, session_info: Dict[str, Any], output_path: str):
        """Export session summary to CSV"""
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Metric', 'Value'])
            
            # Convert timestamp to readable format
            timestamp = datetime.fromtimestamp(session_info['timestamp'])
            
            # Write summary data
            summary_data = [
                ['Session ID', session_info['id']],
                ['Test Date', timestamp.strftime('%Y-%m-%d %H:%M:%S')],
                ['Test Mode', session_info['mode']],
                ['Duration (s)', session_info['duration']],
                ['Packet Size (bytes)', session_info['packet_size']],
                ['Transmission Rate (pkt/s)', session_info['transmission_rate']],
                ['Packets Sent', session_info['packets_sent']],
                ['Packets Received', session_info['packets_received']],
                ['Packets Lost', session_info['packets_lost']],
                ['Packet Loss Rate (%)', session_info['packet_loss_rate']],
                ['Bytes Transmitted', session_info['bytes_transmitted']],
                ['Average Latency (s)', session_info['average_latency']],
                ['Average Bandwidth (bytes/s)', session_info['average_bandwidth']],
                ['Notes', session_info.get('notes', '')]
            ]
            
            writer.writerows(summary_data)
    
    def _export_timeseries_csv(self, data: List[tuple], output_path: str, value_column: str):
        """Export time series data to CSV"""
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Timestamp', 'Time (s)', value_column])
            
            # Write data
            for timestamp, value in data:
                readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                writer.writerow([readable_time, timestamp, value])
    
    def _export_errors_csv(self, error_logs: List[tuple], output_path: str):
        """Export error logs to CSV"""
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Timestamp', 'Time (s)', 'Error Message'])
            
            # Write error data
            for timestamp, error_message in error_logs:
                readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                writer.writerow([readable_time, timestamp, error_message])
    
    def create_export_summary(self, sessions: List[Dict[str, Any]], output_path: str) -> bool:
        """Create a summary CSV of multiple sessions"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                header = [
                    'Session ID', 'Date', 'Mode', 'Duration (s)', 'Packet Size', 
                    'Rate (pkt/s)', 'Sent', 'Received', 'Lost', 'Loss Rate (%)',
                    'Bytes', 'Avg Latency (s)', 'Avg Bandwidth (bytes/s)', 'Notes'
                ]
                writer.writerow(header)
                
                # Write session data
                for session in sessions:
                    timestamp = datetime.fromtimestamp(session['timestamp'])
                    row = [
                        session['id'],
                        timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        session['mode'],
                        session['duration'],
                        session['packet_size'],
                        session['transmission_rate'],
                        session['packets_sent'],
                        session['packets_received'],
                        session['packets_lost'],
                        session['packet_loss_rate'],
                        session['bytes_transmitted'],
                        session['average_latency'],
                        session['average_bandwidth'],
                        session.get('notes', '')
                    ]
                    writer.writerow(row)
            
            self.logger.info(f"Session summary exported: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Summary export failed: {e}")
            return False
