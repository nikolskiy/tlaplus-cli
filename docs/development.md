# Development Guidelines

- Use TDD.
- The TDD Workflow: Depersonalizing and stripping payloads like spedific sha, ids, user names, logins, etc. scales parsing validation without exposing any environment to secrets leakage logic, allowing deep test data verification via mocker.
- Subprocess Resilience: Ensuring lines scraped from backend Java execution calls are isolated manually with index parsing split("\n")[0], effectively preventing UI help strings or errors from dumping into valid storage dictionaries natively.
- Strict Python Pathing Standards (Ruff enforced): Disregarding legacy with open("...") as formats for robust .open() abstractions on system paths natively.
- Pytest Parameter Patching: Leveraging mock.patch natively onto sequential I/O calls to prevent nested and redundant disk allocations in repetitive iteration tests, keeping the pipelines exceptionally fast.