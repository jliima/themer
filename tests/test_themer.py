"""Tests for Themer. Run from the repository root: python3 -m unittest discover tests

The unit tests import the `themer` script; the command tests run it in a throwaway HOME so nothing outside the
temporary folder is touched. The theme in tests/fixtures is a test fixture; Themer itself ships no themes."""

import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def load_module():
  loader = importlib.machinery.SourceFileLoader("themer_script", str(ROOT / "themer"))
  spec = importlib.util.spec_from_loader("themer_script", loader)
  mod = importlib.util.module_from_spec(spec)
  loader.exec_module(mod)
  return mod


themer = load_module()


class ColorsAndTemplates(unittest.TestCase):
  def test_oklch_round_trip(self):
    for h in ("#5faff1", "#091017", "#ffffff", "#000000", "#c0392b"):
      back = themer.oklch_to_hex(*themer.hex_to_oklch(h))
      self.assertEqual(back, h)

  def test_fixture_theme_fills_the_contract(self):
    pal = themer.load_theme(str(FIXTURES / "ember"))
    self.assertEqual(themer.validate(pal), [])

  def test_template_tokens_and_filters(self):
    pal = themer.load_theme(str(FIXTURES / "ember"))
    ctx = themer.context(pal, "dark")
    plain = themer.render("{{ accent }}", ctx)
    self.assertRegex(plain, r"^#[0-9a-f]{6}$")
    self.assertEqual(themer.render("{{ accent | strip }}", ctx), plain[1:])
    self.assertEqual(themer.render("{{ scheme }} {{ variant }}", ctx), "EmberDark dark")


class Commands(unittest.TestCase):
  def setUp(self):
    self.tmp = tempfile.TemporaryDirectory()
    self.home = Path(self.tmp.name) / "home"
    self.home.mkdir()
    self.env = {k: v for k, v in os.environ.items() if not k.startswith(("XDG_", "THEMER_"))}
    self.env["HOME"] = str(self.home)

  def tearDown(self):
    self.tmp.cleanup()

  def run_cmd(self, *cmd):
    return subprocess.run([str(c) for c in cmd], env=self.env, capture_output=True, text=True, cwd=self.tmp.name)

  def install(self, *args):
    res = self.run_cmd(ROOT / "install.sh", *args)
    self.assertEqual(res.returncode, 0, res.stderr)
    return res

  def test_install_seeds_the_kde_example_once(self):
    self.install()
    kde = self.home / ".config/themer/templates/kde"
    self.assertTrue((kde / "kdeglobals.ini").is_file())
    self.assertTrue((self.home / ".local/bin/themer").is_symlink())
    (kde / "kdeglobals.ini").write_text("mine\n")
    self.install()
    self.assertEqual((kde / "kdeglobals.ini").read_text(), "mine\n")

  def test_themes_and_dry_run_with_only_the_example_template(self):
    self.install()
    self.assertIn("no themes installed", self.run_cmd(ROOT / "themer", "themes").stdout)
    res = self.run_cmd(ROOT / "themer", "install", FIXTURES / "ember")
    self.assertEqual(res.returncode, 0, res.stderr)
    res = self.run_cmd(ROOT / "themer", "apply", "--theme", "ember", "--dry-run")
    self.assertEqual(res.returncode, 0, res.stderr)
    self.assertIn("would write", res.stdout)
    self.assertIn("skipped GTK 4 and libadwaita colors (no template gtk/themer.css", res.stdout)

  def test_apply_without_a_theme_explains_itself(self):
    self.install()
    res = self.run_cmd(ROOT / "themer", "apply", "--dry-run")
    self.assertNotEqual(res.returncode, 0)
    self.assertIn("no theme to use", res.stderr)

  def test_dotfiles_folder_is_found_from_the_stowed_settings(self):
    dots = Path(self.tmp.name) / "anywhere" / "dots"
    (dots / ".config/themer").mkdir(parents=True)
    (dots / ".config/themer/settings.toml").write_text("[dotfiles]\nenabled = true\nstow = \"\"\n")
    conf = self.home / ".config/themer"
    conf.mkdir(parents=True)
    (conf / "settings.toml").symlink_to(dots / ".config/themer/settings.toml")
    res = self.run_cmd(ROOT / "themer", "doctor", "--theme", FIXTURES / "ember")
    self.assertIn(f"dotfiles  {dots.resolve()}", res.stdout)


if __name__ == "__main__":
  unittest.main()
