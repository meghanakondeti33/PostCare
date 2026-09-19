# Known Prototype Limitations & Tradeoffs (LIMITATIONS.md)

1. **Simulated Telephony**:
   - The platform includes a deterministic Voice Interaction Simulator rather than live PSTN telephony integration (Twilio / WebRTC). Audio recordings are simulated URLs.

2. **Synthetic Healthcare Data**:
   - Synthetic dataset contains 300 patient discharge records across 4 hospitals. No real Protected Health Information (PHI) is used.

3. **Mock EHR Backend**:
   - EHR operations are handled by an in-memory / relational mock FHIR service rather than a live HL7/FHIR server integration.

4. **Security Certification**:
   - Implements JWT authentication, bcrypt/SHA256 password hashing, RBAC, and multi-tenant isolation. However, full production HIPAA / SOC2 compliance would require dedicated KMS key encryption, HSM integration, and independent security auditing.
