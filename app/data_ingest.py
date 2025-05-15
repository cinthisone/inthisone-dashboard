import threading
import queue
import time
import requests
import json
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import logging
from pdfminer.high_level import extract_text
from PySide6.QtCore import QObject, Signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DataIngest")

class DataIngestManager(QObject):
    """
    Manages background data ingestion from various sources
    """
    # Define signals for different data types
    pdf_data_ready = Signal(str, str)  # source_id, text_content
    html_data_ready = Signal(str, str)  # source_id, html_content
    api_data_ready = Signal(str, object)  # source_id, json_data
    
    def __init__(self):
        super().__init__()
        self.task_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.session = requests.Session()
        self.active_tasks = {}  # Track active tasks by source_id
    
    def start(self):
        """Start the data ingest manager thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._worker_thread, daemon=True)
        self.thread.start()
        logger.info("Data ingest manager started")
    
    def stop(self):
        """Stop the data ingest manager thread"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        
        self.executor.shutdown(wait=False)
        logger.info("Data ingest manager stopped")
    
    def _worker_thread(self):
        """Main worker thread that processes the task queue"""
        while self.running:
            try:
                # Get task with timeout to allow checking running flag
                task = self.task_queue.get(timeout=1.0)
                if task:
                    source_id, task_type, params = task
                    
                    # Execute the appropriate task
                    if task_type == "pdf":
                        self._process_pdf(source_id, params)
                    elif task_type == "html":
                        self._process_html(source_id, params)
                    elif task_type == "api":
                        self._process_api(source_id, params)
                    
                    self.task_queue.task_done()
            
            except queue.Empty:
                # No tasks, just continue
                pass
            except Exception as e:
                logger.error(f"Error in worker thread: {e}")
    
    def _process_pdf(self, source_id, params):
        """Process a PDF file and extract text"""
        try:
            file_path = params.get("file_path")
            logger.info(f"Processing PDF: {file_path}")
            
            # Extract text from PDF
            text = extract_text(file_path)
            
            # Emit signal with results
            self.pdf_data_ready.emit(source_id, text)
            logger.info(f"PDF processed: {file_path}")
            
            # Remove from active tasks
            self.active_tasks.pop(source_id, None)
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
            self.active_tasks.pop(source_id, None)
    
    def _process_html(self, source_id, params):
        """Process an HTML page by scraping it"""
        url = params.get("url")
        selector = params.get("selector", None)
        
        try:
            logger.info(f"Scraping HTML: {url}")
            
            # Fetch the page with retries
            response = self._fetch_with_retry(url)
            
            if response and response.status_code == 200:
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract content based on selector if provided
                if selector:
                    elements = soup.select(selector)
                    content = "\n".join([el.get_text() for el in elements])
                else:
                    content = response.text
                
                # Emit signal with results
                self.html_data_ready.emit(source_id, content)
                logger.info(f"HTML scraped: {url}")
            else:
                logger.error(f"Failed to fetch HTML from {url}: {response.status_code if response else 'No response'}")
            
            # Remove from active tasks
            self.active_tasks.pop(source_id, None)
            
        except Exception as e:
            logger.error(f"Error scraping HTML {url}: {e}")
            self.active_tasks.pop(source_id, None)
    
    def _process_api(self, source_id, params):
        """Process a REST API request"""
        url = params.get("url")
        method = params.get("method", "GET")
        headers = params.get("headers", {})
        data = params.get("data", None)
        
        try:
            logger.info(f"Fetching API: {url}")
            
            # Fetch the API with retries
            response = self._fetch_with_retry(
                url, 
                method=method,
                headers=headers,
                data=data
            )
            
            if response and response.status_code == 200:
                try:
                    # Parse JSON response
                    json_data = response.json()
                    
                    # Emit signal with results
                    self.api_data_ready.emit(source_id, json_data)
                    logger.info(f"API data fetched: {url}")
                except ValueError:
                    logger.error(f"Invalid JSON response from {url}")
            else:
                logger.error(f"Failed to fetch API from {url}: {response.status_code if response else 'No response'}")
            
            # Remove from active tasks
            self.active_tasks.pop(source_id, None)
            
        except Exception as e:
            logger.error(f"Error fetching API {url}: {e}")
            self.active_tasks.pop(source_id, None)
    
    def _fetch_with_retry(self, url, method="GET", headers=None, data=None, max_retries=3, backoff_factor=1.5):
        """Fetch a URL with exponential backoff retry logic"""
        headers = headers or {}
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, headers=headers, timeout=10)
                elif method.upper() == "POST":
                    response = self.session.post(url, headers=headers, json=data, timeout=10)
                elif method.upper() == "PUT":
                    response = self.session.put(url, headers=headers, json=data, timeout=10)
                elif method.upper() == "DELETE":
                    response = self.session.delete(url, headers=headers, timeout=10)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                return response
                
            except requests.RequestException as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Max retries reached for {url}: {e}")
                    return None
                
                # Calculate backoff time
                backoff_time = backoff_factor ** retry_count
                logger.info(f"Retrying {url} in {backoff_time:.2f} seconds (attempt {retry_count}/{max_retries})")
                time.sleep(backoff_time)
    
    def ingest_pdf(self, source_id, file_path):
        """Queue a PDF file for ingestion"""
        if source_id in self.active_tasks:
            logger.info(f"Task for {source_id} already in queue, skipping")
            return False
        
        params = {"file_path": file_path}
        self.task_queue.put((source_id, "pdf", params))
        self.active_tasks[source_id] = "pdf"
        return True
    
    def ingest_html(self, source_id, url, selector=None):
        """Queue an HTML page for ingestion"""
        if source_id in self.active_tasks:
            logger.info(f"Task for {source_id} already in queue, skipping")
            return False
        
        params = {"url": url, "selector": selector}
        self.task_queue.put((source_id, "html", params))
        self.active_tasks[source_id] = "html"
        return True
    
    def ingest_api(self, source_id, url, method="GET", headers=None, data=None):
        """Queue a REST API request for ingestion"""
        if source_id in self.active_tasks:
            logger.info(f"Task for {source_id} already in queue, skipping")
            return False
        
        params = {
            "url": url,
            "method": method,
            "headers": headers or {},
            "data": data
        }
        self.task_queue.put((source_id, "api", params))
        self.active_tasks[source_id] = "api"
        return True