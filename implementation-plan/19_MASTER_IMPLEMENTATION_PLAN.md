# 19. MASTER IMPLEMENTATION PLAN & SYSTEM BLUEPRINT

> **Document ID:** `OPENGEN-MASTER-019`  
> **Author:** Principal Software Architect, Senior Full-Stack Engineer, AI Infrastructure Engineer  
> **Project:** OpenGen Framework Transformation  
> **Date:** November 2026  
> **Target Release:** OpenGen v1.0.0  
> **Directory Scope:** `implementation-plan/` (Connecting Reports 01 through 18)  

---

## 1. Executive Master Blueprint

This Master Implementation Plan serves as the definitive engineering contract for transforming the existing repository at `f:\document generator\opengen` into the full, open-source, multi-engine **OpenGen Framework**.

### The OpenGen Target State:
OpenGen is an open-source, self-hostable, provider-independent generation framework providing:
- **Engine A (Document Generation):** Word template preservation, Jinja2 dynamic table loops, PDF layout reconstruction, local fact harvesting, anti-hallucination validation, and 3-loop visual layout healing.
- **Engine B (Presentation Generation):** Outline planning, 16:9 coordinate geometry layout solving, native shapes, native Microsoft Excel-backed charts, and slide-level regeneration. (100% editable `.pptx`).
- **Engine C (Image Generation):** Studio-grade rasters via FLUX.1 [schnell] (Apache 2.0) and DALL-E 3, native scalable vector SVGs via Recraft AI, and prompt-hash persistent caching.
- **Engine D (Pure Realistic Handwriting):** Anti-detection handwriting synthesis with 5-8 non-repeating glyph alternates per character, Brownian baseline drift, ballpoint/gel pen physics, and Direct-to-Notebook transparent PDF printing for real physical lined paper.
- **4 Standard Ingress Interfaces:** Python SDK (`opengen.Client`), FastAPI REST API (`/api/v1`), FastMCP Server (Claude / Antigravity tools), and Typer CLI (`opengen`).
- **Underlying Pillars:** Multi-provider gateway (`LiteLLM`), zero-daemon task queue (`SqliteHuey`), 3-tier persistent cache (`diskcache`), and zero-token deterministic engineering.

---

## 2. Synthesis of Reports & Cross-Reference Map

Every subsystem, task, and architectural decision is documented in the dedicated implementation reports:

