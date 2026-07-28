# Audiobook Studio v0.3.0 Update R1.8

This is a focused repair for the R1.7 verification failure:

```text
Responsive GUI smoke test failed: No module named 'psutil'
```

Install from the extracted update folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_v030_r1_8.ps1 -ProjectRoot "D:\Python\AudiobookStudio"
```

R1.8 reuses the healthy R1.7 `.venv` and installs only the missing direct
runtime dependencies. It then performs the full application verification.
