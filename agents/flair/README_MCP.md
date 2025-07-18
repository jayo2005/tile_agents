# FLAIR Agent - MCP Implementation

## Overview

The FLAIR MCP Agent (`mcp_agent.py`) uses MCP servers directly for all Odoo operations, eliminating the need for custom scripts or modules.

## MCP Server Usage

### Odoo MCP Server
Used for:
- Creating products: `mcp__ODOO16__create`
- Searching products: `mcp__ODOO16__search_read`
- Updating products: `mcp__ODOO16__write`
- Managing categories and attributes

### GitHub MCP Server
Used for:
- Progress reporting to issue #1
- Error logging
- Status updates

### Puppeteer MCP Server
Used for:
- Additional web scraping from flairshowers.com if needed
- Verifying product information
- Downloading updated images

## Import Process

1. **Initialize Categories**: Creates FLAIR product category hierarchy
2. **Initialize Attributes**: Sets up product attributes (Size, Glass Type, etc.)
3. **Load Products**: Reads from JSON files in data directory
4. **Import Products**: For each product:
   - Check if already exists (by code or name)
   - Create product with all specifications
   - Upload product image
   - Create variants for different sizes/configurations
5. **Report Progress**: Updates GitHub issue with import status

## Usage

```python
from agents.flair.mcp_agent import FlairMCPAgent

# Initialize agent
agent = FlairMCPAgent()

# Run full import
agent.import_all_products()
```

## Product Mapping

FLAIR products are mapped to Odoo with:
- Standard fields: name, type, category, description
- Custom fields: x_vendor, x_product_url, x_glass_thickness, x_standard_height
- Variants: Created for each size/configuration option

## Error Handling

- Products that fail to import are logged but don't stop the process
- Existing products are skipped (no duplicates)
- Progress is reported even if errors occur
- Final report shows success/failure statistics

## Configuration

The agent uses `config.json` for:
- Data source path
- Batch size for imports
- Image import settings
- MCP server settings
