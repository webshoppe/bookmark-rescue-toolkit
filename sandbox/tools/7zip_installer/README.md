# 7zip_installer

Place the 7-Zip Windows 64-bit installer here before running `setup_tools.bat`.

## Download

Official download page:
https://www.7-zip.org/download.html

Choose the **Windows x64 executable installer** row:
```text
7z2409-x64.exe   (or the latest version available)
```

Direct link to the current stable release:
https://www.7-zip.org/a/7z2409-x64.exe

## Notes

- 7-Zip must be reinstalled each sandbox session since the sandbox resets on close
- `setup_tools.bat` detects and installs it automatically on each run
- The installer binary is listed in `.gitignore` and is never committed
- PeaZip portable in `tools\PeaZip\` provides archive browsing without reinstalling

## Further Reading

- [7ZIP_GUIDE.md](../guides/7ZIP_GUIDE.md) - usage guide
- [TOOLS_README.md](../TOOLS_README.md) - overview of all sandbox tools
