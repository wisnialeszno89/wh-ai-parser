# Universal Agent — Project Vision, Architecture, Roadmap, and Continuation Context

**Status:** agreed product direction and working engineering handoff  
**Last updated:** 2026-10-22  
**Primary integration branch:** `feature/browser-navimind-bridge`  
**Purpose of this document:** preserve the agreed direction and the real implementation checkpoint so future work and future ChatGPT conversations can continue without reconstructing intent from chat history.

This is the living project reference. Update it when a major architectural decision, product principle, roadmap priority, or engineering milestone changes.

## 1. Product vision

Build a **Universal Digital Worker**: a dependable digital employee that can receive a business goal in ordinary language, understand relevant files and the active computer environment, carry out a scoped workflow across applications, verify the result, remember useful experience, and advise the user when it sees a demonstrably better way to work.

The product is not only a PDF parser or a macro recorder. It should gradually become a configurable assistant for office and business operations. The initial scope must remain grounded in workflows we can test reliably; breadth must not come at the cost of pretending the agent succeeded when it did not.

Examples of future user requests:

- “Read this PDF and these photos, prepare a quote, and show me which dimensions are uncertain.”
- “Take the data from these files, compare them in Excel, and prepare a summary.”
- “Draft a reply to this email using our company rules; do not send it until I approve.”
- “Repeat the workflow I showed you yesterday, but use the new customer’s details.”
- “You have repeated this manual step several times. Is there a safer or faster process?”

The long-term objective is an agent that helps across different computers and common business applications, while respecting the permissions and safeguards of each environment.

## 2. Product architecture: NaviMind + local execution runtime

Treat **NaviMind and wh-ai-parser as complementary parts of one product**, not competing agents.

### NaviMind — reasoning and knowledge services

Over time, NaviMind should provide or coordinate:

- task understanding, planning, and reasoning;
- general knowledge and research using approved internet access;
- continuity of purpose and access to relevant, permissioned knowledge;
- suggestions for alternative approaches, with reasons and supporting evidence;
- a remote reasoning interface that communicates in structured semantic data.

### wh-ai-parser — local perception, control, and proof of outcome

The local runtime should remain responsible for:

- observing the real local application and desktop state;
- interpreting UI Automation/native controls and other approved perception sources;
- reading approved local documents and retaining exact source provenance;
- choosing from locally approved application adapters and semantic actions;
- validating targets and permissions immediately before execution;
- executing one bounded action at a time and observing again;
- verifying the actual resulting state, recording outcomes, and enabling safe resume;
- maintaining local enforcement even when the reasoning service is remote or unavailable.

**Trust boundary:** NaviMind can propose a plan or semantic action, but the local runtime decides whether the action is allowed and whether the current target is valid. Remote text, webpages, emails, PDFs, screenshots, and other external content are data to analyze—not instructions that can grant permissions or expand the action allowlist.

The existing NaviMind bridge already follows this principle: remote reasoning receives semantic world state rather than local coordinates, window handles, or executor internals; local safety and verification remain authoritative.

## 3. The standard execution loop

The intended general pattern is:

1. **Understand the goal.** Identify the expected deliverable, constraints, available sources, and actions that require approval.
2. **Observe and collect evidence.** Inspect the current app state and approved documents; retain the origin of every important extracted fact.
3. **Normalize and validate.** Build typed facts, mark uncertainty and conflicts, and ask for clarification or stop when critical information is unsupported.
4. **Plan the next bounded step.** Prefer one verifiable semantic action rather than a long unobserved sequence.
5. **Check permissions and target scope.** Validate the actual current control/document and the action policy locally.
6. **Execute.** Perform only the approved step.
7. **Re-observe and verify.** Confirm that the intended state change really occurred; do not infer success merely because a click or keystroke was issued.
8. **Checkpoint and learn.** Record a compact outcome, diagnostics, and reusable workflow information without storing unnecessary sensitive data.
9. **Deliver the result.** Summarize what was completed, what was not, what remains uncertain, and what needs human approval.

The agent must be able to stop safely, cancel, request manual review, and resume from a checkpoint. Add step, time, and resource limits to workflows as the runtime matures.

## 4. Inputs, evidence, and document understanding

The long-term input model should cover natural-language instructions and common business materials: PDF files, scanned pages, photos, screenshots, email content, Word documents, Excel workbooks, CSV files, and relevant browser pages.

For important extracted fields, preserve as much of the following as the source type allows:

- source identity or approved alias;
- page number, image/region, email, worksheet/cell, or other source location;
- exact evidence text or value;
- extraction method (for example, native PDF text or OCR);
- confidence/quality and any limitation;
- conflict information when sources disagree.

**Never disguise a guess as a verified fact.** If a critical dimension, amount, date, customer detail, or other required value lacks evidence or conflicts with another source, the agent should ask, flag manual review, or stop before taking a consequential action.

