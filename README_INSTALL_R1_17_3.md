\
# Install Audiobook Studio R1.17.3

Close Audiobook Studio, extract the update into a new folder, then run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\install_v030_r1_17_3.ps1 `
    -ProjectRoot "D:\Python\AudiobookStudio"
```

R1.17.3 is cumulative. It installs the complete corrected source rather than a
small overlay. It preserves the verified runtime, models, books, projects,
outputs, local settings, pronunciation rules, and private voice recordings.

The old OCR cache format is rejected automatically. The next generation of the
1945 PDF must process and account for all 10 pages before narration can begin.
