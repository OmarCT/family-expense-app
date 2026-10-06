# Family Expense App — Implementation Plan

Oct 5, 2026 · @Omar Celis Torres

## Overview

The app is built in five vertical slices: money correctness first, then the distributed spine, offline sync, scanning with price history, and budgets. Your family can use it online by the end of slice 1, and each later slice adds one capability on top of events that already exist.

**Goal:** a household expense app for mobile and web with offline-first entry, per-item splits between users and groups, a pairwise ledger, analytics, price history and budgets, designed as a distributed system on purpose.

**Guiding principles**

- Money is exact: integer centavos, one rounding rule, and shared test vectors that both the Python server and the TypeScript clients must pass.
- The ledger is append-only: expenses are immutable revisions, settlements and reversals are entries, and every projection can be rebuilt from the event log.
- The server is the source of truth. Phones queue writes and never merge them.
- Visibility is enforced in three places: in the event itself, by PostgreSQL row-level security, and in the feed and projector filters.
- Every slice ends with something the family can use and with tests that prove its invariants.

**Stack at a glance**

| Layer | Choice |
| --- | --- |
| Clients | React Native (iOS, Android) and React web in TypeScript, with a shared package for money rules and the sync client |
| Core service | Python / FastAPI on PostgreSQL, REST with an OpenAPI contract, row-level security |
| Async | Transactional outbox, managed queue, and small Python consumers (analytics projector, budget and alert evaluator, notifier, image cleanup) |
| Read models | A separate PostgreSQL instance for analytics and price history |
| Auth | Managed identity provider: email code, Google and Apple sign-in |
| Hosting | Managed cloud containers, managed PostgreSQL with point-in-time recovery, object storage |
| Observability | OpenTelemetry, a correlation ID on every hop, lag metrics and a restore drill |

## Slice 0 — Foundations

Slice 0 sets up one repository, one CI pipeline and one API contract, so every later slice lands on the same rails and a broken money rule fails the build.

**Work items**

- Monorepo layout: `apps/mobile`, `apps/web`, `packages/domain` (money rules, units), `packages/sync-client`, `services/core`, `services/workers`, `contracts/openapi.yaml`, `testvectors/`.
- CI: lint, type-check, unit tests in both languages, contract tests, and a job that runs the shared test vectors against Python and TypeScript. Container images are built on merge.
- Environments: local (Docker Compose with PostgreSQL, a queue emulator and an S3-compatible store), staging and production, defined as infrastructure as code from the start.
- Identity: a development and a production tenant of the managed provider, with email code, Google and Apple sign-in.
- OpenAPI skeleton: `/v1` paths, one error format, the client ID as idempotency key, the base revision on edits, and a generated TypeScript client plus server-side request validation.
- Internationalisation: a translation-key framework in both clients, `es-MX` as the first locale, seeded names stored as keys.
- Database migrations tool, and the event envelope with a schema version field (additive changes by default, upcasters for breaking ones).
- Observability baseline: structured logs with a correlation ID and OpenTelemetry wiring, with no personal data in logs.

**Exit criteria:** a signed-in user calls a `/v1` endpoint from both app shells through the generated client, the service is deployed to staging by CI, and a deliberately wrong test vector turns the build red.

## Slice 1 — Money correctness

Slice 1 delivers an online-only ledger your family can use for real: manual expenses with items, per-item splits, balances and settlements, all backed by exact money rules. It is the one part that cannot be wrong, so it comes first.

**Order of work**

1. **Test vectors first.** JSON cases for share splitting, largest remainder with the hash tie-break, proportional allocation of extras, discounts and negative items, group expansion, and unit conversion to base units (mass, volume, count). Implement the rules in `packages/domain` (TypeScript) and `services/core` (Python) until both pass the same file.
2. **Data model.** Households and memberships (admin, member); placeholders (name-only, claimable); groups (creator-owned); categories (seeded keys, per household); expenses as immutable revisions with tombstones; items (raw name, category, line total in centavos, quantity, unit and base quantity, optional product link, currency code); per-user item shares with the group tag; one or more payers (registered users only); settlements, reversals and forgiveness as ledger entries.
3. **Row-level security.** Household membership and participants-only visibility as policies, with per-request context scoped to the transaction, plus a test suite that tries to cross the boundary as a non-member, a removed member and a non-participant.
4. **Write API.** Create expense, edit with a base revision (409 and the current revision when stale), delete as a tombstone, record and reverse settlements, settle on behalf of a placeholder, and forgive a debt (payer only).
5. **Balances.** Pairwise balances per household computed from entries in the core, plus a "settle with the fewest payments" suggestion computed on demand. Placeholders stay out of the simplification.
6. **Online-only clients.** Sign-in, households with single-use expiring invites (optionally carrying a placeholder to claim), quick entry (one implicit item and the household default split), itemized entry, expense list, categories, balances and the settle screen.
7. **Property-based tests** for the invariants below, from day one.

