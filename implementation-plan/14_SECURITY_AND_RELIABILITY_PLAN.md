# 14. SECURITY, RELIABILITY & HARDENING SPECIFICATION

> **Document ID:** `OPENGEN-SEC-014`  
> **Author:** Principal Software Architect, Senior Full-Stack Engineer, AI Infrastructure Engineer  
> **Project:** OpenGen Framework  
> **Date:** November 2026  
> **Standard:** OWASP Top 10 API Security / Zero-Trust Local Boundary  

---

## 1. Executive Summary

Because OpenGen parses user-uploaded binary files (DOCX, PDF, images) and interacts with multiple external AI APIs, it presents several attack vectors:
1. **Malicious File Uploads:** Zip bombs, XML Entity Expansion (Billion Laughs), recursive PDF page trees, and embedded script payloads.
2. **Filesystem Exploits:** Path traversal attacks (`../../etc/passwd` or `..\Windows\System32`) attempting to read or overwrite host system files.
3. **SSRF & Network Ingress:** Image fetch requests targeting local loopback (`127.0.0.1`) or AWS/GCP cloud metadata endpoints (`169.254.169.254`).
4. **Credential Exposure:** Accidental leaking of user provider API keys into application logs, error traces, or disk caches.

This specification details the cryptographic, filesystem, and runtime hardening measures implemented across OpenGen.

---

## 2. Security Threat Model & Defense Matrix

| Attack Vector | Vulnerability Type | Severity | OpenGen Defense Mechanism | Enforcing Module |
|---|---|---|---|---|
| **Path Traversal (`../`)** | Arbitrary File Read/Write | **P0 (Critical)** | `pathlib.Path.resolve().is_relative_to(ALLOWED_WORKSPACE)` assertion. | `opengen.security.path_guard` |
| **API Key Log Leak** | Information Disclosure | **P0 (Critical)** | `pydantic.SecretStr` + `LogSanitizer` regex filter scrubbing all log sinks. | `opengen.security.sanitizer` |
| **XML Entity Expansion** | Denial of Service (Billion Laughs) | **P0 (Critical)** | `defusedxml.minidom` / `defusedxml.lxml` on all DOCX and PPTX XML streams. | `opengen.security.xml_guard` |
| **Zip Decompression Bomb** | Host Memory/Disk Exhaustion | **P0 (Critical)** | Max uncompressed size: 100 MB; Max expansion ratio: 10:1. | `opengen.security.zip_guard` |
| **PDF Page Tree Bomb** | CPU Freeze / DoS | **P1 (High)** | Max 500 page cap; tree recursion depth limit = 20. | `opengen.security.pdf_guard` |
| **SSRF (Image Fetch)** | Internal Network Pivot | **P1 (High)** | Disallow loopback, RFC1918 private subnets, and cloud metadata (`169.254.169.254`). | `opengen.security.network_guard` |
| **Worker Zombie Processes** | Process Leakage / OOM | **P1 (High)** | Headless processes (LibreOffice) enforce strict 60s subprocess timeouts. | `opengen.engines.document.validation` |
| **API Denial of Service** | Resource Exhaustion | **P2 (Medium)** | Token-bucket rate limiting via `slowapi` (60 req/min docs; 10 req/min images). | `opengen.api.middleware` |

---

## 3. Detailed Security Subsystem Implementation

### 3.1 Path Traversal Guard (`src/opengen/security/path_guard.py`)
Every input template path, reference path, or output destination MUST pass through the `PathGuard`:

```python
from pathlib import Path
from opengen.domain.errors import SecurityViolationError
from opengen.config import settings

class PathGuard:
    @staticmethod
    def assert_safe_path(user_supplied_path: str, allow_absolute: bool = False) -> Path:
        resolved = Path(user_supplied_path).resolve()
        allowed_root = settings.BASE_DIR.resolve()

        # Block traversal outside the allowed workspace root
        if not resolved.is_relative_to(allowed_root):
            raise SecurityViolationError(
                f"Path traversal detected: '{user_supplied_path}' resolves outside allowed workspace root."
            )

        # Disallow symlinks pointing outside the root
        if resolved.is_symlink():
            target = resolved.readlink().resolve()
            if not target.is_relative_to(allowed_root):
                raise SecurityViolationError("Symlink escape attempt blocked.")

        return resolved
```

