<h1 align="center">RenPy Visual Script Editor</h1>

<p align="center">
  A <strong>visual node-based script editor</strong> for Ren'Py that lets you create <code>.rpy</code> scenarios without writing code by hand.
</p>

<p align="center">
  <a href="README.md">Русский</a> |
  <a href="README_EN.md">English</a> |
  <a href="docs/WIKI.md">Wiki (RU)</a> |
  <a href="docs/WIKI_EN.md">Wiki (EN)</a>
</p>

![Main editor window](docs/images/editor_main.png)
---

## 🚀 Features

- 🎬 **Visual node-based scripting** for Ren'Py scenes
- 👤 **Character management** with colored nameplates
- 💬 **Dialogue, narration, and choice menus** with `jump` / `call` support
- 🖼 **Backgrounds, CGs, and sprites** (including composite sprites from `sprites.rpy`)
- 🎵 **Music, sound effects, and ambience** with fadein / fadeout
- 🏷 **Labels, jumps, pauses, and Python blocks**
- 👀 **Live scene preview** with draggable sprites
- 🧩 **Composite sprite parsing** - automatic layer compositing
- 📦 **Auto-indexing** of `default/` and `custom/` resource folders
- 🏷️ **Tags & grouping** for backgrounds and CGs
- 🔍 **Node search**, mass text replacement, undo/redo
- 📺 **Presentation mode** - run the script without exporting to Ren'Py
- 📄 **`.rpy` generation**, `define` block export, resource declarations
- 🔄 **Import existing `.rpy`** while preserving unrecognized code
- 🌐 **Git integration**, auto-save, command palette
---
## 📥 Installation

### Pre-built binary

Download the latest release from **[Releases](../../releases)**.

After extraction, the folder structure should look like this:

```
RenPyVisualEditor/
├── RenPyVisualEditor.exe
├── resources/
│   ├── default/
│   └── custom/
├── characters.json
└── resources_config.json
```

### Running from source

```bash
pip install -r requirements.txt
python main.py
```

---

## 📁 Resource structure

```
resources/
    default/     ← base game assets (excluded from define export)
        bg/ cg/ sprites/ music/ sounds/
    custom/      ← your assets (included in define export)
        bg/ cg/ sprites/ music/ sounds/
```

> For details on tags, composite sprites, and resource overrides, see the [Wiki](docs/WIKI_EN.md).

---

## ⌨️ Quick start

1. **Create a project:** `File → New Project` (Ctrl+N)
2. **Add characters:** `Project → Characters...` (Ctrl+P)
3. **Build a scene:** click **«+ Add Node»** and pick a node type
4. **Preview:** the right panel shows the live scene state
5. **Export:** `Generate → Export .rpy` (Ctrl+E)

---

## 🛠 System requirements

- Windows 7/10/11 (for the `.exe` build)
- Python 3.8+ (for running from source)
- Recommended resolution: 1920×1080 or higher

---

## 📚 Documentation

- **[English Wiki](docs/WIKI_EN.md)** - full user guide
- **[Русская Wiki](docs/WIKI.md)** - полное руководство на русском

---

## 🤝 Feedback

- **Discord:** https://discord.com/invite/XsCq2ndRGX
---
## 📄 License
This project is licensed under the **MIT License**.
