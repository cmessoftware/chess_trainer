## AI Assistant Rules (Course Scope Only)

## Scope
- Work only on `docs/ai_chess_coach_course` and its OpenSpec artifacts unless explicitly instructed.
- Reuse existing project infrastructure; do not reimplement PGN parsing/feature extraction.

## Command Conventions
- Run OpenSpec commands from `docs/ai_chess_coach_course`.
- Preferred command format:

```powershell
mamba run -n chess_trainer npx -y @fission-ai/openspec <command>
```

- Useful commands:

```powershell
mamba run -n chess_trainer npx -y @fission-ai/openspec list
mamba run -n chess_trainer npx -y @fission-ai/openspec validate <change-name>
mamba run -n chess_trainer npx -y @fission-ai/openspec show <change-name> --type change --no-interactive
```

## Format and Writing Conventions
- Keep requirements explicit and testable.
- Use `SHALL` for mandatory behavior in specs.
- Use scenario format with `Given / When / Then`.
- Keep each change focused on one coherent goal.

## Change Workflow
1. Create or update a change in `openspec/changes/<change-name>/`.
2. Include `proposal.md`, `design.md`, `tasks.md`, and delta specs.
3. Validate before implementation.
4. Archive completed changes under `openspec/changes/archive/`.

## Guardrails
- Do not add new libraries without explicitly stating:
  1. Why existing dependencies cannot solve the problem.
  2. The new library maintenance status and license.
- If a requirement cannot be fulfilled without architectural change, stop and ask for explicit approval.
- If contracts change, update specs in the same change set.
- Contracts include API schemas, interfaces/types, database schemas, and shared data models.
