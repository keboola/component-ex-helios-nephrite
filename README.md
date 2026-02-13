Helios Nephrite Extractor
=========================

Extracts data from Helios Nephrite ERP system via its REST API.

**Table of Contents:**

[TOC]

Prerequisites
=============

**IMPORTANT: Before using this component for the first time, you must contact Keboola support to set up the integration with your Helios Nephrite instance. This is a one-time setup required for each new client.**

Once the setup is complete, check the acknowledgment checkbox in the configuration to proceed.

Features
========

| **Feature**             | **Description**                                           |
|-------------------------|-----------------------------------------------------------|
| Generic UI Form         | Dynamic UI form for easy configuration.                   |
| Row-Based Configuration | Allows structuring the configuration in rows.             |
| Incremental Loading     | Fetch only new or modified records based on timestamp.    |
| Full Load               | Extract all records from an entity.                       |
| Rate Limiting           | Configurable requests per minute to avoid API throttling. |
| Batch Processing        | Configurable batch size for optimal performance.          |

Supported Entities
==================

The following entities can be extracted:

- **Companies** - Business partner companies
- **Contacts** - Contact persons
- **Employees** - Employee records
- **Products** - Product catalog
- **Departments** - Organizational departments
- **Branch Offices** - Company branch locations
- **Resources** - Business resources
- **Warehouses** - Warehouse locations
- **VAT Codes** - VAT/tax code definitions

If you need additional entities, please submit your request to [ideas.keboola.com](https://ideas.keboola.com/).

Configuration
=============

Connection
----------

| Parameter                    | Description                                                              | Required |
|------------------------------|--------------------------------------------------------------------------|----------|
| Server URL                   | Helios Nephrite application server URL (e.g., https://your-server.heliosnephrite.cz) | Yes      |
| User Name                    | Login username (format: DOMAIN\firstname.lastname for Windows auth)     | Yes      |
| Password                     | Login password                                                           | Yes      |
| Database Profile             | Database profile name                                                    | Yes      |
| Use Windows Authentication   | Enable Windows authentication (default: false)                           | No       |
| Language                     | Language for API responses (cs, en, de, sk). Default: en                 | No       |

Row Configuration
-----------------

| Parameter            | Description                                                    | Required |
|----------------------|----------------------------------------------------------------|----------|
| Entity               | Entity to extract (see Supported Entities above)               | Yes      |
| Output Table Name    | Custom output table name (defaults to entity name)             | No       |
| Load Type            | Loading mode: Incremental Load or Full Load                    | No       |
| Batch Size           | Number of records per API request (1-10000, default: 1000)     | No       |
| Requests Per Minute  | Rate limiting - max API requests per minute (1-600, default: 30) | No    |
| Debug Mode           | Enable verbose logging                                         | No       |

Output
======

For each entity, the component outputs:

**Main Table** (`{entity}.csv`)
- Contains all scalar fields from the entity
- Primary key: `id`
- Custom attributes are expanded to individual columns with `custom_` prefix

**Child Tables** (created as needed)
- `{entity}_addresses.csv` - Address records
- `{entity}_customAttributes.csv` - Custom attribute definitions
- `{entity}_customRelations.csv` - Custom relationships
- `{entity}_categories.csv` - Category assignments
- `{entity}_manufacturers.csv` - Manufacturer information
- `{entity}_images.csv` - Image references

All child tables include a `parent_id` column linking back to the main entity.

Development
===========

To customize the local data folder path, replace the `CUSTOM_FOLDER` placeholder with your desired path in the `docker-compose.yml` file:

```
volumes:
  - ./:/code
  - ./CUSTOM_FOLDER:/data
```

Clone this repository, initialize the workspace, and run the component using the following commands:

```
git clone https://github.com/keboola/component-ex-helios-nephrite component-helios-nephrite
cd component-helios-nephrite
docker-compose build
docker-compose run --rm dev
```

Run the test suite and perform lint checks using this command:

```
docker-compose run --rm test
```

Integration
===========

For details about deployment and integration with Keboola, refer to the [deployment section of the developer documentation](https://developers.keboola.com/extend/component/deployment/).