**Invariants checked on every run**

- Shares of each item sum exactly to its line total, and allocated extras sum to the ticket extras.
- Balances across a household sum to zero.
- A retried write with the same client ID returns the original result and never creates a duplicate.
- An expense marked participants-only is never returned to a non-participant.

**Exit criteria:** your family logs real expenses for two weeks, balances match a manual check, and the property-based suite and boundary tests are green in CI.

## Slice 2 — Distributed spine

Slice 2 adds the event pipeline that every later feature depends on: a transactional outbox, a sequence-numbered change feed, push hints and the first projector. Build it now, while the domain is still small.

**Order of work**

1. **Outbox in the ledger transaction.** Every write inserts its event in the same commit. The sequence number is assigned at commit time, in order per household, so a client can never miss a change that commits late.
2. **Relay to the managed queue** behind a thin adapter, with a correlation ID carried from the API request through to every consumer.
3. **Change feed API.** "Changes since sequence N" per household, collapsing superseded revisions, carrying tombstones and events such as "removed from this household". Visibility filtering applies here, so hidden expenses never reach non-participants, not even as tombstones.
4. **Push hints.** FCM and APNs for phones and SSE or WebSocket for open web tabs. A hint only says "something changed"; the client then pulls.
5. **First projector** in the separate analytics PostgreSQL: spend per category, member and month. Consumers are idempotent (keyed by event ID) and can rebuild from the log. A "last updated" marker on analytics screens comes from consumer lag.
6. **Web analytics screen** reading the projection.
7. **Fault injection** (deferred from slice 1): duplicate, reorder, delay and drop messages, kill a consumer between "processed" and "offset committed", and restart the relay, then re-check the invariants. Add replay-equality: rebuild every projection from the log and compare it with the live one.
8. **Operations.** Outbox lag, per-consumer lag and dead-letter depth metrics with alerts that fire only on stuck or growing conditions. A consumer that meets an unknown event version stops and alerts.

**Exit criteria:** a second family member sees an expense on another device within seconds through the feed, replay-equality passes in CI, and killing a consumer mid-batch loses and duplicates nothing.

## Slice 3 — Offline-first

Slice 3 lets the phone add expenses with no signal and sync them later, without losing or duplicating anything. Offline scope is add-only; edits, deletes, group changes and settlements stay online.

**Order of work**

1. **Local database.** SQLite on the phone holds the write queue, reference data (members, placeholders, groups, categories, products) and a read cache with recent expenses and last-known balances, labelled "as of last sync". Pending expenses show as pending.
2. **Client-generated IDs** on every queued write, used as the idempotency key. A resent write returns the stored result.
3. **Sync client** in `packages/sync-client`, with no assumption about the storage layer so a web read cache can be added later. It drains the queue, then pulls the feed from its cursor.
4. **Bootstrap.** A new install or second device gets a snapshot (reference data, complete balances, about six months of expenses) stamped with sequence S, then follows the feed from S. Older history loads on demand when online.
5. **Staleness rule.** A cursor older than the threshold, or a gap that is too large, discards the cache and re-bootstraps instead of replaying the gap.
6. **Server-side validation of queued writes.** Anything that fails business validation (a removed participant, a merged product) is saved as a flagged draft, and dead product links are dropped while the raw name is kept. Only malformed requests and authorization failures are rejected. A rejected write stays on the device as "not synced: you are no longer a member".
7. **Payload versioning.** Queued writes carry an API version and are upgraded on arrival, or become a flagged draft if they cannot be, so an app release never strands an offline queue.
8. **Purge on removal.** The "removed from household" event deletes that household's local data, including cached receipt images, and server-side session revocation backs it up.
9. **Sync tests.** Run the sync client against a simulated flaky network (dropped responses, repeated pushes, stale cursors) and assert it converges to the server state.

**Exit criteria:** a phone in airplane mode adds five expenses, reconnects, and the server holds exactly five. A phone offline for weeks re-bootstraps correctly, and a removed member's device is purged on its next sync.

