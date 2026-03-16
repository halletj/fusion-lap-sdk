# LAPIS Research: Lightweight API Specification for Intelligent Systems

> **Note:** The format is officially called **LAPIS** (Lightweight API Specification
> for Intelligent Systems). It is commonly referred to as a "LAP" or compressed API
> representation for LLMs.

## Overview

LAPIS is a domain-specific API description format designed as a **token-efficient
conversion target from OpenAPI**, optimized for LLM consumption rather than
documentation or code generation. It achieves an **average 85.5% token reduction**
compared to OpenAPI YAML while preserving all semantic information LLMs need for API
reasoning.

- **Author:** Daniel Garcia Garcia (cr0hn), Independent Researcher, Spain
- **Published:** February 2026
- **Paper:** [arxiv.org/abs/2602.18541](https://arxiv.org/abs/2602.18541)
- **Repository:** [github.com/cr0hn/LAPIS](https://github.com/cr0hn/LAPIS)
- **License:** CC BY 4.0
- **Status:** v0.1.0 (draft, stable for experimentation, subject to breaking changes before v1.0)

## The Problem

OpenAPI was designed in 2010-2015 for documentation tools, SDK generators, and testing
platforms -- not for LLM consumption. When fed into LLM context windows, OpenAPI specs
exhibit measurable inefficiencies:

| Problem | Example |
|---|---|
| **Structural overhead** | JSON Schema's nested `type`/`properties`/`required` architecture wastes tokens |
| **Error duplication** | GitHub's 404 error appears **531 times** across 1,080 endpoints with identical schemas |
| **Irrelevant metadata** | Contact info, licenses, extensions add no value for LLM reasoning |
| **Missing operational context** | Rate limits, webhook triggers, operation sequencing lack structural representation |

## Design Principles

1. **Token minimality** -- Target 70-80% fewer tokens than equivalent OpenAPI YAML
2. **LLM-native syntax** -- Function signatures and indentation resembling human whiteboard descriptions
3. **Lossless OpenAPI conversion** -- Fully automatable transformation with deterministic rules
4. **Human readability** -- Self-describing format requiring no additional documentation
5. **Semantic completeness** -- Preserves all information LLMs need for API reasoning

## Document Structure

LAPIS documents contain up to seven sections in fixed order:

| Section | Required | Purpose |
|---|---|---|
| `[meta]` | Yes | API name, base URL, version, authentication |
| `[types]` | No | Reusable type definitions |
| `[ops]` | Yes | API endpoints |
| `[webhooks]` | No | Push events with trigger conditions |
| `[errors]` | No | Centralized error definitions |
| `[limits]` | No | Rate limits and quotas |
| `[flows]` | No | Multi-step operation sequences |

File conventions: `.lapis` extension, UTF-8 encoding, suggested MIME type `text/lapis`.

## Syntax Examples

### Meta

```
[meta]
api: Invoice Service
base: https://api.example.com/v2
version: 2.1.0
auth: bearer header:Authorization
```

### Types

Flat, single-line definitions with eight scalar types: `str`, `int`, `float`, `bool`,
`date`, `datetime`, `file`, `any`.

```
Invoice:
  id: str
  customer_id: str
  status: InvoiceStatus
  lines: [InvoiceLine]
  total: float

InvoiceStatus: draft | sent | paid | overdue
```

Modifiers: arrays `[T]`, maps `{str:T}`, optional `T?`, defaults `T = value`,
annotations `@since:X.Y`, `@deprecated`.

### Operations

Signature syntax with directional markers (`>` for inputs, `<` for outputs):

```
create_invoice POST /invoices
  Creates an invoice for a customer.
  > customer_id: str
  > lines: [InvoiceLine]
  > billing_address?: Address
  < Invoice
```

Operation modifiers: `+paginated`, `+idempotent`, `+stream`.

### Webhooks

Arrow syntax with trigger conditions marked by `!`:

```
invoice_paid -> POST /webhooks/invoice-paid
  ! When invoice.status changes to "paid".
  < event_id: str @header:X-Event-ID
  < invoice_id: str
```

### Centralized Errors

Errors defined once globally or scoped to specific operations:

```
[errors]
401 unauthorized
  Token is missing, expired, or invalid.
404 not_found
  Resource not found.
409 duplicate_customer @ops:create_customer
  A customer with this email already exists.
  ~ existing_customer_id: str
```

### Rate Limits

Structured representation enabling LLM reasoning about throttling:

```
[limits]
on_exceed: 429 retry_after
plan: free
  rate: 60/m @key
  quota: 1000/mo @key "monthly requests"
```

### Operation Flows

Declares multi-step sequences with sequencing (`->`), repetition (`*`), and branching
(`|`):

```
invoice_lifecycle "Invoice lifecycle"
  create_invoice -> update_invoice* -> send_invoice
  -> ...(awaiting payment) -> invoice_paid | invoice_overdue
```

## Benchmarks

### Token Reduction vs OpenAPI YAML

Tested against five production APIs:

| API | Endpoints | OpenAPI YAML Tokens | LAPIS Tokens | Reduction |
|---|---|---|---|---|
| GitHub | 1,080 | 1,811,843 | 313,101 | **82.7%** |
| DigitalOcean | 545 | 586,731 | 54,201 | **90.8%** |
| Twilio | 197 | 306,453 | 24,197 | **92.1%** |
| HTTPBin | 73 | 6,007 | 1,689 | **71.9%** |
| Petstore | 19 | 4,634 | 800 | **82.7%** |

**Average: 85.5% reduction.** Results consistent across cl100k_base and o200k_base tokenizers.

### Cross-Format Comparison (GitHub API)

| Format | Reduction vs OpenAPI YAML |
|---|---|
| OpenAPI JSON | baseline |
| OpenAPI JSON minified | ~7% |
| LAPIS | **86.6% vs JSON, 79.8% vs minified JSON** |

Savings derive from structural redesign, not whitespace elimination.

### Cost Implications

For GitHub API spec as LLM context at $3.00/M input tokens:

- OpenAPI YAML: **$5.44** per call
- LAPIS: **$0.94** per call
- Savings: **$4.50 per thousand calls**

### Where Savings Come From

| Source | Estimated Contribution |
|---|---|
| Metadata elimination (contact, licenses, extensions) | ~25-30% |
| Signature syntax vs nested YAML/JSON structures | ~25% |
| Type system compaction (single-line enums, direct refs) | ~15% |
| Error centralization (define once vs per-operation) | ~10-20% |

## Information Gain Beyond Subtraction

LAPIS doesn't just compress -- it adds structured representations for concepts OpenAPI
cannot express:

- **Webhook triggers** -- Semantic conditions that cause webhook delivery
- **Structured rate limits** -- Machine-readable rate/quota/tier information
- **Operation flows** -- Explicit multi-step sequences for planning complex interactions

These provide *more information per token* than OpenAPI by carrying operational
semantics absent from or buried in free-text descriptions.

## Comparison with Related Technologies

| Technology | Relationship to LAPIS |
|---|---|
| **OpenAPI** | LAPIS is a conversion target, not a replacement. Organizations keep OpenAPI as source of truth |
| **TOON** (Token-Oriented Object Notation) | Generic serialization format, 30-60% reduction. Addresses encoding overhead but can't eliminate structural redundancies like error duplication |
| **LLM Function Calling Schemas** | Compact per-function schemas from OpenAI/Anthropic/Google, but lack type reuse, operation relationships, error semantics, API-level metadata |
| **Model Context Protocol (MCP)** | Complementary -- MCP handles *how* LLMs call tools, LAPIS describes *what* the API does |

## Conversion from OpenAPI

Automated deterministic rules transform OpenAPI 3.x to LAPIS:

1. Resolve all `$ref` pointers
2. Flatten `allOf` schemas; select most common `oneOf`/`anyOf` variant
3. Extract schemas referenced multiple times as named types
4. Map each path/method combination to an operation
5. Deduplicate and centralize error responses
6. Extract webhooks from OpenAPI 3.1 webhook objects
7. Discard irrelevant metadata (contact, license, examples, extensions, etc.)

### Tools

- **CLI:** `pip install lapis-spec` then `lapis -i openapi.yaml -o api.lapis`
- **Browser:** [cr0hn.github.io/LAPIS/](https://cr0hn.github.io/LAPIS/) (client-side, no data transmitted)
- **VS Code extension:** Syntax highlighting for `.lapis` files

## Limitations

1. **Lossy by design** -- Deliberately discards info useful for non-LLM consumers (detailed JSON Schema validation, response headers, OAuth flow details)
2. **No comprehension benchmark yet** -- Lacks controlled experiments measuring whether LLMs produce *better* API calls with LAPIS vs OpenAPI (planned as future work)
3. **Converter fidelity** -- Reference converter handles standard OpenAPI 3.x but may struggle with complex `oneOf`/`anyOf` compositions
4. **One-way conversion** -- No bidirectional/round-trip conversion (planned)

## Non-Goals

LAPIS explicitly does **not** aim to:

- Replace OpenAPI as documentation source
- Define transport or execution protocols
- Support bidirectional conversion (yet)
- Serve as general-purpose data serialization

## Future Work

1. LLM comprehension evaluation with controlled experiments
2. Bidirectional conversion for round-trip workflows
3. MCP integration for combined description/execution workflows
4. Extended benchmarks on larger API corpus and additional tokenizers

## Sources

- [LAPIS Paper (arXiv)](https://arxiv.org/abs/2602.18541)
- [LAPIS Full HTML Paper](https://arxiv.org/html/2602.18541)
- [LAPIS GitHub Repository](https://github.com/cr0hn/LAPIS)
