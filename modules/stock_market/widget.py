from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QGridLayout,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont
import requests
import json
from datetime import datetime, timedelta
import os

class StockWidget(QFrame):
    """Widget to display individual stock information"""
    def __init__(self, symbol, data, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.data = data
        self._init_ui()
        
    def _init_ui(self):
        layout = QGridLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Symbol
        symbol_label = QLabel(self.symbol)
        symbol_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: palette(text);
        """)
        layout.addWidget(symbol_label, 0, 0)
        
        # Current Price
        price = float(self.data.get('close', 0))
        price_label = QLabel(f"${price:.2f}")
        price_label.setStyleSheet("color: palette(text); font-size: 14px;")
        layout.addWidget(price_label, 0, 1)
        
        # Change
        open_price = float(self.data.get('open', price))  # Use close as fallback
        change = price - open_price
        change_pct = (change / open_price) * 100 if open_price else 0
        change_color = "green" if change >= 0 else "red"
        change_text = f"{'+' if change >= 0 else ''}{change:.2f} ({change_pct:.1f}%)"
        change_label = QLabel(change_text)
        change_label.setStyleSheet(f"color: {change_color}; font-size: 14px;")
        layout.addWidget(change_label, 0, 2)
        
        # High/Low
        high_low = QLabel(f"H: ${float(self.data.get('high', 0)):.2f} L: ${float(self.data.get('low', 0)):.2f}")
        high_low.setStyleSheet("color: palette(text); font-size: 12px;")
        layout.addWidget(high_low, 1, 1, 1, 2)
        
        self.setLayout(layout)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            StockWidget {
                border: 1px solid palette(mid);
                border-radius: 5px;
                background-color: palette(base);
            }
        """)
        
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

