# Recurrent Card Collection Specification

## Purpose

Define how recurrent-card invoices avoid remesa, are collected by Redsys recurring charge, and enter the unpaid workflow when collection fails.

## Requirements

### Requirement: Recurrent-card invoices stay out of remesa

The system MUST prevent invoices configured for recurrent card collection from being assigned to any remesa or payment order.

#### Scenario: Automatic remesa selection skips card invoices

- GIVEN an open invoice configured for recurrent card collection
- WHEN automatic remesa invoice selection runs
- THEN the invoice SHALL NOT be selected
- AND it SHALL NOT receive a payment order assignment

#### Scenario: Manual add flow rejects card invoices

- GIVEN a user manually adds a recurrent-card invoice to a payment order
- WHEN the add action is confirmed
- THEN the system MUST reject the card invoice
- AND the card invoice SHALL remain without payment order assignment

### Requirement: Scheduled Redsys collection charges eligible card invoices

The system MUST provide a scheduled collection job that attempts Redsys recurring charges only for eligible recurrent-card invoices.

#### Scenario: Eligible invoice is charged

- GIVEN an open, due recurrent-card invoice with active reusable card credentials
- WHEN the scheduled collection job runs
- THEN the system MUST attempt one Redsys recurring charge for the invoice amount

#### Scenario: Ineligible invoices are skipped

- GIVEN an invoice that is not open, not due, lacks reusable card credentials, or is not recurrent-card
- WHEN the scheduled collection job runs
- THEN the system MUST NOT attempt a Redsys charge for that invoice

### Requirement: Successful Redsys charges advance invoices through existing payment flow

The system MUST record successful Redsys recurring charges through the same business payment progression used by existing successful collections.

#### Scenario: Successful charge settles invoice

- GIVEN an eligible recurrent-card invoice receives a successful Redsys response
- WHEN the result is processed
- THEN the invoice MUST advance to the appropriate paid or settled state
- AND it MUST NOT enter the unpaid workflow

#### Scenario: Already settled invoice is not charged again

- GIVEN a recurrent-card invoice already settled by a previous successful charge
- WHEN the scheduled collection job runs again
- THEN the system MUST NOT submit another Redsys charge for that invoice

### Requirement: Failed Redsys charges enter impagats with visible error notes

The system MUST record a dated Redsys failure note in invoice additional information and route the invoice into the unpaid/pending workflow.

#### Scenario: Failed charge records note and pending state

- GIVEN an eligible recurrent-card invoice receives a failed Redsys response
- WHEN the result is processed
- THEN invoice additional information MUST include the failure date and Redsys error reason
- AND the invoice MUST enter the business-approved unpaid/pending workflow

#### Scenario: Failure note preserves existing information

- GIVEN a recurrent-card invoice already has additional information
- WHEN a Redsys failure is recorded
- THEN the dated failure note MUST be visible without deleting the previous information

### Requirement: Retry handling is idempotent per failure event

The system MUST avoid duplicate failure notes and repeated pending transitions for the same Redsys failure event.

#### Scenario: Same failure event is processed twice

- GIVEN a recurrent-card invoice already has a note and pending transition for a Redsys failure event
- WHEN the same failure event is processed again
- THEN the system MUST NOT add a duplicate failure note
- AND it MUST NOT create another pending transition for that same event

#### Scenario: New retry failure is traceable

- GIVEN a recurrent-card invoice has a previous Redsys failure recorded
- WHEN a later collection attempt fails with a new failure event
- THEN the system MAY record a new dated failure note
- AND it MUST preserve the existing unpaid workflow state consistently
