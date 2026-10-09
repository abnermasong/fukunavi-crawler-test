# BigQuery Integration

How BigQuery processes crawled data from GCS into tables used by Looker Studio.

## Data Flow

```text
Crawler → GCS files → staging_* tables → refresh_core_tables() → core_* tables → Looker Studio
```

## 1. staging_* Tables

**What they are:** The data exactly as collected by the crawler, stored as NDJSON files in GCS. Records are kept as-is—no primary keys and no relationships between entities.

**Tables:** `staging_corporations`, `staging_evaluation_agencies`, `staging_depots`, `staging_evaluations`

**External Table Definition:**

```sql
CREATE OR REPLACE EXTERNAL TABLE `{dataset}.staging_corporations`
OPTIONS (
  format = 'NEWLINE_DELIMITED_JSON',
  uris = ['gs://{bucket_name}/output/staging/corporations_data.ndjson'] 
);
```

**Key points:**

- Read-only; used only to feed `core_*` tables
- Schema auto-detected from NDJSON structure
- No unique IDs assigned yet

## 2. core_* Tables

**What they are:** Processed, production-ready tables where each record has a unique ID and relationships are explicitly established (e.g., depots → corporations, evaluations → depots + agencies). These tables are used for analytics and reporting (e.g., Looker Studio).

**Tables:** `core_corporations`, `core_evaluation_agencies`, `core_depots`, `core_evaluations`

**Updated by:** `refresh_core_tables()` stored procedure (triggered by Make.com after a successful monthly crawl)

```sql
CREATE OR REPLACE PROCEDURE `{project_id}.{dataset}.refresh_core_tables`()
BEGIN
--- CORPORATIONS
--- EVALUATION AGENCIES
--- DEPOTS
--- EVALUATIONS
END
```

<details>
<summary>Click to view CREATE TABLE STATEMENTS</summary>

```sql
-- Corporations
CREATE OR REPLACE TABLE `{dataset}.core_corporations` (
  id STRING OPTIONS(description="Primary key ID"),
  corporation_name STRING OPTIONS(description="Corporation name"),
  corporation_type STRING OPTIONS(description="Corporation type (NPO/Company/Social Welfare)"),
  address STRING OPTIONS(description="Headquarters address"),
  phone_number STRING OPTIONS(description="Phone number"),
  update_date STRING OPTIONS(description="Page update date"),
  source_url STRING OPTIONS(description="Source URL"),
  data_hash STRING OPTIONS(description="Difference detection log"),
  created_at TIMESTAMP OPTIONS(description="Data creation date"),
  updated_at TIMESTAMP OPTIONS(description="Data update date")
);

-- Evaluation Agencies
CREATE OR REPLACE TABLE `{dataset}.core_evaluation_agencies` (
  id STRING OPTIONS(description="Primary key ID"),
  agency_name STRING OPTIONS(description="Evaluation agency name"),
  certification_number STRING OPTIONS(description="Certification number"),
  agency_type STRING OPTIONS(description="Evaluation agency type (NPO/Company/Social Welfare)"),
  address STRING OPTIONS(description="Address"),
  phone_number STRING OPTIONS(description="Phone number"),
  hp STRING OPTIONS(description="Evaluation agency website URL"),
  target_categories STRING OPTIONS(description="Supported evaluation fields (JSON)"),
  is_accepting BOOLEAN OPTIONS(description="Evaluation implementation info (accepting/not accepting)"),
  is_social_care BOOLEAN OPTIONS(description="Social care support (available/unavailable)"),
  is_active BOOLEAN OPTIONS(description="Whether operating or not"),
  source_url STRING OPTIONS(description="Source URL"),
  data_hash STRING OPTIONS(description="Difference detection log"),
  created_at TIMESTAMP OPTIONS(description="Data creation date"),
  updated_at TIMESTAMP OPTIONS(description="Data update date")
);

-- Depots
CREATE OR REPLACE TABLE `{dataset}.core_depots` (
  id STRING OPTIONS(description="Primary key ID"),
  corporation_id STRING OPTIONS(description="Foreign key to core_corporations.id"),
  corporation_name STRING OPTIONS(description="Operating corporation name"),
  depot_name STRING OPTIONS(description="Facility name"),
  depot_code INT64 OPTIONS(description="Facility number"),
  address STRING OPTIONS(description="Facility address"),
  city STRING OPTIONS(description="City/Ward/Town/Village"),
  phone_number STRING OPTIONS(description="Phone number"),
  fax_number STRING OPTIONS(description="FAX number"),
  hp STRING OPTIONS(description="Facility website URL"),
  service_type STRING OPTIONS(description="Service type"),
  capacity INT64 OPTIONS(description="Facility capacity"),
  staff_count INT64 OPTIONS(description="Staff count"),
  opened_date DATE OPTIONS(description="Opening date"),
  is_active BOOL OPTIONS(description="Whether operating or not"),
  source_url STRING OPTIONS(description="Source URL"),
  data_hash STRING OPTIONS(description="Difference detection log"),
  update_date STRING OPTIONS(description="Page update date"),
  created_at TIMESTAMP OPTIONS(description="Data creation date"),
  updated_at TIMESTAMP OPTIONS(description="Data update date")
);

-- Evaluations
CREATE OR REPLACE TABLE `{dataset}.core_evaluations` (
  id STRING OPTIONS(description="Primary key ID"),
  depot_id STRING OPTIONS(description="Foreign key to core_depots.id"),
  evaluation_agency_id STRING OPTIONS(description="Foreign key to core_evaluation_agencies.id"),
  depot_name STRING OPTIONS(description="Evaluated facility name"),
  evaluation_agency_name STRING OPTIONS(description="Evaluation agency name"),
  evaluation_year INT64 OPTIONS(description="Evaluation fiscal year"),
  evaluation_date DATE OPTIONS(description="Evaluation start date"),
  evaluation_end_date DATE OPTIONS(description="Evaluation end date"),
  source_url STRING OPTIONS(description="Source URL"),
  data_hash STRING OPTIONS(description="Difference detection log"),
  created_at TIMESTAMP OPTIONS(description="Data creation date"),
  updated_at TIMESTAMP OPTIONS(description="Data update date")
);

```

