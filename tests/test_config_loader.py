"""Tests for the config_loader module."""

from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError
from pydantic_yaml import to_yaml_str
from ruamel.yaml.error import YAMLError

from miniflux_entries_processor.actions import (
    AddTodoistTaskAction,
    LogAction,
    MarkAsReadAction,
    RunInSequenceAction,
    StarAction,
    UnstarAction,
)
from miniflux_entries_processor.conditions import (
    AllOfCondition,
    AnyOfCondition,
    FeedIdInListCondition,
    FeedUrlInListCondition,
    MatchAllCondition,
    RegexPartialMatchCondition,
)
from miniflux_entries_processor.config_loader import (
    Config,
    Rule,
    load_config,
    load_config_file,
)
from miniflux_entries_processor.exceptions import ConfigError
from miniflux_entries_processor.settings import TodoistSettings
from miniflux_entries_processor.sources import StarredSource, UnreadSource

TEST_CONFIGS_PATH = Path(__file__).parent / "test_configs"
_TODOIST_TEST_TOKEN = "todoist_test_token"  # noqa: S105

_DEFAULT_SOURCE = UnreadSource()
_DEFAULT_CONDITION = MatchAllCondition()
_DEFAULT_ACTION = LogAction()


_SOURCES = (UnreadSource(), StarredSource())
_CONDITIONS = (
    MatchAllCondition(),
    FeedIdInListCondition(feed_ids=frozenset({42})),
    FeedUrlInListCondition(feed_urls=frozenset({"http://example.com/feed.atom"})),
    RegexPartialMatchCondition(fields=("title",), patterns=("pattern",)),
    AllOfCondition(
        conditions=(
            FeedIdInListCondition(feed_ids=frozenset({42})),
            MatchAllCondition(),
        )
    ),
    AnyOfCondition(
        conditions=(
            FeedIdInListCondition(feed_ids=frozenset({42})),
            RegexPartialMatchCondition(fields=("title",), patterns=("pattern",)),
        )
    ),
)
_ACTIONS = (
    LogAction(),
    AddTodoistTaskAction(
        project_id="project_id",
        due_string="today",
        priority=1,
        labels=frozenset({"reading", "tech"}),
        todoist_settings=TodoistSettings.model_construct(
            todoist_api_token=SecretStr(_TODOIST_TEST_TOKEN)
        ),
    ),
    UnstarAction(),
    StarAction(),
    MarkAsReadAction(),
    RunInSequenceAction(actions=(LogAction(),)),
)


def _save_config(config: Config, file_path: Path) -> None:
    """Save the configuration to a YAML file."""
    file_path.write_text(to_yaml_str(config), encoding="utf-8")


