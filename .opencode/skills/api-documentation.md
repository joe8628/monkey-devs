# API Documentation

Read all source files in the project. Produce `docs/api-reference.md` covering every public interface:

For each public function, class, or endpoint:
- **Name** and module path
- **Purpose**: one sentence
- **Parameters**: name, type, description for each
- **Returns**: type and description
- **Raises**: exceptions that callers must handle
- **Example**: minimal working usage example

Use the source code as the authoritative ground truth. Do not document private functions (prefixed with `_`).
