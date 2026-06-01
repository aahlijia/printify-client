# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-06-01

### Added
- PEP 561 `py.typed` marker — the package now ships type information, so type
  checkers (mypy, pyright) pick up the library's annotations downstream.

### Changed
- **BREAKING:** renamed the exception `TimeoutError` to `PrintifyTimeoutError`
  so it no longer shadows the Python built-in. Update imports:
  `from printify_client import PrintifyTimeoutError`.
- `Shop.calculate_shipping` now fetches only the products referenced by the
  order (by ID) instead of the entire catalog, greatly reducing API calls for
  large shops. An unknown `product_id` now raises `NotFoundError`.
- Product pagination is metadata-driven: it reads `last_page` from the first
  response and fetches the remaining pages in a single concurrent wave, instead
  of probing in fixed batches.
- Order parsing is now unified on the shared `parse_order` helper, and
  `parse_order`/`parse_address` tolerate partial payloads (missing `status`
  defaults to `pending`; a missing or malformed `created_at` falls back to the
  current time).

### Fixed
- Product pagination no longer silently truncates the catalog when a page
  request fails: only a `404` ends pagination, while authentication, network,
  and parse errors now propagate.
- An empty product list is now cached instead of being re-fetched on every call
  (the cache lookup distinguishes "empty" from "absent").
- Shipping cost calculation raises `ShippingCalculationError` instead of a bare
  `TypeError` when a profile contains `null` or non-numeric cost data.
- Transient `ConnectionError`s are now retried with exponential backoff,
  consistent with the existing `Timeout` handling.

### Internal
- Package version is single-sourced from `printify_client.__version__` via
  setuptools dynamic metadata.
- `CacheManager` reimplemented on `OrderedDict` for O(1) LRU updates and
  evictions.
- CI publish workflow upgraded to `actions/upload-artifact@v4` and
  `actions/download-artifact@v4`.
- Removed dead/duplicated code and unused imports; the package and test suite
  are clean under `ruff`.

## [0.1.0] - 2026-06-01

### Added
- Initial release: a Python client for the Printify REST API.
- `Shop` facade orchestrating product, shipping, and order operations.
- Product listing with pagination, single-product fetch, and attribute
  filtering.
- Shipping cost calculation with per-item breakdown.
- Order creation with input validation.
- Resilient `APIClient` with Bearer auth, connection pooling, and retry with
  exponential backoff.
- Thread-safe TTL + LRU response cache.
- Typed data models and a clear `PrintifyError` exception hierarchy.

[Unreleased]: https://github.com/printify/printify-client/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/printify/printify-client/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/printify/printify-client/releases/tag/v0.1.0