A sensible development sequence is to establish deterministic parsing, explicit provenance, typed data contracts, and rejection tests first. Add model-assisted extraction only behind the same evidence and validation boundary.

## 5. Learning and memory

Learning is a key product capability and some foundations already exist. The agent can record demonstrated semantic workflows and persist compact execution experience. The goal is useful adaptation—not uncontrolled self-modification.

Keep four distinguishable memory categories:

1. **Task/session memory:** current goal, discovered facts, decisions, blockers, checkpoints, and resume state.
2. **Procedural memory:** user-demonstrated workflows and reusable semantic skills, with parameterized values where safe.
3. **User/company knowledge:** approved preferences, process rules, application conventions, templates, and business-specific terminology.
4. **Experience memory:** the outcome of prior attempts, verification results, common failures, and concise diagnostics.

Learning rules:

- Observe and record results, but do not automatically promote every observation into a trusted rule.
- Distinguish user-provided facts, verified outcomes, inferred hypotheses, and external information.
- Test learned skills against explicit preconditions, target scope, expected postconditions, and failure paths before relying on them.
- Version skills and make changes traceable; retain the ability to disable or roll back a faulty skill.
- Avoid unnecessary retention of raw requests, credentials, sensitive document contents, and machine-specific execution identifiers.
- Reuse prior experience only when the application, goal, and context match sufficiently; otherwise request review.

The existing learned-workflow path intentionally uses semantic state transitions rather than storing raw key events, screen coordinates, or machine-specific window handles.

## 6. General computer knowledge and internet access

The agent should eventually research software documentation, business rules, and relevant public information through NaviMind or a dedicated research adapter.

External sources must remain distinguishable from trusted local/runtime knowledge. Preserve source references, retrieval context, uncertainty, conflicting claims, and limitations where possible. Web content and text found inside user-provided files must never be allowed to override system policy, user permissions, or local action safeguards.

Start with bounded, auditable research rather than unrestricted browsing or automatic execution based on webpages.

## 7. Proactive advisor

Beyond doing exactly what it was told, the agent should sometimes point out a better way to work. Useful triggers include repeated manual operations, frequent corrections, recurring errors, unnecessary duplicate entry, and avoidable handoffs.

A recommendation should contain:

- the observed pattern and the evidence supporting it;
- the proposed change and why it may be better;
- expected benefit, expressed as a measurement or an honest estimate;
- risks, assumptions, and the reversibility of the change;
- a suggested next step that the user can accept or reject.

Do not interrupt constantly or make unsupported claims about productivity. Begin with suggestions, not silent process changes. Any learned or process-level change that could materially affect work should be reviewed, tested, and reversible.

## 8. Safety and user control

These are product requirements, not optional polish:

- Dry-run or simulated execution by default for new workflows.
- Explicit opt-in for physical/live computer control and tightly scoped live tests.
- Local allowlists and target validation for semantic actions.
- Consequential actions—such as sending, submitting, deleting, purchasing, or transmitting sensitive data—must require an appropriate approval gate. Drafting is not the same as sending.
- External content is never an authorization source.
- Fail closed on unsupported, ambiguous, conflicting, or low-confidence situations.
- Verify the postcondition after each meaningful action.
- Provide cancellation, bounded execution, checkpoints, safe resume, and an auditable report.
- Protect credentials and company data; minimize retention and separate business tenants/data when moving toward a commercial service.
- Make capability boundaries visible: state when an operation was simulated, blocked, partially completed, or not actually verified.

## 9. Office and business product direction

The platform should grow around a common semantic task and adapter contract rather than a separate one-off automation for every application. Current adapter foundations include filesystem, Word, Excel, email-draft, and browser adapters; provider-specific details should remain behind those contracts.

Potential business workflows include document intake, quote preparation, structured data extraction, spreadsheet consolidation, report drafting, email drafting, browser-based data entry, and repeatable operations inside specialist desktop applications such as WindowHub.

Commercial readiness will eventually require environment discovery, configuration and permissions, application/provider adapters, safe updates, diagnostics, data isolation, clear deployment requirements, and an understandable user/admin experience. These are future product requirements and should not be represented as complete until implemented and tested.

## 10. Success measures

Measure correctness and trust, not simply the number of actions or lines of automation. Useful metrics include:

- percentage of defined real tasks completed correctly end-to-end;
- percentage requiring manual intervention and why;
- source/evidence coverage for critical extracted fields;
- action verification pass rate;
- frequency of false success reports, which should trend to zero;
- recovery and resume success after a blocked or interrupted step;
- time saved compared with a documented manual baseline;
- rate of harmful regressions in learned workflows;
- user acceptance of proactive suggestions.

