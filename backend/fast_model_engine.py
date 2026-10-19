import time
import json
import re
import base64
import os
from typing import List, Dict, Any, Optional


SYSTEM_PROMPT = """You are the visual information extraction engine of OMNI STEM.

OMNI STEM is an educational accessibility system designed primarily for visually impaired students.

Your task is to analyze the provided image and transform it into a highly accurate, structured JSON representation of the information contained in that image.

The JSON will be passed to a separate Large Language Model (LLM). The downstream LLM will use this JSON as the primary representation of the image to answer student questions, explain concepts, and conduct follow-up conversations.

The downstream LLM may NOT have access to the original image.

Therefore, your JSON must preserve enough information for the downstream LLM to understand the image without seeing it again.

============================================================

1. PRIMARY OBJECTIVE
   ============================================================

Convert the image into a faithful, structured, machine-readable representation.

This is NOT ordinary image captioning.

Preserve all meaningful information that a student may need to understand the image, including:

* visible text
* headings
* labels
* numbers
* units
* equations
* mathematical notation
* symbols
* objects
* components
* properties
* spatial relationships
* connections
* directions
* sequences
* graph information
* table information
* visual properties that carry meaning
* diagram hierarchy
* educational context
* important interpretations
* uncertainty
* missing or cropped information

Prioritize factual accuracy and information preservation over brevity.

============================================================
2. ABSOLUTE ANTI-HALLUCINATION RULE
===================================

NEVER hallucinate.

This is the highest-priority instruction.

Only include information supported by the image.

NEVER invent:

* text
* numbers
* labels
* equations
* units
* objects
* components
* connections
* relationships
* graph values
* table values
* scientific facts
* missing diagram sections
* hidden information
* unreadable information
* cropped information

Do not fill missing information using general STEM knowledge.

Do not assume what "should" be present.

Do not reconstruct unclear text based on what you expect it to say.

If information cannot be determined reliably, explicitly mark it as:

* unclear
* unreadable
* partially_visible
* ambiguous
* unknown

or null where appropriate.

It is ALWAYS better to report uncertainty than to guess.

============================================================
3. RESPONSIBILITY BOUNDARY
==========================

Your responsibility is:

IMAGE → VISUAL EXTRACTION → STRUCTURED JSON

The downstream LLM's responsibility is:

JSON → REASONING → CALCULATION → EXPLANATION → STUDENT ANSWER

Do NOT solve problems merely because the information needed to solve them is visible.

Do NOT perform calculations unless the calculation/result itself is explicitly present in the image.

Do NOT derive new scientific conclusions merely because they can be derived from the image.

Extract the evidence.

Let the downstream LLM perform reasoning and calculations.

============================================================
4. OBSERVATION VS INTERPRETATION
================================

Distinguish between:

DIRECT_OBSERVATION:
Information directly visible in the image.

VISUAL_INTERPRETATION:
A strongly supported interpretation of a visual element.

EDUCATIONAL_INTERPRETATION:
A likely scientific, mathematical, engineering, or technical meaning supported by the image.

Never present an interpretation as a direct observation.

Example:

Direct observation:
"The image contains a zigzag symbol labeled R1."

Visual interpretation:
"The zigzag symbol is consistent with a resistor."

Educational interpretation:
"R1 likely represents a resistor in the circuit."

If an interpretation is uncertain, explicitly state the uncertainty.

============================================================
5. IMAGE CLASSIFICATION
=======================

Identify all relevant image categories.

Possible categories include:

* equation
* mathematical_diagram
* graph
* chart
* table
* circuit_diagram
* engineering_diagram
* technical_drawing
* flowchart
* process_diagram
* architecture_diagram
* biology_diagram
* chemistry_diagram
* physics_diagram
* laboratory_setup
* scientific_illustration
* technical_photograph
* real_world_stem_object
* screenshot
* handwritten_notes
* textbook_content
* mixed_stem_content
* other_stem
* non_stem

Multiple categories may be assigned.

Also identify, when supported:

* STEM domain
* subdomain
* topic
* educational context
* likely purpose

Do not claim a specific educational level unless evidence exists in the image.

============================================================
6. READING ORDER
================

Preserve meaningful visual and logical reading order.

When the image contains:

* title
* introductory text
* diagram
* labels
* annotations
* explanation
* table
* caption
* footnotes

represent their logical/visual order.

Do not randomly reorder information.

Reading order should help the downstream LLM reconstruct how a human would naturally interpret the image.

============================================================
7. TEXT EXTRACTION
==================

Extract ALL meaningful visible text.

Include:

* titles
* headings
* labels
* annotations
* numbers
* units
* equations
* legends
* table text
* handwritten text
* symbols

Preserve visible wording as accurately as possible.

Do not silently correct spelling.

Do not silently correct mathematical notation.

If text is partially readable:

* preserve what is actually visible
* identify the unreadable portion
* mark it as uncertain

Do not guess the missing text.

============================================================
8. OBJECT EXTRACTION
====================

Identify meaningful objects, components, entities, regions, or structures.

For each object, extract when applicable:

* unique ID
* type
* label
* description
* properties
* values
* units
* position
* bounding box
* source/evidence
* uncertainty

Use unique IDs so relationships can reference objects unambiguously.

Never create an object simply because that object would normally exist in a particular type of diagram.
Junction nodes and shared rails/buses (see Section 12A for circuit diagrams) count as objects and must be extracted the same as physical components — do not omit them because they aren't a discrete part.

============================================================
9. RELATIONSHIPS AND CONNECTIONS
================================

Explicitly represent meaningful relationships.

Possible relationships include:

* connected_to
* electrically_connected_to
* mechanically_connected_to
* points_to
* leads_to
* contains
* part_of
* depends_on
* follows
* precedes
* intersects
* attached_to
* represents
* labels
* compares_with
* caused_by
* results_in

Relationships must reference object or text IDs whenever possible.

For directional relationships, preserve direction.

Example:

object_01 → connected_to → object_02

Do not infer relationships that are not visually supported.

============================================================
10. SPATIAL INFORMATION
=======================

Preserve meaningful spatial relationships.

Examples:

* above
* below
* left_of
* right_of
* inside
* outside
* adjacent_to
* centered_in
* surrounding
* aligned_with
* overlapping
* intersecting
* near

Example:

object_01 is left_of object_02.

Spatial information is especially important because OMNI STEM is intended for visually impaired students.

============================================================
11. EVIDENCE
============

Important extracted information should be traceable to visual evidence.

Evidence may reference:

* direct visual observation
* text region
* object
* relationship
* graph region
* table region
* diagram region

Whenever practical, connect an extracted fact to the relevant object ID, text ID, or image region.

Evidence must explain WHERE the information came from, not provide a new interpretation.

============================================================
12. BOUNDING BOXES
==================

Use bounding boxes when they help identify the location of:

* objects
* labels
* text
* graph elements
* important regions

Format:

{
"x_min": 0,
"y_min": 0,
"x_max": 0,
"y_max": 0
}

Coordinates refer to the original image.

If reliable coordinates cannot be determined, use null.

Never invent coordinates.

============================================================
12A. CIRCUIT NODE TRACING (circuit_diagram / schematic / engineering_diagram)
============================================================

Apply this section whenever image_type includes "circuit_diagram",
"schematic", or "engineering_diagram" with electrical wiring.

MANY circuits are NOT a single series loop. Wires frequently split
into three, four, or more branches at a shared rail or junction
point. Treat every such point as its own object — never approximate
it as a chain of two-way "connected_to" edges between the
components that happen to sit near it.

STEP 1 — IDENTIFY JUNCTION NODES BEFORE LISTING RELATIONSHIPS

Scan the full wiring first. A junction node exists wherever:
- three or more component leads meet at the same wire/rail, OR
- a dot is drawn at a wire intersection, OR
- a single continuous wire visibly runs past/through more than two
  component terminals (e.g. a shared top rail or ground bus)

For each junction node found, create an object:

{
  "id": "node_01",
  "type": "junction_node",
  "label": "Top rail (B+)"            // short human-readable name, or null
  "description": "Shared wire connecting R1(top), C2(top), T1(CT), C4(+), B1(+).",
  "properties": [],
  "values": [],
  "units": [],
  "bounding_box": null,
  "source": "direct_observation",
  "uncertainty": null
}

STEP 2 — CONNECT EVERY LEAD TO ITS ACTUAL NODE

In "relationships", NEVER connect two components directly (A → B)
unless a wire runs from A straight to B with no other component
lead touching that wire in between.

If three or more leads share a wire, connect EACH lead to the
junction node individually:

  { "source": "obj_R1",  "relationship": "connected_to", "target": "node_01" }
  { "source": "obj_C2",  "relationship": "connected_to", "target": "node_01" }
  { "source": "obj_T1",  "relationship": "connected_to", "target": "node_01" }
  { "source": "obj_C4",  "relationship": "connected_to", "target": "node_01" }
  { "source": "obj_B1",  "relationship": "connected_to", "target": "node_01" }

Do NOT also add direct edges between those components (e.g. do not
add "obj_B1 → obj_C4" as well — that wire does not exist; both
merely terminate at node_01).

STEP 3 — DO NOT SIMPLIFY TO A SERIES LOOP

Before finalizing, check: does your relationships list imply a
single unbroken loop touching every component exactly once? If a
circuit has more than one power-rail branch, more than one
transistor lead, or more than 5-6 components, a pure series loop
is almost always WRONG. Re-trace the wiring rather than defaulting
to the simplest topology.

STEP 4 — TWO-TERMINAL COMPONENTS STILL NEED BOTH ENDS TRACED

For every resistor, capacitor, LED, etc., explicitly trace BOTH
terminals to whatever they touch (a node, or a component lead)
independently. Do not assume a component's second terminal follows
the "next" component in reading order — trace it visually.

If a wire's destination is genuinely unclear (faint, occluded,
ambiguous crossing without a dot), do NOT guess a connection.
Add an entry to "uncertainties" instead, with target = the
component ID and issue describing which terminal is ambiguous.

============================================================
13. MATHEMATICAL CONTENT
========================

When mathematical information is present, preserve:

* equations
* formulas
* variables
* constants
* operators
* fractions
* roots
* powers
* subscripts
* superscripts
* integrals
* derivatives
* limits
* matrices
* vectors
* symbols
* numerical values
* units

Preserve the original mathematical structure.

When possible, provide LaTeX as an additional machine-readable representation.

Do NOT solve, simplify, or manipulate equations unless the result is explicitly present in the image.

============================================================
14. GRAPHS AND CHARTS
=====================

For graphs and charts extract:

* graph type
* title
* x-axis
* y-axis
* axis labels
* units
* scale
* tick marks
* data points
* curves
* lines
* bars
* legends
* categories
* labels
* intersections
* extrema
* visible trends

Do not fabricate exact numerical values.

If a value can only be approximately determined from the image, explicitly identify it as approximate.

============================================================
15. TABLES
==========

For tables preserve:

* title
* column headers
* row headers
* cell values
* units
* footnotes
* meaningful formatting

Preserve row-column relationships exactly.

Do not reorder table information unnecessarily.

============================================================
16. PROCESSES AND FLOWCHARTS
============================

Extract:

* steps
* nodes
* decisions
* conditions
* inputs
* outputs
* arrows
* direction
* sequence
* dependencies

Preserve the sequence represented in the image.

============================================================
17. VISUAL INFORMATION
======================

Record visual properties when they carry educational, scientific, technical, or structural meaning.

Examples:

* color
* shape
* size
* orientation
* line style
* arrow direction
* shading
* highlighting
* symbols
* patterns

Do not waste output describing purely decorative details.

============================================================
18. EDUCATIONAL INTERPRETATION
==============================

When strongly supported by the image, identify:

* represented concept
* scientific principle
* mathematical concept
* engineering concept
* technical purpose
* meaning of important symbols

Clearly label these as interpretations.

Never use interpretation to fill missing visual information.

============================================================
19. IMAGE QUALITY AND COMPLETENESS
==================================

Assess whether image quality affects extraction.

Identify:

* blur
* low resolution
* poor text readability
* occlusion
* cropping
* missing portions
* overlapping content
* difficult handwriting
* ambiguous symbols

If important information is affected, record the limitation explicitly.

============================================================
20. NON-STEM IMAGES
===================

If the image does not contain STEM content:

Classify it as non_stem.

Do not force it into a STEM category.

Provide a short factual description of what was detected.

============================================================
21. ACCESSIBILITY PRIORITY
==========================

Remember that the final student may not be able to see the image.

Therefore, information that a sighted student would normally obtain simply by looking at the image must be explicitly represented whenever relevant.

Pay particular attention to:

* spatial relationships
* arrows
* connections
* labels
* relative positions
* meaningful colors
* shapes
* orientation
* hierarchy
* sequence
* highlighting
* diagram structure
* graph trends
* table structure
* visual distinctions

Never assume that the downstream LLM can visually infer information that you did not encode.

============================================================
22. JSON QUALITY
================

The output must:

* be valid JSON
* follow the supplied JSON Schema exactly
* contain no Markdown
* contain no comments
* contain no text outside JSON
* use consistent IDs
* preserve relationships
* preserve meaningful spatial information
* preserve visible text
* preserve numerical information
* preserve units
* preserve mathematical notation
* preserve reading order
* explicitly represent uncertainty
* distinguish observation from interpretation
* include evidence where applicable
* avoid unnecessary duplication
* avoid unsupported assumptions
* never hallucinate

Prefer structured fields over long paragraphs.

============================================================
23. FINAL VERIFICATION
======================

Before producing the final JSON, internally verify:

1. Did I inspect the complete image?
2. Did I classify the image correctly?
3. Did I identify the relevant STEM domain?
4. Did I extract all meaningful visible text?
5. Did I preserve numbers and units?
6. Did I identify meaningful objects?
7. Did I assign unique IDs?
8. Did I capture important relationships?
9. Did I capture directional relationships?
10. Did I preserve meaningful spatial information?
11. Did I preserve mathematical notation?
12. Did I capture graph/table/process information?
13. Did I preserve meaningful visual properties?
14. Did I preserve reading order?
15. Did I identify image-quality limitations?
16. Did I identify cropping or missing information?
17. Did I separate observation from interpretation?
18. Did I explicitly record uncertainty?
19. Did I provide evidence for important extracted information?
20. Did I avoid unsupported assumptions?
21. Did I avoid hallucination?
22. Is the output valid according to the supplied JSON Schema?

If something is uncertain:

REPORT THE UNCERTAINTY.

DO NOT GUESS.

============================================================
FINAL OUTPUT
============

Return ONLY the JSON object defined by the supplied schema.
"""

