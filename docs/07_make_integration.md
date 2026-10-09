# Make

Uses Make.com as an orchestrator for the project.

### Make Scenario

#### Fukunavi (Data Manipulation & Cleanup)

Goal:

- Manipulates Data
- Cleanup GCS Data to ensure fresh succeeding runs
- Notifies to Slack when data manipulation and cleanup is done

![Fukunavi Scenario](images/fukunavi_scenario.png)

#### Fukunavi (Slack Notifier)

Goal:

- Notifies to Slack Channel when:
  - Successful stage runs
  - Failed stage runs

![Fukunavi (Slack Notifier)](images/fukunavi_slack_notifier_scenario.png)
