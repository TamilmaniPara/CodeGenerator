# Create Jira Data Element Task

You are operating inside a VS Code repository.

Your objective is to:

1. Read the review configuration JSON.
2. Analyze the complete codebase associated with the review.
3. Identify all external data inputs used by the code.
4. Generate the Jira task content.
5. Save the generated task definition to `jira/generated_jira_task.json`.
6. Execute the Python Jira creation script.
7. Create the Jira Task immediately.

Do NOT use Jira MCP, Jira integration, browser automation, or any other Jira integration.

Jira creation must be performed by the Python script.

---

# STEP 1 — READ CONFIGURATION

Read:

`config/review_config.json`

The JSON contains:

```text
jira.epic_key
review.id
review.name
metadata
data_sources
```

Do not assume that the metadata contains only predefined fields.

Read every key/value pair under `metadata`.

The Epic key must come from:

`jira.epic_key`

The Review ID must come from:

`review.id`

The Review Name must come from:

`review.name`

Do not invent these values.

---

# STEP 2 — ANALYZE THE CODEBASE

Analyze the source code associated with this review.

The objective is to identify every external data input actually consumed by the application.

Search the entire relevant repository, not just one Python file.

Trace function and method calls where necessary.

Look for:

* SQL queries
* Database connections
* Database clients
* Database tables
* Database views
* Database columns
* Excel files
* CSV files
* JSON files
* YAML files
* S3
* APIs
* File readers
* Data access classes
* DAO/repository classes
* Helper functions
* Shared libraries
* Configuration-driven queries
* Dynamically constructed SQL
* DataFrame reads
* Spark reads

Examples of code patterns to investigate include:

```text
pd.read_sql
pd.read_sql_query
pd.read_excel
pd.read_csv
cursor.execute
connection.execute
SELECT
FROM
JOIN
spark.read
boto3
requests
httpx
openpyxl
yaml.safe_load
json.load
```

These are examples only. Inspect the actual technologies used by the repository.

---

# STEP 3 — TRACE INDIRECT DATA SOURCES

Do not stop at the first function.

For example:

main.py
↓
review.py
↓
processor.py
↓
data_provider.py
↓
database.py
↓
SQL query

Trace this chain until the actual external source is identified.

Similarly:

main.py
↓
reference_loader.py
↓
ExcelReader
↓
pd.read_excel()

must be identified as an Excel source.

---

# STEP 4 — DATABASE DATA ELEMENTS

For every database query, identify:

* Source ID
* Source Name
* Database Name
* Schema Name
* Table/View Name
* Column Name
* Column Description
* Input Type
* Code Location

If the code contains:

SELECT
trade_id,
trade_date,
currency_pair,
notional
FROM trades

create four data elements:

* trade_id
* trade_date
* currency_pair
* notional

Do not represent the whole table as one data element when individual columns are available.

If `SELECT *` is used and columns cannot be determined statically:

column_name = `NOT_DETERMINED`

Do not invent column names.

---

# STEP 5 — EXCEL / FILE DATA ELEMENTS

For Excel inputs identify:

* Source ID
* Source Name
* File name/path
* Sheet name
* Column name
* Column description
* Input Type
* Code Location

For CSV/JSON/other files identify equivalent information.

A file mentioned only in comments is NOT an input unless the code actually reads it.

---

# STEP 6 — SOURCE ID AND SOURCE NAME

Source ID and Source Name must come from:

`config/review_config.json`

For example:

```json
"data_sources": {
  "SRC001": {
    "source_name": "Trade Database",
    "type": "Database"
  }
}
```

If code accesses the Trade Database, use:

Source ID = `SRC001`

Source Name = `Trade Database`

Do not create source IDs.

Do not create source names.

If code contains an external source that cannot be mapped to configuration:

source_id = `NOT_CONFIGURED`

source_name = `NOT_CONFIGURED`

Add an appropriate analysis note.

---

# STEP 7 — COLUMN DESCRIPTION

Find descriptions in this order:

