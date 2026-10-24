"""Tests for the config_loader module."""

from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError
from pydantic_yaml import to_yaml_str
from ruamel.yaml.error import YAMLError

from miniflux_entries_processor.actions import (
    AddTodoistTaskAction,
    LogAction,
    RunInSequenceAction,
    UnstarAction,
)
from miniflux_entries_processor.conditions import (
    AllOfCondition,
    AnyOfCondition,
    FeedIdInListCondition,
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
            Config(rules=frozenset([Rule(name=name, source=s, condition=c, action=a)])),
            id=name,
        )
        for (s, c, a) in frozenset(
            [(s, _DEFAULT_CONDITION, _DEFAULT_ACTION) for s in _SOURCES]
            + [(_DEFAULT_SOURCE, c, _DEFAULT_ACTION) for c in _CONDITIONS]
            + [(_DEFAULT_SOURCE, _DEFAULT_CONDITION, a) for a in _ACTIONS]
        )
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


def test_Config_or_operator_merges_rules_and_preserves_operands() -> None:
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
    common_rule = Rule(
        name="Common Rule",
        source=StarredSource(),
        condition=MatchAllCondition(name="match_all"),
        action=LogAction(name="log", level="warning"),
    )

    config1 = Config(rules=frozenset([rule1]))
    config2 = Config(rules=frozenset([rule2]))
    config1_with_common = Config(rules=frozenset([rule1, common_rule]))
    config2_with_common = Config(rules=frozenset([rule2, common_rule]))

    # act
    combined_config = config1 | config2
    combined_config_with_common = config1_with_common | config2_with_common

    # assert
    assert combined_config.rules == frozenset([rule1, rule2])
    assert combined_config_with_common.rules == frozenset([rule1, rule2, common_rule])
    assert config1.rules == frozenset([rule1])
    assert config2.rules == frozenset([rule2])
    with pytest.raises(TypeError):
        config1 | "not a config"  # type: ignore[operator]


def test_load_config_merges_yaml_and_yml_from_directory(
    tmp_path: Path,
) -> None:
    # arrange
    config_dir = tmp_path / "configs"
    config_dir.mkdir()

    yaml_config_path = config_dir / "config1.yaml"
    yaml_rule = Rule(
        name="Yaml Rule",
        source=StarredSource(),
        condition=MatchAllCondition(name="match_all"),
        action=LogAction(name="log", level="info"),
    )
    _save_config(Config(rules=frozenset([yaml_rule])), yaml_config_path)

    yml_config_path = config_dir / "config2.yml"
    yml_rule = Rule(
        name="Yml Rule",
        source=StarredSource(),
        condition=FeedIdInListCondition(
            name="feed_id_in_list",
            feed_ids=frozenset({99}),
        ),
        action=LogAction(name="log", level="debug"),
    )
    _save_config(Config(rules=frozenset([yml_rule])), yml_config_path)

    (config_dir / "invalid.txt").write_text("not a yaml", encoding="utf-8")

    # act
    loaded_config = load_config([config_dir])

    # assert
    assert loaded_config.rules == frozenset([yaml_rule, yml_rule])


def test_load_config_merges_rules_from_mixed_file_and_directory_paths(
    tmp_path: Path,
) -> None:
    # arrange
    config_dir = tmp_path / "configs"
    config_dir.mkdir()

    dir_yaml_path = config_dir / "dir_config.yaml"
    dir_yaml_rule = Rule(
        name="Dir Yaml Rule",
        source=StarredSource(),
        condition=MatchAllCondition(name="match_all"),
        action=LogAction(name="log", level="info"),
    )
    _save_config(Config(rules=frozenset([dir_yaml_rule])), dir_yaml_path)

    standalone_yml_path = tmp_path / "standalone_config.yml"
    standalone_yml_rule = Rule(
        name="Standalone Yml Rule",
        source=StarredSource(),
        condition=FeedIdInListCondition(
            name="feed_id_in_list",
            feed_ids=frozenset({100}),
        ),
        action=LogAction(name="log", level="debug"),
    )
    _save_config(Config(rules=frozenset([standalone_yml_rule])), standalone_yml_path)

    # act
    loaded_config = load_config([config_dir, standalone_yml_path])

    # assert
    assert loaded_config.rules == frozenset([dir_yaml_rule, standalone_yml_rule])
