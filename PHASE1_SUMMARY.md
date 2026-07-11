# Phase 1 File Summary

## Replaced files
- app.py
- config.json
- library.json
- requirements.txt
- test_engine.py
- core/config.py
- core/library.py
- engines/base.py
- engines/factory.py
- engines/kokoro.py
- engines/manager.py

## New files
- .gitignore
- core/paths.py
- engines/manifest.py
- engines/manifests/kokoro.json
- engines/manifests/piper.json
- engines/manifests/xtts.json
- tests/test_paths.py
- tests/test_engine_manager.py
- verify_phase1.py

## Deliberately unchanged
- core/project.py
- core/generator.py
- core/resume.py
- core/progress.py
- core/chunk_validator.py
- controllers/generation_controller.py
- workers/generator_worker.py
- all UI files

Those generation and resume files should be upgraded as Phase 2 after this
foundation passes on the actual Windows machine.