## Slice 4 — Drafts, scanning, catalog and price history

Slice 4 turns a ticket photo into a draft expense and makes item prices comparable over time. Drafts are the safety net: nothing counts toward balances or analytics until a household member confirms it.

**Order of work**

1. **Draft state.** Drafts use the same revisions and optimistic concurrency as expenses, so two members confirming at once cannot both win. Any household member can confirm. A draft is prefilled with the scanner as payer and the household's default split on every item.
2. **Product catalog.** Households own it. Any member can create a product, and an item keeps its raw name with an optional product link. Merges are an admin action stored as reversible aliases, never as rewrites, and confirmed raw names become aliases so the same ticket text links itself next time. A product can carry a default category.
3. **Units and price history.** Items store the line total in centavos plus quantity and unit as written and in a canonical base unit (mass, volume, count). Unit price and price per liter or kg are derived on read. A price point is dated by the expense date. Items without a product link or unit are left out of price trends.
4. **On-device scanner.** ML Kit (Android) and Apple Vision (iOS) behind small native wrappers. A heuristic parser extracts merchant, date, items, quantities and prices, and marks uncertain lines. A check that items plus tax and discounts equal the ticket total flags most mistakes.
5. **Image handling.** The photo is queued like any other write and uploaded when there is a connection to a private bucket, served only through short-lived signed URLs after a membership check. It is deleted after the retention period; the raw OCR text stays with the draft.
6. **Confirm screen.** Fix extraction mistakes, link products, override splits, and confirm. Each confirmed draft stores the raw OCR text and the corrected items, which become the regression test set for the parser.
7. **Price-history projector and screens.** A price series per product, normalized per liter or kg, shown on web and mobile. Unlinked quick items count toward spend analytics only.
8. **Participants-only handling.** Hidden expenses stay out of shared price history and out of catalog autocomplete, and a product first created inside one stays private until a non-participant uses it.

**Exit criteria:** a real ticket from a store your family uses becomes a correct draft in under a minute of review, a confirmed draft shows up in price history, and the parser has a test set of real tickets that fails a build when accuracy drops.

## Slice 5 — Budgets, alerts, recurring drafts and lifecycle

Slice 5 adds the features that read the data the earlier slices already produce: budgets with alerts, recurring drafts, the notification inbox, export, and the account and household lifecycle rules.

**Order of work**

1. **Budgets.** Three levels: household budgets measured on item totals, personal budgets measured on a member's owed share (including their participants-only expenses), and group budgets measured on shares carrying the group tag. A budget is owned by its creator, and ownership passes to an admin if the creator leaves. Archiving a category or group closes its budgets with a notice.
2. **Budget and alert evaluator.** A consumer reading projected totals. It alerts at 80% and at the limit, and only the owner of the budget gets the alert.
3. **Notification inbox.** The inbox is the source of truth and push is only a delivery channel. Notifications are deduplicated by event ID and recipient, users can mute types, and the notifier re-checks visibility at delivery time so a hidden expense or a household the user left never produces a push.
4. **Recurring rules.** Monthly and weekly templates on a household-timezone date that generate drafts for a member to confirm. The scheduler is idempotent, keyed by rule ID and period, and after downtime it generates every missed period exactly once.
5. **Price-increase alerts.** Computed from the price history projection, delivered through the same inbox.
6. **Export.** A background job that reads through the requester's own permissions, writes a self-describing CSV and JSON file (schema version, centavos with currency code, base units with the original text, names beside IDs) to object storage, and notifies the member with a short-lived link. Files are deleted after the retention period.
7. **Leaving and deleting.** Leaving a household keeps debts on a frozen record. Deleting an account anonymizes the person as "Former member" in every household and purges email, auth links, personal budgets and receipt images, while shares and payments stay in the ledger. If the last admin leaves, the oldest member is promoted.
8. **Security hardening.** Revocable per-device sessions that are revoked automatically on removal, rate limits on the sync and invite endpoints, a cap on invite attempts, secrets in the secret manager, and an optional biometric lock in the mobile settings.
9. **Release hardening.** Store submission (iOS and Android), Sign in with Apple, privacy notices covering the data protection rights of access and deletion, and the first scheduled restore drill running the replay-equality check.

**Exit criteria:** an 80% budget alert reaches only its owner, a recurring rent rule creates exactly one draft per month through a simulated restart, an export contains nothing the requester could not already see, and a deleted account leaves balances intact with no personal data behind.

