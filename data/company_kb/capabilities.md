# Ashgrove Digital — Capability Statement (fictional)

Ashgrove Digital is a fictional UK systems integrator and managed-service provider. Its Customer Operations AI Platform ("Ashgrove CX Platform") is delivered as a managed service with implementation and change services around it.

## Agent assist

The agent desktop add-in suggests grounded answers drawn only from approved knowledge sources, generates editable interaction summaries, recommends dispositions and next-best actions, and lets agents edit every AI output before it is saved to the CRM. Suggestions show the source passage they came from.

## Knowledge grounding and citations

Every AI-generated answer carries citations to the source document and clause. Retrieval is permission-aware: the platform enforces source-level access permissions by mapping knowledge collections to identity-provider groups (Microsoft Entra ID or Okta). Knowledge items carry an owner, review date, expiry date and feedback workflow; expired items are excluded from retrieval automatically.

## Conversational self-service

Supports authenticated and unauthenticated conversational journeys on web chat, in-app messaging and WhatsApp. Escalation to a human agent transfers the full transcript, detected intent, collected data and authentication state to the receiving agent.

## Quality monitoring

Evaluates up to 100% of interactions against configurable quality criteria and scorecards, with calibration workflows for QA teams and evidence links back to the transcript.

## Analytics and reporting

Operational, adoption and outcome dashboards (handling time, containment, knowledge usage, AI acceptance rate) with exportable event data and Power BI / Tableau templates.

## Platform resilience

The Ashgrove CX Platform is built for always-on customer operations. Its multi-zone cloud architecture is designed for high availability, and enterprise clients run mission-critical journeys on it 24/7. Contractual availability commitments are set out in the Managed Service SLA, not in this capability statement.

## Hosting

The platform runs on Microsoft Azure. UK clients are hosted in Azure UK South with disaster recovery in Azure UK West.
