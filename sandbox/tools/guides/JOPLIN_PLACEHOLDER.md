# Joplin - Planned Integration

> **Status: Planned - not yet implemented**
> 
> This guide is a placeholder for a future Joplin integration with the BRT sandbox environment and a broader personal dev sandbox setup.

## What Joplin Would Provide

- Markdown note-taking with a proper editor and rendered preview
- Persistent notes via the host-backed `tools\Notes\` folder
- Access from both the sandbox and the host simultaneously
- Exportable to Markdown, HTML, and PDF

## Planned Approach

The integration would:

1. Use Joplin portable pointed at `tools\Notes\` as its profile directory
2. Pre-load a notebook with BRT-specific notes and quick-reference cards
3. Make notes accessible from the host at `C:\Bookmark_Rescue\tools\Notes\`
4. Include a setup guide for configuring sync with a self-hosted server
   or local filesystem

## In the Meantime

For notes within the sandbox, the `tools\Notes\` folder is host-backed and accessible from both environments. Any text editor (Notepad++ or the standard Windows Notepad) can be used to create and edit notes there.

## Further Reading

- [Joplin official site](https://joplinapp.org/)
- [Joplin portable download](https://joplinapp.org/help/install/)
- This sandbox is part of a broader planned IsolationVault dev environment guide - see the IsolationVault repository when available
