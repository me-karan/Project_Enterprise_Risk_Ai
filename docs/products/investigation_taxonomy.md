# AuraRisk Investigation Taxonomy

## 1. Purpose

This document defines the investigation scenarios supported by AuraRisk.

Each scenario identifies:

- The triggering event.
- Expected suspicious or non-suspicious behavior.
- Required evidence.
- Relevant agents.
- Applicable policy categories.
- Expected investigation outcomes.
- Human approval requirements.

The taxonomy informs:

- Synthetic data generation.
- Fraud and credit-risk feature engineering.
- Model training labels.
- Agent routing.
- Policy retrieval.
- Case evaluation.
- Investigator UI design.

## 2. Top-Level Investigation Categories

AuraRisk supports five primary investigation categories:

1. Fraud investigation.
2. Credit-risk investigation.
3. Transaction-monitoring investigation.
4. Policy-compliance investigation.
5. Mixed-signal investigation.

Mixed-signal investigations involve evidence from multiple categories.

## 3. Fraud Investigation Scenarios

### 3.1 Account Takeover

#### Description

An unauthorized person obtains access to an existing customer's account.

#### Typical Signals

- Login from an unfamiliar device.
- Login from an unusual location.
- Recent password or contact-detail change.
- New beneficiary added shortly before a payment.
- Unusually large transaction.
- Rapid multiple transfers.
- Activity outside the customer's typical transaction hours.

#### Required Evidence

- Customer profile.
- Device history.
- Login or access-event history.
- Beneficiary history.
- Transaction history.
- Transaction amount compared with historical baseline.
- Fraud-model score.
- Model explanation.
- Account-security policy.

#### Expected Agents

- Customer Context Agent.
- Transaction Agent.
- Fraud Agent.
- Policy RAG Agent.
- Investigation Agent.
- Validator.
- Reporting Agent.

#### Potential Outcomes

- Continue monitoring.
- Escalate to fraud operations.
- Recommend a temporary account hold.
- Request customer verification.

#### Approval Requirement

Account holds and escalations require human approval.

### 3.2 Card or Payment Fraud

#### Description

A payment is inconsistent with the customer's established behavior and may
represent unauthorized card or account use.

#### Typical Signals

- Unusual merchant category.
- Unfamiliar transaction geography.
- Multiple declined payments followed by a successful payment.
- Abnormally large amount.
- High-risk merchant.
- Transaction frequency above historical baseline.

#### Required Evidence

- Merchant details.
- Transaction location.
- Customer transaction baseline.
- Recent decline history.
- Fraud-model score.
- Payment-monitoring policy.

#### Potential Outcomes

- Clear alert.
- Request customer verification.
- Escalate for fraud investigation.

### 3.3 Identity or Application Fraud

#### Description

An applicant or customer profile contains conflicting information or
signals of a potentially fabricated identity.

#### Typical Signals

- Reused phone number across unrelated customers.
- Reused device across multiple applications.
- Inconsistent employment information.
- Address discrepancies.
- Recent account creation followed by high-value activity.
- Unusual mismatch between declared income and transaction behavior.

#### Required Evidence

- KYC profile.
- Application metadata.
- Device relationships.
- Address and employment information.
- Customer-account creation history.
- Identity-verification policy.

#### Potential Outcomes

- Request additional KYC evidence.
- Escalate to identity-fraud review.
- Place the case under enhanced monitoring.

### 3.4 Mule Account Behavior

#### Description

An account appears to receive funds from multiple unrelated sources and
quickly transfer those funds elsewhere.

#### Typical Signals

- High incoming-to-outgoing transaction velocity.
- Short holding period between credits and debits.
- Multiple unrelated senders.
- Funds transferred to newly added beneficiaries.
- Account balance remains low despite high transaction throughput.

#### Required Evidence

- Incoming transaction history.
- Outgoing transaction history.
- Sender and beneficiary relationships.
- Holding-time calculations.
- Customer occupation and declared account purpose.
- Transaction-monitoring policy.

#### Potential Outcomes

- Escalate to fraud operations.
- Recommend enhanced customer verification.
- Recommend a temporary account hold.

## 4. Credit-Risk Investigation Scenarios

### 4.1 Elevated Probability of Default

#### Description

The registered credit-risk model identifies an increased likelihood of
customer default.

#### Typical Signals

