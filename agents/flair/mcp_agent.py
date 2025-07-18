#!/usr/bin/env python3
"""
FLAIR Product Import Manager Agent - MCP Version

This agent uses MCP servers to import FLAIR products into Odoo.
"""

import json
import os
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# Import the MCP Odoo client wrapper
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.mcp_odoo_client import MCPOdooClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlairMCPAgent:
    """FLAIR agent using MCP servers for Odoo integration."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the FLAIR agent with MCP client."""
        self.config = self.load_config(config_path)
        self.data_path = Path(self.config["data_source"])
        self.odoo_client = MCPOdooClient()
        self.products = []
        self.category_cache = {}  # Cache category IDs
        self.attribute_cache = {}  # Cache attribute IDs
        
    def load_config(self, config_path: str) -> Dict:
        """Load agent configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def initialize_categories(self):
        """Create or get all required product categories."""
        logger.info("Initializing product categories...")
        
        # Create main category
        main_category_id = self.odoo_client.get_or_create_category("FLAIR Showers")
        
        # Create sub-categories
        for category_name in self.config["product_categories"]:
            cat_id = self.odoo_client.get_or_create_category(
                category_name, 
                parent_id=main_category_id
            )
            self.category_cache[category_name] = cat_id
            logger.info(f"Category '{category_name}' ready with ID: {cat_id}")
    
    def initialize_attributes(self):
        """Create required product attributes."""
        logger.info("Initializing product attributes...")
        
        # Common attributes for FLAIR products
        attributes = {
            "Size": [],  # Will be populated from products
            "Glass Type": ["Clear Glass", "Matte Black Glass", "Frosted Glass"],
            "Door Configuration": ["Left", "Right", "Reversible"],
            "Frame Finish": ["Silver", "Matte Black", "Chrome", "Brushed Nickel"]
        }
        
        for attr_name, values in attributes.items():
            if values:  # Only create if we have predefined values
                attr_id = self.odoo_client.create_product_attribute(attr_name, values)
                self.attribute_cache[attr_name] = attr_id
    
    def load_products(self) -> List[Dict]:
        """Load all product data from JSON files."""
        products = []
        all_products_file = self.data_path / "all_products.json"
        
        if all_products_file.exists():
            with open(all_products_file, 'r') as f:
                products = json.load(f)
                logger.info(f"Loaded {len(products)} products from all_products.json")
        
        self.products = products
        return products
    
    def import_product_to_odoo(self, flair_product: Dict) -> Optional[int]:
        """
        Import a single FLAIR product to Odoo using MCP.
        
        Returns:
            Product ID if successful, None otherwise
        """
        try:
            # Check if product already exists
            existing = self._check_existing_product(flair_product)
            if existing:
                logger.info(f"Product already exists: {flair_product['product_name']} (ID: {existing['id']})")
                return existing['id']
            
            # Prepare product data
            odoo_values = self._prepare_odoo_product(flair_product)
            
            # Create the product using MCP
            product_id = self.odoo_client.create_product(odoo_values)
            logger.info(f"Created product: {flair_product['product_name']} (ID: {product_id})")
            
            # Handle product image
            self._import_product_image(product_id, flair_product)
            
            # Create variants if needed
            if self.config["import_settings"]["create_variants"]:
                self._create_product_variants(product_id, flair_product)
            
            return product_id
            
        except Exception as e:
            logger.error(f"Error importing product {flair_product.get('product_name', 'Unknown')}: {str(e)}")
            return None
    
    def _check_existing_product(self, flair_product: Dict) -> Optional[Dict]:
        """Check if product already exists in Odoo."""
        # First try by product code
        if "specifications" in flair_product:
            specs = flair_product["specifications"]
            if "door_options" in specs and specs["door_options"]:
                code = specs["door_options"][0].get("code")
                if code:
                    existing = self.odoo_client.get_product_by_code(code)
                    if existing:
                        return existing
        
        # Try by exact name match
        products = self.odoo_client.search_products(
            domain=[['name', '=', flair_product['product_name']]],
            limit=1
        )
        return products[0] if products else None
    
    def _prepare_odoo_product(self, flair_product: Dict) -> Dict:
        """Prepare product data for Odoo."""
        # Determine category
        category_name = self._determine_category(flair_product)
        category_id = self.category_cache.get(category_name, 1)
        
        # Build product values
        odoo_values = {
            "name": flair_product.get("product_name", ""),
            "type": "product",
            "categ_id": category_id,
            "sale_ok": True,
            "purchase_ok": False,
            "list_price": 0.0,  # To be set later
            "standard_price": 0.0,
            "description_sale": self._build_description(flair_product),
            "default_code": self._extract_default_code(flair_product),
            "x_vendor": "FLAIR",  # Custom field for vendor
            "x_product_url": flair_product.get("product_url", ""),  # Custom field
        }
        
        # Add basic info as custom fields
        if "basic_info" in flair_product:
            info = flair_product["basic_info"]
            if "glass_thickness" in info:
                odoo_values["x_glass_thickness"] = info["glass_thickness"]
            if "height" in info:
                odoo_values["x_standard_height"] = info["height"]
        
        return odoo_values
    
    def _determine_category(self, product: Dict) -> str:
        """Determine the product category."""
        product_name = product.get("product_name", "").lower()
        
        # Check each category keyword
        category_keywords = {
            "bifold": "Bifold Doors",
            "sliding": "Sliding Doors",
            "slider": "Sliding Doors",
            "pivot": "Pivot Doors",
            "hinge": "Hinge Doors",
            "quadrant": "Quadrant Enclosures",
            "corner": "Corner Entry"
        }
        
        for keyword, category in category_keywords.items():
            if keyword in product_name:
                return category
        
        return "Shower Enclosures"  # Default
    
    def _build_description(self, product: Dict) -> str:
        """Build product description."""
        lines = []
        
        if "basic_info" in product:
            info = product["basic_info"]
            lines.append("**Product Specifications:**")
            
            if "glass_thickness" in info:
                lines.append(f"- Glass Thickness: {info['glass_thickness']}")
            if "height" in info:
                lines.append(f"- Standard Height: {info['height']}")
            if "glass_options" in info:
                options = ", ".join(info['glass_options'])
                lines.append(f"- Glass Options: {options}")
        
        if "specifications" in product:
            specs = product["specifications"]
            if "door_options" in specs and specs["door_options"]:
                lines.append("\n**Available Configurations:**")
                for i, option in enumerate(specs["door_options"][:5]):
                    lines.append(f"- {option['code']}: {option['size']} (Adj: {option['adjustment']})")
                
                if len(specs["door_options"]) > 5:
                    lines.append(f"- Plus {len(specs['door_options']) - 5} more options")
        
        if "product_url" in product:
            lines.append(f"\n[View on FLAIR website]({product['product_url']})")
        
        return "\n".join(lines)
    
    def _extract_default_code(self, product: Dict) -> str:
        """Extract or generate default code."""
        if "specifications" in product:
            specs = product["specifications"]
            if "door_options" in specs and specs["door_options"]:
                return specs["door_options"][0].get("code", "")
        
        # Generate from name
        name_parts = product.get("product_name", "").split()
        return "FLAIR-" + "-".join([p[:3].upper() for p in name_parts[:3]])
    
    def _import_product_image(self, product_id: int, flair_product: Dict):
        """Import product image if available."""
        if not self.config["import_settings"]["image_import"]:
            return
        
        # Construct image filename
        product_name = flair_product.get("product_name", "")
        image_filename = product_name.lower().replace(" ", "_") + ".png"
        image_path = self.data_path / image_filename
        
        if image_path.exists():
            try:
                self.odoo_client.upload_product_image(product_id, str(image_path))
                logger.info(f"Uploaded image for product {product_id}")
            except Exception as e:
                logger.error(f"Failed to upload image: {str(e)}")
    
    def _create_product_variants(self, template_id: int, flair_product: Dict):
        """Create product variants based on specifications."""
        if "specifications" not in flair_product:
            return
        
        specs = flair_product["specifications"]
        variant_count = 0
        
        # Create variants for door options
        if "door_options" in specs:
            for door_option in specs["door_options"][1:]:  # Skip first (it's the main product)
                try:
                    attribute_values = {
                        "Size": door_option["size"],
                        "Code": door_option["code"],
                        "Adjustment": door_option["adjustment"]
                    }
                    
                    variant_id = self.odoo_client.create_product_variant(
                        template_id, 
                        attribute_values
                    )
                    variant_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to create variant: {str(e)}")
        
        if variant_count > 0:
            logger.info(f"Created {variant_count} variants for product {template_id}")
    
    def import_all_products(self):
        """Import all FLAIR products to Odoo."""
        if not self.products:
            self.load_products()
        
        # Initialize categories and attributes first
        self.initialize_categories()
        self.initialize_attributes()
        
        # Track import statistics
        stats = {
            "total": len(self.products),
            "imported": 0,
            "skipped": 0,
            "failed": 0,
            "start_time": datetime.now()
        }
        
        batch_size = self.config["import_settings"]["batch_size"]
        
        logger.info(f"Starting import of {stats['total']} products...")
        
        for i in range(0, stats['total'], batch_size):
            batch = self.products[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} products)")
            
            for product in batch:
                result = self.import_product_to_odoo(product)
                
                if result:
                    stats['imported'] += 1
                else:
                    stats['failed'] += 1
            
            # Report progress to GitHub
            self._report_progress(stats)
        
        # Final report
        stats['end_time'] = datetime.now()
        stats['duration'] = str(stats['end_time'] - stats['start_time'])
        
        logger.info(f"Import completed: {stats['imported']} imported, {stats['failed']} failed")
        self._create_final_report(stats)
    
    def _report_progress(self, stats: Dict):
        """Report import progress to GitHub issue."""
        progress = {
            "timestamp": datetime.now().isoformat(),
            "processed": stats['imported'] + stats['failed'],
            "total": stats['total'],
            "success_rate": (stats['imported'] / (stats['imported'] + stats['failed']) * 100) if (stats['imported'] + stats['failed']) > 0 else 0
        }
        
        # This would update GitHub issue #1 with progress
        logger.info(f"Progress: {progress['processed']}/{progress['total']} ({progress['success_rate']:.1f}% success)")
    
    def _create_final_report(self, stats: Dict):
        """Create final import report."""
        report = {
            "agent": "FLAIR Product Import Manager",
            "import_summary": stats,
            "timestamp": datetime.now().isoformat(),
            "data_source": str(self.data_path)
        }
        
        # Save report
        report_path = Path("import_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Import report saved to {report_path}")


if __name__ == "__main__":
    # Example usage
    agent = FlairMCPAgent()
    
    # For testing, just load and display info
    agent.load_products()
    
    if agent.products:
        print(f"\nLoaded {len(agent.products)} products")
        print(f"\nSample product structure:")
        print(json.dumps(agent.products[0], indent=2))
        
        # Show what would be imported
        sample_odoo = agent._prepare_odoo_product(agent.products[0])
        print(f"\nSample Odoo mapping:")
        print(json.dumps(sample_odoo, indent=2))
        
        print("\nTo import all products, run: agent.import_all_products()")
