# Ashgrove Responsible AI Governance Standard (fictional)

## Human oversight of customer-impacting decisions

Any AI action that affects a customer's money, cover, entitlement or account (refunds, credits, claims, payments, eligibility) requires human approval above a configurable threshold. The default threshold is GBP 250. Ashgrove will not deploy fully autonomous financial or entitlement decisions without a threshold and a human approval route; this is a design principle, not a product gap.

## Prohibited and restricted uses

The platform must not give personalised clinical, medical, legal or financial advice; it signposts to qualified professionals instead. No biometric identification. No automated eligibility decisions for public services without a human decision-maker.

## Evaluation and version control

Every production prompt, model and adapter change is versioned, evaluated against a maintained evaluation set, and approved before release. Approval records are retained.

## Groundedness and safety monitoring

A pre-response groundedness check blocks answers whose support in retrieved sources falls below a threshold. Harmful-output filters and drift monitoring run continuously, with alerts to the service team.

## Model and prompt change control

Changes follow a documented change process with rollback, A/B evaluation and sign-off by the client's AI owner.
