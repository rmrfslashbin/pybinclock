# CLAUDE.md

Guidance for working in this repository.

## What this is

PyBinClock is a binary clock for a Raspberry Pi driving a Pimoroni **Unicorn
HAT Mini** (17×7 RGB LED matrix). It shows the local date/time as six rows of
binary bits (year, month, day, hour, minute, second) plus a status row.

**This repo runs live**: it is deployed as a systemd service (`pybinclock.service`)
on this Pi (`rpi01`) and is actively displaying on hardware. Treat changes as
production — verify, then redeploy and restart the service (see below).

## Layout

```
pybinclock/
  PyBinClock.py     # CurrentTime: datetime -> per-field binary lists; console clock
  BinClockLEDs.py   # THE LED controller (config-driven) + mock-hardware fallback + main loop
  config.py         # Config/DisplayConfig/ColorScheme/ButtonConfig dataclasses + JSON load/save
tests/              # pytest, runs with mock hardware (no Pi needed)
themes/             # example color-theme config JSONs
setup.sh / uninstall.sh   # systemd install/uninstall
sample_config.json  # example config
5x7.ttf             # bitmap font for scrolling-text mode
```

There is **one** LED controller module (`BinClockLEDs.py`). Earlier there were
three (`BinClockLEDs.py` with buttons, `_nobuttons.py`, `_improved.py`); they
were consolidated into the single config-driven `LEDController`. Behavior is
selected via config, not by importing different modules:
- `enable_buttons: true`  -> interactive (A=pause, B=mode toggle, X=exit)
- `enable_buttons: false` -> headless (the service uses this)

## Tooling / commands

- Package manager is **uv**. `requires-python >=3.10` (Python 3.9 is EOL; the Pi
  runs 3.11). If you bump this, update it in FOUR places: `pyproject.toml`
  `requires-python`, `[tool.mypy] python_version`, `[tool.black] target-version`,
  and `.pre-commit-config.yaml` black `language_version`.
- Install dev deps: `uv sync --extra dev`
- Quality gate (all currently clean): `make all` (= format, lint, type-check, test),
  or individually `make format` / `make lint` / `make type-check` / `make test`.

### Test gotcha

`pytest-cov` is configured via `addopts` in `pyproject.toml`. Immediately after
uv rebuilds the editable package, a bare `uv run pytest` can fail with
`unrecognized arguments: --cov` because the plugin isn't yet registered. The
reliable invocation is:

```
uv run python -m pytest -p pytest_cov
```

`make test` (`uv run pytest`) works once the env is synced.

### Module/function name collision

The entry-point function `BinClockLEDs` lives in module `pybinclock.BinClockLEDs`,
and `__init__.py` re-exports the function — so `pybinclock.BinClockLEDs`
resolves to the *function*, shadowing the submodule attribute. Same pattern for
`PyBinClock`. Consequences:
- `from pybinclock.BinClockLEDs import BinClockLEDs` works fine (this is what the
  service wrapper and entry points use).
- To get the *module* object (e.g. to monkeypatch `HARDWARE_AVAILABLE` in a
  script), use `importlib.import_module("pybinclock.BinClockLEDs")`. In tests,
  `@patch("pybinclock.BinClockLEDs.HARDWARE_AVAILABLE", ...)` resolves correctly.

### Config notes

- `ColorScheme` fields are non-optional (populated via `default_factory`).
- There are **no** `width`/`height` settings — panel size comes from the
  hardware `get_shape()`. The loader ignores unknown/legacy keys, so old config
  files (and `_comment` annotations) load without error.

## Deployment (systemd)

Install target: `/usr/local/lib/pybinclock/` (root-owned, except `.venv` which is
user-owned). Wrapper: `/usr/local/bin/pybinclock`. Service runs as user
`rmrfslashbin`, env `GPIOZERO_PIN_FACTORY=lgpio`, and loads
`~/.config/pybinclock/config.json` (which sets `enable_buttons: false`).

`setup.sh` performs a full install but does NOT stop the service first, clean
stale files in the target, or restart. A safe manual redeploy:

```bash
sudo systemctl stop pybinclock.service
# clean + copy fresh sources
sudo rm -rf /usr/local/lib/pybinclock/pybinclock/__pycache__
sudo cp pybinclock/*.py /usr/local/lib/pybinclock/pybinclock/
sudo cp pyproject.toml uv.lock 5x7.ttf /usr/local/lib/pybinclock/
# resync deps against the lock, then hand the venv back to the user
( cd /usr/local/lib/pybinclock && sudo /home/rmrfslashbin/.local/bin/uv sync --frozen )
sudo chown -R rmrfslashbin:rmrfslashbin /usr/local/lib/pybinclock/.venv
sudo systemctl start pybinclock.service
```

If you delete/rename a module, also remove the stale file from the install
target (`cp -r` won't). If you change the module the wrapper imports, regenerate
`/usr/local/bin/pybinclock`.

Verify after deploy:
```bash
systemctl is-active pybinclock.service
sudo journalctl -u pybinclock -n 20 --no-pager      # expect "Starting BinClockLEDs"
sudo journalctl -u pybinclock --since "1 min ago" -p warning --no-pager   # expect none
```

Normal running CPU is ~1% (one 1 Hz update loop). A pegged CPU means something
is wrong.

## Conventions

- Line length 88 (black + flake8). `.flake8` ignores E203/W503; `__init__.py`
  ignores F401 (re-exports).
- Keep `pyproject.toml`, `sample_config.json`, and `config.create_sample_config`
  in sync when adding/removing config fields.
- Hardware libs (`gpiozero`, `unicornhatmini`, `RPi.GPIO`, `lgpio`) are only
  present on the Pi; code must degrade to mock hardware off-device (it does).
