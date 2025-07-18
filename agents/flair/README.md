# FLAIR Product Import Agent

This agent manages the import of FLAIR shower products into Odoo.

## Overview

The FLAIR agent is responsible for:
- Reading product data from scraped JSON files
- Mapping FLAIR product attributes to Odoo fields
- Creating product variants for different sizes and options
- Managing product images
- Reporting import status

## Data Source

- **Location**: `/mnt/z_drive/Danny Flair/product_data/`
- **Format**: JSON files with product specifications
- **Images**: PNG files for each product

## Usage

```python
from agents.flair.agent import FlairAgent

# Initialize agent
agent = FlairAgent()

# Load products
agent.load_products()

# Import to Odoo
agent.import_products(batch_size=10)

# Check status
status = agent.report_status()
```

## Product Structure

FLAIR products have the following structure:
- **Basic Info**: Glass thickness, height, glass options
- **Specifications**: Door options with codes, sizes, and adjustments
- **Variants**: Different sizes and configurations

## MCP Integration

The agent uses:
- **Odoo MCP**: For creating products and variants
- **GitHub MCP**: For status reporting to issue #1
- **Puppeteer MCP**: For additional web scraping if needed

## Configuration

See `config.json` for agent settings including:
- Data source path
- Product categories
- Import batch size
- MCP server settings