@pytest.fixture(autouse=True)
def mock_os_environ(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TODOIST_API_TOKEN", _TODOIST_TEST_TOKEN)


@pytest.fixture
def test_configs_path() -> Path:
    """Provide the base path to the test configuration files directory."""
    return TEST_CONFIGS_PATH


@pytest.mark.parametrize(
    ("path", "cause_type", "message_contains"),
    [
        pytest.param(
            TEST_CONFIGS_PATH / "invalid_yaml.yaml", YAMLError, None, id="invalid_yaml"
        ),
        pytest.param(
            TEST_CONFIGS_PATH / "invalid_schema.yaml",
            ValidationError,
            "Field required",
            id="invalid_schema",
        ),
        pytest.param(
            TEST_CONFIGS_PATH / "non_existent.yaml",
            ValidationError,
            "Path does not point to a file",
            id="file_not_found",
        ),
    ],
)
def test_load_config_file_raises_ConfigError_for_invalid_input(
    path: Path,
    cause_type: type[Exception],
    message_contains: str | None,
) -> None:
    # act & assert
    with pytest.raises(ConfigError) as exc_info:
        load_config_file(path)
    assert isinstance(exc_info.value.__cause__, cause_type)
    if message_contains is not None:
        assert message_contains in str(exc_info.value.__cause__)


@pytest.mark.parametrize(
    ("path_suffix", "message_contains"),
    [
        ("non_existent.yaml", "Path does not point to a file"),
        ("non_existent_dir", "Path does not point to a directory"),
    ],
)
def test_load_config_raises_ConfigError_for_invalid_path(
    tmp_path: Path, path_suffix: str, message_contains: str
) -> None:
    # arrange
    path = tmp_path / path_suffix
    # act & assert
    with pytest.raises(ConfigError) as exc_info:
        load_config([path])
    assert isinstance(exc_info.value.__cause__, ValidationError)
    assert message_contains in str(exc_info.value.__cause__)


@pytest.mark.parametrize(
    "config",
    [
        pytest.param(
            Config(rules=(Rule(name=name, source=s, condition=c, action=a),)),
            id=name,
        )
        for (s, c, a) in [
            *[(s, _DEFAULT_CONDITION, _DEFAULT_ACTION) for s in _SOURCES],
            *[(_DEFAULT_SOURCE, c, _DEFAULT_ACTION) for c in _CONDITIONS],
            *[(_DEFAULT_SOURCE, _DEFAULT_CONDITION, a) for a in _ACTIONS],
        ]
        for name in [f"{type(s).__name__}_{type(c).__name__}_{type(a).__name__}"]
    ],
)
def test_Config_can_be_written_to_and_loaded_from_yaml(
    config: Config,
    tmp_path: Path,
) -> None:
    # arrange
    path = tmp_path / "config.yaml"
    path.write_text(to_yaml_str(config), encoding="utf-8")

    # act
    loaded = load_config_file(path)

    # assert
    assert loaded == config


def test_Config_or_operator_merges_rules_in_order_and_preserves_operands() -> None:
    # arrange
    rule1 = Rule(
        name="Rule 1",
        source=StarredSource(),
        condition=MatchAllCondition(name="match_all"),
        action=LogAction(name="log", level="info"),
    )
    rule2 = Rule(
        name="Rule 2",
        source=StarredSource(),
        condition=FeedIdInListCondition(
            name="feed_id_in_list",
            feed_ids=frozenset({1}),
        ),
        action=LogAction(name="log", level="debug"),
    )
    rule3 = Rule(
        name="Rule 3",
        source=StarredSource(),
        condition=MatchAllCondition(name="match_all"),
        action=LogAction(name="log", level="warning"),
    )

    config1 = Config(rules=(rule1,))
    config2 = Config(rules=(rule2, rule3))

    # act
    combined_config = config1 | config2

    # assert
    assert combined_config.rules == (rule1, rule2, rule3)
    assert config1.rules == (rule1,)
    assert config2.rules == (rule2, rule3)
    with pytest.raises(TypeError):
        config1 | "not a config"  # type: ignore[operator]


def test_load_config_file_preserves_rule_order_within_file(tmp_path: Path) -> None:
    # arrange
    rule_a = Rule(
        name="A",
        source=UnreadSource(),
        condition=MatchAllCondition(),
        action=LogAction(),
    )
    rule_b = Rule(
        name="B",
        source=UnreadSource(),
        condition=MatchAllCondition(),
        action=LogAction(level="debug"),
    )
    path = tmp_path / "config.yaml"
    _save_config(Config(rules=(rule_a, rule_b)), path)

    # act
    loaded = load_config_file(path)

    # assert
    assert loaded.rules == (rule_a, rule_b)


def test_load_config_loads_directory_files_in_filename_order(tmp_path: Path) -> None:
    # arrange
    config_dir = tmp_path / "configs"
    config_dir.mkdir()

    later_rule = Rule(
        name="Later",
        source=StarredSource(),
        condition=MatchAllCondition(),
        action=LogAction(),
    )
    earlier_rule = Rule(
        name="Earlier",
        source=StarredSource(),
        condition=MatchAllCondition(),
        action=LogAction(level="debug"),
    )
    _save_config(Config(rules=(later_rule,)), config_dir / "b.yaml")
    _save_config(Config(rules=(earlier_rule,)), config_dir / "a.yml")
    (config_dir / "ignored.txt").write_text("not a yaml", encoding="utf-8")

    # act
    loaded = load_config([config_dir])

    # assert
    assert loaded.rules == (earlier_rule, later_rule)


def test_load_config_merges_paths_in_argument_order(tmp_path: Path) -> None:
    # arrange
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    dir_rule = Rule(
        name="From Dir",
        source=StarredSource(),
        condition=MatchAllCondition(),
        action=LogAction(),
    )
    file_rule = Rule(
        name="From File",
        source=UnreadSource(),
        condition=MatchAllCondition(),
        action=LogAction(level="debug"),
    )
    _save_config(Config(rules=(dir_rule,)), config_dir / "dir.yaml")
    file_path = tmp_path / "standalone.yml"
    _save_config(Config(rules=(file_rule,)), file_path)

    # act
    loaded = load_config([config_dir, file_path])

    # assert
    assert loaded.rules == (dir_rule, file_rule)


def test_load_config_file_rejects_unknown_keys(tmp_path: Path) -> None:
    # arrange
    path = tmp_path / "config.yaml"
    path.write_text(
        """
rules:
  - name: typo-rule
    source:
      name: unread
    condition:
      name: match_all
    action:
      name: add_todoist_task
      project_id: "p"
      due_strng: today
""",
        encoding="utf-8",
    )

    # act & assert
    with pytest.raises(ConfigError) as exc_info:
        load_config_file(path)
    assert isinstance(exc_info.value.__cause__, ValidationError)
    assert "due_strng" in str(exc_info.value.__cause__)
