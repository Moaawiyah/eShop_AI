"""Feature flag settings and the flags service."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from pydantic import ValidationError

from app.api.config import PublicFlagsResponse
from app.core.settings import Settings
from app.platform.flags import PUBLIC_FLAGS, FeatureFlags, Flag

MakeSettings = Callable[..., Settings]
FIELDS = ("feature_ai_assistant", "feature_external_product_sources", "feature_notifications")


def test_all_flags_default_to_off(make_settings: MakeSettings) -> None:
    settings = make_settings()
    assert [getattr(settings, name) for name in FIELDS] == [False, False, False]
    flags = FeatureFlags(settings)
    assert not any(flags.is_enabled(flag) for flag in Flag)


@pytest.mark.parametrize(("raw", "expected"), [("true", True), ("1", True), ("false", False)])
def test_environment_overrides(
    make_settings: MakeSettings, monkeypatch: pytest.MonkeyPatch, raw: str, expected: bool
) -> None:
    monkeypatch.setenv("FEATURE_AI_ASSISTANT", raw)
    assert make_settings().feature_ai_assistant is expected


def test_invalid_value_fails_validation(
    make_settings: MakeSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FEATURE_AI_ASSISTANT", "maybe")
    with pytest.raises(ValidationError):
        make_settings()


def test_flag_settings_are_immutable(make_settings: MakeSettings) -> None:
    with pytest.raises(ValidationError):
        make_settings().feature_notifications = True  # type: ignore[misc]  # frozen model


def test_every_flag_maps_to_a_settings_field() -> None:
    assert set(FIELDS) == {f"feature_{flag.value}" for flag in Flag}
    assert set(FIELDS) <= set(Settings.model_fields)


@pytest.mark.parametrize("flag", list(Flag))
def test_is_enabled_per_flag(make_settings: MakeSettings, flag: Flag) -> None:
    flags = FeatureFlags(make_settings(**{f"feature_{flag.value}": True}))
    assert {f for f in Flag if flags.is_enabled(f)} == {flag}
    assert flags.enabled_names() == [flag.value]


def test_public_flags_contain_only_the_allow_list(make_settings: MakeSettings) -> None:
    settings = make_settings(**dict.fromkeys(FIELDS, True))
    public = FeatureFlags(settings).public_flags()
    assert public == {"ai_assistant": True}
    assert set(public) == {flag.value for flag in PUBLIC_FLAGS}


def test_response_model_matches_the_allow_list() -> None:
    assert set(PublicFlagsResponse.model_fields) == {flag.value for flag in PUBLIC_FLAGS}