- Rising credit utilization.
- Deteriorating repayment behavior.
- Increased delinquency.
- Declining account inflows.
- High debt-to-income ratio.
- Repeated minimum-only repayments.

#### Required Evidence

- Loan or credit-account details.
- Repayment history.
- Outstanding balance.
- Utilization history.
- Income or inflow estimates.
- Credit-model score.
- Model explanation.
- Lending policy.

#### Expected Agents

- Customer Context Agent.
- Credit Risk Agent.
- Transaction Agent.
- Policy RAG Agent.
- Investigation Agent.
- Validator.
- Reporting Agent.

#### Potential Outcomes

- Continue monitoring.
- Recommend manual credit review.
- Recommend repayment-support outreach.
- Escalate to credit-risk operations.

#### Approval Requirement

Any recommended change to lending terms or customer limits requires human
approval.

### 4.2 Early Delinquency

#### Description

A customer recently missed one or more payments and may be entering a
higher-risk repayment pattern.

#### Typical Signals

- Payment overdue.
- Repeated partial payments.
- Returned payment attempts.
- Increasing days past due.
- Reduced account inflows.

#### Required Evidence

- Repayment schedule.
- Payment history.
- Days past due.
- Historical delinquency.
- Inflow trends.
- Collections or repayment policy.

#### Potential Outcomes

- Request repayment review.
- Recommend customer outreach.
- Escalate to credit-risk operations.

### 4.3 Credit Utilization Spike

#### Description

A customer's credit utilization increases sharply over a short period.

#### Typical Signals

- Utilization approaching or exceeding a configured threshold.
- Multiple cash advances.
- Rapid balance growth.
- Reduced repayment amounts.
- Spending inconsistent with historical income.

#### Required Evidence

- Credit limit.
- Outstanding balance.
- Utilization history.
- Cash-advance history.
- Repayment history.
- Lending policy.

#### Potential Outcomes

- Continue monitoring.
- Recommend manual credit review.
- Escalate if combined with delinquency or fraud signals.

### 4.4 Income or Affordability Deterioration

#### Description

Changes in account inflows suggest that a customer may have reduced
repayment capacity.

#### Typical Signals

- Missing expected salary deposits.
- Declining monthly inflows.
- Increased overdraft usage.
- Rising obligations relative to income.
- Repeated failed payments.

#### Required Evidence

- Monthly inflow history.
- Salary-deposit pattern.
- Loan repayment obligations.
- Debt-to-income estimate.
- Recent transaction activity.
- Affordability policy.

#### Potential Outcomes

- Recommend credit review.
- Recommend additional customer verification.
- Recommend supportive repayment outreach.

## 5. Transaction-Monitoring Scenarios

### 5.1 Transaction Structuring

#### Description

Multiple transactions appear deliberately split to avoid a configured
review or monitoring threshold.

#### Important Note

The synthetic threshold used by AuraRisk is an internal demonstration
control. It is not presented as a universal legal or regulatory threshold.

#### Typical Signals

- Repeated transactions immediately below an internal review threshold.
- Multiple transactions within a short period.
- Shared beneficiary across multiple transfers.
- Combined amount materially exceeds the individual threshold.

#### Required Evidence

- Transaction amounts.
- Transaction timestamps.
- Configured internal monitoring threshold.
- Beneficiary details.
- Aggregated transaction amount.
- Relevant internal monitoring policy.

#### Potential Outcomes

- Escalate to transaction-monitoring review.
- Request contextual information.
- Recommend enhanced monitoring.

### 5.2 Velocity Anomaly

#### Description

The number or value of transactions exceeds the customer's normal behavior
within a short time window.

#### Typical Signals

- Five-minute, hourly, or daily transaction count spike.
- Rapid sequential transfers.
- Multiple newly added beneficiaries.
- High deviation from historical activity.

#### Required Evidence

- Rolling transaction counts.
- Rolling transaction amounts.
- Historical activity baseline.
- Beneficiary history.
- Fraud-model score.
- Transaction-monitoring policy.

#### Potential Outcomes

- Continue monitoring.
- Request customer verification.
- Escalate if accompanied by additional fraud signals.

### 5.3 Unusual Geography

#### Description

Transaction location differs materially from the customer's historical
geographic pattern.

#### Typical Signals

