# Anchor a user interface design in a text specification

## Executive summary

The problem: you want to persist the current state of a user interface design as text, without code, screenshots or pixel mockups. A different team or a coding agent must be able to build it on an unrelated stack and give the same user experience. EARS and breadboarding capture the high level but leave the inside of each screen open.

The recommendation: write the design as a package of markdown files whose primary structure is a closed inventory of places, regions and named states. Each state has a face: what the user perceives, in reading order, with exact strings and rank numbers. Each rule is an EARS statement scoped to a named state, with a stable identifier, a level, a capability mark and an origin. Where two rules can apply to one situation, a first-match decision table decides. A modality-neutral core holds intent; one reviewed sheet for each modality (web, mobile, terminal) holds keys, addresses, token values and permitted adaptations. A fixture with a service double and a controlled clock makes each rule decidable. Public scenarios trace to rules. Held-out probes, written from the reference by a person other than the specification author, stay hidden from implementing agents. A specification version is accepted after a mechanical trigger lint and a cold read by at least three readers plus one reader with no specification. The original implementation stays the reference until a second implementation passes.

The evidence: six experts, each from a different school, wrote a 2,000-word specification of one reference application. Blind readers who never saw the application answered held-out questions from each specification alone. All six formats scored 39 to 40 of 40 on two independent question sets; a reader with no specification scored 14 and 17. The only wrong answers came from one conflict between two rules. State scope and first-match tables are designed to prevent that conflict. The published research points the same way. Independent builds diverge on behavior between regions of state. In one preprint, a rule inside a decision table was followed more often than the same rule as prose. Independent agent builds share defaults, so agreement among them proves little.

The main limits: both question sets hit a ceiling, so the experiment shows that writing decisions down works and does not rank notations. Nobody has built a port from the consensus format yet, and nobody has measured its authoring and review cost. No published study implements one text specification on unrelated stacks and compares the user experience. Text does not capture composition, visual weight, motion feel or continuous interaction such as drag and scroll physics.

## Context

You build software with LLM coding agents from human-curated markdown specifications in a git repository. People review the specifications in pull-request diffs and mostly do not review implementation code. Tests are human-reviewed. Held-out evaluation scenarios are plain text in the same repository. You write requirements in EARS syntax with ASD-STE100 controlled English. The domain is regulated (clinical-trial software), so each requirement needs a stable identifier and a trace to verification. A design usually exists first as a working implementation that was built iteratively with agents.

Six researchers studied the literature in six tracks:

- model-based user interface engineering;
- behavior specification formalisms;
- interaction-design documentation methods and human-factors standards;
- design systems, tokens and accessibility semantics;
- text formats from the LLM era;
- cross-stack verification and conformance.

A panel of six experts then proposed formats and specified a reference application in each format. Blind readers tested the specifications, and the experts debated nine motions in two rounds. A moderator wrote up the consensus.

The reference application is Tessera, an image browser of about 800 lines in one file. It has a catalog with filtering, a category grid with infinite scroll and sorting, and an image view with editable tags. It stands in for "the current state of a design".

## Problem statement

Find a text form for a user interface design that meets these conditions:

- It anchors the design: a reviewer can see in a diff when a user-visible decision changes.
- It needs no code, screenshots or pixel-perfect mockups.
- An implementer can build from it alone and give the same user experience. The target can be a different web framework, a native mobile toolkit or a terminal user interface.
- It can be extracted from an existing implementation.
- It fits EARS, controlled English, stable identifiers and traceability to verification.
- It defines "the same user experience" in a way that a check can decide.

## Glossary

Each term below has one meaning in this report.

- *Place*: a top-level view that a user can navigate to, for example the catalog, a category or an image.
- *Region*: a part of a place, or of the whole application, that holds its own state. Examples: the grid, the tag list, a notice area.
- *State*: a named condition of a region that a user can tell apart from its other conditions, for example `Category.MoreFailed`. State names are identifiers.
- *Face*: the description of what the user perceives in one state. It lists content items in reading order, each with a rank number, an emphasis mark and exact strings.
- *Rank*: a number on a content item. A build without enough room drops the item with the highest rank number first. Rank is separate from reading order.
- *Closed inventory*: the rule that an item that no face lists does not exist. A trigger with no rule keeps the platform default.
- *Rule*: one EARS statement scoped to a state. It has an identifier, a level (must or should), a capability mark such as `[pointer]`, and an origin (where it came from).
- *Frame rule*: the convention that a rule changes only what it names.
- *Decision table*: a first-match table for a trigger or region that two or more rules could claim. The first matching row wins, and the last row is "otherwise".
- *Memory table*: a table that gives the fate of each region under a step, Back or Forward, reload and direct address.
- *Timeline*: the states of one request with time marks (`@250` for 250 ms): start, slow, success, failure, retry, abandoned.
- *Property*: an "Always" or "Eventually" statement about the whole application, which names the faults under which it holds.
- *Data rule*: a rule on data (normalization, formats, ordering) with example values from the fixture.
- *Task*: a user goal with a start state, steps, an outcome and a step count. One step is one user intention, not one key press or tap.
- *Layout intent*: a word that names a layout relationship without coordinates, for example stack, cluster, grid with a minimum tile width, pinned, far end.
- *Presentation commitment*: an appearance statement that exists only where the experience depends on a concrete value. It has a level and a check method (outline, token or inspection).
- *Modality sheet*: one reviewed file for each modality (web, native mobile, terminal). It holds key and gesture bindings, addresses, token values, sizes, thresholds, permitted adaptations and changed step counts.
- *Fixture*: a fixed data set plus a *service double* (a stand-in for the back end) with deterministic latency, injected faults and a controlled clock.
- *Scenario*: a public, Given-When-Then check that cites the rule identifiers it verifies and asserts only what the user perceives.
- *Probe*: a held-out question or check in the same form as a scenario. A person other than the specification author writes it from the reference. Implementers never see it.
- *Adapter*: the code that fires intents, advances the clock and observes a build on one stack. It holds no expectations.
- *Closure check*: a check that a build shows no places, states or content items outside the inventory, and none missing.
- *Trigger lint*: a mechanical check that groups rules by state and trigger. It fails when two rules claim one trigger without a table or an "overrides" reference.
- *Cold read*: an acceptance step. Readers who never saw the application answer the probe bank from the specification alone and list their guesses and contradictions.
- *Control reader*: a cold reader who has no specification. A probe that the control answers correctly marks a decision that convention carries.
- *Double extraction*: two independent extractions of the same place into the same slots, compared line by line.
- *Re-derivation audit*: a periodic step. Several fresh implementers build from the specification, and a control build gets only the inventory. The probes run on the reference, the builds and the control.
- *Reference oracle*: the original implementation, used as the source of truth until a second implementation passes all scenarios and probes.
- *Determinacy*: the share of design decisions that all conforming implementations resolve the same way.

## What the research shows

The literature agrees on where the line between experience and implementation lies, and on where independent implementations diverge. It has no controlled study of the exact problem. The sections below separate peer-reviewed work, standards, preprints, vendor claims and practitioner reports.

### Independent builds diverge on behavior between regions of state

