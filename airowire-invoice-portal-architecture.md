# Airowire Invoice Portal — Architecture Overview

**Stack:** React (frontend) + Flask (backend) + SQL (SQLAlchemy) + APScheduler
**Email source:** Microsoft Graph API — mocked for now, swapped in later without touching downstream code
**Branding:** White background, orange buttons/accents (Airowire logo colors)

---

## 1. Design Principle: Everything Talks Through Interfaces, Not Implementations

The whole point of this architecture is that **no module should know or care whether email data is real (Graph API) or fake (fixtures)**. Every module below is built against a contract (a fixed input/output shape). As long as the contract is respected, you can swap the mock mail source for the real one later by changing exactly one file — nothing else in the system changes.

This also means each module can be built and tested in isolation, which is what lets you build this in a day: you're not waiting on one module to test another.

```
                    ┌─────────────────────┐
                    │   Mail Source Layer   │   ← swappable: Mock now, Graph API later
                    │  (graph_service.py)   │
                    └──────────┬────────────┘
                               │  emits: normalized email objects
                               ▼
                    ┌─────────────────────┐
                    │   Filter Engine       │   ← keyword rules (subject/body)
                    └──────────┬────────────┘
                               │  emits: filtered email objects
                               ▼
                    ┌─────────────────────┐
                    │   Threading Engine     │   ← conversationId + fallback heuristics
                    └──────────┬────────────┘
                               │  emits: (email, thread_id, confidence)
                               ▼
                    ┌─────────────────────┐
                    │   Storage Layer         │   ← SQLAlchemy models, no business logic
                    └──────────┬────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Attachment Handler    │   ← saves files, links to email row
                    └──────────┬────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Scheduler (APScheduler)│  ← orchestrates the above every N mins
                    └─────────────────────┘

                    ┌─────────────────────┐
                    │   Flask REST API        │   ← Inbox / Sent / Thread / Send endpoints
                    └──────────┬────────────┘
                               ▼
                    ┌─────────────────────┐
                    │   React Frontend         │   ← Dashboard / Inbox / Sent / Thread / Compose
                    └─────────────────────┘
```

Each box is a separate Python module/folder. None of them import each other's internals — they only pass data structures defined in a shared `schemas.py`.

---

## 2. Module Breakdown

### 2.1 Mail Source Layer (`services/mail_source/`)

**Responsibility:** produce a list of "raw email" objects. Nothing else.

Define an interface (even just a Python `Protocol` or abstract base class):

```python
class MailSourceInterface:
    def fetch_messages(self, mailbox: str, since: datetime) -> list[RawEmail]:
        ...
    def send_message(self, mailbox: str, to: list[str], subject: str, body: str, attachments: list) -> SendResult:
        ...
```

Two implementations:
- `MockMailSource` — reads from a fixtures JSON file shaped exactly like Graph API's message schema (`conversationId`, `subject`, `from`, `toRecipients`, `receivedDateTime`, `body`, `hasAttachments`, `attachments[]`).
- `GraphMailSource` (built later) — real Graph API calls, same method signatures.

**Why this matters for you:** your fixtures file becomes your test data. Make 3–4 fake "threads" in it — e.g. an AWS invoice with 2 replies, a Microsoft invoice with a forwarded/mangled subject, a customer invoice you "sent" with a customer reply — so the Threading Engine has real scenarios to prove itself against.

### 2.2 Filter Engine (`services/filter_engine.py`)

**Responsibility:** given a `RawEmail` and a list of active keyword rules, return `True`/`False`.

```python
def matches_filters(email: RawEmail, keywords: list[str]) -> bool:
    haystack = f"{email.subject} {email.body}".lower()
    return any(kw.lower() in haystack for kw in keywords)
```

Keywords come from the `keyword_filters` table (already in your schema) — so this stays fully configurable from the UI later without code changes. Keep this module pure/stateless: input email + keyword list → boolean. No DB calls inside it.

### 2.3 Threading Engine (`services/threading_engine.py`) — the important one

**Responsibility:** decide which existing thread (if any) an incoming email belongs to, or create a new one.

This runs in two tiers:

**Tier 1 — Primary match (`conversationId`)**
If `email.conversationId` matches an existing `email_threads.conversation_id`, attach it there. Confidence = `exact`. This handles the vast majority of real Outlook-to-Outlook traffic and all of your mock "happy path" threads.

