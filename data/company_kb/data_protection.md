# Ashgrove Data Protection Standard (fictional)

## Data residency

UK clients' production customer content is hosted in Azure UK South, with disaster recovery in Azure UK West. Backups remain in the UK. Ashgrove marketing summarises this as "your UK data stays in the UK".

## Support access and international transfers

Because support follows the sun, support engineers in Bengaluru, India may access production data remotely during incidents. This is an international transfer covered by the UK International Data Transfer Agreement, with just-in-time approval and full audit. Clients that cannot accept any offshore access must take the UK Sovereign Support option.

## Subprocessors

Microsoft (hosting), Ashgrove India Pvt Ltd (support), and the LLM provider configured for the client. The subprocessor list is maintained and clients are notified 30 days before changes.

## Retention and deletion

Retention is configurable per data class (transcripts, summaries, audit logs, knowledge). Deletion requests are honoured within 30 days. On contract exit all client data is deleted within 30 days and a deletion certificate is issued.

## AI data use

Client data is never used to train shared or foundation models. Task-specific adapters may be trained on a client's own data only inside that client's tenant, with written opt-in, and are deleted on exit.