- New transaction country or region.
- Location inconsistent with recent customer activity.
- Multiple distant transactions within an implausible time window.
- High-risk geography under internal policy.

#### Required Evidence

- Current transaction location.
- Historical location profile.
- Device or login location.
- Previous transaction timestamp.
- Geographic-risk policy.

#### Potential Outcomes

- Clear alert if context explains the transaction.
- Request customer verification.
- Escalate if corroborating risk signals exist.

## 6. Policy-Compliance Scenarios

### 6.1 Expired or Incomplete KYC

#### Description

Customer identity-verification documents are incomplete or past their
internal review date.

#### Required Evidence

- KYC completion status.
- Last verification date.
- Customer risk tier.
- Applicable KYC review policy.

#### Potential Outcomes

- Request additional customer information.
- Escalate to KYC operations.
- Apply enhanced monitoring if required by internal policy.

### 6.2 Product Policy Violation

#### Description

Observed customer activity conflicts with an approved product or lending
policy.

#### Typical Signals

- Loan amount outside product eligibility criteria.
- Missing required documentation.
- Product usage inconsistent with approved terms.
- Exposure exceeding a configured internal policy limit.

#### Required Evidence

- Product metadata.
- Customer eligibility data.
- Relevant policy document.
- Policy version and effective date.
- Specific violated policy section.

#### Potential Outcomes

- Escalate to policy review.
- Request additional evidence.
- Recommend manual exception review.

## 7. Mixed-Signal Scenarios

### 7.1 High Fraud Risk and High Credit Risk

The customer simultaneously shows:

- Suspicious transaction activity.
- Elevated probability of default.
- Weak repayment behavior.

The system must avoid treating the two risks as interchangeable.

Fraud and credit findings must be presented separately before synthesis.

### 7.2 High Model Score but Weak Supporting Evidence

A model score is elevated, but the available transactional or customer
evidence does not support a strong conclusion.

Expected behavior:

- Preserve the model score.
- Present the model explanation.
- Identify missing or weak evidence.
- Avoid unsupported escalation.
- Request additional review where appropriate.

### 7.3 Strong Transaction Evidence but Low Model Score

The fraud model score is low, but deterministic transaction analytics show
behavior that violates an approved monitoring control.

Expected behavior:

- Preserve both the model output and the rule-based evidence.
- Explain the disagreement.
- Retrieve the relevant policy.
- Escalate for manual review if the documented policy requires it.

### 7.4 Legitimate Activity Resembling Fraud

A customer generates a suspicious signal that is explained by valid
historical or contextual evidence.

Examples:

- An established business customer processes seasonal high-value payments.
- A customer travels and uses a previously verified device.
- A known beneficiary receives an unusually large but expected payment.

Expected behavior:

- Present the suspicious indicators.
- Present the legitimate contextual evidence.
- Explain why the case should be cleared or monitored.
- Do not escalate solely because an individual feature is unusual.

## 8. Risk Severity Levels

### LOW

- Limited suspicious evidence.
- Activity largely consistent with customer history.
- No material policy violation.

### MEDIUM

- One or more suspicious signals.
- Incomplete evidence.
- Additional review or monitoring may be appropriate.

### HIGH

- Multiple corroborating suspicious signals.
- Material policy concerns.
- Strong model or deterministic evidence.
- Human review required before consequential action.

### CRITICAL

- Multiple severe signals with strong supporting evidence.
- Potential immediate customer or institution impact.
- Urgent analyst attention required.
- Consequential action still requires documented human approval.

## 9. Investigation Outcomes

Supported case outcomes:

- `CLEAR_ALERT`
- `CONTINUE_MONITORING`
- `REQUEST_MORE_INFORMATION`
- `ESCALATE_FRAUD_REVIEW`
- `ESCALATE_CREDIT_REVIEW`
- `ESCALATE_POLICY_REVIEW`
- `RECOMMEND_ACCOUNT_HOLD`
- `RECOMMEND_CUSTOMER_VERIFICATION`
- `RECOMMEND_REPAYMENT_OUTREACH`

## 10. Taxonomy Maintenance

The investigation taxonomy must be updated when:

- A new case category is introduced.
- A new financial product is supported.
- A policy materially changes.
- A new agent is added.
- A new evaluation failure reveals missing scenario coverage.

Changes must be reviewed together with the gold-case dataset.