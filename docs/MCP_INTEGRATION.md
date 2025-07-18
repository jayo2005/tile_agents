# MCP Server Integration Guide

## Overview

The tile_agents project uses MCP (Model Context Protocol) servers for all external integrations. This eliminates the need for custom scripts or modules.

## Available MCP Servers

### 1. Odoo MCP Server (`mcp__ODOO16__*`)

**Functions:**
- `search_read`: Search and retrieve records
- `create`: Create new records
- `write`: Update existing records
- `unlink`: Delete records
- `fields_get`: Get field definitions for a model

**Example Usage:**
```python
# Create a product
product_id = mcp__ODOO16__create(
    model="product.product",
    values={
        "name": "FLAIR Bifold Door",
        "type": "product",
        "list_price": 299.99
    }
)

# Search for products
products = mcp__ODOO16__search_read(
    model="product.product",
    domain=[["name", "ilike", "FLAIR"]],
    fields=["id", "name", "list_price"],
    limit=10
)
```

### 2. GitHub MCP Server (`mcp__github__*`)

**Functions:**
- `create_issue`: Create new issues
- `create_issue_comment`: Add comments to issues
- `add_issue_labels`: Add labels to issues
- `close_issue`: Close issues
- `push_files`: Push files to repository

**Example Usage:**
```python
# Update issue with progress
mcp__github__create_issue_comment(
    owner="jayo2005",
    repo="tile_agents",
    issue_number=1,
    body="Import progress: 50/100 products completed"
)
```

### 3. Puppeteer MCP Server (`mcp__puppeteer__*`)

**Functions:**
- `puppeteer_navigate`: Navigate to URL
- `puppeteer_screenshot`: Take screenshots
- `puppeteer_click`: Click elements
- `puppeteer_fill`: Fill form fields
- `puppeteer_evaluate`: Execute JavaScript

**Example Usage:**
```python
# Navigate to product page
mcp__puppeteer__puppeteer_navigate(
    url="https://flairshowers.com/products/bifold-door"
)

# Take screenshot
mcp__puppeteer__puppeteer_screenshot(
    name="bifold_door_page",
    selector=".product-image"
)
```

## Best Practices

### 1. Error Handling
Always wrap MCP calls in try-except blocks:
```python
try:
    result = mcp__ODOO16__create(model="product.product", values=data)
except Exception as e:
    logger.error(f"Failed to create product: {str(e)}")
```

### 2. Batch Operations
For multiple operations, batch when possible:
```python
# Good: Single search for multiple products
products = mcp__ODOO16__search_read(
    model="product.product",
    domain=[["default_code", "in", product_codes]],
    fields=["id", "name", "default_code"]
)

# Avoid: Multiple individual searches
for code in product_codes:
    product = mcp__ODOO16__search_read(...)
```

### 3. Field Validation
Check required fields before creating records:
```python
required_fields = ["name", "type"]
for field in required_fields:
    if field not in values:
        raise ValueError(f"Missing required field: {field}")
```

### 4. Progress Reporting
Report progress regularly for long operations:
```python
for i, batch in enumerate(batches):
    # Process batch
    ...
    
    # Report progress
    if i % 10 == 0:
        mcp__github__create_issue_comment(
            owner="jayo2005",
            repo="tile_agents",
            issue_number=1,
            body=f"Progress: {i * batch_size}/{total} processed"
        )
```

## Odoo Model Reference

### Product Models
- `product.product`: Product variants
- `product.template`: Product templates
- `product.category`: Product categories
- `product.attribute`: Product attributes (Size, Color, etc.)
- `product.attribute.value`: Attribute values

### Common Fields
- `name`: Product name
- `default_code`: SKU/Internal Reference
- `list_price`: Sale price
- `standard_price`: Cost price
- `type`: 'product', 'service', or 'consu'
- `categ_id`: Category ID
- `image_1920`: Main product image (base64)

## Testing MCP Calls

Before running full imports, test with single products:
```python
# Test creating a single product
test_product = {
    "name": "TEST - FLAIR Door",
    "type": "product",
    "list_price": 99.99
}

try:
    product_id = mcp__ODOO16__create(
        model="product.product",
        values=test_product
    )
    print(f"Created test product with ID: {product_id}")
    
    # Clean up
    mcp__ODOO16__unlink(
        model="product.product",
        ids=[product_id]
    )
except Exception as e:
    print(f"Test failed: {str(e)}")
```