1. Database metadata
2. Repository data dictionary
3. Configuration
4. Documentation
5. Comments/docstrings

Do NOT invent business descriptions from column names.

If no description is available:

`Description not available`

---

# STEP 8 — DERIVED DATA

Distinguish external inputs from internally calculated values.

For example:

```python
df["pnl"] = df["price"] * df["quantity"]
```

`price` and `quantity` may be external data elements.

`pnl` is derived data.

Do not classify internally calculated fields as external data elements.

---

# STEP 9 — REMOVE DUPLICATES

If the same data element is consumed in multiple locations, create only one logical data-element record.

Combine all relevant code locations.

Example:

```json
"code_locations": [
  "src/trade_reader.py:45",
  "src/pnl_processor.py:72"
]
```

---

# STEP 10 — JIRA SUMMARY

Create the summary exactly as:

`<review_id>-<review_name>-dataelements`

Example:

`REV001-FX Options Data Review-dataelements`

---

# STEP 11 — JIRA DESCRIPTION

The description must contain exactly these main sections:

## Review Metadata

Display all metadata key/value pairs from the configuration.

Example:

| Key              | Value        |
| ---------------- | ------------ |
| Business Area    | Market Risk  |
| Review Type      | Data Quality |
| Review Frequency | Monthly      |

## Data Elements

Use these columns:

| Source ID | Source Name | Database Name | Schema Name | Table/View Name | Column Name | Column Description | Input Type | Code Location |
| --------- | ----------- | ------------- | ----------- | --------------- | ----------- | ------------------ | ---------- | ------------- |

## Analysis Notes

Include only relevant findings such as:

* Source discovered but not configured
* Dynamic SQL prevented exact column identification
* SELECT * prevented column-level identification
* Description unavailable
* Other material limitations

---

# STEP 12 — GENERATED JSON

Create:

`jira/generated_jira_task.json`

Use this structure:

```json
{
  "epic_key": "",
  "review_id": "",
  "review_name": "",
  "summary": "",
  "labels": [
    "data-elements"
  ],
  "metadata": {},
  "data_elements": [],
  "analysis_notes": []
}
```

Each `data_elements` item must have:

```json
{
  "source_id": "",
  "source_name": "",
  "database_name": "",
  "schema_name": "",
  "table_name": "",
  "column_name": "",
  "column_description": "",
  "input_type": "",
  "code_locations": []
}
```

---

# STEP 13 — VALIDATE BEFORE CREATION

Validate:

* Epic key exists
* Review ID exists
* Review Name exists
* Summary is correct
* `data-elements` label exists
* Metadata was completely extracted
* Relevant code paths were analyzed
* Database inputs were identified
* Excel/file inputs were identified
* Source IDs/names were mapped
* Duplicate data elements were removed
* Unknown information was not invented

If Review ID, Review Name, or Epic Key is missing, STOP and report the problem.

Do not create Jira in that situation.

---

# STEP 14 — RUN PYTHON JIRA CREATION

After generating and validating:

`jira/generated_jira_task.json`

execute:

```bash
python jira/create_jira_task.py jira/generated_jira_task.json
```

Do NOT use dry-run mode.

Do NOT ask the user for confirmation.

The Python script is responsible for:

1. Reading the generated JSON.
2. Connecting to Jira.
3. Reading the Epic.
4. Obtaining Epic assignee.
5. Obtaining Epic reporter.
6. Creating the Jira Task under the Epic.
7. Applying label `data-elements`.
8. Creating the generated description.
9. Returning the created Jira key and URL.

If the Python command fails, report the exact error.

Do not retry Jira creation automatically if the first creation may have succeeded but the response was lost, because this could create duplicate Jira tasks.

---

# STEP 15 — FINAL RESPONSE

After successful creation report:

Review ID:
Review Name:
Epic:
Jira Task:
Summary:
Number of Data Elements:
Number of Sources:
Configuration Gaps:

Also provide the generated Jira key and URL returned by the Python script.

Do not include the full source-code analysis in the final response.
