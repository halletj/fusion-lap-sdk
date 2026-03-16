"""End-to-end test: run full build and validate output."""

from pathlib import Path
from fusion_lap.build import build_lap_files

FIXTURES = Path(__file__).parent / "fixtures" / "fake_adsk"


def test_e2e_build_and_validate(tmp_path):
    """Build from fixture stubs, validate all expected outputs."""
    build_lap_files(
        output_dir=str(tmp_path),
        stubs_path=str(FIXTURES),
    )

    # fusion-base.lap must exist and contain all three sections
    base = (tmp_path / "fusion-base.lap").read_text()
    assert "[graph]" in base
    assert "[gotchas]" in base
    assert "centimeters" in base

    # At least one domain file must contain our fixture classes
    all_content = ""
    for lap_file in tmp_path.glob("fusion-*.lap"):
        all_content += lap_file.read_text()

    assert "ExtrudeFeature" in all_content
    assert "Point3D" in all_content
    assert "FeatureOperations" in all_content

    # Verify no empty domain files (besides potentially misc)
    for lap_file in tmp_path.glob("fusion-*.lap"):
        content = lap_file.read_text()
        assert len(content) > 10, f"{lap_file.name} is suspiciously empty"
