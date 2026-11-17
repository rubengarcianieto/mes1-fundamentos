# Risk register

> **Status: draft (v0.1).** Last updated: 2026-11-16.
> This register lists the main risks of SNAIL and how the design intends to
> reduce them. Each risk is marked **implemented**, **partly implemented**,
> **planned** or **ongoing**. "Planned" is never a claim that it already works.

> **Scope note.** SNAIL is a personal, non-commercial learning project. This
> register takes the risk-management principle of Article 9 of the EU AI Act as
> a design inspiration: **compliance by design inspired by the AI Act, not a
> legal obligation.** The project makes no claim of legal compliance or of
> exemption. If a public demo is released, or if SNAIL is ever opened to other
> users, the requirements that may apply (including transparency under
> Article 50 and data protection) will be reviewed first, ideally with
> specialist advice.

Related documents: [Design intent](DESIGN_INTENT.md) and
[References](REFERENCES.md).

## 1. How to read this register

- **Severity** and **likelihood** are qualitative judgements by the author.
  They are provisional and will be revisited as the system is built and
  measured.
- **Mitigations** describe intent. The technical details will be decided when
  each piece is built, and recorded in a separate decisions document.
- **Status** says what exists today.

## 2. Overview

| ID | Risk | Severity | Likelihood | Status |
|---|---|---|---|---|
| R-01 | Hallucination and goal drift | Critical | High | Planned |
| R-02 | Prompt injection through blackboard content | Critical | Medium | Planned |
| R-03 | Correlated errors and verifier bias | High | High | Planned |
| R-04 | Free-tier quotas, outages and changing terms | High | High | Planned |
| R-05 | Endless loops and wasted quota | Medium | Medium | Planned |
| R-06 | Log tampering and state corruption | High | Low | Partly implemented |
| R-07 | Secret exposure in a public repository | Critical | Low | Planned |
| R-08 | Privacy of requests and audit records | Medium | Medium | Planned |
| R-09 | Unintended side effects from tool use | High | Medium | Planned |
| R-10 | Overstated claims in public documentation | Medium | Medium | Ongoing |
| R-11 | Scope and schedule of a solo learning project | Medium | High | Ongoing |

## 3. Risks in detail

### R-01: Hallucination and goal drift

- **Description:** A chain of steps can drift away from the user's original
  request even if every step looks plausible. Models can also state false
  things fluently.
- **Impact:** Irrelevant or wrong final answers, and wasted quota.
- **Mitigation (intent):**
  - Each step is verified separately by a different model (see R-03).
  - Several drift signals are combined, for example the distance from the root
    request, judge checks and the rejection history per type of task. They
    are measured before being trusted, because no single metric is reliable.
  - An agent that spends tokens without progress is stopped (see R-05).
  - A hash does not detect drift: it only shows that a record was not changed.
- **Status:** Planned.

### R-02: Prompt injection through blackboard content

- **Description:** Content from external sources, or written by another agent,
  may contain instructions meant to hijack the agents that read it. The source
  can be outside the system or an agent that is compromised or misbehaving.
  The blackboard is where content is exchanged, so it is also where such
  instructions could spread. It does not prevent injection by itself.
- **Impact:** Unauthorised actions, bypassed design invariants and a corrupted
  verification chain.
- **Mitigation (intent):**
  - Invariant 2: content is data, never instructions.
  - Every entry is validated against a schema.
  - Each agent gets only the permissions its current step needs, and they are
    revoked afterwards.
  - Dedicated injection tests, once the mechanisms exist.
- **Status:** Planned. The entry schema is already validated with pydantic.

### R-03: Correlated errors and verifier bias

- **Description:** A verifier from the same model family as the producer tends
  to approve its output and to repeat its mistakes. Language-model judges can
  also be influenced by the order in which options are shown or by who wrote
  them.
- **Impact:** Flawed results are approved, which undermines the main premise
  of the project.
- **Mitigation (intent):**
  - Invariant 3: the verifier is never the producer, nor from the same model
    family.
  - The order of presentation is randomised and the judge does not see who
    wrote what.
  - If enough model families cannot be reached with free tiers, this is
    documented as a known limitation.
  - The judges are themselves measured.
- **Status:** Planned.

### R-04: Free-tier quotas, outages and changing terms

- **Description:** Free tiers have quotas that can run out, services that can
  be slow or unavailable, and terms that change. Tasks that run for hours or
  days are exposed to all of this.
- **Impact:** Interrupted or incomplete tasks, or a design that depends on a
  service that changes or disappears.
