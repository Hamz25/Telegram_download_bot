import csv
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

REPORTS_CSV = 'reports.csv'
REPORTS_PENDING_JSON = 'reports_pending.json'

def get_or_create_reports_csv():
    """Ensure reports CSV file exists with headers."""
    if not os.path.exists(REPORTS_CSV):
        with open(REPORTS_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['report_id', 'user_id', 'username', 'message', 'timestamp', 'status', 'admin_response'])
    return REPORTS_CSV

def save_report(user_id: int, username: Optional[str], message: str) -> str:
    """
    Save a user report.
    
    Args:
        user_id: User's Telegram ID
        username: User's username
        message: Report message
        
    Returns:
        str: Report ID
    """
    csv_path = get_or_create_reports_csv()
    report_id = f"RPT_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                report_id,
                user_id,
                username or 'Unknown',
                message,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'pending',
                ''
            ])
        print(f"✅ Report saved: {report_id}")
        return report_id
    except Exception as e:
        print(f"❌ Error saving report: {e}")
        return None

def get_pending_reports() -> List[Dict]:
    """
    Get all pending reports.
    
    Returns:
        List of report dictionaries
    """
    csv_path = get_or_create_reports_csv()
    reports = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['status'] == 'pending':
                    reports.append(row)
    except Exception as e:
        print(f"⚠️ Error reading reports: {e}")
    
    return reports

def get_all_reports() -> List[Dict]:
    """
    Get all reports (pending and resolved).
    
    Returns:
        List of report dictionaries
    """
    csv_path = get_or_create_reports_csv()
    reports = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                reports.append(row)
    except Exception as e:
        print(f"⚠️ Error reading reports: {e}")
    
    return reports

def mark_report_resolved(report_id: str, admin_response: str = "") -> bool:
    """
    Mark a report as resolved.
    
    Args:
        report_id: Report ID
        admin_response: Admin's response message
        
    Returns:
        bool: True if successful
    """
    csv_path = get_or_create_reports_csv()
    reports = []
    found = False
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['report_id'] == report_id:
                    row['status'] = 'resolved'
                    row['admin_response'] = admin_response
                    found = True
                reports.append(row)
        
        if found:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                if reports:
                    writer = csv.DictWriter(f, fieldnames=reports[0].keys())
                    writer.writeheader()
                    writer.writerows(reports)
            print(f"✅ Report {report_id} marked as resolved")
            return True
    except Exception as e:
        print(f"❌ Error updating report: {e}")
    
    return False

def get_report_count() -> int:
    """Get total number of reports."""
    return len(get_all_reports())

def get_pending_count() -> int:
    """Get number of pending reports."""
    return len(get_pending_reports())
