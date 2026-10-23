## Configuration reference

This document describes the YAML configuration format for `miniflux-entries-processor`.

Configuration is written in YAML. Each rule has a `name`, a `source`, a `condition` block, and an `action` block.

The `source` controls where entries are fetched from:

- `saved` for saved entries
- `all` for the All feed (`global.all`)

### Conditions

Each rule has a condition that determines whether it matches a given entry.

Available condition types:

| Name                | Description                         | Parameters                    |
| ------------------- | ----------------------------------- | ----------------------------- |
| `match_all`         | Matches all entries                 | None                          |
| `regex_partial_match` | Matches when any of the given entry fields (title, author, summary_contents) contains text matching any of the patterns | `fields`: list of `"title"`, `"author"`, `"summary_contents"`; `patterns`: list of regex strings |
| `stream_id_in_list` | Matches entries in given stream IDs | `stream_ids`: list of strings |

### Actions

Each rule has an action that is executed when the condition matches.

Available action types:

| Name                    | Description                                        | Parameters                                                |
| ----------------------- | -------------------------------------------------- | --------------------------------------------------------- |
| `log`                   | Logs entry details                                 | `level`: `info`, `debug`, `warning`, or `error`           |
| `add_todoist_task`      | Adds entry as a task in Todoist                    | `project_id` (required), `due_string`, `priority` (1–4), `labels` (list of label names) |
| `remove_from_feedly_tag` | Removes entry from a Feedly tag (e.g. saved). **There is no undo.** | `tag` (required) |
| `run_in_sequence`       | Runs multiple actions in sequence; stops on first failure | `actions`: list of action objects                        |

When using the `add_todoist_task` action, set the `TODOIST_API_TOKEN` environment variable (or add it to a `.env` file).

For `remove_from_feedly_tag`, set `tag` to `"global.saved"` for the built-in saved list, or to a tag label (e.g. `tech`) for user-created tags. The Feedly token directory is read from the `FEEDLY_TOKEN_DIR` environment variable (default: `~/.config/feedly`), as with other Feedly usage.

### Schema

To view the full JSON schema for the configuration, run:

```bash
miniflux-entries-processor --show-config-schema
```

### Example configuration

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

  - name: "Add all saved entries to Todoist"
    source:
      name: "saved"
    condition:
      name: "match_all"
    action:
      name: "add_todoist_task"
      project_id: "YOUR_PROJECT_ID"

  - name: "Log entries from All feed"
    source:
      name: "all"
    condition:
      name: "match_all"
    action:
      name: "log"
      level: "info"

  - name: "Add to Todoist then remove from saved"
    source:
      name: "saved"
    condition:
      name: "match_all"
    action:
      name: "run_in_sequence"
      actions:
        - name: "add_todoist_task"
          project_id: "YOUR_PROJECT_ID"
        - name: "remove_from_feedly_tag"
          tag: "global.saved"
```