</details>

<details>
<summary>Click to view ADDING PK CONSTRAINTS</summary>

```sql
-- Add primary key constraints (not enforced in BigQuery, but serves as metadata)
ALTER TABLE `{dataset}.core_corporations`
ADD PRIMARY KEY(id) NOT ENFORCED;

ALTER TABLE `{dataset}.core_evaluation_agencies`
ADD PRIMARY KEY(id) NOT ENFORCED;

ALTER TABLE `{dataset}.core_depots`
ADD PRIMARY KEY(id) NOT ENFORCED;

ALTER TABLE `{dataset}.core_evaluations`
ADD PRIMARY KEY(id) NOT ENFORCED;
```

</details>

---

### Step 1: Corporations

Corporation records from the `staging_corporations` table are upserted into `core_corporations`. Each unique corporation is assigned a permanent ID using `GENERATE_UUID()` on first insert.

**Example:**

- Staging (crawler output):

    ```json
    {"corporation_name": "ABC Company", "corporation_type": "NPO", "address": "Tokyo", "phone_number": "03-1234-5678", "update_date": "2026-03-15", "source_url": "https://example.com/corp/123", "data_hash": "abc123", "created_at": "2026-03-15T10:00:00"}
    ```

- After processing (core table):

    ```json
    {"id": "uuid-123", "corporation_name": "ABC Company", "corporation_type": "NPO", "address": "Tokyo", "phone_number": "03-1234-5678", "update_date": "2026-03-15", "source_url": "https://example.com/corp/123", "data_hash": "abc123", "created_at": "2026-03-15T10:00:00", "updated_at": "2026-04-08T09:00:00"}
    ```

**Result:**

`ABC Company` is assigned a permanent ID (`uuid-123`) that can be referenced by other tables.

**Core Concept:**

This step uses a BigQuery `MERGE` statement, which combines update and insert logic into one query.

- `staging_corporations.corporation_name` is matched against `core_corporations.corporation_name`
- if a match is found, `staging_corporations.data_hash` is compared with `core_corporations.data_hash`
- if the data has changed, the existing record is updated
- if no match is found, a new record is created with a new ID using `GENERATE_UUID()`

**Query:**

```sql
-- CORPORATIONS
MERGE `{dataset}.core_corporations` AS c_corporations
USING `{dataset}.staging_corporations` AS src

ON c_corporations.corporation_name = src.corporation_name

WHEN MATCHED
AND IFNULL(c_corporations.data_hash,'') != IFNULL(src.data_hash,'')
THEN UPDATE SET
  corporation_type = src.corporation_type,
  address          = src.address,
  phone_number     = src.phone_number,
  update_date      = src.update_date,
  source_url       = src.source_url,
  data_hash        = src.data_hash,
  updated_at       = CURRENT_TIMESTAMP()

WHEN NOT MATCHED THEN
INSERT (
  id,
  corporation_name,
  corporation_type,
  address,
  phone_number,
  update_date,
  source_url,
  data_hash,
  created_at,
  updated_at
)
VALUES (
  GENERATE_UUID(),
  src.corporation_name,
  src.corporation_type,
  src.address,
  src.phone_number,
  src.update_date,
  src.source_url,
  src.data_hash,
  src.created_at,
  CURRENT_TIMESTAMP()
);
```

