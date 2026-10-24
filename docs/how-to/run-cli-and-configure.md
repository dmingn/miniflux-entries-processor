## How to run the CLI and configure rules

This guide shows different ways to run `miniflux-entries-processor` and how to structure your YAML configuration.

### Run with a single config file

```bash
miniflux-entries-processor config.yaml
```

### Run with multiple files or directories

You can pass multiple YAML files and directories. Rules from all sources are merged in argument order. Within a directory, YAML files are loaded in filename order:

```bash
miniflux-entries-processor config1.yaml config2.yaml ./rules/
```

### Miniflux credentials

Set `MINIFLUX_BASE_URL` and `MINIFLUX_API_KEY` in the environment or in a `.env` file in the current directory.

### JSON logs

```bash
miniflux-entries-processor --json-log config.yaml
```

### Validate configuration without contacting Miniflux

To validate configuration files without contacting Miniflux, use `--validate-config`:

```bash
miniflux-entries-processor --validate-config config.yaml
```

### Show configuration schema

```bash
miniflux-entries-processor --show-config-schema
```

For the full configuration reference, see [`configuration.md`](../reference/configuration.md).
