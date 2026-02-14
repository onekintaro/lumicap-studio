# LumiCap Studio 💜

A modular caption engine with its own native project format: `.lcap`

------------------------------------------------------------------------

## ✨ Vision

LumiCap Studio started as a simple subtitle utility --- but quickly
evolved into something bigger:

A structured, extensible caption engine designed for creators who care
about precision, styling, workflow control, and long‑term
maintainability.

Instead of being tied to a single export format (like After Effects
JSON), LumiCap introduces a native project format:

> `.lcap` --- a versioned, engine-aware caption project file.

This allows: - Project persistence - Version migration - Multi-export
support - Draft/Release workflows - Future plugin architecture

------------------------------------------------------------------------

## 🧠 Philosophy

LumiCap is built around separation of concerns:

-   `core/` → pure logic (parsing, grouping, exporting)
-   `ui/` → CustomTkinter interface
-   `.lcap` → neutral engine project format

The goal is to keep UI separate from business logic, making the engine
reusable in: - CLI tools - Automation scripts - Batch processors -
Future web or plugin integrations

------------------------------------------------------------------------

## 📦 Native Format: `.lcap`

Every `.lcap` file includes:

-   `format` (always `"lcap"`)
-   `version` (for migration support)
-   `meta` (e.g. draft state)
-   `settings` (engine configuration used to build the project)
-   `groups` (caption groups with timing, style, and steps)

Example structure:

``` json
{
  "format": "lcap",
  "version": 1,
  "meta": {
    "draft": true
  },
  "settings": {
    "normalize_punct_spacing": true,
    "disable_highlight_at_out": true,
    "default_style": "Normal"
  },
  "groups": [
    {
      "key": "example_key",
      "style": "Normal",
      "text": "Example subtitle",
      "in": 7.05,
      "out": 13.14,
      "steps": []
    }
  ]
}
```

------------------------------------------------------------------------

## 🚀 Current Features

-   SRT Import
-   Intelligent Grouping (key-based)
-   Multi-select batch styling
-   Protect toggle (`!` style)
-   Full JSON preview
-   Native `.lcap` export
-   Draft metadata support
-   Modular architecture

------------------------------------------------------------------------

## 🔮 Planned Features

-   `.lcap` project loading
-   Timeline editor
-   Style presets
-   Multi-export targets
-   Autosave & versioning
-   Plugin system
-   Executable build via PyInstaller

------------------------------------------------------------------------

## 🛠 Tech Stack

-   Python 3.13+
-   CustomTkinter
-   Dataclasses
-   Modular core architecture
-   Git version control

------------------------------------------------------------------------

## 💜 Background Story

LumiCap Studio began as a simple idea:

"Wouldn't it be nice if subtitles weren't painful?"

It was supposed to be a small export helper.

Then ADHD kicked in.

What followed was not a patch.
It was escalation.

- Reusable grouping logic  
- Style propagation  
- Protection mechanisms  
- Persistent project states  
- A native project format  
- A full engine architecture  

Instead of stacking features onto one script,
the project evolved into a structured system —
separating core logic from interface layers
and defining its own framework.

LumiCap is not just a subtitle tool.

It is what happens
when engineering hyperfocus meets ADHD.

------------------------------------------------------------------------

## 📄 License

Distributed under the GNU GPL-3.0 License.  
See the LICENSE file for more information.

© 2026 Rebecca