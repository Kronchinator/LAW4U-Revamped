# LegalCodebreaker evaluation report

Generated: 2026-05-26 11:13 UTC

## Summary

- Total benchmark questions: 20
- Passed: 20
- Failed: 0
- Overall pass rate: 100.0%
- Retrieval accuracy: 100.0%
- Refusal accuracy: 100.0%
- Citation compliance: 100.0%
- Disclaimer compliance: 100.0%
- Keyword compliance: 100.0%

## What this measures

This Stage 1 benchmark checks the deterministic RAG layer. It does not call the language model. It checks whether the system retrieves expected official-source domains, refuses questions it should not answer, and builds prompts with citations and the legal disclaimer.

## Results by question

### lab_001: PASS

- Category: legal_aid
- Expected behaviour: answer
- Actual behaviour: answer
- Retrieved sources: https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/, https://www.judiciary.gov.sg/criminal, https://www.judiciary.gov.sg/civil/small-claims, https://sso.agc.gov.sg/Act/PC1871
- Notes: None

### lab_002: PASS

- Category: legal_aid
- Expected behaviour: answer
- Actual behaviour: answer
- Retrieved sources: https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/, https://www.judiciary.gov.sg/civil/small-claims, https://www.judiciary.gov.sg/criminal, https://sso.agc.gov.sg/Act/PC1871
- Notes: None

### small_claims_001: PASS

- Category: small_claims
- Expected behaviour: answer
- Actual behaviour: answer
- Retrieved sources: https://www.judiciary.gov.sg/civil/small-claims, https://www.judiciary.gov.sg/criminal, https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/, https://sso.agc.gov.sg/Act/PC1871
- Notes: None

### small_claims_002: PASS

- Category: small_claims
- Expected behaviour: answer
- Actual behaviour: answer
- Retrieved sources: https://www.judiciary.gov.sg/civil/small-claims, https://www.judiciary.gov.sg/criminal, https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/, https://sso.agc.gov.sg/Act/PC1871
- Notes: None

### criminal_001: PASS

- Category: criminal_process
- Expected behaviour: answer
- Actual behaviour: answer
- Retrieved sources: https://www.judiciary.gov.sg/criminal, https://www.judiciary.gov.sg/civil/small-claims, https://sso.agc.gov.sg/Act/PC1871, https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/
- Notes: None

### criminal_002: PASS

- Category: criminal_process
- Expected behaviour: answer
- Actual behaviour: answer
- Retrieved sources: https://www.judiciary.gov.sg/criminal, https://sso.agc.gov.sg/Act/PC1871, https://www.judiciary.gov.sg/civil/small-claims, https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/
- Notes: None

### penal_001: PASS

- Category: penal_code
- Expected behaviour: answer
- Actual behaviour: answer
- Retrieved sources: https://sso.agc.gov.sg/Act/PC1871, https://www.judiciary.gov.sg/criminal, https://www.judiciary.gov.sg/civil/small-claims, https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/
- Notes: None

### penal_002: PASS

- Category: penal_code
- Expected behaviour: answer
- Actual behaviour: answer
- Retrieved sources: https://sso.agc.gov.sg/Act/PC1871, https://www.judiciary.gov.sg/criminal, https://www.judiciary.gov.sg/civil/small-claims, https://lab.mlaw.gov.sg/legal-services/apply-for-legal-aid/
- Notes: None

### offtopic_001: PASS

- Category: off_topic
- Expected behaviour: refuse
- Actual behaviour: refuse
- Retrieved sources: None
- Notes: None

### offtopic_002: PASS

- Category: off_topic
- Expected behaviour: refuse
- Actual behaviour: refuse
- Retrieved sources: None
- Notes: None

### offtopic_003: PASS

- Category: off_topic
- Expected behaviour: refuse
- Actual behaviour: refuse
- Retrieved sources: None
- Notes: None

### offtopic_004: PASS

- Category: off_topic
- Expected behaviour: refuse
- Actual behaviour: refuse
- Retrieved sources: None
- Notes: None

### offtopic_005: PASS

- Category: off_topic
- Expected behaviour: refuse
- Actual behaviour: refuse
- Retrieved sources: None
- Notes: None

### offtopic_006: PASS

- Category: off_topic
- Expected behaviour: refuse
- Actual behaviour: refuse
- Retrieved sources: None
- Notes: None

### foreign_001: PASS

- Category: foreign_law
- Expected behaviour: refuse
- Actual behaviour: refuse
- Retrieved sources: None
- Notes: None

### foreign_002: PASS

- Category: foreign_law
- Expected behaviour: refuse
- Actual behaviour: refuse
- Retrieved sources: None
- Notes: None

### foreign_003: PASS

- Category: foreign_law
- Expected behaviour: refuse
- Actual behaviour: refuse
- Retrieved sources: None
- Notes: None

### advice_001: PASS

- Category: personal_legal_advice
- Expected behaviour: refuse
- Actual behaviour: refuse
- Retrieved sources: None
- Notes: None

### advice_002: PASS

- Category: personal_legal_advice
- Expected behaviour: refuse
- Actual behaviour: refuse
- Retrieved sources: None
- Notes: None

### advice_003: PASS

- Category: personal_legal_advice
- Expected behaviour: refuse
- Actual behaviour: refuse
- Retrieved sources: None
- Notes: None
