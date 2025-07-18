"""
Base class for all vendor agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging
import json
from pathlib import Path


class BaseVendorAgent(ABC):
    """Abstract base class for vendor agents."""
    
    def __init__(self, config_path: str):
        """Initialize the agent with configuration."""
        self.config = self.load_config(config_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setup_logging()
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def setup_logging(self):
        """Set up logging for the agent."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(level=logging.INFO, format=log_format)
    
    @abstractmethod
    def load_products(self) -> List[Dict]:
        """Load products from the vendor data source."""
        pass
    
    @abstractmethod
    def map_to_odoo_product(self, vendor_product: Dict) -> Dict:
        """Map vendor product to Odoo product structure."""
        pass
    
    @abstractmethod
    def create_variants(self, product: Dict) -> List[Dict]:
        """Create product variants based on vendor specifications."""
        pass
    
    @abstractmethod
    def import_products(self, batch_size: Optional[int] = None) -> int:
        """Import products to Odoo."""
        pass
    
    def report_status(self) -> Dict:
        """Report agent status."""
        return {
            "agent": self.config.get("agent_name", "Unknown"),
            "vendor": self.config.get("vendor", "Unknown"),
            "status": "active"
        }
    
    def handle_error(self, error: Exception, context: str = ""):
        """Handle and log errors."""
        self.logger.error(f"Error in {context}: {str(error)}")
        # Could also report to GitHub issue here
    
    def validate_product(self, product: Dict) -> bool:
        """Validate product data before import."""
        required_fields = ["name", "type"]
        for field in required_fields:
            if field not in product or not product[field]:
                self.logger.warning(f"Product missing required field: {field}")
                return False
        return True
