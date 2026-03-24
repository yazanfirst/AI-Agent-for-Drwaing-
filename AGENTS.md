# Restaurant Fitout AI Agent

## Goal
Build a pattern-learning restaurant fitout system that:
- learns from old approved DXF drawings
- extracts reusable layout patterns
- generates new layouts based on site input and LOD
- uses real AutoCAD blocks (no fake geometry)

---

## Core Principles

### 1. No Guessing
- Do NOT guess equipment sizes
- Do NOT guess block geometry
- Do NOT invent layout decisions

### 2. No Vague Output
Invalid:
- "back of kitchen"
- "near counter"

Valid:
- explicit coordinates (x, y)
- rotation
- CAD block name

---

## Data Sources

- `data/references/`
  → Old approved DXF drawings (ground truth)

- `data/equipment/equipment_library_complete.json`
  → semantic equipment definitions (sizes, categories)

- `data/equipment/block_catalog_from_drawings.json`
  → real block names extracted from DXF INSERTs

- `data/rules/`
  → brand rules and LOD definitions

---

## System Architecture

### Step 1 — Extraction
Extract structured data from DXF:
- blocks (INSERT)
- geometry
- text
- extents
- block definitions

### Step 2 — Reference Cases
Convert each drawing into:
- site type
- equipment usage
- block usage
- spatial relationships

Store in:
- `data/extracted_cases/`

---

### Step 3 — Pattern Learning
Learn patterns from references:
- zone ratios
- equipment sequences
- adjacency rules
- block clusters

Store in:
- `data/patterns/`

---

### Step 4 — Generation
For a new site:
- classify site
- match closest pattern
- adapt pattern to new geometry
- place real CAD blocks

---

### Step 5 — LOD Rendering

LOD 100:
- zoning only

LOD 200:
- zones + key equipment + basic seating

LOD 300:
- full fitout with:
  - CAD block placement
  - doors
  - seating
  - detailed layout

---

## Engineering Rules

- Use Python
- Use ezdxf for DXF
- Use shapely for geometry
- Use pydantic for schemas
- Use pytest for testing

---

## Critical Constraints

- Do NOT use rectangles as final output (only for temporary debug if needed)
- Do NOT output equipment without CAD block mapping
- If CAD block is missing → mark unresolved
- If geometry cannot be verified → do not fake it

---

## Output Requirements

Every layout must include:
- coordinates
- rotation
- CAD block name
- zone assignment

---

## Development Order

1. schemas.py
2. site_reader.py
3. block_definition_extractor.py
4. reference_extractor.py
5. pattern_miner.py
6. template_matcher.py
7. layout_adapter.py
8. lod_renderer.py
9. validator.py
10. exporter.py

---

## Final Rule

This is NOT a text generator.
This is an engineering system.

If data is missing → expose it  
Do NOT hide it with guesses
