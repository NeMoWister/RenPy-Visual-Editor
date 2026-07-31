<h1 align="center">User Guide - RenPy Visual Script Editor</h1>

<p align="center">
  Complete documentation for the visual <strong>Ren'Py</strong> script editor.
</p>

<p align="center">
  <a href="../README.md">Русский</a> |
  <a href="../README_EN.md">English</a> |
  <a href="WIKI.md">Wiki (RU)</a> |
  <a href="WIKI_EN.md">Wiki (EN)</a>
</p>

---

## Table of contents

1. [Quick start](#1-quick-start)
2. [General structure](#2-general-structure)
3. [Resource folders](#3-resource-folders)
4. [Composite sprites](#4-composite-sprites-spritesrpy)
5. [Node types](#5-node-types)
6. [Tags & grouping](#6-tags--grouping)
7. [Scene preview](#7-scene-preview)
8. [Characters](#8-characters)
9. [Importing `.rpy` scripts](#9-importing-rpy-scripts)
10. [Generation & export](#10-generation--export)
11. [Hotkeys](#11-hotkeys)
12. [FAQ](#12-faq)
13. [Version history](#13-version-history)

---

## 1. Quick start 🚀

### First launch

Create a new project via `File → New Project` (Ctrl+N).

![Editor UI](images/editor_main.png)

> 🖼️ *Screenshot: main window. Left - scene & node list, center - node editor, right - live preview.*

### Preparing resources

Create a `resources/` folder next to the executable:

```
resources/
  custom/
    bg/          ← backgrounds (.jpg, .png)
    cg/          ← CG illustrations
    sprites/     ← sprites (character folders: sprites/us/normal/smile.png)
    music/       ← music (.ogg, .mp3)
    sounds/      ← sound effects
```

Assets in `default/` are usable in the editor but **not exported** in `define`/`image` blocks (assumed to be declared in the base game template).

### Typical flow

1. **Label** - chapter entry point
2. **Scene** - show background and clear sprites
3. **Music** - background track
4. **Show sprite** - place a character
5. **Dialogue** - spoken line

![Adding a node](images/how_to_add_node.png)

> 🖼️ *Screenshot: dropdown menu when clicking «+ Add Node».*

---

## 2. General structure 🗂️

- A **Project** contains **Scenes**. Each scene is a sequence of **Nodes**.
- A **Node** is a single action: show background, speak a line, play music, etc.
- Left panel - scene list and node list of the current scene.
- Center panel - editor for the selected node.
- Right panel - **live preview**: background, sprites, current dialogue line.

---

## 3. Resource folders 📦

### Two resource sources

| Folder | Purpose | Exported in define? |
|--------|---------|---------------------|
| `resources/default/` | Base template assets | ❌ No |
| `resources/custom/` | Your assets | ✅ Yes |

### Automatic names

| Category | Example file | Auto-generated name |
|----------|-------------|---------------------|
| Background | `bg/bus_stop.jpg` | `bg bus_stop` |
| CG | `cg/d1_food_normal.jpg` | `cg d1_food_normal` |
| Sprite | `sprites/us/normal/smile.png` | `us_normal_smile` |
| Music | `music/name.ogg` | `music_list["name"]` |
| Sound | `sounds/achievement.ogg` | `sfx_achievement` |

### Name overrides

`Project → Resource Settings → Name Overrides`

- **Save** - apply changes
- **Export / Import** - transfer override sets between projects
- **Reset** - delete all overrides (⚠️ irreversible)

![Resource settings](images/resources_settings.png)

> 🖼️ *Screenshot: resource settings window with the name override table.*

---

## 4. Composite sprites (sprites.rpy) 🧩

If a **sprites.rpy** file exists inside `resources/*/sprites/`, the editor automatically parses `ConditionSwitch` and `im.Composite` declarations and composites layers for the preview.

**Parsing example:**
```renpy
image cs normal stethoscope far = ConditionSwitch(
    "persistent.sprite_time=='sunset'", im.MatrixColor(im.Composite((630,1080),
        (0,0), "sprites/far/cs/cs_1_body.png",
        (0,0), "sprites/far/cs/cs_1_stethoscope.png",
        (0,0), "sprites/far/cs/cs_1_normal.png"), im.matrix.tint(0.94, 0.82, 1.0)),
    ...
)
```

**In the editor:**
- Character → Distance (far / close / normal) → Emotion
- Layers are composited automatically in the preview
- Conditional tinting (`im.matrix.tint`) is ignored in preview

**Hiding:** use `hide cs`, not the full emotion name.

![Composite sprite picker](images/select_sprite.png)

> 🖼️ *Screenshot: sprite carousel. Character folders → distance → emotion with composited preview.*

---

## 5. Node types 🎬

| Node | Description | Generated example |
|------|-------------|-------------------|
| **Dialogue** | Character speech | `me "Text"` |
| **Narrator** | Text without a name | `"Text"` |
| **Scene** | Background + clear sprites | `scene bg bus_stop` |
| **Background (show)** | Change background only | `show bg bus_stop` |
| **CG** | Full-screen illustration | `show cg d1_food_normal` |
| **Show sprite** | Sprite with position & transition | `show un smile at left with dissolve` |
| **Hide sprite** | Hide specific sprite or whole character | `hide un` |
| **Text window** | Show/hide dialogue window | `window show` / `window hide` |
| **Effect (with)** | Standalone transition | `with dissolve` |
| **Music** | Play with fadein | `play music music_list["name"] fadein 2` |
| **Stop music** | Stop with fadeout | `stop music fadeout 3` |
| **Sound** | Sound effect | `play sound sfx_achievement` |
| **Ambience** | Environmental loops | `play ambience ...` / `stop ambience` |
| **Label** | Entry point | `label chapter_1:` |
| **Jump** | Jump to label | `jump chapter_2` |
| **Choice menu** | Branching menu | `menu:` |
| **Pause** | Click wait or timer | `pause` / `pause 2.0` |
| **Return** | Return from call | `return` |
| **Python code** | Arbitrary code | `$ flag = True` |
| **Raw code** | Unrecognized block (imported) | preserved verbatim |

### scene vs show

- **`scene`** - clears **all** sprites and CGs before showing the background. Use when changing location.
- **`show`** - changes only the background; characters stay on screen.

### Choice menu

Each option has:
- **Text** - what the player sees
- **Label** - where to jump/call
- **«call» checkbox** - default is `jump`; enable for `call` (returns after `return`)
- **Body** - inline Ren'Py code executed when chosen

![Choice menu node](images/renpy_menu.png)

> 🖼️ *Screenshot: choice menu node with three options, label fields, and call checkboxes.*

### Transitions

Built-in: `dissolve`, `fade`, `fade2`, `fade3`, `flash`, `pixellate`, `blinds`, `squares`, `wipeleft`, `wiperight`, `wipeup`, `wipedown`, `vpunch`, `hpunch`, `dspr`.

The field is editable: you can type a custom `define transform mytrans` name.

**Grouping:** if consecutive nodes share the same transition, they are exported with a single trailing `with`.

---

## 6. Tags & grouping 🏷️

`Project → Resource Tags`

1. Create a **category** (e.g., «Location»)
2. Add **tags** («beach», «school», «night»)
3. Assign tags to resources via right-click in the carousel
4. In the BG/CG node, select «Group by → Location»

Untagged resources appear under «No tag».

![Tag editor](images/add_tag_menu.png)

> 🖼️ *Screenshot: tag category editor adding a new «Time of Day» category.*

![Tag grouping](images/tags_sorted.png)

> 🖼️ *Screenshot: background carousel grouped by pseudo-folders «Location».*

---

## 7. Scene preview 👀

The right panel shows the scene state at the selected node:
- Background / CG
- All visible sprites
- Current dialogue line

**Interactive:**
- **Drag a sprite** - change `xalign` (horizontal position)
- **Click a sprite** - delete the node that showed it
- **Hover** - highlight with a «remove» tooltip

**Default anchors:** `left`, `cleft`, `center`, `cright`, `right`, `fleft`, `fright`.

![Scene preview](images/scene_preview.png)

> 🖼️ *Screenshot: preview window with a background, two character sprites, and a dialogue box.*

---

## 8. Characters 👤

`Project → Characters...` (Ctrl+P)

- **Name** - displayed in the UI
- **Variable** - written to `.rpy` (`me`, `th`, `un`)
- **Color** - name color in dialogue

**Buttons:**
- Export / Import character list as JSON
- Reset list

---

## 9. Importing `.rpy` scripts 🔄

`File → Import .rpy script`

**Recognized:**
- `scene`, `show`, `hide` (backgrounds, CGs, sprites)
- `window show` / `window hide`
- `with` (including grouped transitions)
- Dialogues and narration
- `play music`, `stop music`, `play sound`, `play ambience`
- `label`, `jump`, `call`, `return`, `pause`
- `menu:` with options and bodies
- `$ ...` and `python:` blocks
- Conditional blocks (`if`) - as RAW nodes

**Becomes RAW:**
- `show X:` with ATL block if `X` is unknown
- `init python`, `transform`, `screen`
- Any unrecognized constructs

---

## 10. Generation & export 📄

| Action | Hotkey | Result |
|--------|--------|--------|
| View code | Ctrl+G | Window with final `.rpy` |
| Export `.rpy` | Ctrl+E | Save script file |
| Export character defines | - | `define ... = Character(...)` |
| Export resource defines | - | `image ...` / `define ...` from `custom/` only |

---

## 11. Hotkeys ⌨️

| Keys | Action |
|------|--------|
| Ctrl+N | New project |
| Ctrl+O | Open project |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save as |
| Ctrl+P | Characters |
| F5 | Re-index resources |
| Ctrl+G | View generated code |
| Ctrl+E | Export `.rpy` |
| Ctrl+C / Ctrl+V | Copy / paste nodes |
| Ctrl+Z / Ctrl+Y | Undo / redo |
| Ctrl+Shift+P | Command palette |

---

## 12. FAQ ❓

**Q: I added files to `resources/` but don't see them.**
A: Press F5 («Re-index resources») or restart the editor.

**Q: What's the difference between Scene and Background?**
A: `scene` clears all sprites; `show` only changes the background.

**Q: My composite sprite won't hide.**
A: Use the character name: `hide cs`, not the full emotion name.

**Q: A tag category doesn't appear in the CG node.**
A: Categories only appear where resources have those tags. Tag at least one CG.

**Q: `show X:` with ATL became RAW.**
A: If `X` isn't found in resources, the code is preserved verbatim. Make sure the file is in the correct folder and press F5.

---

## 13. Version history 📜

### v1.4.0
- Choice menus with nested node support
- «Where used» resource usage viewer
- Built-in audio player with waveform visualization
- Presentation mode: start from any node, rewind, breadcrumbs
- Script timing analysis
- Per-line merge helper on export
- Multi-file export (one `.rpy` per chapter)
- Smart import (match existing resources)
- Import characters with auto-detected colors
- Spell checking
- Git integration (commit graph, LFS, tags)
- Command palette (Ctrl+Shift+P)
- NVL / ADV mode support

### v1.3.0
- Collapsible node groups
- Copy / paste nodes and chains
- Node search with jump-to-result
- Color-coded node markers
- Undo / redo
- Dialogue counter per character
- Mass text replacement
- Favorites / recently used resources
- Export to plain text & import corrections
- Custom node templates
- Presentation mode (beta)
- Auto-save & crash recovery
- Drag-n-drop resources into carousel
- In-app versioning (snapshots)

### v1.2.0
- Character name recoloring from settings
- Updated UI design

### v1.1.0
- Dialogue length hint (200/340 chars)
- In-editor music & sound playback
- Tags for BG and CG
- `.rpy` script import
- Nodes: scene, stop music, window show/hide

### v1.0.0
- Core visual node editor
- Sprite subfolders (normal/far/close)
- Composite sprite support (`sprites.rpy`)
- `default/` and `custom/` folders
- Automatic resource naming
- Live scene preview
- Transition handling (dissolve, dspr, etc.)
- Choice menu with jump/call
- User guide

---

*Documentation is current for version 1.4.0.*
