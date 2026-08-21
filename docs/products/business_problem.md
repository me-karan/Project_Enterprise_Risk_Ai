# AuraRisk: AI Banking Risk and Fraud Investigation Platform

## 1. Executive Summary

AuraRisk is an evidence-grounded investigation platform for suspicious
banking customers, accounts, transactions and repayment behaviour.

The platform combines:

- Fraud detection models
- Credit probability-of-default models
- Transaction-pattern analytics
- Customer and KYC context
- Banking policy retrieval
- Governed multi-agent investigation
- Human approval for consequential actions
- Complete case-level auditability

AuraRisk does not replace fraud, credit-risk or compliance analysts.
It reduces the time required to collect evidence, interpret model outputs,
identify relevant policies and prepare an investigation report.

## 2. Business Problem

Financial institutions generate large numbers of alerts from fraud rules,
credit-risk models, transaction-monitoring systems and policy controls.

Investigators must manually collect information from multiple systems:

- Customer and KYC databases
- Account records
- Transaction histories
- Loan and repayment records
- Fraud-model outputs
- Credit-risk scores
- Model explanations
- Internal policies
- Previous investigation cases

This process is slow, repetitive and difficult to audit.

Model scores alone are also insufficient because they do not explain:

- Which behaviour caused the alert
- Whether a customer has an established historical pattern
- Which policy applies
- Whether fraud and credit signals agree
- Which evidence supports the conclusion
- What information is still missing
- Whether a recommended action requires approval

## 3. Product Goal

AuraRisk will create a unified, evidence-backed investigation case from a
suspicious customer, account or transaction.

The system must:

1. Collect only authorized case data.
2. Run deterministic analytics and registered ML models.
3. Retrieve applicable policy sections.
4. Coordinate specialist analysis through a controlled workflow.
5. Distinguish facts, model outputs and inferred hypotheses.
6. Link every material conclusion to evidence.
7. Validate the investigation before presentation.
8. Require analyst approval for consequential actions.
9. Preserve a complete audit trail.

## 4. Primary Users

### Fraud Analyst

Investigates suspicious transactions and possible account takeover,
identity fraud or payment abuse.

### Credit-Risk Analyst

Reviews probability of default, repayment behaviour, affordability,
utilization and credit-policy violations.

### Investigation Supervisor

Reviews escalated cases, resolves conflicting findings and approves
consequential recommendations.

### Compliance or Audit Reviewer

Reviews the evidence, policy versions, model versions, decisions and
approval history after a case is completed.

### Platform Administrator

Manages users, roles, model routing policies, budgets, service health and
audit access. The administrator cannot silently modify a completed case.

## 5. Investigation Inputs

A case can begin with:

- A suspicious transaction identifier
- A customer identifier
- An account identifier
- A fraud-model alert
- A credit-risk threshold breach
- A repayment anomaly
- A policy-control violation
- A streaming transaction event

Sensitive identifiers must be tokenized or masked outside their authorized
data boundary.

## 6. Investigation Outputs

A completed investigation must contain:

- Case identifier and trace identifier
- Investigation trigger
- Customer and account summary
- Transaction timeline
- Fraud-model score and explanation
- Credit-risk score and explanation
- Transaction-pattern findings
- Relevant policy findings with citations
- Evidence inventory
- Ranked investigation hypotheses
- Missing or contradictory evidence
- Recommended disposition
- Recommendation confidence
- Validation result
- Human approval status
- Model and policy versions
- Tool-call and workflow audit events

## 7. In-Scope Capabilities

- Synthetic banking-data generation
- Batch and streaming feature engineering
- Fraud classification
- Credit probability-of-default modeling
- Score calibration
- SHAP-based model explanations
- Secure FastAPI services
- Role-based access control
- AI Gateway controls
- Least-privilege MCP tools
- Hybrid policy retrieval
- Governed multi-agent orchestration
- Grounding and contradiction validation
- Human-in-the-loop approval
- Investigator web interface
- Offline evaluation
- End-to-end observability
- Containerized and Kubernetes deployment

## 8. Out-of-Scope Capabilities

The portfolio implementation will not:

- Use real customer PII
- Transfer real money
- Connect directly to a live core-banking system
- Query a real sanctions provider
- Automatically reject a loan
- Automatically freeze an account
- Provide legal or regulatory advice
- Train models on protected real-world banking datasets

External services will be represented by synthetic data or controlled
mock adapters.

## 9. Decision Boundaries

### Automatically Allowed

- Read authorized case data
- Calculate deterministic features
- Invoke registered read-only models
- Retrieve approved policy documents
- Create draft findings
- Request additional evidence
- Recommend low-risk follow-up

### Human Approval Required

- Account-freeze recommendation
- Fraud escalation
- Credit-limit reduction recommendation
- Loan-review escalation
- Suspicious-activity escalation
- Any external notification
- Any write operation affecting customer state

### Always Prohibited

- Executing a consequential action without approval
- Accessing data outside the user's authorized scope
- Hiding missing evidence
- Presenting an inference as a verified fact
- Using an unregistered production model
- Using an expired policy without warning
- Modifying a completed audit record

## 10. Evidence Classification

Every investigation statement must be classified as one of:

- `FACT`: Directly obtained from an approved source.
- `MODEL_OUTPUT`: Produced by a versioned ML model.
- `POLICY`: Retrieved from an approved policy document.
- `INFERENCE`: A hypothesis derived from one or more evidence items.
- `RECOMMENDATION`: A proposed analyst action.

Every inference and recommendation must reference one or more evidence IDs.

## 11. Case Lifecycle

A case moves through the following states:

1. `CREATED`
2. `DATA_COLLECTION`
3. `SPECIALIST_ANALYSIS`
4. `SYNTHESIS`
5. `VALIDATION`
6. `AWAITING_APPROVAL`
7. `COMPLETED`
8. `REJECTED`
9. `FAILED`

A failed workflow must preserve its existing state and support a safe retry.

## 12. Initial Success Criteria

### Investigation Quality

- Every material conclusion references evidence.
- Model outputs include model name and version.
- Policy findings include document, section and version.
- Unsupported conclusions fail validation.
- Completed cases can be reconstructed from the audit log.

### Safety

- No consequential action bypasses human approval.
- Sensitive identifiers are masked in application and model logs.
- Unauthorized users receive no case data.
- Agents cannot access tools outside their assigned permissions.

### ML Quality

Fraud models will be evaluated using:

- Precision-recall AUC
- Recall at a controlled false-positive rate
- Precision at the investigation threshold
- Calibration
- Cost-sensitive error analysis

Credit-risk models will be evaluated using:

- ROC-AUC
- KS statistic
- Gini coefficient
- Brier score
- Calibration curve
- Population stability index
- Approval and risk-band analysis

### GenAI and Agent Quality

- Agent-routing accuracy
- Tool-selection accuracy
- Evidence completeness
- Citation correctness
- Unsupported-claim rate
- Policy-retrieval recall
- Task-completion rate
- False-escalation rate
- Analyst agreement
- End-to-end latency
- Token and model cost per case

Performance targets will be finalized after establishing the first
measurable baseline. Targets must not be selected only to match a
pre-existing model result.

## 13. Key Product Principle

AuraRisk is not a chatbot placed on top of a fraud model.

It is a controlled investigation workflow in which deterministic systems,
ML models, retrieval services, agents, validators and human reviewers have
separate, explicitly defined responsibilities.