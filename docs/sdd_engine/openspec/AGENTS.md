## Core rules

- Do not add new libraries without explicitly stating: (1) why existing dependencies cannot solve the problem, and (2) the library's maintenance status and license.
- Avoid changing the architecture style.
- If a requirement cannot be fulfilled without an architectural change, stop and ask for explicit approval before proceeding.
- In case of doubts or unclear requirements, ask for clarification before implementing.
- If contracts change, update the specs.
- Contracts include REST/GraphQL API schemas, TypeScript/language interfaces, database table schemas, and any shared data models.
- Append all specification changes to a single file named spec_changes.log, with one entry per change including a timestamp, the file affected, and a short description of what changed.