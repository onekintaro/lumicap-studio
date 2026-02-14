# LCAP Format Specification

LumiCap Studio Native Project Format

Version: 1.0 Status: Draft Engine: LumiCap Studio

------------------------------------------------------------------------

# 1. Purpose

LCAP (`.lcap`) is the native project format for LumiCap Studio.

It is designed to:

-   Persist full project state
-   Preserve engine configuration
-   Support draft/release workflows
-   Enable future migration between format versions
-   Remain independent from specific export targets

LCAP files are JSON-based and versioned.

------------------------------------------------------------------------

# 2. File Extension

.lcap

LCAP files MUST be valid UTF-8 encoded JSON documents.

------------------------------------------------------------------------

# 3. Root Structure

An LCAP file MUST contain the following root-level fields:

    {
      "format": "lcap",
      "version": 1,
      "source": "...",
      "meta": { ... },
      "settings": { ... },
      "groups": [ ... ]
    }

------------------------------------------------------------------------

# 4. Root Fields

## 4.1 format (required)

Type: string\
Value: "lcap"

Used to identify the file as an LCAP document.

------------------------------------------------------------------------

## 4.2 version (required)

Type: integer

Indicates the format version.\
Current version: 1

Future versions MUST increment this value if breaking structural changes
occur.

------------------------------------------------------------------------

## 4.3 source (optional)

Type: string or null

Original import source (e.g., SRT file path).\
Used for informational and debugging purposes.

------------------------------------------------------------------------

## 4.4 meta (optional but recommended)

Type: object

Metadata about the project state.

Example:

    "meta": {
      "draft": true,
      "created_with": "LumiCap Studio",
      "created_at": "2026-02-14T02:45:00Z"
    }

### meta.draft

Type: boolean

Indicates whether the project is considered a draft.

Tools MAY warn users when loading draft projects.

------------------------------------------------------------------------

## 4.5 settings (optional but recommended)

Type: object

Stores engine configuration used to build the project.

Example:

    "settings": {
      "normalize_punct_spacing": true,
      "disable_highlight_at_out": true,
      "default_style": "Normal"
    }

Settings ensure deterministic rebuild behavior when reloading projects.

------------------------------------------------------------------------

## 4.6 groups (required)

Type: array of Group objects

Represents logical subtitle groups.

------------------------------------------------------------------------

# 5. Group Object

Each group MUST contain:

    {
      "key": "...",
      "style": "...",
      "text": "...",
      "in": 0.0,
      "out": 0.0,
      "steps": [ ... ]
    }

## Fields

### key

Type: string or null

Normalized key used for text grouping and style propagation.

### style

Type: string

Current style identifier.\
Special value `"!"` MAY indicate protected state.

### text

Type: string

Final rendered subtitle text for this group.

### in

Type: number (float)

Start time in seconds.

### out

Type: number (float)

End time in seconds.

### steps

Type: array of Step objects

Represents highlight or timing sub-events.

------------------------------------------------------------------------

# 6. Step Object

    {
      "t": 0.0,
      "start": 0,
      "end": 0,
      "label": ""
    }

## Fields

### t

Type: number (float)

Time offset relative to group start.

### start

Type: integer

Character start index.

### end

Type: integer

Character end index.

### label

Type: string

Optional label for step classification.

------------------------------------------------------------------------

# 7. Validation Rules

1.  `format` MUST equal "lcap"
2.  `version` MUST be supported by the engine
3.  `groups` MUST be an array
4.  All timing values MUST be non-negative
5.  `in` MUST be less than or equal to `out`
6.  Steps MUST NOT exceed text length boundaries

------------------------------------------------------------------------

# 8. Forward Compatibility

Unknown fields MUST be ignored by compliant parsers.\
This allows safe extension of the format.

------------------------------------------------------------------------

# 9. Versioning Strategy

Minor internal changes without structural modifications DO NOT require
version increment.

Breaking structural changes MUST increment the `version` field.

Future migration utilities MAY convert older versions to newer versions.

------------------------------------------------------------------------

# 10. Example Complete File

    {
      "format": "lcap",
      "version": 1,
      "source": "example.srt",
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

------------------------------------------------------------------------

End of Specification.
