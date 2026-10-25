## Configuration reference

This document describes the YAML configuration format for `miniflux-entries-processor`.

Configuration is written in YAML. Each rule has a `name`, a `source`, a `condition` block, and an `action` block. Rules are evaluated in the order they appear after configuration files are merged. Unknown keys are rejected.

The `source` controls where entries are fetched from:

- `starred` for starred entries
- `unread` for unread entries

### Conditions

Each rule has a condition that determines whether it matches a given entry.

Available condition types:

| Name                | Description                         | Parameters                    |
| ------------------- | ----------------------------------- | ----------------------------- |
| `match_all`         | Matches all entries                 | None                          |
| `all_of`            | Matches when every nested condition matches | `conditions`: list of condition objects |
| `any_of`            | Matches when any nested condition matches | `conditions`: list of condition objects |
| `regex_partial_match` | Matches when any of the given entry fields (title, author, content) contains text matching any of the patterns | `fields`: list of `"title"`, `"author"`, `"content"`; `patterns`: list of regex strings |
| `feed_id_in_list` | Matches entries whose feed ID is in the given list | `feed_ids`: list of integers |
| `feed_url_in_list` | Matches entries whose feed URL is in the given list | `feed_urls`: list of strings |

### Actions

Each rule has an action that is executed when the condition matches.

Available action types:

| Name                    | Description                                        | Parameters                                                |
| ----------------------- | -------------------------------------------------- | --------------------------------------------------------- |
| `log`                   | Logs entry details                                 | `level`: `info`, `debug`, `warning`, or `error`           |
| `add_todoist_task`      | Adds entry as a task in Todoist                    | `project_id` (required), `due_string`, `priority` (1–4), `labels` (list of label names) |
| `star` | Stars an entry if it is not currently starred | None |
| `unstar` | Removes the star from an entry if it is currently starred | None |
| `mark_as_read` | Marks an entry as read | None |
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
      name: "feed_url_in_list"
      feed_urls:
        - "http://example.org/feed.atom"
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

  - name: "Star and mark matching unread entries as read"
    source:
      name: "unread"
    condition:
      name: "all_of"
      conditions:
        - name: "feed_id_in_list"
          feed_ids:
            - 42
        - name: "regex_partial_match"
          fields:
            - "title"
          patterns:
            - "interesting"
    action:
      name: "run_in_sequence"
      actions:
        - name: "star"
        - name: "mark_as_read"

  - name: "Mark noisy unread entries as read"
    source:
      name: "unread"
    condition:
      name: "all_of"
      conditions:
        - name: "feed_id_in_list"
          feed_ids:
            - 42
        - name: "any_of"
          conditions:
            - name: "regex_partial_match"
              fields:
                - "title"
              patterns:
                - "noise"
            - name: "regex_partial_match"
              fields:
                - "content"
              patterns:
                - "reposted"
    action:
      name: "mark_as_read"
```
