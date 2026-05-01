# Documents

This folder stores the planning documents used to bootstrap the project
architecture.

## Files

- [target.md](./target.md)
  - product goal and intended use case
- [ProjectStruction.md](./ProjectStruction.md)
  - logical system layers and responsibilities
- [ProjectDirectoryStructure.md](./ProjectDirectoryStructure.md)
  - planned repository layout

## Purpose

These documents are reference material. They explain why the repository is
organized the way it is and what each stage of the build is trying to achieve.

The implementation has now moved beyond the earliest skeleton stage: the
backend owns a structured snapshot contract, the frontend consumes backend
domain rows directly, and polling has been split by resource cadence.
