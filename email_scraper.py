"""
Email scraper module
Extracts email addresses from dentist websites
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class EmailScraper:
    def __init__(self, timeout=10):
        """
        Initialize email scraper
        
        Args:
            timeout (int): Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
    
    def extract_emails(self, website_url):
        """
        Extract email addresses from a website
        
        Args:
            website_url (str): URL of the website
            
        Returns:
            list: List of unique email addresses found
        """
        try:
            if not website_url or not website_url.startswith('http'):
                return []
            
            emails = set()
            
            # Fetch the main page
            emails.update(self._scrape_page(website_url))
            
            # Try common contact pages
            base_url = self._get_base_url(website_url)
            contact_pages = [
                f"{base_url}/contact",
                f"{base_url}/contact-us",
                f"{base_url}/about",
                f"{base_url}/about-us"
            ]
            
            for contact_url in contact_pages:
                emails.update(self._scrape_page(contact_url))
            
            # Remove noreply and no-reply addresses
            emails = {
                email for email in emails
                if 'noreply' not in email.lower() and 'no-reply' not in email.lower()
            }
            
            return list(emails)
        
        except Exception as e:
            logger.warning(f"Error extracting emails from {website_url}: {str(e)}")
            return []
    
    def _scrape_page(self, url):
        """
        Scrape a single page for email addresses
        
        Args:
            url (str): URL to scrape
            
        Returns:
            set: Set of email addresses found
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # Find all emails
            emails = set(self.email_pattern.findall(text))
            
            logger.debug(f"Found {len(emails)} emails on {url}")
            
            return emails
        
        except requests.exceptions.RequestException as e:
            logger.debug(f"Error fetching {url}: {str(e)}")
            return set()
        except Exception as e:
            logger.debug(f"Error parsing {url}: {str(e)}")
            return set()
    
    def _get_base_url(self, url):
        """Extract base URL from a given URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"