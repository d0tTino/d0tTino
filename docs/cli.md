# CLI Scenarios

These examples demonstrate common workflows using the `ai` command line helpers.

## Multi-user session

1. Alice signs in and sets her working context:
   ```bash
   ai login alice
   ai switch-context work
   ```
2. She schedules a team meeting and verifies it:
   ```bash
   ai calendar add "Team sync tomorrow at 10am"
   ai calendar view --day 2024-07-12 --layers work
   ```
3. Bob uses the same machine later:
   ```bash
   ai login bob
   ai switch-context personal
   ai calendar view --day 2024-07-12 --layers personal
   ```

## Budget analysis

1. Generate cost-cutting ideas:
   ```bash
   ai finance analyze --goal "Lower cloud spending"
   ```
2. Review the options produced by the previous step:
   ```bash
   ai finance view
   ```
3. Repeat the cycle with updated goals as your plan evolves.
