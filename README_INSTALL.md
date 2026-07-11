# AudiobookStudio Phase 1 Upgrade

This package is a safe first upgrade for:

`D:\Python\AudiobookStudio`

It preserves the current PySide6 UI and generation contracts. It does **not**
replace the existing `core/project.py`, `core/generator.py`, controllers, or
workers.

## What this phase changes

- Portable project-root path handling.
- Private `config.local.json` and `library.local.json`.
- Atomic JSON writes.
- Lazy Kokoro loading so the GUI can start without immediately loading Torch.
- Manifest-based TTS engine discovery.
- Safer engine unload and GPU-memory release.
- Atomic WAV chunk writes.
- Accurate optional pitch shifting through librosa.
- Removal of the personal book path from tracked JSON defaults.
- Basic tests and a verification command.

## Automatic installation

Open PowerShell in this extracted upgrade folder and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_phase1.ps1 -ProjectRoot "D:\Python\AudiobookStudio"
```

The installer:

1. Creates a timestamped backup inside your project.
2. Copies your old `config.json` to `config.local.json`.
3. Copies your old `library.json` to `library.local.json`.
4. Places every replacement at the correct path.
5. Does not delete your existing project files.

## Dependency installation

Use the same virtual environment you use for AudiobookStudio:

```powershell
cd "D:\Python\AudiobookStudio"
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

PyTorch is intentionally not pinned in `requirements.txt`. Install the correct
Windows CUDA or CPU build using the official PyTorch installer selector.

## Verification

```powershell
cd "D:\Python\AudiobookStudio"
.\.venv\Scripts\python.exe verify_phase1.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe test_engine.py --list
```

Generate a short Kokoro test:

```powershell
.\.venv\Scripts\python.exe test_engine.py `
  --engine kokoro `
  --voice af_heart `
  --text "Audiobook Studio is ready." `
  --output "Output\engine_test.wav"
```

Launch the application:

```powershell
.\.venv\Scripts\python.exe app.py
```

## Exact destination map

| Upgrade file | Put it in |
|---|---|
| `app.py` | `D:\Python\AudiobookStudio\app.py` |
| `config.json` | `D:\Python\AudiobookStudio\config.json` |
| `library.json` | `D:\Python\AudiobookStudio\library.json` |
| `requirements.txt` | `D:\Python\AudiobookStudio\requirements.txt` |
| `.gitignore` | `D:\Python\AudiobookStudio\.gitignore` |
| `test_engine.py` | `D:\Python\AudiobookStudio\test_engine.py` |
| `verify_phase1.py` | `D:\Python\AudiobookStudio\verify_phase1.py` |
| `core/paths.py` | `D:\Python\AudiobookStudio\core\paths.py` |
| `core/config.py` | `D:\Python\AudiobookStudio\core\config.py` |
| `core/library.py` | `D:\Python\AudiobookStudio\core\library.py` |
| `engines/base.py` | `D:\Python\AudiobookStudio\engines\base.py` |
| `engines/manifest.py` | `D:\Python\AudiobookStudio\engines\manifest.py` |
| `engines/manager.py` | `D:\Python\AudiobookStudio\engines\manager.py` |
| `engines/factory.py` | `D:\Python\AudiobookStudio\engines\factory.py` |
| `engines/kokoro.py` | `D:\Python\AudiobookStudio\engines\kokoro.py` |
| `engines/manifests/*.json` | `D:\Python\AudiobookStudio\engines\manifests\` |
| `tests/*.py` | `D:\Python\AudiobookStudio\tests\` |

## Git commit

After the checks pass:

```powershell
cd "D:\Python\AudiobookStudio"
git status
git add .
git commit -m "Add portable paths and manifest-based TTS engines"
git push origin main
```

Do not commit `config.local.json`, `library.local.json`, models, generated
audio, logs, output, cache, or project working folders. The included
`.gitignore` excludes them.
