# Engineering & Clinical Assumptions (ASSUMPTIONS.md)

1. **Patient Consent & Communication Preferences**:
   - Assumed all imported discharge patients have provided operational consent for post-discharge telephone follow-up during hospital admission registration.

2. **Telephony Execution Mode**:
   - Real outbound telephony (Twilio / WebRTC) is abstracted via an interactive Voice Interaction Simulator. Simulated call outcomes (`COMPLETED`, `NO_ANSWER`, `BUSY`, `VOICEMAIL`, `DROPPED`) provide deterministic behavior for queue & safety evaluation.

3. **EHR Integration Layer**:
   - Real EHR systems (Epic, Cerner) are abstracted via a FHIR R4 Mock EHR service interface supporting `Patient`, `Encounter`, `Observation`, `Communication`, and `Task` resource writes.

4. **Hospital Timezone & Calling Windows**:
   - Outreach calls respect hospital local time settings (e.g. 08:00 to 20:00). Tasks falling outside calling hours remain in `PENDING` state until the window opens.

5. **Consensus Policy Default**:
   - Default consensus policy is set to `STRICT_CONSERVATIVE` (if any AI assessment or rule engine flags URGENT, CONCERNING, or UNCERTAIN, force escalation) to minimize clinical risk.