---

### Step 2: Evaluation Agencies

Evaluation agency records from the `staging_evaluation_agencies` table are upserted into `core_evaluation_agencies`. Each unique evaluation agency is assigned a permanent ID using `GENERATE_UUID()` on first insert.

**Example:**

- Staging (crawler output):

    ```json
    {"agency_name": "XYZ Evaluators", "certification_number": "CERT-456", "agency_type": "NPO", "address": "Osaka", "phone_number": "06-9876-5432", "hp": "https://xyz.com", "target_categories": "Children and Adults with Disabilities, Elderly (Residential Care)", "is_accepting": true, "is_social_care": false, "is_active": true, "source_url": "https://example.com/agency/456", "data_hash": "def456", "created_at": "2026-03-15T10:30:00"}
    ```

- After processing (core table):

    ```json
    {"id": "uuid-456", "agency_name": "XYZ Evaluators", "certification_number": "CERT-456", "agency_type": "NPO", "address": "Osaka", "phone_number": "06-9876-5432", "hp": "https://xyz.com", "target_categories": "Children and Adults with Disabilities, Elderly (Residential Care)", "is_accepting": true, "is_social_care": false, "is_active": true, "source_url": "https://example.com/agency/456", "data_hash": "def456", "created_at": "2026-03-15T10:30:00", "updated_at": "2026-04-08T09:05:00"}
    ```

**Result:**

`XYZ Evaluators` is assigned a permanent ID (`uuid-456`) that can be referenced by other tables.

**Core Concept:**

This step uses a BigQuery `MERGE` statement, which combines update and insert logic into one query.

- `staging_evaluation_agencies.agency_name` is matched against `core_evaluation_agencies.agency_name`
- if a match is found, `staging_evaluation_agencies.data_hash` is compared with `core_evaluation_agencies.data_hash`
- if the data has changed, the existing record is updated
- if no match is found, a new record is created with a new ID using `GENERATE_UUID()`

**Query:**

```sql
-- EVALUATION AGENCIES
MERGE `{dataset}.core_evaluation_agencies` AS c_agencies
USING `{dataset}.staging_evaluation_agencies` AS src

ON c_agencies.agency_name = src.agency_name

WHEN MATCHED
AND IFNULL(c_agencies.data_hash,'') != IFNULL(src.data_hash,'')
THEN UPDATE SET
  certification_number = src.certification_number,
  agency_type          = src.agency_type,
  address              = src.address,
  phone_number         = src.phone_number,
  hp                   = src.hp,
  target_categories    = src.target_categories,
  is_accepting         = src.is_accepting,
  is_social_care       = src.is_social_care,
  is_active            = src.is_active,
  source_url           = src.source_url,
  data_hash            = src.data_hash,
  updated_at           = CURRENT_TIMESTAMP()

WHEN NOT MATCHED THEN
INSERT (
  id,
  agency_name,
  certification_number,
  agency_type,
  address,
  phone_number,
  hp,
  target_categories,
  is_accepting,
  is_social_care,
  is_active,
  source_url,
  data_hash,
  created_at,
  updated_at
)
VALUES (
  GENERATE_UUID(),
  src.agency_name,
  src.certification_number,
  src.agency_type,
  src.address,
  src.phone_number,
  src.hp,
  src.target_categories,
  src.is_accepting,
  src.is_social_care,
  src.is_active,
  src.source_url,
  src.data_hash,
  src.created_at,
  CURRENT_TIMESTAMP()
);
```

---

### Step 3: Depots

Depot records from the `staging_depots` table are upserted into `core_depots`. Each unique depot is assigned a permanent ID using `GENERATE_UUID()` on first insert.

**Example:**

- Staging (crawler output):

    ```json
    {"corporation_name": "ABC Company", "depot_name": "Care Home A", "depot_code": 12345, "address": "Shibuya Tokyo", "city": "Shibuya", "phone_number": "03-1111-2222", "fax_number": "03-1111-2223", "hp": "https://carehomea.com", "service_type": "Elderly Care", "capacity": 50, "staff_count": 15, "opened_date": "2020-01-01", "is_active": true, "source_url": "https://example.com/depot/789", "data_hash": "ghi789", "update_date": "2026-03-15", "created_at": "2026-03-15T11:00:00"}
    ```

