**BANK FRAUD DETECTION PIPELINE**
A comprehensive Snowflake data pipeline demonstrating real-time fraud detection using Dynamic Tables for automatic incremental refresh and multi-layer data architecture.

📋 Overview
This project showcases a production-ready fraud detection system built entirely in Snowflake, leveraging Dynamic Tables to automatically process and analyze transaction data without manual orchestration. The pipeline monitors banking transactions, identifies suspicious patterns, and provides analytics-ready data for fraud monitoring dashboards.

🎯 Key Features

Automatic Data Refresh: Dynamic Tables handle incremental updates without manual triggers
Three-Layer Architecture: Raw → Clean → Analytics layers for data quality and separation of concerns
Real-Time Fraud Monitoring: Continuous risk assessment with configurable refresh intervals
Dependency Management: Snowflake automatically tracks and refreshes dependent tables
BI-Ready Analytics: Pre-aggregated tables optimized for dashboards and reporting

🏗️ Architecture

<img width="782" height="675" alt="image" src="https://github.com/user-attachments/assets/a3f9d7dc-cf92-4702-91cc-5e5db7abcbd3" />


📦 Prerequisites

Snowflake account with appropriate privileges
COMPUTE_WH warehouse (or modify warehouse name in code)
Permission to create databases, schemas, tables, and dynamic tables

🚀 Setup Instructions

Step 1: Clone and Execute

Copy the entire SQL script to your Snowflake worksheet
Execute the script section by section (recommended) or all at once
The script will create:

Database: fraud_demo
Schemas: raw, analytics
1 raw data table
3 dynamic tables



Step 2: Verify Setup
sql-- Check database and schemas
SHOW DATABASES LIKE 'fraud_demo';
SHOW SCHEMAS IN DATABASE fraud_demo;

-- Verify tables
SHOW TABLES IN DATABASE fraud_demo;
SHOW DYNAMIC TABLES IN DATABASE fraud_demo;
Step 3: Load Demo Data
The script includes sample data with:

3 legitimate transactions
2 suspicious transactions (high risk)
3 confirmed fraud transactions

Execute the INSERT statements in Step 3 to populate the raw table.
🔄 How Dynamic Tables Work
Dynamic Tables automatically refresh based on the TARGET_LAG parameter:
TableTarget LagPurposetransactions_clean1 minuteNear real-time filtered datadaily_transaction_summary5 minutesBusiness metrics aggregationfraud_risk_summary2 minutesFraud monitoring metrics
Target Lag indicates acceptable freshness delay. Snowflake determines optimal refresh timing and method (full or incremental).

📊 Data Model
transactions_raw (Source Table)
Contains all incoming transaction data with fraud indicators:

Transaction details (ID, timestamp, amount, type)
Customer and account information
Merchant details and categorization
Location and device data
Fraud indicators (flag, risk score, status)

transactions_clean (Dynamic Table)
Filtered view containing only approved, legitimate transactions for clean analytics.
daily_transaction_summary (Dynamic Table)
Aggregated daily metrics including:

Total transactions and amounts by category/country
Average transaction amounts
Risk score statistics
Unique customer counts

fraud_risk_summary (Dynamic Table)
Fraud-focused analytics including:

Fraud counts and rates by country
Declined and pending review transactions
Total fraud amounts blocked
Average risk scores

🧪 Testing the Pipeline
Test Automatic Refresh
Insert new data into the raw table:
sqlINSERT INTO fraud_demo.raw.transactions_raw VALUES
(1012, CURRENT_TIMESTAMP, 50007, 107, 99.99, 'PURCHASE', 
 'Online Store', 'RETAIL', 'Toronto', 'Canada', 
 'DEV005', '192.168.1.110', FALSE, 0.10, 'APPROVED');
Wait for the target lag period (1-5 minutes depending on table), then query the dynamic tables to see the new data automatically propagated.

📈 Analytics Queries
The project includes ready-to-use queries for:

Daily Transaction Summary: View transaction volumes and amounts by date
Fraud Risk by Country: Identify high-risk geographic regions
High-Risk Countries Analysis: Aggregate fraud metrics for risk assessment

Execute these queries from Step 7 of the script.

🔍 Monitoring & Observability
Check Dynamic Table Status
sqlSHOW DYNAMIC TABLES IN DATABASE fraud_demo;
View Refresh History
sqlSELECT 
    name,
    target_lag_sec,
    state,
    refresh_end_time,
    refresh_action,
    refresh_trigger
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
    NAME => 'fraud_demo.analytics.transactions_clean'
));

💡 Key Concepts Demonstrated
Incremental Processing: Dynamic Tables eliminate the need for streams and tasks
Dependency Management: Snowflake tracks table dependencies automatically
Layered Architecture: Separation of raw, clean, and analytics layers
Real-Time Analytics: Configurable refresh intervals for near real-time insights
No Manual Orchestration: Snowflake handles refresh scheduling and execution

🛠️ Customization
Adjust Refresh Frequency
Modify the TARGET_LAG in CREATE DYNAMIC TABLE statements:
Lower values = fresher data, higher compute costs
Higher values = lower costs, less fresh data

Change Warehouse
Replace WAREHOUSE = compute_wh with your warehouse name.
Extend Analytics
Add new dynamic tables following the same pattern to create additional aggregations or transformations.

📝 Author
Vincent Mbira

📄 License
This project is provided as-is for educational and demonstration purposes.

🤝 Contributing
Feel free to fork this project and adapt it for your specific fraud detection needs. Consider adding:
- Additional fraud detection rules
- Machine learning model integration
- Alert mechanisms for high-risk transactions

Historical trend analysis tables