# =====================================================================
# OMNI STEM JSON Schema
# =====================================================================

OMNI_STEM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,

    "required": [
        "schema_version",
        "image_metadata",
        "summary",
        "reading_order",
        "text_content",
        "objects",
        "relationships",
        "spatial_information",
        "mathematical_content",
        "graph_data",
        "table_data",
        "process_information",
        "visual_information",
        "educational_interpretation",
        "uncertainties"
    ],

    "properties": {

        "schema_version": {
            "type": "string"
        },

        "image_metadata": {
            "type": "object",
            "additionalProperties": False,

            "required": [
                "image_type",
                "stem_domain",
                "subdomain",
                "topic",
                "title",
                "caption",
                "educational_context",
                "image_quality",
                "image_completeness"
            ],

            "properties": {

                "image_type": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "stem_domain": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "subdomain": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "topic": {
                    "type": ["string", "null"]
                },

                "title": {
                    "type": ["string", "null"]
                },

                "caption": {
                    "type": ["string", "null"]
                },

                "educational_context": {
                    "type": ["string", "null"]
                },

                "image_quality": {
                    "type": "object",
                    "additionalProperties": False,

                    "required": [
                        "overall",
                        "text_readability",
                        "blur",
                        "occlusion",
                        "cropping"
                    ],

                    "properties": {

                        "overall": {
                            "type": "string"
                        },

                        "text_readability": {
                            "type": "string"
                        },

                        "blur": {
                            "type": "boolean"
                        },

                        "occlusion": {
                            "type": "boolean"
                        },

                        "cropping": {
                            "type": "boolean"
                        }
                    }
                },

                "image_completeness": {
                    "type": "object",
                    "additionalProperties": False,

                    "required": [
                        "status",
                        "missing_information"
                    ],

                    "properties": {

                        "status": {
                            "type": "string"
                        },

                        "missing_information": {
                            "type": ["string", "null"]
                        }
                    }
                }
            }
        },

        "summary": {
            "type": "object",
            "additionalProperties": False,

            "required": [
                "what_is_shown",
                "main_concept",
                "purpose"
            ],

            "properties": {

                "what_is_shown": {
                    "type": ["string", "null"]
                },

                "main_concept": {
                    "type": ["string", "null"]
                },

                "purpose": {
                    "type": ["string", "null"]
                }
            }
        },

        "reading_order": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "text_content": {
            "type": "array",

            "items": {
                "type": "object",
                "additionalProperties": False,

                "required": [
                    "id",
                    "content",
                    "type",
                    "reading_order_index",
                    "readability",
                    "source",
                    "bounding_box",
                    "uncertainty"
                ],

                "properties": {

                    "id": {
                        "type": "string"
                    },

                    "content": {
                        "type": "string"
                    },

                    "type": {
                        "type": "string"
                    },

                    "reading_order_index": {
                        "type": "integer"
                    },

                    "readability": {
                        "type": "string"
                    },

                    "source": {
                        "type": "string"
                    },

                    "bounding_box": {
                        "type": ["object", "null"],

                        "additionalProperties": False,

                        "required": [
                            "x_min",
                            "y_min",
                            "x_max",
                            "y_max"
                        ],

                        "properties": {

                            "x_min": {
                                "type": "number"
                            },

                            "y_min": {
                                "type": "number"
                            },

                            "x_max": {
                                "type": "number"
                            },

                            "y_max": {
                                "type": "number"
                            }
                        }
                    },

                    "uncertainty": {
                        "type": ["string", "null"]
                    }
                }
            }
        },

        "objects": {
            "type": "array",

            "items": {
                "type": "object",
                "additionalProperties": False,

                "required": [
                    "id",
                    "type",
                    "label",
                    "description",
                    "properties",
                    "values",
                    "units",
                    "bounding_box",
                    "source",
                    "uncertainty"
                ],

                "properties": {

                    "id": {
                        "type": "string"
                    },

                    "type": {
                        "type": "string"
                    },

                    "label": {
                        "type": ["string", "null"]
                    },

                    "description": {
                        "type": "string"
                    },

                    # ---- FIXED: closed key/value array instead of free-form object ----
                    "properties": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["key", "value"],
                            "properties": {
                                "key": {
                                    "type": "string"
                                },
                                "value": {
                                    "type": "string"
                                }
                            }
                        }
                    },
                    # ---------------------------------------------------------------------

                    "values": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },

                    "units": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },

                    "bounding_box": {
                        "type": ["object", "null"],

                        "additionalProperties": False,

                        "required": [
                            "x_min",
                            "y_min",
                            "x_max",
                            "y_max"
                        ],

                        "properties": {

                            "x_min": {
                                "type": "number"
                            },

                            "y_min": {
                                "type": "number"
                            },

                            "x_max": {
                                "type": "number"
                            },

                            "y_max": {
                                "type": "number"
                            }
                        }
                    },

                    "source": {
                        "type": "string"
                    },

                    "uncertainty": {
                        "type": ["string", "null"]
                    }
                }
            }
        },

        "relationships": {
            "type": "array",

            "items": {
                "type": "object",
                "additionalProperties": False,

                "required": [
                    "source",
                    "relationship",
                    "target",
                    "direction",
                    "evidence"
                ],

                "properties": {

                    "source": {
                        "type": "string"
                    },

                    "relationship": {
                        "type": "string"
                    },

                    "target": {
                        "type": "string"
                    },

                    "direction": {
                        "type": ["string", "null"]
                    },

                    "evidence": {
                        "type": "string"
                    }
                }
            }
        },

        "spatial_information": {
            "type": "array",

            "items": {
                "type": "object",
                "additionalProperties": False,

                "required": [
                    "subject",
                    "relation",
                    "reference",
                    "evidence"
                ],

                "properties": {

                    "subject": {
                        "type": "string"
                    },

                    "relation": {
                        "type": "string"
                    },

                    "reference": {
                        "type": "string"
                    },

                    "evidence": {
                        "type": "string"
                    }
                }
            }
        },

        "mathematical_content": {
            "type": "object",
            "additionalProperties": False,

            "required": [
                "present",
                "equations",
                "symbols",
                "variables",
                "units",
                "notes"
            ],

            "properties": {

                "present": {
                    "type": "boolean"
                },

                "equations": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "symbols": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "variables": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "units": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "notes": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        },

        "graph_data": {
            "type": "object",
            "additionalProperties": False,

            "required": [
                "present",
                "graph_type",
                "title",
                "x_axis",
                "y_axis",
                "series",
                "observations"
            ],

            "properties": {

                "present": {
                    "type": "boolean"
                },

                "graph_type": {
                    "type": ["string", "null"]
                },

                "title": {
                    "type": ["string", "null"]
                },

                "x_axis": {
                    "type": ["string", "null"]
                },

                "y_axis": {
                    "type": ["string", "null"]
                },

                "series": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "observations": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        },

        "table_data": {
            "type": "object",
            "additionalProperties": False,

            "required": [
                "present",
                "title",
                "headers",
                "rows",
                "notes"
            ],

            "properties": {

                "present": {
                    "type": "boolean"
                },

                "title": {
                    "type": ["string", "null"]
                },

                "headers": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "rows": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                },

                "notes": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        },

        "process_information": {
            "type": "object",
            "additionalProperties": False,

            "required": [
                "present",
                "steps",
                "sequence"
            ],

            "properties": {

                "present": {
                    "type": "boolean"
                },

                "steps": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "sequence": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        },

        "visual_information": {
            "type": "object",
            "additionalProperties": False,

            "required": [
                "meaningful_colors",
                "shapes",
                "orientation",
                "highlighting",
                "other_meaningful_visual_features"
            ],

            "properties": {

                "meaningful_colors": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "shapes": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "orientation": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "highlighting": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "other_meaningful_visual_features": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        },

        "educational_interpretation": {
            "type": "object",
            "additionalProperties": False,

            "required": [
                "present",
                "concepts",
                "interpretations"
            ],

            "properties": {

                "present": {
                    "type": "boolean"
                },

                "concepts": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "interpretations": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        },

        "uncertainties": {
            "type": "array",

            "items": {
                "type": "object",
                "additionalProperties": False,

                "required": [
                    "target",
                    "issue",
                    "reason",
                    "affected_information"
                ],

                "properties": {

                    "target": {
                        "type": "string"
                    },

                    "issue": {
                        "type": "string"
                    },

                    "reason": {
                        "type": "string"
                    },

                    "affected_information": {
                        "type": "string"
                    }
                }
            }
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Groq API config — key is read from environment variable GROQ_API_KEY
# ─────────────────────────────────────────────────────────────────────────────
GROQ_MODEL = "qwen/qwen3.8-27b"   # vision-capable model on Groq



# ─────────────────────────────────────────────────────────────────────────────
# JSON fallback parser (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def fallback_json_parser(raw_text: str) -> dict:
    """Attempts to extract and parse JSON from a raw model response."""
    # First, try to parse directly
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    # Second, try finding a JSON block (e.g., inside ```json ... ``` or just {...})
    start_idx = raw_text.find('{')
    end_idx = raw_text.rfind('}')

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(raw_text[start_idx:end_idx + 1])
        except json.JSONDecodeError:
            pass

    # Absolute fallback if all parsing fails
    print("⚠️ Failed to parse valid JSON from model response. Using fallback schema.")
    return {
        "diagram_type": "Parse Error",
        "components": [{"error": "Could not parse components"}],
        "relationships": [],
        "clarification_required": True,
        "candidate_entities": []
    }


# ─────────────────────────────────────────────────────────────────────────────
# NEW: GroqCloud vision inference (internal helper)
# ─────────────────────────────────────────────────────────────────────────────
def _call_groq_vision(image_path: str, user_query: str) -> dict:
    """
    Sends the image + query to the GroqCloud chat completions API (vision model)
    and returns a parsed dict matching the OMNI_STEM_SCHEMA structure.

    Raises:
        EnvironmentError  — GROQ_API_KEY is not set
        RuntimeError      — Groq API returned an error or timed out
        ValueError        — Response content could not be parsed as valid JSON
    """
    # 1. Key guard — fail fast with a clear message
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY environment variable is not set. "
            "Add it to your .env file or export it in your shell before starting the server."
        )

    # 2. Lazy import so startup isn't broken when groq isn't installed yet
    try:
        from groq import Groq, APIError, APITimeoutError, APIConnectionError
    except ImportError as exc:
        raise ImportError(
            "The 'groq' package is not installed. Run: pip install 'groq>=0.9.0'"
        ) from exc

    # 3. Encode image to base64 data URI
    with open(image_path, "rb") as img_file:
        image_b64 = base64.b64encode(img_file.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[-1].lower().lstrip(".")
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "gif": "image/gif", "webp": "image/webp"
    }
    mime_type = mime_map.get(ext, "image/png")

    # 4. Build messages payload
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}
                },
                {
                    "type": "text",
                    "text": user_query
                }
            ]
        }
    ]

    # 5. Call Groq with structured output (json_schema / response_format)
    client = Groq(api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "omni_stem_vision_analysis",
                    "strict": True,
                    "schema": OMNI_STEM_SCHEMA
                }
            },
            max_completion_tokens=8000,
            temperature=0,
            timeout=120,
        )
    except APITimeoutError as exc:
        raise RuntimeError(
            f"Groq API timed out after 120 s. The model may be overloaded — please retry. Details: {exc}"
        ) from exc
    except APIConnectionError as exc:
        raise RuntimeError(
            f"Could not connect to Groq API. Check your internet connection. Details: {exc}"
        ) from exc
    except APIError as exc:
        raise RuntimeError(
            f"Groq API returned an error (status {exc.status_code}): {exc.message}"
        ) from exc

    # 6. Extract and parse the response content
    raw_content = completion.choices[0].message.content
    if not raw_content:
        raise ValueError("Groq API returned an empty response content.")

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        # Groq structured-output should always be valid JSON, but fall back gracefully
        parsed = fallback_json_parser(raw_content)
        if parsed.get("diagram_type") == "Parse Error":
            raise ValueError(
                f"Could not parse JSON from Groq response. Raw content: {raw_content[:500]!r}"
            )

    return parsed


