# AuraRisk Non-Functional Requirements

## Security

- Protected API endpoints require authenticated users.
- Role-based access controls apply to cases, tools, and approvals.
- Unauthorized access attempts must never return customer data.
- Sensitive identifiers must be masked in application logs.
- Secrets must not be committed to version control.

## Approval and Safety

- Consequential actions require authorized human approval.
- Account-hold recommendations require two distinct approvers.
- Expired or stale approvals must be rejected.
- Prohibited actions must never execute.
- Agents and service accounts cannot approve their own recommendations.

## Data Quality

- All generated records must pass schema validation.
- Customer, account, transaction, and loan relationships must be valid.
- Synthetic datasets must contain no real customer information.
- Features must not use data from after the prediction timestamp.

## Fraud Model

- Fraud PR-AUC must exceed the positive-class prevalence baseline.
- Fraud recall at the selected threshold must be at least 75%.
- Every prediction must include its model version and explanation.

## Credit-Risk Model

- Credit ROC-AUC target: at least 0.75.
- Credit KS statistic target: at least 0.30.
- Calibration must improve over a constant base-rate predictor.
- Every prediction must include model and feature versions.

## Policy Retrieval

- Policy Recall@5 target: at least 90%.
- Citation correctness target: at least 95%.
- Expired policies must not be presented as current.
- Every material policy claim must include a citation.

## Agent Quality

- Required-agent routing accuracy target: at least 95%.
- Gold-case task success target: at least 90%.
- Every material conclusion must reference supporting evidence.
- Unsupported material-claim rate must not exceed 2%.

## Performance

- API request acceptance p95: at most 500 milliseconds.
- Complete investigation p95: at most 45 seconds.
- Expected-load API error rate: at most 1%.

## Reliability

- Failed investigations must resume from saved workflow state.
- Duplicate events must not create duplicate material actions.
- Transient failures must use bounded retries.
- Permanent failures must be recorded and surfaced.

## Auditability

- Every investigation must include a trace identifier.
- Model calls, tool calls, policy retrieval, and approvals must be recorded.
- Completed cases must be reconstructable from their audit events.