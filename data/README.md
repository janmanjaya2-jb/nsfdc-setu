# NSFDC Setu - Data Documentation

## 1. Scheme Data

File:

`schemes.json`

This file contains the three NSFDC schemes used by the prototype:

- Micro Finance Scheme (MFS)
- Term Loan Scheme (TL)
- Educational Loan Scheme (EDU)

The dataset contains scheme limits, loan amount, interest rate,
moratorium information, tenure and eligible activity information.

## 2. Channel Partner Data

File:

`odisha_partners.json`

This file contains prototype Channel Partner locations in Odisha.

Each partner record contains:

- partner_id
- name
- type
- district
- address
- latitude
- longitude
- handles_schemes
- partner_status
- scheme_eligibility_status
- fund_utilization_status
- source
- last_verified

## 3. Data Usage

The Backend and Geo Locator modules read these JSON files instead
of hard-coding scheme and partner information.

The partner coordinates are used by the Geo Locator to calculate
distance and identify nearby partner locations.

## 4. Prototype Limitations

Branch-level NPA and fund-utilization information is not publicly
available for the prototype.

Therefore:

`fund_utilization_status = prototype_placeholder`

This must not be interpreted as actual branch-level financial data.

In a production system, this information should be obtained from
NSFDC's authorized internal MIS/API.

Individual branch-level scheme eligibility should also be verified
against authoritative NSFDC/channel-partner information before
production deployment.

## 5. Data Quality

The prototype data is structured in JSON format and validated for:

- Valid JSON syntax
- Required fields
- Partner identifiers
- Geographic coordinate ranges
- Consistent scheme identifiers

## 6. Data Refresh

Scheme information should be refreshed whenever NSFDC updates
its official lending policies.

Partner information should also be periodically refreshed from
authoritative sources.