class StockMarketWidget(QWidget):
    """Widget to display stock market information"""
    def __init__(self, db_manager, ingest_manager):
        super().__init__()
        self.db_manager = db_manager
        self.widget_id = "stock_market"
        
        # Load API keys from environment or settings
        self.api_key = os.getenv('ALPACA_API_KEY') or self.db_manager.get_widget_setting(
            self.widget_id, "api_key", ""
        )
        self.api_secret = os.getenv('ALPACA_API_SECRET') or self.db_manager.get_widget_setting(
            self.widget_id, "api_secret", ""
        )
        
        self._init_ui()
        
        # Set up refresh timer (every minute)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(60 * 1000)  # Update every minute
        
        # Load saved symbols
        self.load_symbols()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Settings section
        settings_layout = QHBoxLayout()
        
        # Symbol input
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Enter stock symbol (e.g., AAPL)")
        settings_layout.addWidget(self.symbol_input)
        
        # API key input
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter Alpaca API Key")
        self.api_key_input.setText(self.api_key)
        settings_layout.addWidget(self.api_key_input)
        
        # API secret input
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setPlaceholderText("Enter Alpaca API Secret")
        self.api_secret_input.setText(self.api_secret)
        self.api_secret_input.setEchoMode(QLineEdit.Password)
        settings_layout.addWidget(self.api_secret_input)
        
        # Add button
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_symbol)
        settings_layout.addWidget(add_btn)
        
        # Update button
        update_btn = QPushButton("Update All")
        update_btn.clicked.connect(self.update_stocks)
        settings_layout.addWidget(update_btn)
        
        layout.addLayout(settings_layout)
        
        # Container for stock widgets
        self.stocks_container = QWidget()
        self.stocks_layout = QVBoxLayout()
        self.stocks_layout.setSpacing(10)
        self.stocks_container.setLayout(self.stocks_layout)
        
        layout.addWidget(self.stocks_container)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Set size policies
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    
    def sizeHint(self):
        return QSize(600, 400)
    
    def minimumSizeHint(self):
        return QSize(400, 200)
    
    def add_symbol(self):
        """Add a new stock symbol to track"""
        symbol = self.symbol_input.text().strip().upper()
        if not symbol:
            return
            
        # Save API keys if provided
        new_api_key = self.api_key_input.text().strip()
        new_api_secret = self.api_secret_input.text().strip()
        
        if new_api_key and new_api_secret:
            self.api_key = new_api_key
            self.api_secret = new_api_secret
            self.db_manager.set_widget_setting(self.widget_id, "api_key", self.api_key)
            self.db_manager.set_widget_setting(self.widget_id, "api_secret", self.api_secret)
        
        # Get current symbols
        symbols = self.db_manager.get_widget_setting(self.widget_id, "symbols", "").split(",")
        symbols = [s.strip() for s in symbols if s.strip()]
        
        # Add new symbol if not already present
        if symbol not in symbols:
            symbols.append(symbol)
            self.db_manager.set_widget_setting(
                self.widget_id, "symbols", ",".join(symbols)
            )
        
        # Clear input
        self.symbol_input.clear()
        
        # Update display
        self.update_stocks()
    
    def update_stocks(self):
        """Update stock information"""
        try:
            if not self.api_key or not self.api_secret:
                print("API credentials not provided")
                return
            
            # Get symbols
            symbols = self.db_manager.get_widget_setting(self.widget_id, "symbols", "").split(",")
            symbols = [s.strip() for s in symbols if s.strip()]
            
            if not symbols:
                return
            
            # Get stock data from Alpaca
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret
            }
            
            # First try to get account info to verify credentials
            account_url = "https://paper-api.alpaca.markets/v2/account"
            print(f"\nChecking account access...")
            account_response = requests.get(account_url, headers=headers)
            print(f"Account check response: {account_response.status_code}")
            print(f"Account response: {account_response.text}")
            
            if account_response.status_code != 200:
                print("Failed to authenticate with Alpaca API. Please verify your API credentials.")
                return
            
            # Get latest quotes from paper trading API
            quotes_url = "https://paper-api.alpaca.markets/v2/stocks/quotes/latest"
            
            # Map common indices to their tradeable symbols
            symbol_map = {
                "SPX": "SPY",  # S&P 500 ETF
                "DJI": "DIA",  # Dow Jones ETF
                "IXIC": "QQQ"  # NASDAQ ETF
            }
            
            # Map symbols to their tradeable equivalents and remove duplicates
            mapped_symbols = list(set(symbol_map.get(sym, sym) for sym in symbols))
            
            params = {
                "symbols": ",".join(mapped_symbols)
            }
            
            print(f"\nMaking request to Alpaca API with key: {self.api_key[:8]}...")
            print(f"Requesting data for symbols: {mapped_symbols}")
            
            response = requests.get(quotes_url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"API Error: {response.status_code}")
                print(f"Response: {response.text}")
                print(f"Request URL: {response.url}")
                return
                
            data = response.json()
            print(f"\nReceived data: {json.dumps(data, indent=2)}")
            
            # Update display with quote data
            self._update_stocks_display(data.get('quotes', {}))
            
        except Exception as e:
            print(f"Error updating stocks: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    def _update_stocks_display(self, stocks_data):
        """Update the stocks display"""
        try:
            # Clear existing widgets
            while self.stocks_layout.count():
                item = self.stocks_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add new stock widgets
            for symbol, quote in stocks_data.items():
                if quote:  # Check if we have data for this symbol
                    # Convert quote data to bar-like format for compatibility
                    bar_data = {
                        'close': quote.get('ap', 0),  # Ask price as current
                        'open': quote.get('ap', 0),   # Use ask price as reference
                        'high': quote.get('ap', 0),
                        'low': quote.get('bp', 0)     # Bid price as low
                    }
                    stock_widget = StockWidget(symbol, bar_data)
                    self.stocks_layout.addWidget(stock_widget)
            
        except Exception as e:
            print(f"Error updating stocks display: {str(e)}")
    
    def load_symbols(self):
        """Load saved symbols and update display"""
        try:
            symbols = self.db_manager.get_widget_setting(self.widget_id, "symbols", "")
            if symbols:
                self.update_stocks()
                
        except Exception as e:
            print(f"Error loading symbols: {str(e)}")
    
    def refresh(self):
        """Refresh the stock data"""
        self.update_stocks()

def register_plugin():
    """Register this widget with the plugin system"""
    return {
        "name": "Stock Market",
        "title": "Stock Market",
        "description": "Display real-time stock market information",
        "widget_class": StockMarketWidget
    } 