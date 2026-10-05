from pathlib import Path

from core.chunk_audio import build_command, pts_to_seconds


def test_pts_to_seconds():
    assert pts_to_seconds(24000) == 1.0
    assert pts_to_seconds(0) == 0.0
    assert pts_to_seconds(12000) == 0.5


def test_build_command_structure():
    cmd = build_command(Path("audio/master.wav"), 0, 24000, Path("out.wav"))
    assert cmd[0] == "ffmpeg"
    assert "-ss" in cmd
    assert cmd[cmd.index("-ss") + 1] == "0.000000000"
    assert "-t" in cmd
    assert cmd[cmd.index("-t") + 1] == "1.000000000"
    assert "-ar" in cmd and "48000" in cmd
    assert "-ac" in cmd and "2" in cmd
    assert cmd[-1] == "out.wav"


def test_build_command_duration():
    cmd = build_command(Path("audio/master.wav"), 12000, 36000, Path("out.wav"))
    assert cmd[cmd.index("-ss") + 1] == "0.500000000"
    assert cmd[cmd.index("-t") + 1] == "1.000000000"
