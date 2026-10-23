"""Tests for AllSource."""

from pytest_mock import MockerFixture

from miniflux_entries_processor.feedly_client import FeedlyClient
from miniflux_entries_processor.sources import AllSource


def test_AllSource_fetch_entries_calls_client_with_correct_stream_id(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_client = mocker.create_autospec(FeedlyClient)
    mock_client.user_id = "test_user_123"
    mock_client.fetch_entries.return_value = iter([])
    source = AllSource()

    # act
    list(source.fetch_entries(mock_client))

    # assert
    expected_stream_id = "user/test_user_123/category/global.all"
    mock_client.fetch_entries.assert_called_once_with(expected_stream_id)