- After processing (core table):

    ```json
    {"id": "uuid-789", "corporation_id": "uuid-123", "corporation_name": "ABC Company", "depot_name": "Care Home A", "depot_code": 12345, "address": "Shibuya Tokyo", "city": "Shibuya", "phone_number": "03-1111-2222", "fax_number": "03-1111-2223", "hp": "https://carehomea.com", "service_type": "Elderly Care", "capacity": 50, "staff_count": 15, "opened_date": "2020-01-01", "is_active": true, "source_url": "https://example.com/depot/789", "data_hash": "ghi789", "update_date": "2026-03-15", "created_at": "2026-03-15T11:00:00", "updated_at": "2026-04-08T09:10:00"}
    ```

**Result:**

`Care Home A` is assigned a permanent ID (`uuid-789`) and linked to its corporation through `corporation_id`.

**Core Concept:**

This step uses a BigQuery `MERGE` statement, which combines update and insert logic into one query.

- `staging_depots.depot_code` is matched against `core_depots.depot_code`
- before the merge happens, staging data is deduplicated so that only the most recent record for `staging_depots.depot_code` is used
- `staging_depots.corporation_name` is matched against `core_corporations.corporation_name` to resolve `corporation_id`
- if a match is found, `staging_depots.data_hash` is compared with `core_depots.data_hash`
- if the data has changed, the existing record is updated
- if no match is found, a new record is created with a new ID using `GENERATE_UUID()`

**Query:**

```sql
-- DEPOTS
MERGE `{dataset}.core_depots` AS c_depots
USING (
  SELECT *
  FROM (
    SELECT
      s_depots.*,
      c_corporations.id AS corporation_id,

      ROW_NUMBER() OVER (
        PARTITION BY s_depots.depot_code
        ORDER BY
          s_depots.update_date DESC,
          s_depots.created_at DESC,
          s_depots.data_hash DESC
      ) AS rn

    FROM `{dataset}.staging_depots` AS s_depots

    LEFT JOIN (
      SELECT *
      FROM (
        SELECT *,
          ROW_NUMBER() OVER (
            PARTITION BY corporation_name
            ORDER BY updated_at DESC
          ) AS rn
        FROM `{dataset}.core_corporations`
      )
      WHERE rn = 1
    ) AS c_corporations
    ON s_depots.corporation_name = c_corporations.corporation_name
  )
  WHERE rn = 1
) AS src

ON c_depots.depot_code = src.depot_code

WHEN MATCHED
AND IFNULL(c_depots.data_hash,'') != IFNULL(src.data_hash,'')
THEN UPDATE SET
  corporation_id   = src.corporation_id,
  corporation_name = src.corporation_name,
  depot_name       = src.depot_name,
  address          = src.address,
  city             = src.city,
  phone_number     = src.phone_number,
  fax_number       = src.fax_number,
  hp               = src.hp,
  service_type     = src.service_type,
  capacity         = src.capacity,
  staff_count      = src.staff_count,
  opened_date      = src.opened_date,
  is_active        = src.is_active,
  source_url       = src.source_url,
  data_hash        = src.data_hash,
  update_date      = src.update_date,
  updated_at       = CURRENT_TIMESTAMP()

WHEN NOT MATCHED THEN
INSERT (
  id,
  corporation_id,
  corporation_name,
  depot_name,
  depot_code,
  address,
  city,
  phone_number,
  fax_number,
  hp,
  service_type,
  capacity,
  staff_count,
  opened_date,
  is_active,
  source_url,
  data_hash,
  update_date,
  created_at,
  updated_at
)
VALUES (
  GENERATE_UUID(),
  src.corporation_id,
  src.corporation_name,
  src.depot_name,
  src.depot_code,
  src.address,
  src.city,
  src.phone_number,
  src.fax_number,
  src.hp,
  src.service_type,
  src.capacity,
  src.staff_count,
  src.opened_date,
  src.is_active,
  src.source_url,
  src.data_hash,
  src.update_date,
  src.created_at,
  CURRENT_TIMESTAMP()
);
```

---

### Step 4: Evaluations

Evaluation records from the `staging_evaluations` table are upserted into `core_evaluations`. Each unique evaluation is assigned a permanent ID using `GENERATE_UUID()` on first insert.

**Example:**

