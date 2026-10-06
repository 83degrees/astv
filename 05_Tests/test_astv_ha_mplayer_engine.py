from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_PATH = (
    REPOSITORY_ROOT
    / "04_Implementation/haos/source/config/packages/astv/astv_scripts.yaml"
)


class HomeAssistantLoader(yaml.SafeLoader):
    pass


HomeAssistantLoader.add_constructor(
    "!include", lambda loader, node: loader.construct_scalar(node)
)


def _ha_mplayer_sequence():
    scripts = yaml.load(
        SCRIPTS_PATH.read_text(encoding="utf-8"), Loader=HomeAssistantLoader
    )
    return scripts["script"]["astv_ha_mplayer_engine"]["sequence"]


def test_advmedia_call_uses_simplified_processing_boundary():
    sequence = _ha_mplayer_sequence()
    call = next(
        step
        for step in sequence
        if step.get("action") == "script.advmedia_process_media_record"
    )

    assert set(call["data"]) == {"media_record", "execution_engine", "media_player"}
    assert call["data"]["execution_engine"] == "{{ execution_context.engine }}"
    assert call["response_variable"] == "advmedia_processed_response"


def test_terminal_playback_consumes_processed_payload():
    sequence = _ha_mplayer_sequence()
    playback = next(
        step for step in sequence if step.get("action") == "media_player.play_media"
    )

    assert playback["target"] == {"entity_id": "{{ media_player_entity }}"}
    assert playback["data"] == "{{ advmedia_processed_response.playback_payload }}"