Every milestone should name the relevant test evidence and remaining gaps.

## 11. Staged roadmap

### Phase A — make the trusted PDF path real end-to-end

- Preserve local, approved PDF ingestion and the trusted source registry.
- Connect extracted pages to typed quote facts with explicit evidence and provenance.
- Keep deterministic validation authoritative; reject fabricated evidence, wrong pages, aliases that do not resolve, and unsupported critical values.
- Cover the flow with synthetic PDFs and runtime tests, including conflicts, scans/no-text pages, invalid paths, and manual-review outcomes.
- Produce a controlled path from source file to a validated quote draft; do not submit/send automatically.

### Phase B — verify WindowHub execution locally

- Re-check the merged runtime and target-scope safeguards.
- Run available automated CI tests and dry-run/simulated paths first.
- Prepare a concise Windows PowerShell smoke procedure and bounded logs for the user's local environment.
- Verify observation -> semantic targeting -> one action -> re-observation -> postcondition.
- Only after dry-run evidence is sound, conduct a narrowly scoped user-supervised live test. Never claim a local WindowHub run occurred unless the local output was actually supplied and reviewed.

### Phase C — reliable office workflows

- Demonstrate complete, verifiable workflows across files, Word, Excel, email drafts, and browser.
- Standardize adapter contracts, task checkpoints, error handling, and result reports.
- Require approval before consequential external actions.

### Phase D — controlled learning and proactive advice

- Evaluate stored experiences and learned skills.
- Add skill validation/versioning/rollback and quality metrics.
- Introduce evidence-based improvement suggestions, initially in advisory mode.

### Phase E — deployable business product

- Add configuration and permission management, diagnostics, deployment guidance, data isolation, secure secrets handling, and upgrade strategy.
- Validate against repeatable real-world workflows in more than one environment before broadening promises or marketing claims.

## 12. Engineering checkpoint as of 2026-10-22

The primary working integration branch is `feature/browser-navimind-bridge`. Its last confirmed integration state in this work was commit `03132b2e8b0376ec59407bb7975d45476584d044` (PR #114). Re-check GitHub before relying on the branch head in future work.

Merged work with successful CI at the time of this checkpoint:

- **PR #110** — protect native WindowHub fields from OCR text fusion.
- **PR #112** — require appropriately scoped targets for WindowHub `write_text`.
- **PR #113** — add trusted local PDF ingestion service based on the existing PDF adapter; preserve provenance; reject unsafe paths and alias replacement; expose a read-only view.
- **PR #114** — wire the PDF ingestion service and source registry into `AgentRuntime`, with fail-closed behavior when ingestion is not configured and tests that untrusted request metadata cannot register trusted PDF sources.

Current known implementation boundaries:

- Trusted local PDF ingestion and the runtime source registry are wired, but a unified, user-facing PDF -> extracted facts -> validated quote task is **not yet complete**.
- The runtime's quote-fact gate validates submitted facts against trusted PDF evidence. A general field extractor that constructs those facts from PDF material is still needed.
- WindowHub still requires validation in the user's actual local environment; GitHub CI does not prove a physical desktop run occurred.
- README documents learned semantic workflows, compact experience memory, NaviMind task reasoning, the knowledge envelope, and the adapter contracts.
- Legacy `app/ai/analyze_pdf.py` and similar scripts have import-time side effects and unsafe placeholder configuration. Treat replacement/deprecation as a separate, tested task; do not re-import these scripts into the runtime as a shortcut.

### Immediate continuation checklist

1. Refresh the current branch head and PR/CI state before making changes.
2. Read this document and `README.md`; consult epic issue #59 for the broad end-to-end workflow and related issues for task-level scope.
3. Continue Phase A with the smallest testable change: connect trusted PDF page extractions to typed facts and exact evidence, with synthetic-PDF tests and fail-closed behavior.
4. Then prepare/run the bounded WindowHub dry-run/local smoke procedure, gathering actual console output from the user wherever physical Windows/WindowHub access is required.
5. Keep changes isolated in a feature branch and submit a PR to `feature/browser-navimind-bridge`; check GitHub Actions and report what was actually tested.
6. Update this checkpoint whenever a PR merges, a milestone changes, or a new blocker is discovered.

### Handoff rules for future ChatGPT sessions

- Start by reading this file and the current README, then re-check live GitHub state. This document is project context, not proof that old commits are still the current head.
- Continue from the latest repository state; do not recreate already merged work.
- Use small, reviewable PRs and tests focused on user-visible guarantees.
- Be explicit about which tests ran in CI, which were simulated, and which require the user's local computer.
- Never imply that background work or physical local testing happened when it did not.
- Keep the user's ultimate goal in view: a useful, learnable, reliable Universal Digital Worker for real office and business work—not merely a set of disconnected demos.
