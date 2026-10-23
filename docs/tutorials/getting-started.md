## Getting started

This tutorial guides you through running `miniflux-entries-processor` for the first time using a simple configuration.

You will:

- check basic requirements
- install the CLI
- configure Feedly authentication
- create a minimal rule file
- run the processor against that configuration

For more background, see the main [`README.md`](../../README.md).

### 1. Requirements

Before you start, ensure that you have:

- Python 3.13+ available in your environment

### 2. Install the CLI

Install from the repository using `pipx`:

```bash
pipx install git+https://github.com/dmingn/miniflux-entries-processor/
```

### 3. Configure Feedly authentication

The tool uses the [feedly-client](https://github.com/feedly/python-api-client) `FileAuthStore` format. By default, it reads tokens from `~/.config/feedly`.

Place `access.token` and `refresh.token` in that directory. Obtain these tokens via the Feedly Developer Token or OAuth flow (see the Feedly Python API client documentation).

To use a different directory, set the `FEEDLY_TOKEN_DIR` environment variable (or add it to a `.env` file).

### 4. Create a minimal rule file

Create a file such as `config.yaml` with the following content:

```yaml
rules:
  - name: "Log saved entries from specific feed"
    source:
      name: "saved"
    condition:
      name: "stream_id_in_list"
      stream_ids:
        - "feed/example.com/123"
    action:
      name: "log"
      level: "info"
```

This rule logs saved entries from the specified feed at `info` level.

For more configuration options (such as Todoist integration), see [`configuration.md`](../reference/configuration.md).

### 5. Run the processor

Run the CLI against your configuration file:

```bash
miniflux-entries-processor config.yaml
```

If everything is set up correctly, entries from the configured feed will be processed and logged.