**Tier 2 — Fallback match (when conversationId is missing, or belongs to a client that doesn't preserve it, e.g. a forwarded mail or an external non-Outlook sender)**

Fallback runs a 3-part heuristic. All three must pass for an automatic match; if only some pass, flag it `needs_review` instead of silently merging (silent wrong-merges are worse than a slightly messy inbox).

1. **Subject normalization + match**
   Strip prefixes/noise before comparing:
   ```python
   def normalize_subject(subject: str) -> str:
       s = subject.strip().lower()
       s = re.sub(r'^(re|fw|fwd)\s*:\s*', '', s)   # strip one prefix
       s = re.sub(r'^(re|fw|fwd)\s*:\s*', '', s)   # run twice for "RE: FW:"
       s = re.sub(r'\s+', ' ', s)
       return s.strip()
   ```
   Compare `normalize_subject(new_email.subject) == normalize_subject(thread.subject)`.

2. **Participant overlap**
   Build a "participant fingerprint" — a sorted, deduped set of every email address that's ever appeared as sender or recipient in that thread. New email must share at least one address (typically the external counterparty, e.g. `billing@microsoft.com`) with the thread's fingerprint.
   ```python
   def participant_fingerprint(addresses: list[str]) -> frozenset:
       return frozenset(a.lower().strip() for a in addresses)
   ```

3. **Time window**
   New email's `receivedDateTime` must fall within a reasonable window of the thread's `last_activity` (e.g. 30 days — configurable). This stops "Invoice" from January and "Invoice" from November being wrongly merged just because the subject matches.

**Confidence scoring:**

| Match type | Conversation ID | Subject normalized | Participants overlap | Time window | Result |
|---|---|---|---|---|---|
| Exact | ✅ | — | — | — | Auto-attach |
| Strong fallback | ❌ | ✅ | ✅ | ✅ | Auto-attach, tagged `fallback_matched` |
| Weak fallback | ❌ | ✅ | ✅ | ❌ | Create new thread, tagged `needs_review` |
| No match | ❌ | ❌ | — | — | New thread |

This `needs_review` flag is your safety net — it means the UI can show "possibly related to Thread X?" instead of the engine silently guessing wrong. That's a cheap addition (one boolean column) that saves you from a much harder bug to debug later.

**Interface:**
```python
def resolve_thread(email: RawEmail, existing_threads: list[Thread]) -> ThreadMatchResult:
    # returns: thread_id (existing or new), confidence, matched_via
    ...
```

Keep this engine completely decoupled from the DB — pass it in-memory thread objects, get back a decision, let the Storage Layer do the actual writing. That's what makes it independently testable: you can unit-test `resolve_thread()` with a list of fake threads and fake emails, no DB required.

### 2.4 Storage Layer (`models/` + `repositories/`)

Plain SQLAlchemy models matching the schema you already have (mailboxes, email_threads, emails, attachments, keyword_filters), plus two additions from the threading logic above:

```sql
ALTER TABLE email_threads ADD COLUMN normalized_subject VARCHAR(500);
ALTER TABLE email_threads ADD COLUMN participant_fingerprint TEXT;  -- JSON array of addresses
ALTER TABLE emails ADD COLUMN thread_match_confidence ENUM('exact','fallback_strong','fallback_weak') DEFAULT 'exact';
ALTER TABLE emails ADD COLUMN needs_review BOOLEAN DEFAULT FALSE;
```

Put all DB writes behind a thin repository layer (`repositories/email_repo.py`, `thread_repo.py`) so the Threading Engine and Scheduler never write raw SQL/ORM calls directly — they call `thread_repo.create_or_update(...)`. This is what keeps modules independent: swap SQLite→SQL Server later without touching business logic.

### 2.5 Attachment Handler (`services/attachment_service.py`)

**Responsibility:** given an email with `hasAttachments = true`, pull attachment bytes from the Mail Source Layer, save to `/uploads/{mailbox}/{email_id}/`, write a row to `attachments` with the path. In mock mode, "fetching" just means copying a sample PDF from your fixtures folder — same function signature as the real Graph download call, so nothing changes later.

### 2.6 Scheduler (`scheduler/email_fetch_job.py`)

Orchestrates the pipeline — this is the only module allowed to call the others in sequence:

```
for each active mailbox:
    since = mailbox.last_synced_time
    raw_emails = mail_source.fetch_messages(mailbox, since)
    for email in raw_emails:
        if filter_engine.matches_filters(email, active_keywords):
            thread_result = threading_engine.resolve_thread(email, existing_threads)
            email_repo.save(email, thread_result)
            if email.has_attachments:
                attachment_service.save_attachments(email)
    mailbox.last_synced_time = now()
```

Runs every 5 minutes via APScheduler. This incremental `since` approach (not full-mailbox fetch) is what you'll want even with mock data, since it's the same pattern the real Graph integration needs.

### 2.7 Flask REST API (`routes/`)

Unchanged from your original plan — thin controllers only, no business logic:

```
GET  /api/invoices/inbox
GET  /api/invoices/sent
GET  /api/thread/{id}
POST /api/send-email          → calls mail_source.send_message()
GET  /api/attachment/{id}
GET  /api/threads/needs-review   ← new, surfaces fallback-flagged threads for manual confirmation
```

### 2.8 React Frontend

Same structure as before — Dashboard, Inbox, Sent, ThreadView, ComposeEmail. One addition: in ThreadView, if `needs_review` is true on an email, show a small "possibly part of another thread" badge with a manual "merge" action — cheap to build, and it's the UI-facing payoff of the confidence scoring above.

---

## 3. Suggested Folder Structure

```
backend/
├── app.py
├── config.py
├── schemas.py                     # shared data contracts (RawEmail, ThreadMatchResult, etc.)
│
├── routes/
│   ├── inbox.py
│   ├── sent.py
│   ├── thread.py
│   └── mail.py
│
├── services/
│   ├── mail_source/
│   │   ├── base.py                # MailSourceInterface
│   │   ├── mock_source.py         # MockMailSource
│   │   └── graph_source.py        # GraphMailSource (built later)
│   ├── filter_engine.py
│   ├── threading_engine.py
│   └── attachment_service.py
│
├── repositories/
│   ├── email_repo.py
│   ├── thread_repo.py
│   └── attachment_repo.py
│
├── models/
│   ├── mailbox.py
│   ├── thread.py
│   ├── email.py
│   └── attachment.py
│
├── scheduler/
│   └── email_fetch_job.py
│
├── fixtures/
│   └── mock_emails.json           # your hand-crafted test threads
│
└── uploads/

frontend/
├── Dashboard/
├── Inbox/
├── Sent/
├── ThreadView/
├── ComposeEmail/
└── Login/
```

---

## 4. What to Tell Your Coding Agent (Antigravity / Copilot), In Order

Build in this sequence so each piece is testable before the next depends on it:

1. `schemas.py` — define `RawEmail`, `ThreadMatchResult` data classes first. Everything else references these.
2. `fixtures/mock_emails.json` — write 4–5 realistic fake threads (include one with a mangled forwarded subject, one with no conversationId, so the fallback logic has something to prove itself on).
3. `mail_source/mock_source.py` implementing `MailSourceInterface`.
4. `filter_engine.py` — pure function, unit test against a few fixture emails.
5. `threading_engine.py` — pure function, unit test `resolve_thread()` against fixtures directly (no DB, no Flask needed yet).
6. Models + repositories + DB schema.
7. `scheduler/email_fetch_job.py` wiring steps 3–6 together, run manually first, confirm DB rows look right.
8. Flask routes exposing what's now in the DB.
9. React screens consuming the routes.
10. Styling pass (white/orange, Airowire branding) last — don't let this eat time earlier in the day.

This order means that if you run out of time, you still have a working backend pipeline with correct threading — the riskiest, most important part — even if the UI polish gets cut short.

---

## 5. What's Explicitly Deferred (say this to your manager)

- Real Azure AD app registration / OAuth / admin consent
- Real Graph API calls (structurally ready — just swap `MockMailSource` → `GraphMailSource`)
- Graph webhook subscriptions (Phase 2, replaces polling)
- Large-attachment upload-session handling (only relevant with real Graph API)
- Send-As/Send-on-Behalf permission config (Azure-side, not code)
