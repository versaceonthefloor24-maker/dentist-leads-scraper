"""
Google Sheets integration module
Handles reading/writing dentist leads to Google Sheets
"""

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
import gspread
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class GoogleSheetsHandler:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
              'https://www.googleapis.com/auth/drive']
    
    def __init__(self, spreadsheet_id, sheet_name):
        """
        Initialize Google Sheets handler
        
        Args:
            spreadsheet_id (str): Google Sheets ID
            sheet_name (str): Sheet name in the spreadsheet
        """
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.client = self.authenticate()
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)
        self.worksheet = self.get_or_create_worksheet()
    
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            # Try to use service account credentials
            if os.path.exists('service_account.json'):
                creds = Credentials.from_service_account_file(
                    'service_account.json',
                    scopes=self.SCOPES
                )
                logger.info("Using service account credentials")
            else:
                # Use OAuth flow for user credentials
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json',
                    scopes=self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("Using OAuth user credentials")
            
            return gspread.authorize(creds)
        
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    def get_or_create_worksheet(self):
        """Get existing worksheet or create a new one"""
        try:
            worksheet = self.spreadsheet.worksheet(self.sheet_name)
            logger.info(f"Using existing worksheet: {self.sheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title=self.sheet_name,
                rows=1000,
                cols=10
            )
            # Add headers
            headers = ["Name", "Address", "Phone", "Website", "Email", "Scraped Date"]
            worksheet.append_row(headers)
            logger.info(f"Created new worksheet: {self.sheet_name}")
        
        return worksheet
    
    def add_leads(self, leads):
        """
        Add dentist leads to Google Sheets
        
        Args:
            leads (list): List of lead dictionaries
        """
        try:
            rows = []
            
            for lead in leads:
                emails = lead.get('emails', [])
                email_str = ', '.join(emails) if emails else 'Not found'
                
                row = [
                    lead.get('name', 'Unknown'),
                    lead.get('address', 'Unknown'),
                    lead.get('phone', 'Unknown'),
                    lead.get('website', 'Unknown'),
                    email_str,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
                rows.append(row)
            
            if rows:
                self.worksheet.append_rows(rows)
                logger.info(f"Successfully added {len(rows)} leads to Google Sheets")
            else:
                logger.warning("No leads to add")
        
        except Exception as e:
            logger.error(f"Error adding leads to Google Sheets: {str(e)}")
            raise
    
    def get_leads(self):
        """
        Retrieve all leads from Google Sheets
        
        Returns:
            list: List of lead dictionaries
        """
        try:
            all_records = self.worksheet.get_all_records()
            logger.info(f"Retrieved {len(all_records)} leads from Google Sheets")
            return all_records
        
        except Exception as e:
            logger.error(f"Error retrieving leads: {str(e)}")
            return []