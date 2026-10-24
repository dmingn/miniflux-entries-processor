## Configuration reference

This document describes the YAML configuration format for `miniflux-entries-processor`.

Configuration is written in YAML. Each rule has a `name`, a `source`, a `condition` block, and an `action` block.

The `source` controls where entries are fetched from:

- `starred` for starred entries
- `unread` for unread entries

### Conditions

Each rule has a condition that determines whether it matches a given entry.

Available condition types:

| Name                | Description                         | Parameters                    |
| ------------------- | ----------------------------------- | ----------------------------- |
| `match_all`         | Matches all entries                 | None                          |
| `regex_partial_match` | Matches when any of the given entry fields (title, author, content) contains text matching any of the patterns | `fields`: list of `"title"`, `"author"`, `"content"`; `patterns`: list of regex strings |
| `feed_id_in_list` | Matches entries whose feed ID is in the given list | `feed_ids`: list of integers |

### Actions

Each rule has an action that is executed when the condition matches.

Available action types:

| Name                    | Description                                        | Parameters                                                |
| ----------------------- | -------------------------------------------------- | --------------------------------------------------------- |
| `log`                   | Logs entry details                                 | `level`: `info`, `debug`, `warning`, or `error`           |
| `add_todoist_task`      | Adds entry as a task in Todoist                    | `project_id` (required), `due_string`, `priority` (1–4), `labels` (list of label names) |
| `unstar` | Removes the star from an entry if it is currently starred | None |
| `run_in_sequence`       | Runs multiple actions in sequence; stops on first failure | `actions`: list of action objects                        |

When using the `add_todoist_task` action, set the `TODOIST_API_TOKEN` environment variable (or add it to a `.env` file).

Miniflux credentials are read from `MINIFLUX_BASE_URL` and `MINIFLUX_API_KEY`.

### Schema

To view the full JSON schema for the configuration, run:

```bash
miniflux-entries-processor --show-config-schema
```

### Example configuration

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

  - name: "Add all starred entries to Todoist"
    source:
      name: "starred"
    condition:
      name: "match_all"
    action:
      name: "add_todoist_task"
      project_id: "YOUR_PROJECT_ID"

  - name: "Log unread entries"
    source:
      name: "unread"
    condition:
      name: "match_all"
    action:
      name: "log"
      level: "info"

  - name: "Add to Todoist then unstar"
    source:
      name: "starred"
    condition:
      name: "match_all"
    action:
      name: "run_in_sequence"
      actions:
        - name: "add_todoist_task"
          project_id: "YOUR_PROJECT_ID"
        - name: "unstar"
```
