# Database Structure

> [!IMPORTANT]
> Key constraints aren't enforced in BigQuery. You are responsible for maintaining the constraints at all times. Queries over tables with violated constraints might return incorrect results.
>
> ref: <https://docs.cloud.google.com/bigquery/docs/primary-foreign-keys>

- `GENERATE_UUID()` is used to generate `PK` hence its type is `string`
- `FK` relationships are established using `BigQuery Procedure` to ensure correct data order dependencies
  - corporations → evaluation_agencies → depots → evaluations


```mermaid
erDiagram
    corporations ||--o{ depots : ""
    evaluation_agencies ||--o{ evaluations : ""
    depots ||--o{ evaluations : ""
    
    corporations {
        string      id               PK "id"
        string      corporation_name    "Corporation name"
        string      corporation_type    "Corporation type (NPO/Company/Social Welfare)"
        string      address             "Headquarters address"
        string      phone_number        "Phone number"
        string      update_date         "Page update date"
        string      source_url          "Source URL"
        string      data_hash           "Difference detection log"
        timestamp   created_at          "Data creation date"
        timestamp   updated_at          "Data update date"
    }
    
    depots {
        string      id             PK "id"
        string      corporation_id FK "Operating corporation"
        string      corporation_name  "Operating corporation name"
        string      depot_name        "Facility name"
        int         depot_code        "Facility number"
        string      address           "Address"
        string      city              "City/Ward/Town/Village"
        string      phone_number      "Phone number"
        string      fax_number        "FAX number"
        string      hp                "Facility website URL"
        string      service_type      "Service type"
        int         capacity          "Capacity"
        int         staff_count       "Staff count"
        date        opened_date       "Opening date"
        bool        is_active         "Whether operating or not"
        string      source_url        "Source URL"
        string      data_hash         "Difference detection log"
        string      update_date       "Update date"
        timestamp   created_at        "Data creation date"
        timestamp   updated_at        "Data update date"
    }
    
    evaluation_agencies {
        string      id                   PK "id"
        string      agency_name             "Evaluation agency name"
        string      certification_number    "Certification number"
        string      agency_type             "Evaluation agency type (NPO/Company/Social Welfare)"
        string      address                 "Address"
        string      phone_number            "Phone number"
        string      hp                      "Evaluation agency website URL"
        string      target_categories       "Supported evaluation fields (JSON)"
        bool        is_accepting            "Evaluation implementation info (accepting/stopped)"
        bool        is_social_care          "Social care support (available/unavailable)"
        bool        is_active               "Whether operating or not"
        string      source_url              "Source URL"
        string      data_hash               "Difference detection log"
        timestamp   created_at              "Data creation date"
        timestamp   updated_at              "Data update date"
    }
    
    evaluations {
        string      id                   PK "id"
        string      depot_id             FK "Facility id"
        string      evaluation_agency_id FK "Evaluation agency id"
        string      depot_name              "Evaluated facility name"
        string      evaluation_agency_name  "Evaluation agency name"
        int         evaluation_year         "Evaluation fiscal year"
        date        evaluation_date         "Evaluation start date"
        date        evaluation_end_date     "Evaluation end date"
        string      source_url              "Source URL"
        string      data_hash               "Difference detection log"
        timestamp   created_at              "Data creation date"
        timestamp   updated_at              "Data update date"
    }
```