- Staging (crawler output):

    ```json
    {"depot_name": "Care Home A", "evaluation_agency_name": "XYZ Evaluators", "evaluation_year": 2026, "evaluation_date": "2026-01-10", "evaluation_end_date": "2026-01-20", "source_url": "https://example.com/eval/999", "data_hash": "jkl999", "created_at": "2026-03-15T11:30:00"}
    ```

- After processing (core table):

    ```json
    {"id": "uuid-999", "depot_id": "uuid-789", "evaluation_agency_id": "uuid-456", "depot_name": "Care Home A", "evaluation_agency_name": "XYZ Evaluators", "evaluation_year": 2026, "evaluation_date": "2026-01-10", "evaluation_end_date": "2026-01-20", "source_url": "https://example.com/eval/999", "data_hash": "jkl999", "created_at": "2026-03-15T11:30:00", "updated_at": "2026-04-08T09:15:00"}
    ```

**Result:**

This evaluation is assigned a permanent ID (`uuid-999`) and linked to both the depot and the evaluation agency through `depot_id` and `evaluation_agency_id`.

**Core Concept:**

This step uses a BigQuery `MERGE` statement, which combines update and insert logic into one query.

- `staging_evaluations.depot_name`, `staging_evaluations.evaluation_agency_name`, and `staging_evaluations.evaluation_year` are used together to identify each evaluation record
- before the merge happens, staging data is deduplicated so that only the most recent record for each combination of `staging_evaluations.depot_name`, `staging_evaluations.evaluation_agency_name`, and `staging_evaluations.evaluation_year` is used
- `staging_evaluations.depot_name` is matched against `core_depots.depot_name` to resolve `depot_id`
- `staging_evaluations.evaluation_agency_name` is matched against `core_evaluation_agencies.agency_name` to resolve `evaluation_agency_id`
- if a match is found, `staging_evaluations.data_hash` is compared with `core_evaluations.data_hash`
- if the data has changed, the existing record is updated
- if no match is found, a new record is created with a new ID using `GENERATE_UUID()`

**Query:**

```sql
-- EVALUATIONS
MERGE `{dataset}.core_evaluations` AS c_evaluations
USING (
  SELECT *
  FROM (
    SELECT
      s_evaluations.*,
      c_depots.id AS depot_id,
      c_agencies.id AS evaluation_agency_id,

      ROW_NUMBER() OVER (
        PARTITION BY
          s_evaluations.depot_name,
          s_evaluations.evaluation_agency_name,
          s_evaluations.evaluation_year
        ORDER BY
          s_evaluations.evaluation_date DESC,
          s_evaluations.evaluation_end_date DESC,
          s_evaluations.created_at DESC,
          s_evaluations.data_hash DESC
      ) AS rn

    FROM `{dataset}.staging_evaluations` AS s_evaluations

    LEFT JOIN `{dataset}.core_depots` AS c_depots
      ON s_evaluations.depot_name = c_depots.depot_name

    LEFT JOIN `{dataset}.core_evaluation_agencies` AS c_agencies
      ON s_evaluations.evaluation_agency_name = c_agencies.agency_name
  )
  WHERE rn = 1
) AS src

ON
  c_evaluations.depot_name = src.depot_name
  AND c_evaluations.evaluation_agency_name = src.evaluation_agency_name
  AND c_evaluations.evaluation_year = src.evaluation_year

WHEN MATCHED
AND IFNULL(c_evaluations.data_hash,'') != IFNULL(src.data_hash,'')
THEN UPDATE SET
  depot_id             = src.depot_id,
  evaluation_agency_id = src.evaluation_agency_id,
  evaluation_date      = src.evaluation_date,
  evaluation_end_date  = src.evaluation_end_date,
  source_url           = src.source_url,
  data_hash            = src.data_hash,
  updated_at           = CURRENT_TIMESTAMP()

WHEN NOT MATCHED THEN
INSERT (
  id,
  depot_id,
  evaluation_agency_id,
  depot_name,
  evaluation_agency_name,
  evaluation_year,
  evaluation_date,
  evaluation_end_date,
  source_url,
  data_hash,
  created_at,
  updated_at
)
VALUES (
  GENERATE_UUID(),
  src.depot_id,
  src.evaluation_agency_id,
  src.depot_name,
  src.evaluation_agency_name,
  src.evaluation_year,
  src.evaluation_date,
  src.evaluation_end_date,
  src.source_url,
  src.data_hash,
  src.created_at,
  CURRENT_TIMESTAMP()
);
```