The strongest result on your exact test is a negative one. Quickstrom (peer-reviewed, PLDI 2022) checked 43 independent TodoMVC implementations of one short prose specification. Against a temporal-logic specification, 20 had faults ([O'Connor and Wickström 2022](https://arxiv.org/abs/2203.11532)). TodoMVC fixed appearance with shared CSS and a template, so appearance matched ([TodoMVC app-spec.md](https://github.com/tastejs/todomvc/blob/master/app-spec.md)). Behavior diverged where the prose was thin. In 4 implementations an unrelated action cleared in-progress input. In 2, an added item changed the filter. In 1, edit did not move focus ([O'Connor and Wickström 2022](https://arxiv.org/abs/2203.11532)). The authors call the prose specification ambiguous and underspecified.

Most of these faults were side effects on state that the triggering action should not touch. The behavior track therefore concluded that "what does not change" needs to be written down. Practitioner sources converge on a checklist of forgotten states. Each screen has ideal, loading, empty, partial and error states ([Hurff 2015](https://www.scotthurff.com/posts/why-your-user-interface-is-awkward-youre-ignoring-the-ui-stack/)). Users expect Back to restore filters, sorts and "load more" positions ([Baymard 2020](https://baymard.com/blog/back-button-expectations)).

No single behavior notation covers the whole problem. Statecharts, transition tables and Elm-style models fix modes, events, guards and timers. Concept specifications, Gherkin examples and temporal properties fix observable outcomes. None of them states what the user perceives, so that layer must be added. Flat tables grow with the product of independent variables; hierarchy and parallel regions keep growth closer to additive. LLMs are weak at writing formal behavior specifications unaided. Across 30 models and 205 TLA+ specifications, the best semantic correctness was 8.6% (preprint, [Bisharat et al. 2026](https://arxiv.org/abs/2606.05792)).

### Abstract models carry intent but not quality

Model-based user interface engineering separated four levels: tasks and domain, abstract user interface, concrete user interface, and final code. By W3C definition the concrete level is toolkit-independent and bound only to a modality ([W3C MBUI Glossary](https://www.w3.org/TR/mbui-glossary/)). The W3C incubator group advised standardizing meta-models and semantics, not one syntax ([W3C MBUI XG Final Report](https://www.w3.org/2005/Incubator/model-based-ui/XGR-mbui-20100504/)).

Automatic generation from abstract models got little industrial use. A review by three leaders of the field states that "the usability of automatically generated UIs is rather low" ([Meixner, Paternò, Vanderdonckt 2011](https://www.degruyterbrill.com/document/doi/10.1524/icom.2011.0026/pdf)). The causes they list attach to automatic generation and tool lock-in, not to the idea of describing a user interface at several levels. In the one measured industrial trial, five Motorola developers used TERESA: design time nearly doubled and prototyping time roughly halved ([Mori, Paternò, Santoro 2003](https://openportal.isti.cnr.it/data/2003/160174/2003_160174.pdf)). The strongest controlled result is narrow. Generated appliance interfaces on a handheld made users faster and more successful than the appliances' own interfaces ([Nichols, Chau, Myers, CHI 2007](https://research.ibm.com/publications/demonstrating-the-viability-of-automatically-generated-user-interfaces)).

Safety-critical domains fix a contract, not a picture. ARINC 661 fixes a closed widget catalog and a runtime protocol; appearance belongs to the display implementer ([Aviation Today 2017](https://interactive.aviationtoday.com/glass-screens-and-widgets-unseen/)). It is flown on the A380, A350 and 787. This is strong evidence that a behavior contract can survive independent implementers, and no evidence about look.

### Interaction-design methods state layout intent without pixels

More than a dozen methods record purpose, objects, content and priority first and leave rendering to the builder. Essential use cases describe what users need with no presupposed widgets. Priority guides sort content from most to least important ([van Nues and Overkamp 2018](https://alistapart.com/article/priority-guides-a-content-first-alternative-to-wireframes/)). These methods state layout intent through rank order, grouping, containment, relative emphasis and named patterns. Evidence for them as handoff documents is thin and mostly anecdotal.

One peer-reviewed study of designer-to-developer handoff (16 professionals) found three breakdowns: missing information, edge cases and unknown technical constraints ([Maudet et al., CSCW 2017](https://www.academia.edu/96507386/Design_Breakdowns)). It recommends that descriptions move from concrete examples to rule-based, complete specifications.

IEC 62366-1 makes the user interface specification one step in a chain. The chain runs from use specification through hazard-related use scenarios to evaluation ([IEC 62366-1 preview](https://assets.vde-verlag.de/iec-normen/preview-pdf/info_iec62366-1%7Bed1.1%7Db.pdf)). The FDA content guidance (final May 2026) asks for a task identifier that links each risk-analysis row to validation ([FDA content guidance](https://fda.gov/media/163694/download)). The EMA guideline for computerised systems in clinical trials asks that each user requirement link to test cases. The link must stay current, and test cases must be pre-approved ([EMA guideline 2023](https://www.ema.europa.eu/en/documents/regulatory-procedural-guideline/guideline-computerised-systems-and-electronic-data-clinical-trials_en.pdf)). That guideline does not mention user interface requirements.

### Design systems and the accessibility tree carry vocabulary and structure

The Design Tokens Community Group format reached its first stable version, 2025.10, on 28 October 2025 ([W3C DTCG announcement](https://w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/)). It is a Community Group report, not a W3C standard. Tokens express named, typed visual values and their variants for each theme or mode. They do not express structure, behavior or layout relationships.

An ARIA Authoring Practices pattern is a compact text contract: roles, states and a key-by-key table ([APG Tabs pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/)). Four independent behavior-only libraries arrived at the same tabs options and nearly the same key map. They diverged where the pattern marks behavior optional or says nothing. The pattern guide is silent on touch and pointer behavior.

The accessibility tree (role, name, state, value, order) is a stack-neutral description of structure. Its mappings to the accessibility API of each desktop operating system are specified ([Core-AAM 1.2](https://www.w3.org/TR/core-aam-1.2/)). Playwright serializes it as YAML for tests ([Playwright ARIA snapshots](https://playwright.dev/docs/aria-snapshots)). Its MCP server gives the same tree to LLM agents in place of screenshots ([Playwright MCP](https://github.com/microsoft/playwright-mcp)). It omits appearance, geometry, emphasis, density and timing by design.

Cross-platform design systems do not define sameness as identical pixels. They hold constant the purpose of components, information architecture, content, token roles and emphasis hierarchy. They let controls, navigation chrome, gestures, scroll physics and density follow the host platform ([Fluent 2 design principles](https://fluent2.microsoft.design/design-principles)). A shared vocabulary for layout intent exists, for example the 13 primitives of Every Layout ([Every Layout](https://every-layout.dev/)). No vendor-neutral, machine-readable standard for layout intent was found.

### LLM-era formats cover look or structure, rarely behavior

Three families of text format exist, and none covers a whole design in stack-neutral, reviewable text:

- Spec-driven development toolkits structure requirements, design and tasks. Examples are GitHub Spec Kit and AWS Kiro ([Böckeler 2025](https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)), OpenSpec and BMAD. None supplies a structure for user interface content; BMAD's front-end templates come nearest. Kiro writes system behaviors in EARS ([Kiro design-first](https://kiro.dev/docs/specs/feature-specs/tech-design-first/)). OpenSpec keeps only externally observable behavior in the specification ([OpenSpec concepts](https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md)).
- Agent design files, such as Google's DESIGN.md, capture visual identity and component styling as tokens plus prose ([DESIGN.md README](https://cdn.jsdelivr.net/gh/google-labs-code/design.md@main/README.md)). They do not capture behavior or flows.
- Declarative runtime representations such as A2UI capture structure, data binding and events against a component catalog and leave styling to each renderer ([a2ui.org](https://a2ui.org/)). Neither A2UI nor json-render publishes a study of experience equivalence across renderers.

Research on regeneration fidelity is almost all visual similarity on single web screens. Inside each study that tests one, a structured intermediate representation beats direct prompting. Examples are SpecifyUI ([arXiv 2509.07334](https://arxiv.org/html/2509.07334v1)) and DeclarUI, where a page-transition graph raised transition coverage on React Native to 88.6% to 96.8% ([arXiv 2409.11667](https://arxiv.org/html/2409.11667v1)). Interactive behavior is reproduced worse than static content ([Interaction2Code](https://arxiv.org/html/2411.03292v3)). Code or text input beats screenshots for precise edits ([DesignBench](https://arxiv.org/html/2506.06251v3)). All of these are preprints.

Practitioner reports on agent-built designs name five things that work. They are a constrained vocabulary, checkable oracles, a compilable reference implementation, short context files and an independent evaluator. Reported failures include one large instruction file, prose-only layout, screenshots as the only context, and agent self-evaluation ([OpenAI harness engineering](https://openai.com/index/harness-engineering/); [Anthropic frontend skills](https://claude.com/resources/articles/improving-frontend-design-through-skills)). None of these reports is controlled.

### Conformance suites and independent implementations make text converge

Standards bodies get independent implementations to converge with a normative text and a shared public test suite. A specification is not finished until independent implementations interoperate ([W3C Process Document](https://www.w3.org/policies/process/)). The combined Interop 2025 score rose from 25 to 95. The 2026 write-up reports that tests written against one implementation were themselves a source of divergence ([Mozilla Hacks 2026](https://hacks.mozilla.org/2026/02/launching-interop-2026/)). ACT Rules Format 1.1 (W3C Recommendation, February 2026) states each test rule in plain language. Each rule has passed, failed and inapplicable examples ([ACT Rules Format 1.1](https://www.w3.org/TR/act-rules-format/)).

In 2026, three preprints applied N-version ideas to coding agents. A replication of the Knight-Leveson experiment with 69 agent configurations found 429 coincident failures against about 115 expected under independence ([Ron, Baudry, Monperrus](https://arxiv.org/html/2606.20158)). Most clustered on two weak requirements. A formal study defines the determinacy of a specification and requires a no-specification control ([Grynets et al.](https://arxiv.org/pdf/2608.19475)). In its benchmark, a full specification left three-implementer agreement almost unchanged (83.1% to 83.8%), yet divergence surfaced twelve gaps. Three of them were hard defects that review missed. The same rule had 23% compliance as a trailing paragraph and 42% inside a decision matrix. The authors note that this effect came mainly from one implementer.

The only case study with a user interface is Jas (preprint, one developer). Five ports of a vector illustration application were built from one shared YAML specification of about 23,000 lines ([Jas, arXiv 2606.07828](https://arxiv.org/html/2606.07828)). Divergence between ports exposed five specification gaps, mostly in degenerate cases and commit timing. The coding assistant resolved ambiguity silently, so gaps surfaced late. Visual and timing comparison was manual and was the largest remaining cost.

Industrial ports in 2026 used the existing implementation, not a written specification, as the reference. Shopify's agents first wrote down the behavior of the React Native app, and engineers approved it before native code was written ([Shopify Engineering](https://shopify.engineering/shop-app-migration)). Language-independent conformance tests are the portable anchor outside user interfaces. With such tests, Willison finds it "pretty astonishing how far today's coding agents can take you" ([Willison, January 2026](https://simonwillison.net/2026/Jan/10/a-software-library-with-no-code/)).

On held-out scenarios, StrongDM often keeps end-to-end scenarios outside the codebase because in-repository tests can be rewritten to match the code ([StrongDM](https://factory.strongdm.ai/)). A pattern catalog states that placing holdouts in the repository does not by itself establish independence ([AgentPatterns](https://agentpatterns.ai/factory-engineering/acceptance-scenario-lifecycle/)). No factory write-up describes verification of a user interface.

### Experience equivalence has measures but no validated definition

Most dimensions of "same experience" have an established measure. The keystroke-level model predicts expert task time from a task script ([Kieras 1993](https://www.cs.umd.edu/~golbeck/INST631/KSM.pdf)). Step counts come from shortest paths in a state model. Response-time limits of about 0.1 s, 1 s and 10 s give feedback classes ([Nielsen 2010](https://www.nngroup.com/alertbox/response-times.html)). Order of information can be checked with an accessibility-tree snapshot on the web. Task success and the System Usability Scale need people.

LLM judges of user interface quality agree with experts less than experts agree with each other. On WebDevJudge (ICLR 2026), the best model judge agreed with human preference 70.34% of the time against 84.56% between humans ([WebDevJudge](https://arxiv.org/html/2510.18560v2)). The judges also rejected functionally equivalent implementations that differed literally from the rubric. This failure mode matters when a web build and a terminal build are compared.

### Where no evidence was found

The researchers searched for each item below and found nothing. Several searches were cut short (see the research limits section), so absence is not proof of absence.

- No controlled study implements one text specification on unrelated stacks and compares the resulting user experience.
- No study gives coding agents the same user interface behavior in different specification formats (statechart, table, Gherkin, prose, EARS) and measures behavioral fidelity.
- No peer-reviewed definition or validated threshold of cross-implementation experience equivalence exists, and no metric for it is proposed.
- No study measures the completeness of a design specification extracted from a running application against ground truth.
- No research covers text-specified terminal user interfaces, or accessibility trees in terminal toolkits.
- No study measures human review accuracy on diffs of state tables or statecharts.
- No source tests whether users perceive platform-adapted variants as the same product.
- No practitioner account applies held-out scenarios to a user interface.

### Strength of the evidence

The table classifies the main findings that the recommendation uses.

| Finding | Source | Kind |
| --- | --- | --- |
| 20 of 43 TodoMVC builds diverged on behavior between regions of state | [O'Connor and Wickström 2022](https://arxiv.org/abs/2203.11532) | Peer-reviewed |
| Handoff breaks on missing information, edge cases and constraints | [Maudet et al. 2017](https://www.academia.edu/96507386/Design_Breakdowns) | Peer-reviewed |
| Generated interfaces had low usability; abstract levels under-determine quality | [Meixner et al. 2011](https://www.degruyterbrill.com/document/doi/10.1524/icom.2011.0026/pdf) | Peer-reviewed review |
| LLM judges agree with experts below expert-to-expert agreement | [WebDevJudge](https://arxiv.org/html/2510.18560v2) | Peer-reviewed (conference poster) |
| Normative text plus shared tests plus interoperating implementations | [W3C Process](https://www.w3.org/policies/process/); [ACT Rules 1.1](https://www.w3.org/TR/act-rules-format/) | Standard |
| Requirements linked to pre-approved test cases | [EMA 2023](https://www.ema.europa.eu/en/documents/regulatory-procedural-guideline/guideline-computerised-systems-and-electronic-data-clinical-trials_en.pdf) | Regulatory guideline |
| A rule in a decision matrix is followed more often than in a paragraph | [Grynets et al.](https://arxiv.org/pdf/2608.19475) | Preprint |
| Agent implementations fail together | [Ron, Baudry, Monperrus](https://arxiv.org/html/2606.20158) | Preprint |
| Divergence between ports exposes specification gaps | [Jas](https://arxiv.org/html/2606.07828) | Preprint, one developer |
| Structured representations beat direct prompting | [DeclarUI](https://arxiv.org/html/2409.11667v1); [SpecifyUI](https://arxiv.org/html/2509.07334v1) | Preprints |
| Holdouts outside the codebase resist test gaming | [StrongDM](https://factory.strongdm.ai/) | Practitioner |
| Reference implementation as anchor for ports | [Shopify](https://shopify.engineering/shop-app-migration) | Practitioner |
| Tokens, design files and catalogs carry look and structure | [DTCG](https://www.designtokens.org/tr/2025.10/); [DESIGN.md](https://cdn.jsdelivr.net/gh/google-labs-code/design.md@main/README.md) | Standard draft, vendor |

## The blind-read experiment

The experiment tested if a 2,000-word text specification carries the design decisions of Tessera to a reader who never saw it. It did not build any implementation.

### Design

Each of the six experts wrote one specification of Tessera in a different format. Each file had a hard limit of 2,000 words, and all six used 1,990 to 1,999. One blind reader per format answered 40 questions about user-visible behavior and appearance from that file alone. A seventh reader answered from convention and a one-paragraph description of the application (the baseline).

Two question sets were used:

- Set A: 40 questions and a key written by the author of the reference application. The key flags 22 questions as decisions that differ from common convention.
- Set B: 40 questions and a key written independently from the code by a different author. The questions stay hidden from the experts. The key flags 29 questions as convention-breaking.

Each answer was graded 1, 0.5 or 0 against the key. Readers also tagged each answer STATED, DERIVED or GUESS. The tags were recorded and not used in grading. The eight areas were content and structure, navigation and history, empty and failure states, keyboard, state and memory, timing and feedback, data rules, and appearance.

### Results

The six formats tied near the maximum on both sets, far above the baseline.

| Format | Set A (of 40) | Set B (of 40) |
| --- | --- | --- |
| Behavior modeling | 40 | 40 |
| Usage-centered interaction design | 40 | 39.5 |
| Semantic contract and design system | 39.5 | 39.5 |
| Conformance engineering | 39 | 39.5 |
| Regeneration empiricism | 40 | 40 |
| Wild card (narrated transcripts) | 39 | 40 |
| No specification (baseline) | 14 | 17 |

Other results from set A:

- Of 207 answers tagged STATED across the six formats, none was graded 0.
- The only two wrong answers were on one question (question 8), in the conformance and wild-card files. Both were tagged DERIVED. The question asks what shows when a user follows a direct link to an image and then uses the up control.
- Four of the six files carried the same conflict. A general rule for arrival in a place stood against a specific rule for return to the grid. Their readers split two to two. The reference loads the grid through the image's batch and focuses its tile on every route.
- The interaction-design file was the only one whose reader reported no conflict on question 8. It used scope words ("by any route", "In all other cases"). It was also the only file that ranked the texts of a catalog row. Its reader was the only one to answer question 40 (prominence) from a statement.
- The key's convention flags mispredicted the baseline on 12 of 40 questions. The baseline got four flagged questions right and eight unflagged questions wrong. About one third of each format's gain over the baseline was on decisions that the key did not flag.
- Where a file was ambiguous, the reader fell back to convention. Both wrong answers matched the baseline answer.

Set B had no confident-wrong answer in any format. No question was missed by more than two formats.

### What the readers could not answer

Each reader listed 11 to 16 ambiguities or contradictions in the file, and five guesses. All six readers named the same four gaps:

- The place and update date of an empty category in the catalog order.
- An error notice that "stays until answered" against a rule that navigation closes notices.
- Where focus goes when Escape leaves a field.
- A return to an image tile beyond the loaded batches.

All six readers also listed geometry and fixture content (category names, image data) as guesses. The scorer attributes these common gaps to the word limit and to the decisions themselves, not to any one notation.

A check for stack vocabulary found that all six files assumed a desktop browser. They assumed Back and Forward, a pointer that can hover, and a Tab key. Two files gave web addresses as paths without the hash form that the reference uses. That is a statement that contradicts the reference, and no question tested it. The conformance file was the only one with capability marks such as `[pointer]`.

### Caveats and what the experiment does not show

Report these results with their limits:

- Both sets are at the ceiling. They separate the formats from the baseline and do not rank the formats. A difference of one point is inside the noise.
- One author and one reader per format: notation, author skill and reader habit cannot be separated. Tagging varied by reader; the same content drew STATED from one reader and DERIVED from another.
- The questions favor detailed behavior. They barely test layout, visual finish or fixture data.
- The author of the reference wrote set A, and a second author wrote set B from the code. Each set tests only the decisions that its author knew or found.
- The reference source had comments that named some decisions. Examples from those comments ("Golden Hour" gives "golden-hour"; "-9 before -10") appear in all six files and in two questions.
- The baseline reader had a one-paragraph description that the scorer did not see. Some baseline answers quote interface text exactly and may rest on it.
- The experiment measures if a reader can answer from the text. It does not measure if a build on another stack matches the reference. It does not measure cost to write and review, or behavior under change.

The panel accepted the main conclusion: writing the decisions down produced the gain, not the notation. The debate then turned to properties that the blind read cannot see: conflict resistance, completeness, convention, verification, modality and maintenance.

## The debate

Six experts each argued one school at full strength. They cross-examined each other's proposals in round 1 and rebutted and voted in round 2. In round 2 they also voted on five merged options from the moderator.

### Six schools and their starting positions

| School | Starting thesis | Main change by round 2 |
| --- | --- | --- |
| Behavior modeling | Experience is behavior over time: state models, rules on named states and events, application-wide properties. | Dropped key names from triggers; scenarios assert faces, never state names; total transition table became an authoring worksheet. |
| Usage-centered interaction design | Experience is the conceptual model, the tasks and the priority of content, with named patterns and principles. | Principles became non-normative notes; rank became a number apart from reading order; kept the task layer. |
| Semantic contract and design system | A closed vocabulary of components with fixed semantics, view trees, tokens and layout intent; the accessibility tree is the oracle. | Web role names moved to the web sheet as bindings of role concepts; behavior moved under named states and owner tables. |
| Conformance engineering | Prose anchors nothing; a conformance suite with identifiers, scenarios, a fixture and budgets does. | Accepted a closed inventory and the task layer; Fail lines must come from an observed wrong build or be marked unconfirmed. |
| Regeneration empiricism | Write only what a competent implementer would get wrong, found by re-derivation against a baseline of conventions. | Gave up the unwritten baseline after both blind reads; minimization demotes rules to an appendix and never deletes them. |
| Wild card | Write the experience as second-person narrated play-throughs (golden transcripts) plus an executable text twin of the application. | Moved transcripts out of the specification into regenerated recordings; dropped the twin as an oracle; kept the independent probe author. |

Several ideas from the wild-card proposal survived:

- `@` time marks inside timelines.
- Plain words in place of stack terms, for example "pinned" for sticky.
- Frozen reference recordings as the regression oracle.
- A probe bank written independently of the specification author.

The wild card also supplied the strongest dissent (see the dissent section).

### How positions changed

The blind read removed the case for any one notation. All six experts then moved toward state scope, first-match tables and a cold-read gate. These changes moved the most votes:

- Rule conflicts (M8). In round 1, four experts preferred the cold-read conflict check, one preferred a total transition table, and one proposed owner decision tables. The behavior modeler gave up the total table after the interaction designer estimated several hundred rows for Tessera.
- Acceptance (M6). The interaction designer argued that on a phone or terminal many must-level verdicts become "inapplicable", and only a task says what the adaptation must keep. All six then signed layered acceptance with a task layer.
- Oracle (M7). Five experts argued that a maintained executable model is a second implementation that nobody reviews. The behavior modeler changed to the reference-implementation option.
- Convention (M3). The regeneration empiricist conceded that a baseline of unwritten conventions belongs to one modality and fails on a new stack. The conformance engineer moved from "state everything" to a closed inventory, because "state everything" has no stopping rule.

### Votes on the nine motions

Votes come from round 2. For a chosen option the count is prefer, accept, object. For a merged option it is sign, sign with amendment, object.

| Motion | Decision | Vote | Main reason |
| --- | --- | --- | --- |
| M1 Primary structure | Places, regions and named states, each with a face | 6, 0, 0 | Both set A errors sat on a situation that two rules claimed; a state scope shows it. |
| M2 Completeness | Merged: matrix and checklist at authoring; cold-read gate; re-derivation audit; double extraction for the first version | 2, 4, 0 | Cold readers found 11 to 16 ambiguity items in each file that analysis had produced. |
| M3 Convention | Closed inventory; rules where an implementer could go wrong | 6, 0, 0 | Judgment mispredicted the control on 12 of 40 questions. |
| M4 Appearance | Merged: tokens, layout intent and emphasis ranks, plus presentation commitments where a concrete value matters; sketches allowed | 2, 4, 0 | States differ by their faces; appearance departures need identifiers and checks. |
| M5 Rules and checks | Traced scenario files plus held-out probes | 6, 0, 0 | Agents fit visible checks; only hidden probes measure determinacy. |
| M6 Acceptance | Merged: layered acceptance plus a task layer on every stack | 0, 6, 0 | Where verdicts become inapplicable, only tasks say what an adaptation must keep. |
| M7 Oracle | Merged: a fixture always; the original as reference until a second build passes; no executable model | 4, 2, 0 | Timing rules need a shared service double; nobody reviews a model. |
| M8 Rule conflicts | Merged: first-match table where two rules can apply; "overrides" elsewhere; cold read as gate | 3, 3, 0 | A table shows an overlap while writing; a cold reader finds conflicts the author does not know. |
| M9 Modality | Neutral core plus one sheet for each modality | 6, 0, 0 | Keys and addresses bind one modality. |

All six objected to three options. These were narrated walkthroughs as the primary structure (M1 d) and scenarios as the specification (M5 c). The third was one modality-neutral specification with no concrete commitments (M9 a). Five objected to recording only deltas from a named baseline (M3 a).

The amendments that the moderator adopted are part of the format below. They include:

- Double extraction for the first version and each new place.
- A control reader in the gate, and an independent probe author.
- A level and a check method on each presentation commitment.
- One step equals one user intention; tasks never replace a must-level verdict.
- A closure check through an adapter that the implementer under test does not write.
- Frozen recordings before retirement of the original.
- A trigger lint, and one decision table per region with no other rule setting that region.

## The consensus approach

The consensus has two parts: a format (what the files contain) and a process (how a version is extracted, accepted, verified and maintained). The companion file "Tessera worked example in consensus format.md" holds the complete specification of the reference application in this format. The examples below are short excerpts in the same notation. Where the moderator filled a gap that no expert closed, this report says so.

The companion file had one check of its own. One blind reader answered question set B from the companion file alone, and the score was 39.5 of 40. The notes of that reader exposed two contradictions in the file, and both are now corrected. The check has the ceiling limit of the other blind reads. The companion file also had a larger limit (3,000 words), so its score does not compare with the six 2,000-word files.

### Package of files

The specification is a set of markdown files. The file names are a moderator choice.

```text
spec/conventions.md      conformance clause, observation vocabulary, glossary
spec/app.md              chart of places, app-wide regions and tables, properties
spec/places/<place>.md   states, faces, rules and tables of one place
spec/data.md             data rules with example values
spec/tasks.md            task layer
spec/appearance.md       token roles, layout intent, presentation commitments
spec/modality/<name>.md  one sheet for each modality
fixture/                 data set and service double
scenarios/<area>.md      public scenarios
sidecar/matrix.md        state-by-event matrix, not normative
trace.md                 generated trace table
```

Held-out probes are not in this package. They are kept where implementing agents cannot read them.

The conformance clause in `conventions.md` defines the levels, the outcomes and the observation vocabulary. A must-level item is one whose absence can block or mislead a user. The outcomes are passed, failed and inapplicable. The observation vocabulary is: place, text, role concept, name, state, focus, announcement, address, history depth and scroll. Role concepts are stack-neutral words such as up-link, place title or exclusive choice. The frame rule is stated here: a rule changes only what it names.

### Identifiers and writing rules

An identifier is an area code plus a number, and it is never reused. State names are identifiers too. The exact syntax is a moderator choice.

```text
Category.MoreFailed state   CAT.Ready.4 content item   GRD-9 rule   NAV-T1.2 table row
TSK-1 task   DAT-4 data rule   VIS-2 commitment   WEB-5 sheet entry   FIX-6 fixture
```

Writing rules:

- Use one EARS pattern for each rule: `While <state>, when <intent>, <app> shall <effect>`; `If <fault>, then ...`; the ubiquitous form for invariants.
- Name an intent as the trigger. Put keys, gestures and addresses in the modality sheet.
- Write effects with the observation vocabulary. Send focus to a named part or to "none".
- Give each statement one identifier, one level, one capability mark and one origin.
- Write a Fail line only from an observed wrong build or a control reader's answer. Otherwise mark it "unconfirmed".
- Quote text exactly from the reference. Do not normalize literals.
- Cite a public definition for a pattern name, with every option taken, or spell the pattern out once.
- State the value of each derived attribute for zero items.
- Write reasons as non-normative notes.
- Use controlled technical English with no stack words.

### Inventory, states and faces

Each place and each region has a `States:` line. Each state has a face. A face lists the content items in reading order, each with a rank number, an emphasis mark and exact strings. The inventory is closed: an item that no face lists does not exist, and an unlisted trigger keeps the platform default.

```text
Category  States: Empty | FirstLoading | FirstFailed | Grid (Idle | More | MoreFailed | Complete)

Catalog.Ready face (excerpt)           rank  emphasis
  1 title "Catalog"                     2     normal
  2 filter field "Filter categories"    3     normal
  3 count line "24 categories"          4     quiet
  4 rows, one link per category         1     primary
```

The rank column answers a question that reading order cannot. On a narrow terminal, the count line (rank 4) goes first and the rows (rank 1) stay.

### Rules and first-match decision tables

Rules sit under the state that scopes them. A specific rule outside a table names the rule that it overrides.

```text
GRD-9 [must] origin: extracted
  If a later batch fails while Category.More, then Tessera shall keep the tiles and show
  below them alert "Couldn't load more images." with button "Retry".  Fail: scrolling retries.
TAG-6 [must] overrides TAG-3
  While Image.Ready, when a commit reaches 12 tags, Tessera shall focus the last remove control.
```

A trigger or region that two rules could claim gets exactly one first-match table with an "otherwise" row. No rule outside the table sets that region. This table removes the question 8 conflict.

```text
NAV-T1 Arrival in a place. First matching row wins.
  1 first paint after start or reload    focus not moved
  2 Category, directly after its image   load through that image's batch; focus its tile, in view
  3 Catalog, by Back or Forward          restore scroll; focus the row of the category last visited
  4 any other Back or Forward            restore scroll; focus the place title
  5 otherwise                            top; focus the place title
```

### Memory tables, timelines and properties

A memory table gives each region against each navigation event. The consensus file names the table and gives no excerpt. The excerpt below was written for this report from the memory rules in one expert's worked example; it shows three of the four events. The companion file has the full table.

```text
MEM-T1 (excerpt)  step   Back or Forward     reload
  theme           kept   kept                kept
  tag edits       kept   kept                lost
  filter text     kept   from the address    from the address
```

Each request is one timeline with `@` time marks for start, slow, success, failure, retry and abandoned.

```text
GRD-L1 next batch  @250 one placeholder tile per expected image | success: tiles | failure: GRD-9
                   retry: placeholders at once | abandoned: discarded, uses no fault
```

Properties are "Always" and "Eventually" statements about the whole application, for example that one Back from an image always returns to the grid. Each property names the faults under which it holds. A property that no check can fail is deleted.

### Data rules

Data rules sit on data, not on controls, and carry example values from the fixture.

```text
DAT-4 Normalize a tag: trim; lower case; spaces and underscores to one hyphen; drop all
      but a-z, 0-9, hyphen; no double or end hyphens.   "Golden Hour" -> "golden-hour"
DAT-7 Size: from 999,500 bytes one-decimal MB, else whole kB.   2,501,130 -> "2.5 MB"
```

### Task layer

Each task has a start state, steps, an outcome and a step count. One step is one user intention, not one key press or tap. A task never replaces a must-level verdict. It binds where a must-level rule becomes inapplicable on a stack, because it says what the adaptation must keep.

```text
TSK-1 Find a category and open it. Start: Catalog.Ready, no filter.
  Steps: focus the filter; enter "film"; open the only match.  Count: 3
  Outcome: Category "Film Scans", in a new history entry.
```

### Appearance

The core holds three kinds of appearance statement:

- Emphasis ranks, inside the faces.
- Token roles with use notes, for example "accent" and where it may appear.
- Layout intent, in a small vocabulary. Examples: stack, cluster, grid with a minimum tile width, side panel with a collapse threshold, pinned, far end.

Token values and concrete sizes go to the modality sheet. Text sketches are allowed and not required. Until the dissent on layout intent is settled, a sheet may replace a layout-intent word as a listed adaptation (a moderator rule).

Presentation commitments exist only where the experience depends on a concrete value. Each has a level and a check method: outline, token or inspection.

```text
VIS-2 [should] [graphic] Accent only on keyboard focus, the active sort, the duplicate pulse. Check: token.
VIS-5 [should] [graphic] A tile shows the whole image, never cropped. Check: inspection.
```

### Modality sheets

One reviewed sheet for each modality holds bindings, addresses, token values, sizes, thresholds, permitted adaptations and changed step counts. A rule becomes inapplicable on a stack only if that stack's sheet lists an adaptation that keeps the rule's intent.

```text
WEB-1 Address: "#/?q=night", "#/c/coastlines?sort=name", "#/c/coastlines/i/1227".
WEB-5 Intent "step to next image": button "Next"; Right arrow while focus is outside Tags and the notice.
WEB-9 accent #f2b544 / #8a5200 (dark / light). Load margin 400 px.
```

A terminal sheet binds the same intents to keys and replaces "hover" rules with listed adaptations. It can also list a changed step count for a task.

### Fixture

The fixture is a fixed data set and a service double with deterministic latency, faults and a controlled clock. Without it, a timing or failure rule has no decidable verdict. Each value (for example the batch size) is stated once, in the fixture or in the sheet.

```text
FIX-5 Latency: catalog 700 ms (first visit); batch 600 ms; image 150 ms (first open); tag save 500 ms.
FIX-6 Faults, once each: first batch of Film Scans; third batch of every category; save of tag
      "flaky", once per image. An abandoned request uses no fault.
```

### Scenarios and probes

Public scenarios are separate files. Each scenario cites the identifiers that it verifies and asserts only what the user perceives, never a state name. Held-out probes have the same form. A person other than the specification author writes them from the reference.

```text
SCN-GRD-9a verifies GRD-9, FIX-6
Given category Coastlines with 48 tiles. When scroll to end.
Then alert "Couldn't load more images." and button "Retry" and 48 tiles.
When scroll to end. Then no request.
```

### What stays out of the specification

- Framework, DOM, CSS, storage and toolkit terms; internal state; network and cache mechanics.
- Keys, addresses, token values and pixel sizes in the core (they go to the sheets).
- Scenarios, recordings and the state-by-event matrix as normative text. Recordings are regenerated, never edited.
- An executable model beside the text.
- Principles as rules, and pattern names with no cited definition.

### Process: extraction from an existing implementation

1. Freeze the reference. Control its clock and its service. Write the fixture first.
2. Extract twice, independently, into the same slots, and compare. Do this for the first version and for each new place.
3. List events and state carriers. Group them into regions. Name each state that a user can tell apart.
4. Fill the state-by-event matrix. Write each cell as an effect, "nothing", "platform default" or "cannot occur". Treat an empty cell as an open question.
5. Apply the forgotten-state checklist (below).
6. Drive the running application with injected faults. After each action, record strings, focus, scroll, address and history depth.
7. Read the code for constants, focus, history and storage calls, failure branches and literals. Use code as evidence; never cite it.
8. Mark each rule as intended or accidental. Delete the accidents.

The forgotten-state checklist covers:

- Each place: ideal, loading, empty, partial, error.
- Each request: slow, failed, retried, abandoned, late.
- Each region: its fate under step, Back, Forward, reload and direct address.
- Every key in every focus context.
- Each limit at 0, 1, the limit and the limit plus 1.
- Each timer on both sides of its threshold.

On Tessera, step 6 found two behaviors that reading did not. The old screen stays for 250 ms on a change of place. A typed comma commits a tag at once.

### Process: acceptance gate for a specification version

1. Lint. Group rules by state and trigger. Fail two rules on one trigger with no table and no "overrides" reference. Also fail an identifier with no check, and a rule that sets a region that a table owns.
2. Cold read. Give the independent probe bank to at least three readers, people or models from different families. They answer from the specification alone and list guesses and contradictions. Give the same probes to one control reader with no specification.
3. Pass. Every reader answers every must-level probe correctly and alike. A wrong or split answer blocks the version. Close or log each listed ambiguity. A probe that the control also answers marks a decision that convention carries.

### Process: verification on a new stack

1. Write the adapter for the stack. Use role locators on the web, the accessibility tree on mobile, and the character grid plus a semantic dump on a terminal. Review it with the modality sheet. Do not let the agent under test write it.
2. Run the public scenarios, the properties and the closure check, then the held-out probes.
3. Apply layered acceptance:
   - The same verdict on every must-level rule on the fixture, or "inapplicable" with a listed adaptation.
   - Every task with its outcome and step count.
   - Should-level appearance by its check method.
4. Keep the original as the reference until a second build passes the scenarios and the probes. Before retirement, freeze its recordings as the regression oracle.
5. If two builds differ and both pass, change the specification first. Regenerate the trace table.

### Process: re-derivation audit and maintenance

The re-derivation audit runs at each release, and in full for a new stack or a new model generation:

1. At least three implementers in fresh contexts build from the specification. A control build gets only the inventory.
2. Run the probes on the reference, the builds and the control.
3. Classify each mismatch as permitted idiom (add it to the sheet), unclear wording (reword), or a gap (add a rule with its origin).
4. Measure agreement with the reference against the control, not agreement among builds, because agent builds share defaults.
5. Move a rule that every build reproduces untold to an appendix with its probe. Never delete it.

Maintenance follows the same order for every change:

1. Edit the specification first. State each value once.
2. Give a new region a `States:` line and a memory-table row for each navigation event, so the diff shows its decisions. Update the matrix sidecar.
3. The specification author updates the public scenarios. The probe author updates the probes.
4. Run the gate. Use double extraction for a new place.
5. Implement on each stack, verify, and regenerate the trace table. Retire the identifier of a removed rule.

### Fit with your repository workflow

The format keeps your practice of human-curated markdown in git, EARS rules and controlled English. Most of it maps directly:

- Stable identifiers, levels and a generated `trace.md` give the requirement-to-verification trace that the EMA guideline asks for.
- Public scenarios are your human-reviewed tests. Each one cites the rule identifiers it verifies.
- The origin field records where each rule came from. The "unconfirmed" mark shows which Fail lines no build has confirmed. Both support review of regulated changes.
- The gate gives each specification version a recorded acceptance decision before agents implement from it.

The tension is with held-out scenarios. You keep held-out evaluation scenarios as plain text in the same repository. The panel requires that held-out probes stay hidden from implementing agents. The research supports the panel. StrongDM often keeps scenarios outside the codebase because a test inside it can be rewritten to match the code. The AgentPatterns catalog states that a holdout in the repository is not independent by location alone; enforcement must come from a separate control.

We think the following resolves the tension without loss of traceability. This is our suggestion, not a panel decision:

- Keep public scenarios in the specification repository, as now.
- Keep held-out probes as plain text in a path that the agents' sandbox cannot mount or read. The path can stay in the same repository, for example excluded from the checkout that the agents get. A separate repository is the stronger control. Give reviewers and auditors read access; give implementing agents none.
- Give each probe an identifier (`PRB-`) and cite the rule identifiers it verifies, as scenarios do.
- For each gate run, record in the main repository the probe bank revision and a hash of the probe files. Also record the readers, the results and the open ambiguities.
- Have someone other than the specification author write and pre-approve the probes. This matches the EMA requirement for pre-approved test cases and the panel's independence rule.

"Hidden" means hidden from implementers. It does not mean hidden from reviewers or auditors.

## How to start

Start small, on one place of your own design, and measure before you adopt the full package.

### First step on one place

1. Choose one place with real state: loading, failure, history and keyboard behavior. A list or grid view is a good candidate.
2. Freeze the current build. Write a fixture for that place with fixed data, latencies and one fault of each kind.
3. Write the `States:` line, one face for each state with rank and emphasis, and the rules under each state. Use your existing EARS and controlled English.
4. Find each trigger that two rules could claim, for example arrival in the place. Write one first-match table for it.
5. Write the memory-table rows for the place, and one timeline for each request.
6. Put keys, addresses and token values in a web sheet. Keep the core free of them.
7. Ask a colleague to write 20 to 30 probes from the running build, without reading your specification. Keep them outside the agents' reach.
8. Run the cold read: three readers from different model families or people, plus one control reader with no specification.
9. Fix each wrong or split answer and each listed ambiguity. Run the cold read again.

The panel's open validation experiment is the natural second step. Have an agent build the same place on a different stack (for example a terminal user interface) from the text alone. Score it against the reference with the probes, and record authoring and review time.

### What to measure

- Probe score of each reader against the control reader. The difference shows how many decisions the text carries that convention does not.
- Number of wrong or split answers on must-level probes. The gate needs zero.
- Number of ambiguity items that each reader lists, before and after revision.
- Number of Fail lines marked "unconfirmed".
- Hours to extract, write and review the place, and hours for the probe author.
- For the port: the share of must-level rules with the same verdict on the fixture.
- For the port: the share of tasks with the same outcome and step count.
- For the port: the count of rules made inapplicable, with and without a listed adaptation.
- Number of layout-intent words that the port's sheet had to replace. This number informs the open dissent on layout intent.

## Fit with EARS and breadboarding

EARS stays as the sentence form of every rule. The consensus format closes the two open slots. The "While" slot takes a named state from the inventory. The "When" slot takes an intent from a closed list. EARS does not say which rule wins when two rules apply, how strings and ranks appear, or how a rule is verified. The format adds state scope, first-match tables, levels, capability marks, origins, "overrides" references and a trace to checks.

The breadboard stays as the chart of places, affordances and connections in `spec/app.md`. A breadboard deliberately leaves the inside of each place open. The format adds that inside. It adds named states, faces with rank and exact text, memory, timelines, data rules and tasks. It also adds appearance, modality sheets, a fixture and a verification process.

The breadboard says where a user can go. EARS says what the application shall do. The new parts say in which state, what the user perceives, which rule wins and how a build proves it.

## Dissent, open questions and limits

### Unresolved disagreements

Each item names the evidence that would settle it.

- Layout intent: in the core (semantic contract) or in the modality sheet (behavior modeling, and interaction design in round 1). Settle it by counting the layout-intent words that a terminal port and a mobile port must replace.
- The state-by-event matrix: the behavior modeler wants it reviewed; the regeneration empiricist and the interaction designer object to a reviewed total matrix. Settle it by reviewing one change request (for example a new Search place) with and without the sidecar.
- The pass criterion: the wild card asks that all readers tag every must-level probe STATED. Tagging varies by reader. Settle it by repeating the gate with more readers.
- Cost and validity. The wild card states that nobody priced the machinery and that the gate uses the instrument that ranked nothing. Every claim about compliance, modality and change is still a prediction. Settle it with one agent-built terminal port from the text alone, scored against the reference, with authoring and review time recorded.
- Relativity to implementers: a rule chosen by experiment depends on who builds. Settle it with audits on two model generations.
- The frame rule decides unwritten cells silently. Settle it with change requests that add a region.
- After retirement of the original, which build is the reference for a design change. No expert addressed this.
- A new design with no implementation has no reference from which to write the probe bank.

### What a text specification does not capture

All six experts accept these limits:

- Composition, spacing rhythm and visual weight beyond rank and emphasis.
- The feel of motion and of continuous interaction, such as drag and scroll physics.
- How several timers interleave.
- Learning and satisfaction, which need validation with users.
- Accidents of the reference that triage misses.
- The up-front cost of a fixture, adapters and scenarios before the first verdict.

The research agrees. Sources say text handles layout gestalt and dynamic behavior worst. Practitioners add companion artifacts and evaluate the built result.

### Limits of this research

- The shared web-search budget ran out part-way through. Several planned searches were not run. These include venue-specific searches of EICS, CHI and UIST 2024 to 2026, and a final search for a head-to-head study of specification formats for agents. Searches on undo semantics, native semantics trees (Flutter, Compose, AccessKit), LLM test migration from Android to iOS, and design-system servers were also not run.
- Some primary texts were not read. These include the IEC 62366-1 clause 5.6 wording (paywalled) and the ARINC 661 standard text. Myers, Hudson and Pausch (2000), Constantine (2003) and Horrocks' statechart book were also not read. GAMP 5, 21 CFR Part 11 and ICH E6(R3) were not checked.
- The notes mark several claims UNVERIFIED, for example some conference venues (Design2Code, Interaction2Code) and a multi-framework portability leaderboard whose paper was not found. This report does not use them.
- Many sources are 2026 preprints. One has a date inferred from its arXiv number ([Grynets et al.](https://arxiv.org/pdf/2608.19475)). Jas is a single-developer study with no control group.
- The researchers read some pages as automatic summaries. Check quotes against the sources before publication.
- The experiment had one author and one reader per format, a 2,000-word limit, and question sets at the ceiling.
- Several parts of the recommendation rest on expert judgment only. These are the modality split, the task layer, layered acceptance, double extraction, the gate criterion, retirement and maintenance.

## Constraints, assumptions, exclusions and success criteria

### Constraints and assumptions

- A working implementation exists and can be frozen as the reference. Without it, the probe bank has no source.
- You can build a fixture: a fixed data set and a service double with controlled latency, faults and clock.
- At least three cold readers from different model families, or people, are available. One more reader acts as the control.
- A person other than the specification author can write the probes.
- Implementing agents can be denied read access to the probe store.
- Each target stack has a way to observe user-visible semantics: role locators, an accessibility tree, or a character grid plus a semantic dump.
- Someone other than the agent under test can write the adapter.
- The application is mostly discrete interaction (views, lists, forms, navigation), like Tessera. Applications built on continuous drawing surfaces or gestures need native code beyond the specification, as in Jas.

### Scope exclusions

The approach does not cover:

- Visual composition, spacing rhythm and visual weight beyond ranks, emphasis marks and presentation commitments.
- Motion feel, animation curves and continuous interaction physics.
- Usability validation with users, for example summative evaluation under IEC 62366-1 or FDA guidance.
- Performance budgets beyond the fixture latencies, and security.
- Back-end behavior, APIs and data storage, except where a user can perceive them.
- Brand, tone of voice and content strategy beyond exact strings.
- A complete regulatory argument for clinical-trial software. The approach supplies identifiers, traces and recorded verification; validation planning stays with your quality process.
- New designs that have no implementation yet.

### Success criteria for adoption

These criteria are our proposal. The panel did not set numeric thresholds. Set your own values for the time limits.

- Gate: on the pilot place, all cold readers answer 100% of must-level probes correctly and alike, after at most two revisions.
- Determinacy: each specification reader scores higher than the control reader by at least half of the probe count. Both blind-read sets showed a larger gap (25 and 22.5 of 40).
- Ambiguity: at acceptance, every listed ambiguity item is closed, or logged with an identifier and an owner.
- Lint: zero failures; every must-level identifier has at least one scenario or probe (100% trace coverage in `trace.md`).
- Port: an agent builds the pilot place on a second stack from the text alone. The build gives the reference verdict on 100% of must-level rules on the fixture. Rules marked inapplicable each cite a listed adaptation.
- Tasks: every task on the second stack reaches its outcome within the step count or the bound in that stack's sheet.
- Audit: in each re-derivation audit, builds agree with the reference on more probes than the control build does. Each mismatch is classified within one release.
- Cost: record authoring, probe-writing and review hours for the pilot place. Adopt for further places only if the cost per place stays under a limit that you set before the pilot.
- Change: a design change reaches the specification before the code in every pull request for the pilot place over one release cycle.

## Sources

Peer-reviewed papers:

- [O'Connor and Wickström, Quickstrom, PLDI 2022 (arXiv 2203.11532)](https://arxiv.org/abs/2203.11532)
- [Maudet, Leiva, Beaudouin-Lafon, Mackay, Design Breakdowns, CSCW 2017](https://www.academia.edu/96507386/Design_Breakdowns)
- [Meixner, Paternò, Vanderdonckt, i-com 2011](https://www.degruyterbrill.com/document/doi/10.1524/icom.2011.0026/pdf)
- [Nichols, Chau, Myers, CHI 2007](https://research.ibm.com/publications/demonstrating-the-viability-of-automatically-generated-user-interfaces)
- [WebDevJudge, ICLR 2026 poster (arXiv 2510.18560)](https://arxiv.org/html/2510.18560v2)

Standards, regulatory documents and specifications:

- [W3C Process Document](https://www.w3.org/policies/process/)
- [W3C ACT Rules Format 1.1](https://www.w3.org/TR/act-rules-format/)
- [W3C MBUI Glossary](https://www.w3.org/TR/mbui-glossary/)
- [W3C MBUI Incubator Group Final Report](https://www.w3.org/2005/Incubator/model-based-ui/XGR-mbui-20100504/)
- [Design Tokens Technical Reports 2025.10](https://www.designtokens.org/tr/2025.10/)
- [W3C DTCG stable version announcement](https://w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/)
- [WAI-ARIA Authoring Practices, Tabs pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/)
- [Core-AAM 1.2](https://www.w3.org/TR/core-aam-1.2/)
- [IEC 62366-1 ed. 1.1 preview](https://assets.vde-verlag.de/iec-normen/preview-pdf/info_iec62366-1%7Bed1.1%7Db.pdf)
- [FDA, Content of Human Factors Information in Medical Device Marketing Submissions, 2026](https://fda.gov/media/163694/download)
- [EMA, Guideline on computerised systems and electronic data in clinical trials, 2023](https://www.ema.europa.eu/en/documents/regulatory-procedural-guideline/guideline-computerised-systems-and-electronic-data-clinical-trials_en.pdf)
- [TodoMVC application specification](https://github.com/tastejs/todomvc/blob/master/app-spec.md)

Preprints:

- [Hickey, Jas, arXiv 2606.07828](https://arxiv.org/html/2606.07828)
- [Ron, Baudry, Monperrus, Knight-Leveson replication with coding agents, arXiv 2606.20158](https://arxiv.org/html/2606.20158)
- [Grynets, Kostetskyi, Lyashkevych, specification determinacy, arXiv 2608.19475](https://arxiv.org/pdf/2608.19475)
- [Bisharat et al., LLMs writing TLA+, arXiv 2606.05792](https://arxiv.org/abs/2606.05792)
- [DeclarUI, arXiv 2409.11667](https://arxiv.org/html/2409.11667v1)
- [SpecifyUI, arXiv 2509.07334](https://arxiv.org/html/2509.07334v1)
- [Interaction2Code, arXiv 2411.03292](https://arxiv.org/html/2411.03292v3)
- [DesignBench, arXiv 2506.06251](https://arxiv.org/html/2506.06251v3)

Technical reports and project documentation:

- [Mori, Paternò, Santoro, TERESA report, 2003](https://openportal.isti.cnr.it/data/2003/160174/2003_160174.pdf)
- [Kieras, Using the Keystroke-Level Model to Estimate Execution Times, 1993](https://www.cs.umd.edu/~golbeck/INST631/KSM.pdf)
- [Playwright, ARIA snapshots](https://playwright.dev/docs/aria-snapshots)
- [Playwright MCP README](https://github.com/microsoft/playwright-mcp)
- [Every Layout](https://every-layout.dev/)
- [Fluent 2 design principles](https://fluent2.microsoft.design/design-principles)

Vendor claims:

- [Kiro, design-first specifications](https://kiro.dev/docs/specs/feature-specs/tech-design-first/)
- [OpenSpec concepts](https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md)
- [Google Labs, DESIGN.md README](https://cdn.jsdelivr.net/gh/google-labs-code/design.md@main/README.md)
- [A2UI](https://a2ui.org/)
- [Anthropic, Improving frontend design through skills](https://claude.com/resources/articles/improving-frontend-design-through-skills)

Practitioner reports and trade press:

- [Böckeler, Exploring spec-driven development tools, 2025](https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- [OpenAI, Harness engineering](https://openai.com/index/harness-engineering/)
- [Shopify Engineering, Shop app migration](https://shopify.engineering/shop-app-migration)
- [StrongDM, Software Factories and the Agentic Moment](https://factory.strongdm.ai/)
- [Willison, A software library with no code, January 2026](https://simonwillison.net/2026/Jan/10/a-software-library-with-no-code/)
- [AgentPatterns, Acceptance Scenario Lifecycle](https://agentpatterns.ai/factory-engineering/acceptance-scenario-lifecycle/)
- [Mozilla Hacks, Launching Interop 2026](https://hacks.mozilla.org/2026/02/launching-interop-2026/)
- [Aviation Today, ARINC 661 widgets, 2017](https://interactive.aviationtoday.com/glass-screens-and-widgets-unseen/)
- [van Nues and Overkamp, Priority guides, A List Apart 2018](https://alistapart.com/article/priority-guides-a-content-first-alternative-to-wireframes/)
- [Hurff, the UI stack, 2015](https://www.scotthurff.com/posts/why-your-user-interface-is-awkward-youre-ignoring-the-ui-stack/)
- [Baymard, Back button expectations, 2020](https://baymard.com/blog/back-button-expectations)
- [Nielsen, Website Response Times, 2010](https://www.nngroup.com/alertbox/response-times.html)
