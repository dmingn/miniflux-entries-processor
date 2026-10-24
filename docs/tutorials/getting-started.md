## Getting started

This tutorial guides you through running `miniflux-entries-processor` for the first time using a simple configuration.

You will:

- check basic requirements
- install the CLI
- configure Miniflux authentication
- create a minimal rule file
- run the processor against that configuration

For more background, see the main [`README.md`](../../README.md).

### 1. Requirements

Before you start, ensure that you have:

- Python 3.13+ available in your environment
- A Miniflux instance and an API key

### 2. Install the CLI

Install from the repository using `pipx`:

```bash
pipx install git+https://github.com/dmingn/miniflux-entries-processor/
```

### 3. Configure Miniflux authentication

Set the Miniflux base URL and API key via environment variables (or a `.env` file in the current directory):

```bash
export MINIFLUX_BASE_URL="https://miniflux.example.com"
export MINIFLUX_API_KEY="your-api-key"
```

Create an API key in the Miniflux settings UI (Settings → API Keys).

### 4. Create a minimal rule file

Create a file such as `config.yaml` with the following content:

```yaml
rules:
  - name: "Log starred entries from specific feed"
    source:
      name: "starred"
    condition:
      name: "feed_id_in_list"
      feed_ids:
        - 42
    action:
      name: "log"
      level: "info"
```

This rule logs starred entries from the specified feed at `info` level.

For more configuration options (such as Todoist integration), see [`configuration.md`](../reference/configuration.md).

### 5. Run the processor

Run the CLI against your configuration file:

```bash
miniflux-entries-processor config.yaml
```

If everything is set up correctly, matching entries will be processed and logged.
