# Tile Agents

Multi-agent system for managing vendor data imports and product synchronization with Odoo.

## Overview

This repository contains project manager agents for different tile vendors. Each agent is responsible for:
- Importing product data from vendor sources
- Mapping vendor data to Odoo product structures
- Managing product variants and specifications
- Handling image imports and associations
- Coordinating with other agents through the MCP server

## Agents

### FLAIR Agent
- **Issue**: [#1](https://github.com/jayo2005/tile_agents/issues/1)
- **Data Source**: `/mnt/z_drive/Danny Flair/`
- **Website**: https://flairshowers.com/
- **Status**: In Development

## Architecture

Each vendor agent:
1. Reads vendor-specific data from scraped sources
2. Transforms data to match Odoo product structure
3. Uses MCP servers (Odoo, GitHub, Puppeteer) for operations
4. Reports status and issues to the MCP server Agent

## MCP Servers

- **GitHub**: Issue tracking and code management
- **Odoo**: Product creation and management
- **Puppeteer**: Web scraping when needed

## Development

Each agent should be developed following the structure defined in their respective GitHub issues.
