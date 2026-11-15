# Design intent

> **Status: initial idea.** SNAIL is a general idea proposed at the start of a
> learning path, from a position of ignorance about many of the topics it
> involves. It will change as it is built, and even its goals may change. Each
> item is marked **implemented** or **planned**. "Planned" is never a claim that
> it already works.

Last updated: 2026-11-09

## 1. Goal

**SNAIL** (Slow Network of AI Layers) is a personal, non-commercial multi-agent
system. It splits a user request into parts and routes each part to free-tier
cloud language models whose capability matches the difficulty of that part.
This lets a set of modest models solve tasks of some complexity.

Its two distinctive traits are **time** and **auditability**:

- **Time.** The system is meant to be **slow but reliable**. A task may take
  hours or even days if the free-tier quotas require it. This makes
  asynchronous programming that tolerates disconnections essential.
- **Auditability.** Every step of the multi-agent system is written to a
  blackboard stored in a free database. Other agents can use it to evaluate
  steps or to complete other parts of the task, and the steps can be reviewed
  afterwards.

## 2. Long-term vision

The end goal shapes the design from the start, even though it will be built
last. **Status: planned.**

A user opens a very simple page with a single text box and submits a request.
Then the user can disconnect. The request lives in the cloud until it is
resolved. When the user signs in again, they can see:

- an approximate estimate of the remaining time,
- the steps already taken,
- a menu to open the audit of those steps.

The first versions will be single-user and simpler (for example, a command
line). Accounts and the web page come later. The core (blackboard, verification
and audit) is built by hand as a learning goal. The interface is expected to be
built later, possibly with help.

## 3. Core requirements

### 3.1 Auditable result

The result is not only the final answer. It is the full chain of steps behind
it, **including the rejected ones**. Anyone should be able to rebuild how an
answer was reached, and to detect if the record was altered afterwards.

### 3.2 Control of hallucination drift

Drift means a step moving away from the original objective. The aim is to
detect it early, before the whole chain is spoiled and before budget is spent.

No single reliable metric exists. The plan is to combine several signals and
to **measure whether they work** before relying on them.

## 4. Design invariants

| # | Invariant | Why | Status |
|---|---|---|---|
| 1 | Append-only log | History must not be rewritten, or it cannot be audited. | Partly implemented: entries are immutable. The log is planned. |
| 2 | Content is data, never instructions | A model's output may contain injected instructions. No output is treated as a command for another agent. | Planned |
| 3 | The verifier is never the producer, nor from the same model family | Models tend to approve their own output and to repeat the same mistakes. | Planned |
| 4 | Iteration cap, with escalation to a human | Prevents endless loops and wasted budget. | Planned |
| 5 | Traceability: model, version and prompt hash for every step | Model answers are not reproducible by default, so the conditions are recorded. | Planned |

## 5. Intended mechanisms (draft)

These describe intent, not final design. The details will be decided when each
piece is built, and recorded in a separate decisions document.

- **Routing.** Each part of a task goes to the model that fits its required
  level of reasoning. Easy parts use lightweight free-tier cloud models. Local
  models are used only during development and testing.
- **Persistent requests.** Each request is a job with an identifier, an owner
  and a status. It is stored in a free-tier database, which is what lets a user
  disconnect and come back later. Something must keep running while the user is
  away. Where and how is not decided yet.
- **Shared blackboard.** Agents do not talk to each other directly. Each one
  reads from and writes to the blackboard, one entry per step.
- **Integrity.** Each entry gets a hash and is linked to the previous one, so
  altering history is detectable. A hash proves a record was not changed. It
  does **not** prove the content is correct, and it does not detect drift.
- **Drift judges.** Light checks run often and measure progress toward the
  objective. An agent that spends tokens without progress is stopped.
  Deeper cross-model verification is kept for uncertain or high-risk steps,
  because free-tier quotas are limited. Judges are language models too and can
  be wrong, so they come from different families and are themselves measured.
- **Permissions.** Each agent gets only the permissions its current step needs.
  They are revoked when the step ends.
- **Injection containment.** The blackboard is where agents exchange content,
  so it is also where a malicious instruction could spread. The source can be
  outside the system or another agent that is compromised or misbehaving.
  Treating content as data, validating every entry against a schema and
  limiting permissions are meant to contain this. The blackboard alone does
  not prevent injection.
- **Durable execution.** Long tasks must survive restarts, disconnections and
  exhausted quotas, resuming without losing work. Free tiers can limit or pause
  services, so the design must tolerate that.

## 6. The EU AI Act

The project is designed with the EU AI Act in mind: **compliance by design
inspired by the AI Act, not a legal obligation.** It is personal and
non-commercial, and it makes no claim of legal compliance. The Act is used as a
source of design principles (risk management, record-keeping, transparency,
human oversight), mapped to concrete artifacts in this repository.

If a public demo is released, or if SNAIL is ever opened to other users, the
requirements that may apply (including data protection) will be reviewed first,
ideally with specialist advice. Sources are in [REFERENCES.md](REFERENCES.md).

## 7. Possible future work

- A simple web page and user accounts, as described in the long-term vision.
- Strong isolation of each agent with micro virtual machines, if time allows
  at the end of the study plan. Until then, the planned isolation is
  containers plus strict permissions.

## 8. Out of scope

- Commercial use, production workloads and sensitive data.
- Guaranteeing correct answers. The system aims to reduce and expose errors,
  not to eliminate them.

## 9. Known limits

- Free-tier quotas and terms change. Each provider's terms must be checked
  before use.
- Requests are sent to third-party providers whose terms may allow them to use
  that data. Until those terms are reviewed, only non-private data should be
  submitted.
- LLM judges can be wrong, biased or agree with the producer.
- This is a solo learning project, so its scope is deliberately small.