# ─────────────────────────────────────────────────────────────────────────────
# Public function — SIGNATURE IS IDENTICAL TO THE OLD COLAB VERSION
#
#   analyze_diagram_remote(image_path, user_query, colab_url)
#   → (dict, float)   ← same return shape as before
#
# The `colab_url` parameter is accepted but IGNORED. It is kept so that every
# call site in main.py and ingestion_engine.py continues to work without any
# modification.
# ─────────────────────────────────────────────────────────────────────────────
def analyze_diagram_remote(image_path: str, user_query: str, colab_url: str):
    """
    Analyse a diagram image and return structured JSON + latency.

    Parameters
    ----------
    image_path : str   — absolute or relative path to the image file
    user_query : str   — the user's question / extraction instruction
    colab_url  : str   — IGNORED (was the old Colab ngrok URL; kept so all
                         callers continue to work without modification)

    Returns
    -------
    (dict, float)  — (raw parsed JSON dict from Groq, latency in seconds)
    """
    start_time = time.time()
    print(f"🚀 Sending request to GroqCloud vision API (model: {GROQ_MODEL})...")

    result_dict = None
    for attempt in range(2):
        try:
            result_dict = _call_groq_vision(image_path, user_query)
            break  # success — raw dict straight from json.loads()

        except EnvironmentError:
            # Missing API key — no point retrying, re-raise immediately
            raise

        except (RuntimeError, ValueError) as e:
            err_str = str(e)
            print(f"⚠️ Attempt {attempt + 1} failed: {err_str}")

            # If it's a 429 rate-limit, sleep the suggested wait time before retrying
            if "429" in err_str and attempt == 0:
                wait_seconds = 65  # safe default — above the 60s token-bucket window
                match = re.search(r"try again in (\d+(?:\.\d+)?)s", err_str)
                if match:
                    wait_seconds = float(match.group(1)) + 2
                print(f"  ⏳ Rate limited — waiting {wait_seconds:.1f}s before retry...")
                time.sleep(wait_seconds)

            if attempt == 1:
                print("❌ Final attempt failed. Using safe fallback dict.")
                result_dict = {"error": err_str, "parse_error": True}

        except Exception as e:
            print(f"❌ Unexpected error calling Groq: {e}")
            result_dict = {"error": str(e), "parse_error": True}
            break

    latency = time.time() - start_time
    print(f"✨ Response received in {latency:.2f}s!")

    return result_dict, latency


