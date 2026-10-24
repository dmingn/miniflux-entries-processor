## How to add rule components

This guide explains how to add or rename rule components in code, including conditions, actions, and related tests.

Rules are made of **conditions** (when to match) and **actions** (what to do).

## Conditions

When adding or renaming a condition:

- **Class name**: Describe what is being matched (for example `MatchAllCondition`, `FeedIdInListCondition`). Verb-first is optional but can improve clarity.
- **File name**: Must match the class name in snake_case only (for example class `MatchAllCondition` → file `match_all_condition.py`, class `FeedIdInListCondition` → file `feed_id_in_list_condition.py`).
- **Config key `name`**: Must match the class name with the `Condition` suffix removed, in snake_case (for example class `MatchAllCondition` → `name: "match_all"`, class `FeedIdInListCondition` → `name: "feed_id_in_list"`). Changing it is a breaking change.

## Actions

When adding or renaming an action:

- **Class name**: Start with a verb so the name reads as “what this action does” (for example `LogAction`, `AddTodoistTaskAction`).
- **File name**: Must match the class name in snake_case only (for example class `LogAction` → file `log_action.py`, class `AddTodoistTaskAction` → file `add_todoist_task_action.py`).
- **Config key `name`**: Must match the class name with the `Action` suffix removed, in snake_case (for example class `LogAction` → `name: "log"`, class `AddTodoistTaskAction` → `name: "add_todoist_task"`). Changing it is a breaking change.

When adding or updating tests for new rule components, follow the project-wide testing conventions described in [`develop-and-test.md`](./develop-and-test.md).
