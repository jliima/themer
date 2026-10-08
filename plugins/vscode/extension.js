// Themer for VS Code.
//
// The color themes themselves are rendered by Themer into ./themes (themer-dark.json, themer-light.json). VS Code reads
// a theme file once and never again, so a theme or variant that Themer re-renders keeps showing the old colors until
// the window is reloaded. This extension watches the rendered files and reloads the window when their content changes.
// Switching between the dark and light variant needs nothing from here: with "window.autoDetectColorScheme" VS Code
// follows the desktop, and both variant files are already loaded.
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const vscode = require("vscode");

const THEMES = ["themer-dark.json", "themer-light.json"];
const DEBOUNCE_MS = 700;

function digest(dir) {
  const hash = crypto.createHash("sha1");
  for (const name of THEMES) {
    try {
      hash.update(fs.readFileSync(path.join(dir, name)));
    } catch {
      hash.update("missing");
    }
  }
  return hash.digest("hex");
}

// True when a Themer theme is what the window shows (or follows, with autoDetectColorScheme).
function themerIsSelected() {
  const workbench = vscode.workspace.getConfiguration("workbench");
  const names = ["colorTheme", "preferredDarkColorTheme", "preferredLightColorTheme"].map((k) => workbench.get(k));
  return names.some((n) => typeof n === "string" && n.startsWith("Themer "));
}

function activate(context) {
  const dir = path.join(context.extensionPath, "themes");
  let loaded = digest(dir);
  let timer;
  let asked = false;

  const reload = () => vscode.commands.executeCommand("workbench.action.reloadWindow");

  async function onChange() {
    const now = digest(dir);
    if (now === loaded) {
      return;
    }
    loaded = now;
    if (!themerIsSelected()) {
      return;
    }
    const auto = vscode.workspace.getConfiguration("themer").get("autoReload", true);
    if (auto && !vscode.debug.activeDebugSession) {
      await reload();
    } else if (!asked) {
      asked = true;
      const pick = await vscode.window.showInformationMessage("Themer rendered new colors.", "Reload Window");
      asked = false;
      if (pick) {
        await reload();
      }
    }
  }

  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(onChange, DEBOUNCE_MS);
  }

  // Watch the folder, not the files: Themer may replace a file instead of writing into it.
  let watcher;
  try {
    fs.mkdirSync(dir, { recursive: true });
    watcher = fs.watch(dir, schedule);
  } catch (err) {
    console.error("themer: cannot watch " + dir, err);
  }

  context.subscriptions.push({
    dispose() {
      clearTimeout(timer);
      if (watcher) {
        watcher.close();
      }
    },
  });
}

function deactivate() {}

module.exports = { activate, deactivate };