---

### 3.2 Secret Sanitization in Logs (`src/opengen/security/sanitizer.py`)
API keys must never appear in log files, console output, or telemetry streams.

```python
import re
import logging

SECRET_PATTERNS = [
    re.compile(r'sk-[a-zA-Z0-9_-]{20,}', re.IGNORECASE),          # OpenAI / Together
    re.compile(r'AIza[a-zA-Z0-9_-]{35}', re.IGNORECASE),          # Google Gemini
    re.compile(r'sk-ant-[a-zA-Z0-9_-]{20,}', re.IGNORECASE),      # Anthropic
    re.compile(r'Bearer\s+[a-zA-Z0-9_.-]{20,}', re.IGNORECASE),   # Generic Bearer Tokens
]

class LogSanitizerFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern in SECRET_PATTERNS:
                record.msg = pattern.sub("[REDACTED_API_KEY]", record.msg)
        return True
```

---

### 3.3 Decompression Bomb & Defused XML Guard (`src/opengen/security/xml_guard.py`)
Office OpenXML files (`.docx`, `.pptx`) are zipped collections of XML files. Attackers can embed a tiny 10 KB zip file that expands to 50 GB of XML, or inject recursive XML entities:

```python
import zipfile
import defusedxml.minidom
from opengen.domain.errors import SecurityViolationError

MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_EXPANSION_RATIO = 10.0                   # 10:1

class SafePackageExtractor:
    @staticmethod
    def verify_and_read_xml(zip_path: str, internal_xml_filename: str) -> str:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            info = zf.getinfo(internal_xml_filename)
            
            # Check decompression ratio
            if info.compress_size > 0:
                ratio = info.file_size / float(info.compress_size)
                if ratio > MAX_EXPANSION_RATIO:
                    raise SecurityViolationError(f"Decompression bomb ratio ({ratio:.1f}:1) exceeds limit.")

            if info.file_size > MAX_UNCOMPRESSED_BYTES:
                raise SecurityViolationError("Uncompressed XML exceeds 100MB limit.")

            raw_bytes = zf.read(internal_xml_filename)
            
            # Parse with defusedxml to neutralize entity expansion
            dom = defusedxml.minidom.parseString(raw_bytes)
            return dom.toxml()
```

---

### 3.4 SSRF Network Guard (`src/opengen/security/network_guard.py`)
When Engine C or Engine A downloads external reference images or SVGs via URL:

```python
import ipaddress
import socket
from urllib.parse import urlparse
from opengen.domain.errors import SecurityViolationError

FORBIDDEN_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),        # RFC1918 Private
    ipaddress.ip_network("172.16.0.0/12"),     # RFC1918 Private
    ipaddress.ip_network("192.168.0.0/16"),    # RFC1918 Private
    ipaddress.ip_network("169.254.169.254/32") # Cloud Metadata
]

def assert_safe_remote_url(url: str):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SecurityViolationError(f"Disallowed scheme: '{parsed.scheme}'")

    hostname = parsed.hostname
    ip_str = socket.gethostbyname(hostname)
    ip_addr = ipaddress.ip_address(ip_str)

    for net in FORBIDDEN_NETWORKS:
        if ip_addr in net:
            raise SecurityViolationError(f"SSRF blocked: Host resolves to protected network ({ip_addr})")
```

---

## 4. Reliability, Fault Recovery & Rate Limiting

1. **Exponential Backoff on Provider Calls:**
   - LiteLLM calls automatically retry 3 times with exponential backoff on HTTP 429 (Rate Limit) and 503 (Overloaded) errors.
   - If the retry budget is exhausted, the call automatically cascades to the configured fallback model (e.g., Gemini -> GPT-4o-mini -> Ollama).
2. **Subprocess Timeout Guard:**
   - Headless LibreOffice and external conversion subprocesses enforce an absolute `timeout=60` seconds. If exceeded, the process tree is cleanly terminated via `taskkill /F /T` (Windows) or `SIGKILL` (Linux).
3. **Ephemeral Scratch Sandboxes:**
   - All intermediate document modifications and temporary page images are created within `tempfile.TemporaryDirectory()`. The directory is purged inside an unconditional `finally:` block, preventing disk bloat.

---
*End of Report 14.*
