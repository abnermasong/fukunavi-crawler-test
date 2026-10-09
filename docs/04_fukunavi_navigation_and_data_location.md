# Fukunavi Navigation & Data Location

## Corporation

<details>
<summary>Navigation & Data Location</summary>

Start URL: <https://www.fukunavi.or.jp/fukunavi/controller?cmd=jgy&actionID=jgyhjn>

### Search Area Page → Depot Index Page

![Search Area Page](images/navigation-and-data-location/corporation/01_corporation.png)

### Depot Index Page → Depot Detail Page

![Depot Index Page](images/navigation-and-data-location/corporation/02_corporation.png)

### Depot Detail Page → Corporation Detail Page

![Depot Detail Page](images/navigation-and-data-location/corporation/03_corporation.png)

### Corporation Detail Page

![Corporation Detail Page](images/navigation-and-data-location/corporation/04_corporation.png)

**Extracted data:**

```mermaid
erDiagram

    corporations {
        string      corporation_name    "Corporation name"
        string      corporation_type    "Corporation type (NPO/Company/Social Welfare)"
        string      address             "Headquarters address"
        string      phone_number        "Phone number"
        string      update_date         "Page update date"
        string      source_url          "Source URL"
    }
```

</details>

## Evaluation Agency

<details>
<summary>Navigation & Data Location</summary>

Start URL: <https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyk&cmd=kknlst&pageId=before&HYKKKN_ID=&ROW=0&BNYCD=&AREA1=2&AREA2=&AREA3=&NAME=&ORDERBY=1&ORDER=1&NSYKKN_NO1=&NSYKKN_NO2=&HYK_CHK=&HYK_SU=&HYK_SU_OLD=&HYK_SU_CHILD=&HYK_SU_HANDI=&HYK_SU_FEMALE=&HYK_SU_WELAARE=&NSY_CHK=&KYK_CHK=>

### Search Area Page → Evaluation Agency Index Page

![Search Area Page](images/navigation-and-data-location/evaluation_agency/01_evaluation_agency.png)

### Evaluation Agency Index Page → Evaluation Agency Detail Page

![Evaluation Agency Index Page](images/navigation-and-data-location/evaluation_agency/02_evaluation_agency.png)

**Extracted data:**

```mermaid
erDiagram

    evaluation_agencies {
        string      certification_number    "Certification number"
        string      address                 "Address"
        string      phone_number            "Phone number"
        string      target_categories       "Supported evaluation fields (JSON)"
        bool        is_accepting            "Evaluation implementation info (accepting/stopped)"
        bool        is_social_care          "Social care support (available/unavailable)"
        bool        is_active               "Whether operating or not"
    }
```

### Evaluation Agency Detail Page

![Evaluation Agency Detail Page](images/navigation-and-data-location/evaluation_agency/03_evaluation_agency.png)

**Extracted data:**

```mermaid
erDiagram

    evaluation_agencies {
        string      agency_name             "Evaluation agency name"
        string      agency_type             "Evaluation agency type (NPO/Company/Social Welfare)"
        string      hp                      "Evaluation agency website URL"
        string      source_url              "Source URL"
    }
```

</details>

## Depot

<details>
<summary>Navigation & Data Location</summary>

Start URL: <https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyksearch&cmd=svcdbr&S_MODE=service&MLT_AREA=&H_NAME=&J_NAME=>

### Category Selection Page → Service Selection Page

![Category Selection Page](images/navigation-and-data-location/depot/01_depot.png)

### Service Selection Page → Search Area Page

![Service Selection Page](images/navigation-and-data-location/depot/02_depot.png)

### Search Area Page → Evaluation Index Page

![Search Area Page](images/navigation-and-data-location/depot/03_depot.png)

### Evaluation Index Page → Evaluation Detail Page

![Evaluation Index Page](images/navigation-and-data-location/depot/04_depot.png)

### Evaluation Detail Page → Depot Detail Page

![Evaluation Detail Page](images/navigation-and-data-location/depot/05_depot.png)

### Depot Detail Page

![Depot Detail Page - 1](images/navigation-and-data-location/depot/06_depot.png)

![Depot Detail Page - 2](images/navigation-and-data-location/depot/07_depot.png)

**Extracted data:**

```mermaid
erDiagram

    depots {
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
    }
```

</details>

## Evaluation

<details>
<summary>Navigation & Data Location</summary>

Start URL: <https://www.fukunavi.or.jp/fukunavi/controller?actionID=hyksearch&cmd=svcdbr&S_MODE=service&MLT_AREA=&H_NAME=&J_NAME=>

### Category Selection Page → Service Selection Page

![Category Selection Page](images/navigation-and-data-location/evaluation/01_evaluation.png)

### Service Selection Page → Search Area Page

![Service Selection Page](images/navigation-and-data-location/evaluation/02_evaluation.png)

### Search Area Page → Evaluation Index Page

![Search Area Page](images/navigation-and-data-location/evaluation/03_evaluation.png)

### Evaluation Index Page → Evaluation Detail Page

![Evaluation Index Page](images/navigation-and-data-location/evaluation/04_evaluation.png)

### Evaluation Detail Page

![Evaluation Detail Page](images/navigation-and-data-location/evaluation/05_evaluation.png)

**Extracted data:**

```mermaid
erDiagram

    evaluations {
        string      depot_name              "Evaluated facility name"
        string      evaluation_agency_name  "Evaluation agency name"
        int         evaluation_year         "Evaluation fiscal year"
        date        evaluation_date         "Evaluation start date"
        date        evaluation_end_date     "Evaluation end date"
        string      source_url              "Source URL"
    }
```

</details>
