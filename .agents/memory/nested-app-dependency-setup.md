---
name: Nested app dependency setup
description: Dependency installation behavior when the repository contains nested backend and frontend applications.
---

When installing dependencies in this repository, verify the target manifest and git diff afterward: the environment package tool may update root-level package manifests even when the operational applications live under backend/ and frontend/.

**Why:** The imported repository contains duplicate root and nested dependency manifests, and an automatic install updated root files that were intended to remain untouched.

**How to apply:** Prefer the operational manifests and always restore unintended root-manifest changes before continuing.