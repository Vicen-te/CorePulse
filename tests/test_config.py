"""
Unit tests for configuration and theme detection.

Usage:
    cd ThermalCore
    source .venv/bin/activate
    python -m pytest tests/test_config.py -v
"""

import sys
import unittest
sys.path.insert(0, "src")

from utils.config import (
    DARK_PALETTE,
    LIGHT_PALETTE,
    detect_dark_mode,
    get_palette,
    apply_palette,
    POLL_INTERVAL_MS,
    TEMP_THRESHOLD_LOW,
    TEMP_THRESHOLD_MEDIUM,
    TEMP_THRESHOLD_HIGH,
)


class TestPalettes(unittest.TestCase):
    """Test color palette structure and consistency."""

    REQUIRED_KEYS = [
        "background", "panel", "accent", "warning",
        "text_primary", "text_secondary",
        "temp_cool", "temp_warm", "temp_hot", "temp_critical",
    ]

    def test_dark_palette_has_all_keys(self) -> None:
        """Dark palette must have all required color keys."""
        for key in self.REQUIRED_KEYS:
            self.assertIn(key, DARK_PALETTE, f"Missing '{key}' in DARK_PALETTE")

    def test_light_palette_has_all_keys(self) -> None:
        """Light palette must have all required color keys."""
        for key in self.REQUIRED_KEYS:
            self.assertIn(key, LIGHT_PALETTE, f"Missing '{key}' in LIGHT_PALETTE")

    def test_palettes_have_same_keys(self) -> None:
        """Both palettes must define the same set of keys."""
        self.assertEqual(set(DARK_PALETTE.keys()), set(LIGHT_PALETTE.keys()))

    def test_all_colors_are_hex(self) -> None:
        """All color values should be valid hex color strings."""
        for name, palette in [("dark", DARK_PALETTE), ("light", LIGHT_PALETTE)]:
            for key, value in palette.items():
                self.assertTrue(
                    value.startswith("#") and len(value) in (4, 7),
                    f"{name}.{key} = '{value}' is not a valid hex color",
                )

    def test_dark_and_light_differ(self) -> None:
        """Dark and light palettes should have different background colors."""
        self.assertNotEqual(DARK_PALETTE["background"], LIGHT_PALETTE["background"])


class TestThemeDetection(unittest.TestCase):
    """Test theme detection function."""

    def test_detect_dark_mode_returns_bool(self) -> None:
        """detect_dark_mode() must return a boolean."""
        result = detect_dark_mode()
        self.assertIsInstance(result, bool)

    def test_get_palette_returns_valid_palette(self) -> None:
        """get_palette() must return a dict with all required keys."""
        palette = get_palette()
        self.assertIsInstance(palette, dict)
        for key in TestPalettes.REQUIRED_KEYS:
            self.assertIn(key, palette)

    def test_get_palette_matches_detection(self) -> None:
        """get_palette() should return the palette matching current theme."""
        is_dark = detect_dark_mode()
        palette = get_palette()
        expected = DARK_PALETTE if is_dark else LIGHT_PALETTE
        self.assertEqual(palette, expected)


class TestApplyPalette(unittest.TestCase):
    """Test palette application to module-level variables."""

    def test_apply_dark_palette(self) -> None:
        """Applying dark palette should update module-level colors."""
        import utils.config as cfg
        apply_palette(DARK_PALETTE)
        self.assertEqual(cfg.COLOR_BACKGROUND, DARK_PALETTE["background"])
        self.assertEqual(cfg.COLOR_WARNING, DARK_PALETTE["warning"])

    def test_apply_light_palette(self) -> None:
        """Applying light palette should update module-level colors."""
        import utils.config as cfg
        apply_palette(LIGHT_PALETTE)
        self.assertEqual(cfg.COLOR_BACKGROUND, LIGHT_PALETTE["background"])
        self.assertEqual(cfg.COLOR_TEXT_PRIMARY, LIGHT_PALETTE["text_primary"])

    def tearDown(self) -> None:
        """Restore original palette."""
        apply_palette(get_palette())


class TestConstants(unittest.TestCase):
    """Test that configuration constants have reasonable values."""

    def test_poll_interval_positive(self) -> None:
        """Poll interval must be positive."""
        self.assertGreater(POLL_INTERVAL_MS, 0)

    def test_poll_interval_reasonable(self) -> None:
        """Poll interval should be between 100ms and 10s."""
        self.assertGreaterEqual(POLL_INTERVAL_MS, 100)
        self.assertLessEqual(POLL_INTERVAL_MS, 10000)

    def test_temperature_thresholds_ordered(self) -> None:
        """Temperature thresholds must be in ascending order."""
        self.assertLess(TEMP_THRESHOLD_LOW, TEMP_THRESHOLD_MEDIUM)
        self.assertLess(TEMP_THRESHOLD_MEDIUM, TEMP_THRESHOLD_HIGH)

    def test_temperature_thresholds_reasonable(self) -> None:
        """Temperature thresholds should be in a sane range for CPUs."""
        self.assertGreaterEqual(TEMP_THRESHOLD_LOW, 30)
        self.assertLessEqual(TEMP_THRESHOLD_HIGH, 110)


if __name__ == "__main__":
    unittest.main()