# ─────────────────────────────────────────────────────────────────────────────
# OLD COLAB-BRIDGE CODE — commented out for easy comparison / revert tonight
# To revert: uncomment the block below and delete the Groq implementation above.
# ─────────────────────────────────────────────────────────────────────────────
# import requests  # (was imported at top level; now unused — re-add if reverting)
#
# def analyze_diagram_remote(image_path: str, user_query: str, colab_url: str):
#     start_time = time.time()
#     import os
#
#     print(f"🚀 Sending request to Remote Colab Server at {colab_url}...")
#
#     parsed_json = {}
#     for attempt in range(2):
#         try:
#             with open(image_path, "rb") as image_file:
#                 files = {"file": (os.path.basename(image_path), image_file, "image/png")}
#                 data = {"user_query": user_query}
#
#                 response = requests.post(
#                     f"{colab_url.rstrip('/')}/analyze", files=files, data=data, timeout=120
#                 )
#                 response.raise_for_status()
#
#             resp_json = response.json()
#
#             if resp_json.get("status") == "success":
#                 parsed_json = resp_json.get("data", {})
#             else:
#                 raw_output = resp_json.get("raw", "{}")
#                 print(f"⚠️ Colab parsing error: {resp_json.get('message')}. Attempting local fallback parse...")
#                 parsed_json = fallback_json_parser(raw_output)
#
#             validated_data = VisionAnalysis(**parsed_json)
#             break  # Success!
#
#         except (requests.exceptions.RequestException, json.JSONDecodeError, ValidationError) as e:
#             print(f"⚠️ Attempt {attempt + 1} failed: {e}")
#             if attempt == 1:
#                 print(f"❌ Final attempt failed. Using safe fallback schema.")
#                 validated_data = VisionAnalysis(
#                     diagram_type="Parse Error",
#                     clarification_required=True
#                 )
#         except Exception as e:
#             print(f"❌ Unexpected error communicating with Colab: {e}")
#             validated_data = VisionAnalysis(
#                 diagram_type="Parse Error",
#                 clarification_required=True
#             )
#             break
#
#     latency = time.time() - start_time
#     print(f"✨ Response Received in {latency:.2f}s!")
#
#     return validated_data.model_dump(), latency


# ─────────────────────────────────────────────────────────────────────────────
# Local Test Execution
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Replace with a test image and query.
    # colab_url is passed but ignored — kept for interface compatibility.
    try:
        res, lat = analyze_diagram_remote(
            "processed_images/page_1_300dpi.png",
            "What is shown in this diagram?",
            "http://localhost:8000"   # ignored — kept for compat
        )
        print(f"Test Result:\n{json.dumps(res, indent=2)}")
    except Exception as e:
        print(f"Test failed: {e}")