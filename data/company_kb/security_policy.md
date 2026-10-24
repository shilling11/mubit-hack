# Ashgrove Information Security Policy Summary (fictional)

## Identity and single sign-on

Supports SAML 2.0 and OpenID Connect single sign-on, with tested integrations for Microsoft Entra ID and Okta. SCIM provisioning is supported.

## Access control

Role-based access control with least privilege. Privileged administration uses a privileged access management tool with just-in-time, time-bound, fully audited access. Access reviews run quarterly.

## Encryption

TLS 1.2 or higher in transit. AES-256 at rest. Customer-managed keys are available through Azure Key Vault.

## Audit logging

Immutable audit logs for user, administrator and AI activity (prompts, retrieved sources, outputs and approvals). Default retention is 13 months, configurable, with export to the client's SIEM.

## Vulnerability management and testing

Monthly authenticated vulnerability scanning, annual CREST-accredited penetration testing, secure SDLC with code review and dependency scanning, and release approval gates.

## Security incident notification

Confirmed security incidents affecting client data are notified to the client within 24 hours of confirmation, with support for the client's 72-hour regulatory reporting obligations.

## Environment separation

Development, test and production environments are logically and administratively separated. Production data is not used in non-production environments without masking.

## Certifications and assurance

Ashgrove holds ISO/IEC 27001:2022, a SOC 2 Type II report (annual) and Cyber Essentials Plus. Ashgrove does not hold HITRUST certification and does not hold PCI DSS certification because the platform does not process payment card data.
