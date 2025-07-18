#!/usr/bin/env python3
"""
FLAIR Product Import Manager Agent

This agent manages the import of FLAIR shower products into Odoo.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlairAgent:
    def __init__(self, config_path: str = "config.json"):
        """Initialize the FLAIR agent with configuration."""
        self.config = self.load_config(config_path)
        self.data_path = Path(self.config["data_source"])
        self.products = []
        
    def load_config(self, config_path: str) -> Dict:
        """Load agent configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def load_products(self) -> List[Dict]:
        """Load all product data from JSON files."""
        products = []
        all_products_file = self.data_path / "all_products.json"
        
        if all_products_file.exists():
            with open(all_products_file, 'r') as f:
                products = json.load(f)
                logger.info(f"Loaded {len(products)} products from all_products.json")
        else:
            # Load individual product files
            for json_file in self.data_path.glob("*.json"):
                if json_file.name != "all_products.json":
                    with open(json_file, 'r') as f:
                        product = json.load(f)
                        products.append(product)
            logger.info(f"Loaded {len(products)} products from individual files")
        
        self.products = products
        return products
    
    def map_to_odoo_product(self, flair_product: Dict) -> Dict:
        """Map FLAIR product data to Odoo product structure."""
        # This is a basic mapping - will be expanded based on Odoo requirements
        odoo_product = {
            "name": flair_product.get("product_name", ""),
            "type": "product",
            "categ_id": self._get_category_id(flair_product),
            "list_price": 0.0,  # Will need pricing logic
            "standard_price": 0.0,
            "description": self._build_description(flair_product),
            "default_code": self._generate_default_code(flair_product),
        }
        
        return odoo_product
    
    def _get_category_id(self, product: Dict) -> int:
        """Determine the Odoo category ID based on product type."""
        # This will need to be mapped to actual Odoo category IDs
        product_name = product.get("product_name", "").lower()
        
        if "bifold" in product_name:
            return 1  # Placeholder - actual ID needed
        elif "sliding" in product_name or "slider" in product_name:
            return 2
        elif "pivot" in product_name:
            return 3
        elif "hinge" in product_name:
            return 4
        elif "quadrant" in product_name:
            return 5
        else:
            return 0  # Default category
    
    def _build_description(self, product: Dict) -> str:
        """Build product description from specifications."""
        desc_parts = []
        
        if "basic_info" in product:
            info = product["basic_info"]
            if "glass_thickness" in info:
                desc_parts.append(f"Glass Thickness: {info['glass_thickness']}")
            if "height" in info:
                desc_parts.append(f"Height: {info['height']}")
            if "glass_options" in info:
                desc_parts.append(f"Glass Options: {', '.join(info['glass_options'])}")
        
        return "\n".join(desc_parts)
    
    def _generate_default_code(self, product: Dict) -> str:
        """Generate a default code/SKU for the product."""
        # Extract from specifications if available
        if "specifications" in product and "door_options" in product["specifications"]:
            door_options = product["specifications"]["door_options"]
            if door_options and "code" in door_options[0]:
                return door_options[0]["code"]
        
        # Fallback to product name based code
        name_parts = product.get("product_name", "").split()
        return "FLAIR-" + "-".join([part[:3].upper() for part in name_parts[:3]])
    
    def create_variants(self, product: Dict) -> List[Dict]:
        """Create product variants based on specifications."""
        variants = []
        
        if "specifications" not in product:
            return variants
        
        specs = product["specifications"]
        
        # Create variants for door options
        if "door_options" in specs:
            for door_option in specs["door_options"]:
                variant = {
                    "name": f"{product['product_name']} - {door_option['size']}",
                    "default_code": door_option["code"],
                    "attribute_values": {
                        "size": door_option["size"],
                        "adjustment": door_option["adjustment"]
                    }
                }
                variants.append(variant)
        
        return variants
    
    def import_products(self, batch_size: int = None):
        """Import products to Odoo in batches."""
        if batch_size is None:
            batch_size = self.config["import_settings"]["batch_size"]
        
        if not self.products:
            self.load_products()
        
        total_products = len(self.products)
        imported = 0
        
        for i in range(0, total_products, batch_size):
            batch = self.products[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} products)")
            
            for product in batch:
                try:
                    # Map to Odoo structure
                    odoo_product = self.map_to_odoo_product(product)
                    
                    # Create variants if enabled
                    if self.config["import_settings"]["create_variants"]:
                        variants = self.create_variants(product)
                        logger.info(f"Product '{product['product_name']}' has {len(variants)} variants")
                    
                    # TODO: Actually create the product in Odoo using MCP
                    logger.info(f"Would import: {odoo_product['name']}")
                    imported += 1
                    
                except Exception as e:
                    logger.error(f"Error importing product {product.get('product_name', 'Unknown')}: {str(e)}")
        
        logger.info(f"Import complete. Processed {imported}/{total_products} products")
        return imported
    
    def report_status(self):
        """Report agent status to GitHub issue."""
        # TODO: Use GitHub MCP to update issue #1 with status
        status = {
            "total_products": len(self.products),
            "categories": len(self.config["product_categories"]),
            "data_source": str(self.data_path)
        }
        logger.info(f"Agent Status: {json.dumps(status, indent=2)}")
        return status


if __name__ == "__main__":
    # Example usage
    agent = FlairAgent()
    agent.load_products()
    status = agent.report_status()
    
    # Test mapping
    if agent.products:
        sample = agent.map_to_odoo_product(agent.products[0])
        print(f"\nSample Odoo mapping:\n{json.dumps(sample, indent=2)}")
        
        # Test variant creation
        variants = agent.create_variants(agent.products[0])
        print(f"\nSample variants ({len(variants)}):")
        for variant in variants[:3]:  # Show first 3
            print(f"  - {variant['name']} ({variant['default_code']})")
