The Helios Nephrite Extractor enables seamless data extraction from the Helios Nephrite ERP system, a comprehensive enterprise resource planning solution widely used in the Czech and Slovak markets. This component connects to the Helios Nephrite REST API to retrieve business-critical data and load it into Keboola Storage for further analysis and integration.

## Key Features

**Flexible Data Loading**
The component supports both incremental and full load modes. Incremental loading fetches only new or modified records based on timestamps, making it ideal for regular synchronization jobs that minimize API calls and processing time. Full load mode extracts all records from an entity, useful for initial data loads or periodic complete refreshes.

**Multiple Business Entities**
Extract data from essential business entities including Companies (business partners), Contacts (contact persons), Employees (employee records), Products (product catalog), Departments (organizational units), Branch Offices (company locations), Resources (business resources), Warehouses (storage locations), and VAT Codes (tax definitions). This comprehensive coverage allows you to build a complete picture of your business operations.

**Intelligent Data Structuring**
The component automatically structures complex data by separating main records from nested child data. For each entity, the component outputs a main table with all scalar fields plus additional child tables for related data such as addresses, custom attributes, custom relations, categories, manufacturers, and images. All child tables include parent references for easy joins.

**Custom Attributes Support**
Helios Nephrite's custom attributes are automatically expanded into individual columns with a `custom_` prefix, making them immediately available for analysis without additional transformation steps.

**Rate Limiting & Batch Processing**
Configure the number of API requests per minute (1-600) to respect server limits and avoid throttling. Adjust batch sizes (1-10,000 records) to optimize performance based on your data volume and network conditions. Built-in exponential backoff handles transient failures gracefully.

**Authentication Options**
The component supports both standard username/password authentication and Windows authentication for environments that require it. Multiple language options (Czech, English, German, Slovak) are available for API responses.

**State Management**
The component maintains extraction state across runs, tracking timestamps and record counts per entity. This enables reliable incremental synchronization and provides visibility into extraction progress.