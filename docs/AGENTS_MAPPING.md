# Agents mapping

> **Status: early reflection draft.** Last updated: 2026-11-21.
> This document is a personal reflection on the core concepts learned in Unit 1
> of the Hugging Face Agents course and how they might apply to SNAIL. It
> captures early architectural thinking rather than a closed design. Anything
> marked *planned* does not exist yet.

Related documents: [Design intent](DESIGN_INTENT.md) and [Risks](RISKS.md).

## 1. What an agent is (in my own words)

- **Agent:** An agent is a goal-driven system built around a reasoning core (an LLM), a set of instructions or role boundaries, memory or shared state, and access to external capabilities. Unlike a passive text generator, it operates autonomously across multiple steps to reach a defined outcome.
- **The loop:** Agents work through a continuous cycle of **Thought** (reasoning about the current state, planning the next step, and deciding what is missing), **Action** (executing a concrete step or calling an external capability), and **Observation** (receiving and interpreting the result of that action to update its understanding before deciding again).
- **Tools:** Tools are specialized functions or interfaces that let the agent perceive or affect the outside world beyond its internal training knowledge. An agent knows how and when to use them through clear descriptions of each tool's purpose, required inputs, and expected outputs provided in its context.

## 2. Initial Roles (Starting Point)

The table below maps an initial set of core roles. As the architecture matures, this set will likely expand to include specialized roles—such as **isolated code-execution agents** running inside sealed containers, or **hallucination-drift monitors** that track whether reasoning or outputs progressively diverge from grounded facts and initial intent. Moreover, a single role does not necessarily map to a single agent instance: for example, the **Interpreter** may need to split into parallel or staged sub-interpreters when a user request includes large attachments or text volumes that exceed a single context window.

| | Interpreter | Verifier | Decomposer |
|---|---|---|---|
| **Purpose** | Clarifies raw user intent, ingests or chunks large inputs, and translates goals into structured problem statements. | Evaluates outputs, claims, or plans against constraints, evidence, and quality criteria. | Breaks down validated interpretations into smaller, ordered, and actionable sub-tasks. |
| **Reads from the blackboard** | Raw user input, attached documents, workspace context, and prior `interpretation` or `verdict` entries. | Any `interpretation`, `task`, or `result` entry alongside acceptance criteria and invariants. | Approved `interpretation` entries, existing `task` states, and `verdict` feedback. |
| **Writes (entry type)** | `interpretation` | `verdict` | `task` |
| **Tools** | Context-chunking and document-inspection tools, schema lookup, and clarification query builders. | Constraint checklists, source/evidence lookup, and consistency validation checks. | Dependency mapping, task-sizing rules, and routing/capability metadata lookup. |
| **Loop: thought / action / observation** | **Thought:** identify missing context or context-window limits; **Action:** split/inspect input and structure intent; **Observation:** confirm clarity and completeness. | **Thought:** select rule or evidence to test; **Action:** cross-check entry against constraints; **Observation:** record pass/fail evidence. | **Thought:** identify sub-problems and dependencies; **Action:** emit discrete tasks; **Observation:** verify coverage and granularity. |
| **Must never (invariants)** | Invent unstated requirements, silently drop input chunks, or bypass ambiguity checks. | Modify primary `result` or `task` content directly, or approve unverified assumptions. | Execute tasks itself, alter original intent, or dispatch unvalidated work. |
| **Stops when** | All input segments are accounted for and the `interpretation` is clear enough to verify, or human input is needed. | A deterministic `verdict` (pass, fail, or escalate) with justification is recorded. | The validated goal is fully partitioned into verifiable sub-tasks. |

## 3. How the roles connect (Expected Workflow)

Rather than a strict linear pipeline, SNAIL is envisioned as a **branching, iterative, and auditable workflow** coordinated through the blackboard and backed by persistent storage:

1. **Ingestion and split interpretation:** The process begins when a user request enters the system. One or more **Interpreter** agents (splitting the workload when attached documents or long inputs would overflow a single context window) analyze the input and write structured `interpretation` entries.
2. **Continuous persistence and cryptographic auditability:** Every agent contribution—along with its intermediate reasoning steps and state transitions—is continuously persisted into a **database**. Each response and blackboard entry carries agent **signatures and cryptographic hashes** so the entire chain of thought and decision lineage can be traced, verified, and audited end-to-end.
3. **Verification gates:** A **Verifier** inspects each `interpretation` (and later every intermediate `result`), writing a `verdict` that either approves progression, triggers revision loops, or flags anomalies such as hallucination drift.
4. **Task decomposition and multi-agent fan-out:** Once an interpretation passes verification, the **Decomposer** breaks it into granular `task` entries. These tasks can branch out across multiple specialized agents and heterogeneous models—including future sandboxed code-execution agents or drift-monitoring agents—producing `result` entries in parallel or sequence while feeding the database incrementally.
5. **Human-in-the-Loop (HITL) as the controlled exit:** When tasks reach completion, hit unresolvable ambiguity, or trigger a verification escalation, the workflow converges toward a **Human-in-the-Loop (HITL)** checkpoint, which serves as the primary—and potentially sole—validated exit boundary before final actions or outputs leave the system.