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

LumiCap Studio began as an experiment to simplify subtitle workflows for
creative scripting and After Effects pipelines.

Very quickly, the need for structure emerged: - Reusable grouping
logic - Style propagation - Protect mechanisms - Persistent project
states

Instead of patching features onto a single export script, the project
evolved into a full engine architecture --- separating logic from
interface and defining a native project format.

LumiCap is not just a subtitle tool.

It is a caption engine framework --- designed to grow.

------------------------------------------------------------------------

## 📄 License

Currently private / internal development. License to be defined.