## Cross-cutting: testing, operations and security

Ten concerns run through the slices, and most of them start in slice 0, 1 or 2 because they are cheap early and painful to retrofit.

| Concern | Approach | Starts in |
| --- | --- | --- |
| Money rules | One JSON file of test vectors run by both the Python and TypeScript suites; CI fails if they disagree | Slice 0–1 |
| Invariants | Property-based tests over random operation sequences (shares sum to totals, balances sum to zero, retries never duplicate, hidden expenses never leak) | Slice 1 |
| Tenant isolation | PostgreSQL row-level security plus app-level checks, a transaction-scoped context, and boundary tests as a non-member, a removed member and a non-participant | Slice 1 |
| Replay and faults | Rebuild every projection from the log and compare with the live one; inject duplicated, reordered, delayed and dropped messages and consumer crashes | Slice 2 |
| Sync behavior | Run the shared sync client against a simulated flaky network and stale cursors, and assert convergence | Slice 3 |
| Event schemas | A version on every event, additive changes by default, upcasters for breaking ones, unknown versions stop the consumer and alert; stored events are never rewritten | Slice 0 |
| Monitoring | OpenTelemetry and structured logs with a correlation ID; metrics for outbox lag, per-consumer lag, dead-letter depth, sync API error rate and flagged-draft rate | Slice 2 |
| Recovery | Point-in-time recovery for PostgreSQL and a scheduled restore drill that runs the replay-equality check on the restored copy | Slice 2, rehearsed in slice 5 |
| API evolution | Versioned `/v1` paths, additive changes within a version, old versions kept while old app releases remain in use | Slice 0 |
| Security baseline | Per-device revocable sessions, rate limits on sync and invites, private bucket with signed URLs, secrets in the secret manager, no personal data in logs | Slice 1, completed in slice 5 |

**Deployment.** Containers on a managed serverless platform, managed PostgreSQL and a managed queue behind a thin adapter. Staging mirrors production, and migrations run in CI before a release.

**Release discipline for the apps.** Because queued offline payloads and stored events outlive app versions, every release is checked against a sample of old payload versions before it ships.

## Risks, open items and sizing

The main risk is scope: this design has many moving parts, and the slice order exists to keep something usable in your family's hands at every step. Calendar dates are not set because they depend on how many hours a week you can give it.

**Relative sizing (my estimate, S < M < L)**

| Slice | Size | What the family gets |
| --- | --- | --- |
| 0 Foundations | S | Nothing visible; the build and contract are ready |
| 1 Money correctness | L | Online expense logging, splits, balances and settlements |
| 2 Distributed spine | M | Changes appear on other devices; first analytics |
| 3 Offline-first | L | Add expenses with no signal |
| 4 Drafts, scanning, price history | L | Ticket photos become drafts; price trends |
| 5 Budgets and lifecycle | L | Budgets, alerts, recurring drafts, export, account deletion |

**Risks**

| Risk | Mitigation |
| --- | --- |
| Scope grows faster than the build | Fixed slice order, a usable app after slice 1, deferred list below |
| Python and TypeScript money rules drift apart | Shared test vectors in CI from slice 0 |
| Offline sync edge cases lose or duplicate writes | Client IDs as idempotency keys, flagged drafts, simulated flaky-network tests |
| Scanner accuracy on real Mexican tickets | Drafts never count until confirmed, line confidence marks, a growing regression set |
| Old app versions meet new schemas | Versioned payloads and events, upcasters, release checks against old samples |
| Store review delays (Sign in with Apple, privacy) | Plan the submission checklist in slice 5 and test builds earlier |

**Decisions still needed before slice 0**

- [ ] Cloud provider and its serverless container, managed PostgreSQL and queue services
- [ ] Managed identity provider
- [ ] React Native setup (managed workflow or bare) and how the ML Kit and Apple Vision wrappers are built
- [ ] Weekly time available, so the sizes above can become dates

**Deferred, not forgotten**

- Import from spreadsheets or other apps (arrives as drafts)
- Email notifications and an offline-capable web app
- Multi-currency (the currency code is already stored on every amount)
- Period locking, product pack size, saved payment details such as a CLABE
- Cross-household settle suggestions, hierarchical categories, nested groups
- Server-side receipt re-extraction with a stronger model, and an English locale
- An expense-level default category, if quick entry feels slow without it
