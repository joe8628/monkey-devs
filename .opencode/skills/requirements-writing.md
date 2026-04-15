# Requirements Writing

Write specifications using EARS notation for acceptance criteria.

Structure every spec with:
- **Problem Statement**: one paragraph describing the problem
- **Goals**: bulleted list of what the system achieves
- **Non-Goals**: explicit list of what is out of scope
- **Functional Requirements** (FR-XX): numbered, each with an EARS acceptance criterion
- **Non-Functional Requirements** (NFR-XX): performance, security, portability, etc.

EARS format: "WHEN [trigger] THE SYSTEM SHALL [behaviour]"

Each FR must map to a single testable behaviour. Avoid vague requirements like "the system should be fast".
