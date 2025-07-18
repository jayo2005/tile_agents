"""
Data mapping utilities for FLAIR products to Odoo.
"""

from typing import Dict, List, Any, Optional
import re


class FlairToOdooMapper:
    """Maps FLAIR product data to Odoo product structure."""
    
    # Product category mappings
    CATEGORY_MAPPINGS = {
        "bifold": "Bifold Doors",
        "sliding": "Sliding Doors",
        "slider": "Sliding Doors",
        "pivot": "Pivot Doors",
        "hinge": "Hinge Doors",
        "quadrant": "Quadrant Enclosures",
        "corner": "Corner Entry",
        "frameless": "Frameless Enclosures"
    }
    
    # Glass option mappings
    GLASS_MAPPINGS = {
        "Silver": "Clear Glass",
        "MatteBlack": "Matte Black Glass",
        "8mm": "8mm Tempered Glass",
        "10mm": "10mm Tempered Glass"
    }
    
    @staticmethod
    def map_product(flair_product: Dict) -> Dict:
        """Map a FLAIR product to Odoo product format."""
        return {
            "name": flair_product.get("product_name", ""),
            "type": "product",
            "sale_ok": True,
            "purchase_ok": False,
            "list_price": 0.0,  # To be determined
            "standard_price": 0.0,
            "categ_id": FlairToOdooMapper.get_category(flair_product),
            "default_code": FlairToOdooMapper.extract_product_code(flair_product),
            "barcode": None,
            "description_sale": FlairToOdooMapper.build_description(flair_product),
            "weight": 0.0,
            "volume": 0.0,
            "product_template_attribute_value_ids": FlairToOdooMapper.map_attributes(flair_product)
        }
    
    @staticmethod
    def get_category(product: Dict) -> str:
        """Determine product category based on product name."""
        product_name = product.get("product_name", "").lower()
        
        for keyword, category in FlairToOdooMapper.CATEGORY_MAPPINGS.items():
            if keyword in product_name:
                return category
        
        return "Shower Enclosures"  # Default category
    
    @staticmethod
    def extract_product_code(product: Dict) -> str:
        """Extract or generate product code."""
        # Try to get from specifications
        if "specifications" in product:
            specs = product["specifications"]
            if "door_options" in specs and specs["door_options"]:
                return specs["door_options"][0].get("code", "")
        
        # Generate from product name
        name = product.get("product_name", "")
        # Extract uppercase letters and numbers
        code_parts = re.findall(r'[A-Z]+|\d+', name)
        return "FLAIR-" + "".join(code_parts[:3])
    
    @staticmethod
    def build_description(product: Dict) -> str:
        """Build a comprehensive product description."""
        lines = []
        
        # Add basic info
        if "basic_info" in product:
            info = product["basic_info"]
            lines.append("Product Specifications:")
            
            if "glass_thickness" in info:
                lines.append(f"- Glass Thickness: {info['glass_thickness']}")
            if "height" in info:
                lines.append(f"- Standard Height: {info['height']}")
            if "glass_options" in info:
                options = ", ".join(info['glass_options'])
                lines.append(f"- Available Glass Options: {options}")
        
        # Add size options
        if "specifications" in product:
            specs = product["specifications"]
            
            if "door_options" in specs and specs["door_options"]:
                lines.append("\nAvailable Sizes:")
                for option in specs["door_options"][:5]:  # Show first 5
                    lines.append(f"- {option['size']} (Adjustable: {option['adjustment']})")
                
                if len(specs["door_options"]) > 5:
                    lines.append(f"... and {len(specs['door_options']) - 5} more sizes")
        
        # Add product URL if available
        if "product_url" in product:
            lines.append(f"\nMore details: {product['product_url']}")
        
        return "\n".join(lines)
    
    @staticmethod
    def map_attributes(product: Dict) -> List[Dict]:
        """Map product attributes for variants."""
        attributes = []
        
        # Glass options
        if "basic_info" in product and "glass_options" in product["basic_info"]:
            for glass_option in product["basic_info"]["glass_options"]:
                attributes.append({
                    "attribute_id": "glass_type",
                    "value": FlairToOdooMapper.GLASS_MAPPINGS.get(glass_option, glass_option)
                })
        
        # Size options from specifications
        if "specifications" in product and "door_options" in product["specifications"]:
            for door_option in product["specifications"]["door_options"]:
                attributes.append({
                    "attribute_id": "size",
                    "value": door_option["size"],
                    "extra_info": {
                        "adjustment": door_option["adjustment"],
                        "code": door_option["code"]
                    }
                })
        
        return attributes
    
    @staticmethod
    def create_variant_dict(base_product: Dict, attribute_values: Dict) -> Dict:
        """Create a product variant dictionary."""
        variant = base_product.copy()
        
        # Update name with variant info
        variant_suffix = " - ".join([f"{k}: {v}" for k, v in attribute_values.items()])
        variant["name"] = f"{base_product['name']} ({variant_suffix})"
        
        # Update SKU
        if "size" in attribute_values:
            size_code = re.sub(r'[^A-Z0-9]', '', attribute_values["size"].upper())
            variant["default_code"] = f"{base_product['default_code']}-{size_code}"
        
        return variant
