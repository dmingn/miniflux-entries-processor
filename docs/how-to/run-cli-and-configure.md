## How to run the CLI and configure rules

This guide shows different ways to run `miniflux-entries-processor` and how to structure your YAML configuration.

For details of the YAML schema itself, see the configuration reference in [`configuration.md`](../reference/configuration.md).

## Running the CLI

### Single config file

Run the processor with a single YAML configuration file:

```bash
miniflux-entries-processor config.yaml
```

### Multiple files and directories

You can pass multiple files and/or directories. Rules are merged:

```bash
miniflux-entries-processor config1.yaml config2.yaml ./rules/
```

### Custom token directory

By default, tokens are read from `~/.config/feedly`. To use a different directory, set the `FEEDLY_TOKEN_DIR` environment variable (or add it to a `.env` file in the current directory).

### Todoist API token

When using the `add_todoist_task` action, set the `TODOIST_API_TOKEN` environment variable (or add it to a `.env` file in the current directory).

### JSON log output

To emit JSON-formatted logs, use `--json-log`:

```bash
miniflux-entries-processor --json-log config.yaml
```

### Validate configuration

To validate configuration files without contacting Feedly, use `--validate-config`:

```bash
miniflux-entries-processor --validate-config config.yaml
```

### Show configuration schema

To view the full JSON schema for the configuration, run:

```bash
miniflux-entries-processor --show-config-schema
```

## Basic configuration structure

A configuration file contains a top-level `rules` list. Each rule has:

- `name`: human-friendly rule name
- `source`: where to read entries from (for example `saved` or `all`)
- `condition`: how to decide whether an entry matches
- `action`: what to do when an entry matches

See [`configuration.md`](../reference/configuration.md) for full details of available conditions and actions.
