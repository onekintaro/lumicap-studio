# After Effects Integration

This directory contains the integration layer between **LumiCap Studio
(.lcap)** and **Adobe After Effects**.

It includes two main scripts:

------------------------------------------------------------------------

## 1️⃣ LumiCap Import / Update Script

**Purpose:**\
Imports `.lcap` files into After Effects and builds animated subtitle
layers.

### What it does

-   Validates `.lcap` format (v1)

-   Creates one Text Layer per `group`

-   Sets:

    -   Source Text
    -   In / Out timing
    -   Highlight Animator
    -   Range Selector keyframes (HOLD interpolation)

-   Stores stable `group.id` in a Layer Marker:

        LCAP id: g_xxxxx

-   Supports **Update Mode**:

    -   Existing layers are matched via marker ID
    -   Text + timing + highlight steps are updated
    -   Position & styling remain untouched

-   Optional:

    -   Creates `Master <Style>` layers
    -   Master layers are created as:
        -   Guide Layers (not rendered)
        -   Shy (hidden in timeline)

------------------------------------------------------------------------

## 2️⃣ Master Apply Script (Style Propagation)

**Purpose:**\
Applies visual styling from `Master <Style>` layers to caption layers.

### Concept

-   Each caption layer is named:

        [Style] First Words

-   The script:

    -   Extracts `[Style]`
    -   Finds corresponding `Master <Style>`
    -   Copies styling (TextDocument, Animators, etc.)

-   Keeps highlight animation intact

-   Does not modify timing

This allows a clean separation between:

  Component        Responsibility
  ---------------- --------------------
  LumiCap Studio   Structure & timing
  Import Script    Layer creation
  Apply Script     Visual styling

------------------------------------------------------------------------

## .lcap Layout Support

Optional layout configuration inside:

``` json
"settings": {
  "layout": {
    "preset": "9:16",
    "comp": { "w": 1080, "h": 1920 },
    "anchor": "bottom_center",
    "safe": { "bottom": 0.12 },
    "offset": { "x": 0, "y": -120 }
  }
}
```

### Behaviour

-   If no active comp → creates comp using layout size
-   Anchor positioning supported:
    -   center
    -   bottom_center
    -   top_center
    -   bottom_left
    -   bottom_right
-   Uses safe bottom margin for social platforms
-   If layout missing → defaults to centered positioning

------------------------------------------------------------------------

## Workflow Overview

``` text
Song → Whisper → SRT
     → LumiCap Studio (.lcap)
     → AE Import Script
     → Master Styling
     → Render
```

------------------------------------------------------------------------

## Design Principles

-   Deterministic updates via stable `group.id`
-   No visual styling inside `.lcap`
-   Separation of structure and design
-   Non-destructive update workflow
-   Layout is optional and non-invasive

------------------------------------------------------------------------

Built for structured subtitle workflows and scalable caption pipelines.
