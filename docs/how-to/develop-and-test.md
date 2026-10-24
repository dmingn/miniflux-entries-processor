## How to develop and test

This document summarizes how to set up a development environment for this project and how to run checks and tests.

## Development environment

This project assumes a Python development environment.

- **Python Version**: Refer to the `.python-version` file in the project root for the recommended Python version.
- **Dependency Management**: `uv` is used for dependency management and virtual environment creation.
- **Environment Setup**: To set up the project's virtual environment and install/sync dependencies, run:

  ```bash
  uv sync
  ```

  This command will create a virtual environment (if one does not exist) and install/sync all required packages as per `uv.lock`.

## Running checks and tests

To ensure code quality and adherence to standards, run:

```bash
make format-and-check
```

This command runs formatting, linting, type checking, and unit tests. Miniflux integration tests are excluded from this target.

### Miniflux integration tests

These tests start Miniflux, Postgres, and an nginx RSS fixture with Docker Compose, then exercise `process()` against the real Miniflux API. They do not go through the CLI entrypoint.

Requirements:

- Docker with Compose support

Run them with:

```bash
make miniflux-integration
```

Docker is required. If Docker is unavailable, these tests fail.

## Testing conventions

This section describes the project-wide testing conventions, including naming, structure, and how to use common pytest features.

### Test naming

- Test function names must read as a natural English sentence.
- Test names may include the class or function name as written in code (PascalCase for classes like `MinifluxClient`, snake_case for functions like `process_entry`).

### Test documentation

- The test name should be the primary description.
- Avoid docstrings unless they add information beyond the name.

### Test body structure (Arrange / Act / Assert)

- Inside each test, mark **Arrange** (setup), **Act** (invocation), and **Assert** (verification) with `# arrange`, `# act`, and `# assert` comments.
- For a single-line act or a short run of asserts, one comment for the block is enough; avoid a comment on every line.

### Parametrization

- When multiple cases differ only by condition or expected value for the same SUT, prefer a single test function with `@pytest.mark.parametrize`.
- Use `pytest.param(..., id="...")` so each case declares its parameters and id together. Choose `id` values that are short and descriptive (for example `invalid_yaml`, `request_exception`, `level_info`).

### Mocking

- Prefer `pytest-mock` via the `mocker` fixture (`MockerFixture`) and create mocks with `mocker.patch`, `mocker.create_autospec`, etc.
- Fixtures that hold real data (e.g. `Entry`, `Feed`) are test data, not mocks; they may be used as-is.