- **Mitigation (intent):**
  - Clients with timeouts and retries with growing waits.
  - Quotas are treated as a normal condition: a task pauses and resumes
    instead of failing, and its work is saved so it survives restarts.
  - Providers can be replaced, and their terms are checked before relying on
    them.
  - Project design intent: The very nature of the project being free-tier 
    based and intentionally built to be "slow but reliable" makes it naturally 
    resistant to timeouts and interruptions. With proper checkpointing, power 
    outages or exhausted quotas do not result in lost work.
- **Status:** Planned. A practice async client already has
  timeouts, retries with growing waits and validation. There is no provider
  layer yet.

### R-05: Endless loops and wasted quota

- **Description:** A producer and a verifier can reject and resubmit the same
  task without converging.
- **Impact:** Wasted quota and a stalled task.
- **Mitigation (intent):**
  - Invariant 4: a fixed maximum number of revisions per task, then escalation
    to a human. This serves as a hands-on design practice for mandatory 
    human oversight (inspired by Article 14 of the EU AI Act). While the regulation 
    targets formal human-in-the-loop controls primarily for high-risk domains 
    (such as HR decisions or critical assessments), implementing it here acts as 
    a "compliance-by-design" practice (used purely as design inspiration, not as 
    a strict legal obligation for this personal non-commercial project).
  - Agents that spend tokens without progress are stopped.
- **Status:** Planned.

### R-06: Log tampering and state corruption

- **Description:** If history can be overwritten, a bug or a misbehaving agent
  can erase or alter its own record, and the answer can no longer be audited.
- **Impact:** Loss of traceability.
- **Mitigation (intent):**
  - Invariant 1: an append-only log. Entries are immutable and linked by hash,
    so any change is detectable.
  - Open question, under consideration: whether agents write to the log
    directly or through a separate component.
  - A hash shows that a record was not changed. It does not show that the
    content is correct.
- **Status:** Partly implemented. Entries are immutable in the first version of
  the schema. The log and the hash links are planned.

### R-07: Secret exposure in a public repository

- **Description:** The repository is public. Committing an API key, a token or
  a log containing credentials would expose it.
- **Impact:** Compromised keys, unauthorised use and possible charges.
- **Mitigation (intent):**
  - Secrets live only in environment files that git ignores. No keys in code,
    tests or logs.
  - If exposure is suspected, the key is revoked and replaced at once.
  - Automated secret scanning is to be evaluated.
- **Status:** Partly implemented. `.env` is already in `.gitignore`.

### R-08: Privacy of requests and audit records

- **Description:** Requests are sent to third-party providers whose terms may
  allow them to use that data. The audit record can also keep sensitive content
  for a long time. If user accounts are ever added, personal data appears.
- **Impact:** Exposure of private data.
- **Mitigation (intent):**
  - Until provider terms are reviewed, only non-private data is submitted.
  - Audit records prefer metadata (model, version, prompt hash, time) over full
    content, with a configurable retention period.
  - Data protection is reviewed before any multi-user version.
- **Status:** Planned.

### R-09: Unintended side effects from tool use

- **Description:** Agents with tools (files, network requests) may take
  destructive or malformed actions because of invented arguments or injected
  instructions.
- **Impact:** Damaged files and unintended requests.
- **Mitigation (intent):**
  - Tool arguments are validated against strict schemas before they run, and
    errors are returned to the agent as information.
  - Narrow permissions, read-only by default, with path and domain allowlists.
  - Isolation with containers plus strict permissions.
- **Status:** Planned.

### R-10: Overstated claims in public documentation

- **Description:** Public documents can claim more than exists, whether
  features, legal status or guarantees. In a public portfolio this harms
  credibility and may give readers a wrong idea about legal compliance.
- **Impact:** Loss of credibility and a wrong legal impression.
- **Mitigation:**
  - Every item is marked planned or implemented.
  - The wording rule: "compliance by design inspired by the AI Act, not a legal
    obligation".
  - Claims are checked against the repository whenever a document is updated.
- **Status:** Ongoing.

### R-11: Scope and schedule of a solo learning project

- **Description:** One person with limited weekly time is building an
  ambitious system, and the goals can grow faster than the time available.
- **Impact:** Unfinished work.
- **Mitigation:**
  - The scope is kept small, and the goals may change as the system is built.
  - Each study month closes with a public deliverable.
  - Lower-priority parts are cut before core ones, and unfinished items are
    listed as future work.
- **Status:** Ongoing.

## 4. Considered and not included

- **Resource limits of local models** (for example, GPU memory). Local models
  are used only during development and testing, as stated in the design intent.
  This risk will be added if that changes.

## 5. Review

This register is reviewed at the end of each study month, and whenever a
mechanism is implemented or a decision changes. Changes are tracked in the git
history.