| Report Number & Title | Primary Purpose & Contents |
|---|---|
| **[01. Codebase Audit](file:///f:/document%20generator/opengen/implementation-plan/01_CODEBASE_AUDIT.md)** | Full module inventory, LOC count, technical debt diagnosis, and test isolation failure analysis. |
| **[02. Research-to-Codebase Mapping](file:///f:/document%20generator/opengen/implementation-plan/02_RESEARCH_TO_CODEBASE_MAPPING.md)** | Alignment of 11 research reports with existing code; critical evaluations (PyMuPDF vs Docling, WeasyPrint vs LibreOffice). |
| **[03. Current vs Target Feature Matrix](file:///f:/document%20generator/opengen/implementation-plan/03_CURRENT_VS_TARGET_FEATURE_MATRIX.md)** | Forensic feature-by-feature status matrix with concrete source-file evidence. |
| **[04. Architecture Gap Analysis](file:///f:/document%20generator/opengen/implementation-plan/04_ARCHITECTURE_GAP_ANALYSIS.md)** | 12 architectural dimensions audited; Clean Architecture / Ports & Adapters gap assessment. |
| **[05. Final System Architecture](file:///f:/document%20generator/opengen/implementation-plan/05_FINAL_SYSTEM_ARCHITECTURE.md)** | Definitive component specifications, Mermaid diagrams, data flows, and domain model architecture. |
| **[06. Repository Migration Plan](file:///f:/document%20generator/opengen/implementation-plan/06_REPOSITORY_MIGRATION_PLAN.md)** | Step-by-step restructuring blueprint moving `app/` to `src/opengen/` (`src` layout) without regressions. |
| **[07. Document Engine Plan (Engine A)](file:///f:/document%20generator/opengen/implementation-plan/07_DOCUMENT_ENGINE_IMPLEMENTATION_PLAN.md)** | Template preservation, Jinja2 table looping (`docxtpl`), table building (`cantSplit`), visual auto-correction. |
| **[08. Presentation Engine Plan (Engine B)](file:///f:/document%20generator/opengen/implementation-plan/08_PRESENTATION_ENGINE_IMPLEMENTATION_PLAN.md)** | Slide planning, coordinate geometry solver, native PPTX shapes, native Excel charts, slide regeneration. |
| **[09. Image Engine Plan (Engine C)](file:///f:/document%20generator/opengen/implementation-plan/09_IMAGE_ENGINE_IMPLEMENTATION_PLAN.md)** | FLUX.1 [schnell], Recraft SVG vectors, DALL-E 3, Pillow compositor, and prompt-hash caching. |
| **[10. Provider Manager Plan](file:///f:/document%20generator/opengen/implementation-plan/10_PROVIDER_MANAGER_IMPLEMENTATION_PLAN.md)** | Multi-provider abstraction (`LiteLLM`), BYOK management, task routing, and exact USD cost accounting. |
| **[11. Orchestration & Token Optimization](file:///f:/document%20generator/opengen/implementation-plan/11_ORCHESTRATION_AND_TOKEN_OPTIMIZATION.md)** | Asynchronous queue (`SqliteHuey`), 3-tier caching (`diskcache`), and 0-token optimization hierarchy. |
| **[12. MCP, REST, SDK & CLI Plan](file:///f:/document%20generator/opengen/implementation-plan/12_MCP_REST_SDK_CLI_PLAN.md)** | 10 MCP tools, `/api/v1` versioned endpoints, `OpenGenClient` SDK, and Typer CLI. |
| **[13. Dependency & License Audit](file:///f:/document%20generator/opengen/implementation-plan/13_DEPENDENCY_AND_LICENSE_AUDIT.md)** | License compatibility (Apache 2.0, MIT, LGPL isolation, AGPL containment) and `pyproject.toml` specification. |
| **[14. Security & Reliability Plan](file:///f:/document%20generator/opengen/implementation-plan/14_SECURITY_AND_RELIABILITY_PLAN.md)** | PathGuard, Billion Laughs (`defusedxml`), zip bomb limits, log sanitization, and SSRF guards. |
| **[15. Testing & Benchmarking Plan](file:///f:/document%20generator/opengen/implementation-plan/15_TESTING_AND_BENCHMARKING_PLAN.md)** | Test isolation (`conftest.py`), unit/integration/E2E suites, latency/memory benchmarks, and CI matrix. |
| **[16. Detailed Engineering Tasks](file:///f:/document%20generator/opengen/implementation-plan/16_DETAILED_ENGINEERING_TASKS.md)** | 28 granular, independently testable engineering tasks with strict acceptance criteria. |
| **[17. Implementation Roadmap](file:///f:/document%20generator/opengen/implementation-plan/17_IMPLEMENTATION_ROADMAP.md)** | 11-phase development roadmap (Phase 0 through Phase 10) with milestones and deliverables. |
| **[18. Risks & Technical Debt Analysis](file:///f:/document%20generator/opengen/implementation-plan/18_RISKS_AND_TECHNICAL_DEBT.md)** | Prioritized technical, security, and operational failure modes with concrete mitigations. |

---

## 3. Master Execution Sequence: 28 Tasks across 11 Phases

The exact engineering execution order is strictly mandated as follows:

```
+---------------------------------------------------------------------------------------------------+
| PHASE 0: AUDIT & PLANNING (COMPLETE)                                                             |
| * Deliverable: 19 Reports in implementation-plan/                                                |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| PHASE 1: CORE FRAMEWORK & SHARED INFRASTRUCTURE                                                   |
| * TASK-001: Build System & Repo Skeleton (pyproject.toml, src/opengen/)                          |
| * TASK-002: Domain Entities & Error Hierarchy (src/opengen/domain/)                               |
| * TASK-003: Test Isolation Harness (tests/conftest.py - fixes legacy test failures)               |
| * TASK-004: Security Guard (PathGuard, DefusedXML, LogSanitizer)                                 |
| * TASK-005: 3-Tier Persistent Cache Engine (diskcache.FanoutCache)                                |
| * TASK-006: Zero-Daemon Async Task Queue (SqliteHuey / RedisHuey)                                 |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| PHASE 2: PROVIDER MANAGER (LiteLLM BRIDGE)                                                        |
| * TASK-007: ProviderManager (Google Gemini, OpenAI, Claude, Together AI, Ollama)                 |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| PHASE 3: DOCUMENT GENERATION ENGINE (ENGINE A)                                                    |
| * TASK-008: Port Document Template Profilers (DOCX & PDF)                                         |
| * TASK-009: Port Reference Intelligence & RapidOCR Extractor                                      |
| * TASK-010: Port Semantic Mapping & Anti-Hallucination Validator                                  |
| * TASK-011: Port DocxPopulator & Advanced TableBuilder (cantSplit / tblHeader)                   |
| * TASK-012: Integrate Jinja2 Dynamic Row Expansion (DocxTplEngine)                                |
| * TASK-013: Port Visual Validation & 3-Loop Auto-Correction                                       |
| * TASK-014: Document Section & Partial Regeneration                                               |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| PHASE 4: PRESENTATION GENERATION ENGINE (ENGINE B)                                                |
| * TASK-015: Storytelling & Outline Planner (PresentationDeckSpec JSON)                           |
| * TASK-016: Coordinate Geometry Layout Solver (16:9 Cards & Font-Scaling Guard)                   |
| * TASK-017: Native PPTX Builder (python-pptx - 100% Editable Shapes)                              |
| * TASK-018: Native Excel-Backed Chart Builder (Bar, Column, Line, Pie)                            |
| * TASK-019: Single Slide Regeneration                                                             |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| PHASE 5: IMAGE GENERATION (ENGINE C) & HANDWRITING SYNTHESIS (ENGINE D)                           |
| * TASK-020: Image Provider Adapters (Together FLUX.1 Schnell & OpenAI DALL-E 3)                   |
| * TASK-021: Recraft Native Vector (SVG) Adapter                                                   |
| * TASK-022: Pillow Compositor & Prompt-Hash Persistent Cache                                      |
| * TASK-023: Handwriting Glyph Bank & Brownian Drift Simulator (Engine D)                          |
| * TASK-024: Direct-to-Notebook Paper Transparent Printing Engine (College & Wide Ruled)           |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| PHASE 6: MODEL CONTEXT PROTOCOL (MCP) SERVER                                                      |
| * TASK-025: FastMCP Server Implementation (10 Agentic Tools for Claude Code / Antigravity)        |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| PHASE 7: REST API, PYTHON SDK & TYPER CLI                                                         |
| * TASK-026: FastAPI v1 REST API Endpoints & Lifespan Setup (/api/v1/)                             |
| * TASK-027: Python SDK Client (opengen.Client)                                                    |
| * TASK-028: Typer Command-Line Interface (opengen CLI)                                            |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| PHASES 8 - 10: OPTIMIZATION, HARDENING & RELEASE                                                  |
| * Phase 8: Token Optimization & Automated Benchmarks (< 350 MB RAM, > 80% Token Savings)          |
| * Phase 9: Security Penetration Testing & Defused XML Audit                                       |
| * Phase 10: Open-Source Release, Docker Compose & Final Documentation                             |
+---------------------------------------------------------------------------------------------------+
```

---

## 4. Final Review & Verification Checklist

Before code implementation commences, the following 13 verification criteria have been confirmed:

1. [x] **All Research Reports Considered:** All 11 research reports in `OPENGEN_COMPREHENSIVE_RESEARCH_REPORT.md` (Product analysis, GitHub repositories, AI provider comparison, System architecture, Workflow design, Token optimization, Security, Milestones, and Engine D handwriting synthesis) were audited and mapped.
2. [x] **Entire Existing Codebase Inspected:** All directories (`app/`, `tests/`, `.ai-document-memory/`), modules, and configuration files were forensically inspected.
3. [x] **Existing Implementations Identified:** Working template preservation, table building, PDF reconstruction, reference extraction, semantic mapping, and visual validation were identified and cataloged.
4. [x] **Existing Reusable Code Preserved:** Over 1,845 lines of high-quality, tested OOXML and visual inspection code will be ported directly without rewriting.
5. [x] **Missing Functionality Identified:** Greenfield requirements for Engine B (Presentations), Engine C (Images), Engine D (Handwriting), FastMCP server, Python SDK, and CLI were planned in detail.
6. [x] **Proposed Architecture Internally Consistent:** All 4 ingress interfaces access the exact same underlying generation engines and domain services via Ports and Adapters.
7. [x] **Dependencies Justified:** Every library is categorized (A, B, C, D, E) with license compatibility and size impact documented.
8. [x] **Licensing Hardened:** Zero viral copyleft (GPL/AGPL) in core; LGPL dynamically isolated; Apache 2.0 framework target verified.
9. [x] **Every Major Feature Has Implementation Tasks:** 28 granular, independently testable tasks cover the entire framework.
10. [x] **Tasks Have Dependencies and Acceptance Criteria:** Clear dependency graph, unit test requirements, and definitions of done established for every task.
11. [x] **Testing Included:** Test isolation harness (`conftest.py`) designed to fix the 2 legacy state contamination failures; benchmarking suite included.
12. [x] **Implementation Order Practical:** Sequential phase hierarchy prevents broken intermediate states.
13. [x] **No Source Code Modified:** The repository source code remains 100% untouched during this analysis and planning turn.

---

## 5. Conclusion & Ready-for-Implementation State

The analysis and planning phase is **100% complete**.

All 19 architectural and implementation reports have been generated and saved into the dedicated `implementation-plan/` directory.

The development team now possesses an exhaustive, production-grade implementation blueprint specifically tailored to the actual OpenGen codebase.

**Awaiting user approval to proceed with Phase 1 execution.**

---
*End of Master Implementation Plan.*
