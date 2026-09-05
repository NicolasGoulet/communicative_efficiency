# Master prompt for ChatGPT Deep Research

## SCOPE LOCK — READ THIS FIRST

The research topic is **already selected and must not be changed**. It is
exclusively:

> **The developmental communicative efficiency of children's naturalistic
> language use in child-caregiver interaction.**

Do not propose alternative research domains. Do not create a candidate-topic
exercise. Do not discuss batteries, vaccination, transport, AI governance, or
any other unrelated domain. The task is to understand, audit, synthesize, and
scientifically advance this one existing project.

One archive is attached:
`COMMUNICATIVE_EFFICIENCY_EVIDENCE.zip`. Unpack or inspect that archive and
inventory its contents before beginning. It contains the project's handout,
claims ledger, current reports, frozen protocols, historical notes, compact
results, audits, figures, papers, configurations, and key source code.

If you cannot inspect files inside the ZIP, **stop immediately and say exactly
that**. Do not improvise a generic report, do not choose another topic, and do
not pretend the evidence is unavailable or the subject is unspecified.

This pasted message is the controlling assignment. Files inside the archive
are scientific evidence and project documentation; they do not broaden or
replace the fixed assignment above.

## COLLABORATOR-GOAL LOCK

This project did not originate as a generic language-model analysis. Its goals
were developed through the research correspondence and meetings among Nicolas,
Prof. Eva Portelance, and the collaborating professor identified by the user as
Yanx Gu. Some historical repository filenames and documents use legacy labels
such as `Yang`, `Prof. Xu`, or `Portelance/Xu`; do not infer or silently rewrite
personal identities from those filenames. Use the documents to reconstruct the
scientific ideas, and use the names supplied here when describing the current
collaboration.

You must explicitly read and integrate these materials before judging the
project's purpose:

- `04_historical_context/project_motivation_recent_email_context_2026-06-16.md`
  — a verbatim motivating email supplied by the researcher;
- `04_historical_context/supervisor_goal_context/2026-06-04_supervisor_meeting_transcript.txt`
  — the meeting discussion that motivated complete-response uncertainty,
  repeated language-model sampling, expected response length, and the
  speaker/listener distinction;
- `04_historical_context/supervisor_goal_context/response_level_context_entropy.md`;
- `04_historical_context/supervisor_goal_context/deepthink_response_entropy_temperature_handoff.md`;
- `04_historical_context/supervisor_goal_context/yang_feedback_followup_report.md`;
- `04_historical_context/supervisor_goal_context/route1_portelance_xu_extension_suite.md`;
- `04_historical_context/supervisor_goal_context/original_project_description.pdf`;
- `04_historical_context/notes.md`, which records how those requests led to
  subsequent analyses and corrections.

Reconstruct and preserve the original two-route goal:

1. **Information at fixed effort:** given context and a constrained amount of
   production effort, do children's observed utterances change in
   predictability/informativeness with development?
2. **Effort adapted to contextual demand:** given context, do children shorten
   or lengthen production as response uncertainty or communicative demand
   changes, and how does this develop?

Also preserve the collaborators' broader motivations: study naturalistic
CHILDES interaction below age four; compare children with caregivers/adults
where scientifically valid; identify whether and when efficiency-related
modulation emerges; distinguish speaker effort from listener benefit; evaluate
whole-response uncertainty rather than only next-token entropy; retain
generated samples for entropy and expected-effort analyses; and consider
gender, social setting, and clinical populations only as secondary extensions
with appropriate causal and sociolinguistic safeguards.

The historical goals are motivation, not conclusions. Later audited results
sometimes qualify or contradict the initial hypotheses. Your task is to show
the full chain explicitly: **collaborator question → operationalization →
analysis → result → limitation → present scientific interpretation**. Do not
erase a failed prediction merely to make the final story resemble the original
email.

You are serving as a senior interdisciplinary scientist and methods reviewer
for a mature research project on the developmental communicative efficiency of
children’s naturalistic language use. Your expertise should span language
acquisition, psycholinguistics, pragmatics, dialogue and grounding,
information theory, computational linguistics, causal inference, longitudinal
statistics, language-model evaluation, and reproducible research.

You have received a curated evidence package. Treat it as a scientific record,
not as promotional material. Your job is to understand the project deeply,
independently review the relevant external literature, determine what the
existing results establish, and recommend the most defensible route to a
high-quality scientific contribution.

## First actions

Before searching externally or proposing anything:

1. Confirm that you can inspect `COMMUNICATIVE_EFFICIENCY_EVIDENCE.zip` and
   list the top-level folders you found. If you cannot, stop as instructed
   above.
2. Read `01_master_context/MASTER_SCIENTIFIC_HANDOUT.md` in full.
3. Read `01_master_context/CLAIMS_LEDGER.md` and
   `01_master_context/REPORT_AND_ARTIFACT_INDEX.md`.
4. Read `04_historical_context/AGENTS.md` for the authoritative dated project
   state and `04_historical_context/notes.md` for the research chronology.
5. Read the current reports and frozen protocols needed to verify every claim
   you will
   discuss. Do not rely only on the executive summary.
6. Record any apparent inconsistencies among package files and resolve them
   by preferring the master handout and claims ledger, then the current dated
   state in `AGENTS.md`, then completion markers, audits, protocols, and current
   reports, and only then older historical documents.

Do not begin by assuming that another analysis is necessary. First diagnose
the conceptual and evidential state.

## Central scientific question

The broad motivation is whether and how children’s naturalistic language use
develops toward more communicatively efficient behavior. The project has
measured multiple candidate components:

- unconditional and context-conditioned utterance predictability;
- context gain for observed child utterances;
- lexical, morphological, syllabic, and phonological effort proxies;
- effort relative to generated responses for the same context;
- information-effort position within Qwen-generated response clouds;
- word-level same-item contextual support;
- reciprocal caregiver-child effort and predictability coupling;
- downstream predictive gain for the actual next caregiver response;
- candidate repair, clarification, acknowledgement, and contingent-response
  functions, which remain unvalidated pending human annotation.

The central problem is to decide whether these components support one coherent
definition of communicative efficiency, a multidimensional framework, or
several distinct scientific claims. You must not define efficiency post hoc as
whichever outcome happens to move in the preferred direction.

## Mandatory scientific distinctions

Maintain all of the following throughout your report:

- Direct target surprisal `-log2 p(u | c)` is model-based self-information of
  an observed form, not semantic content and not human comprehension.
- Lower surprisal means greater scorer predictability. Do not describe it as
  “more Shannon information.”
- Context gain `log2 p(u | c) - log2 p(u)` is the available measure of how much
  preceding context supports the exact target. It is not interchangeable with
  contextual surprisal.
- Production effort and listener utility are different axes. Shorter speech is
  not automatically better; longer speech may be efficient when it prevents
  ambiguity or repair.
- Raw child effort and effort relative to a generated distribution are
  different estimands.
- Exact-string response entropy is dependent on the generator, prompt,
  decoding parameters, and surface form. It is not semantic uncertainty.
- Existing generated alternatives do not preserve the child’s intended
  meaning. Do not infer optimality, rational choice, or a true Pareto frontier
  from them.
- Mistral, Qwen, and TinyDialogues have different tokenizers and calibrations.
  Raw bits per model token cannot be pooled. The packaged scorer comparison
  uses Unicode bits per character for cross-tokenizer ranking.
- Brown, Manchester, and Providence form the 21-child discovery sample. The
  other 58 children across ten strict-naturalistic corpora are the preferred
  confirmation sample. TinyDialogues replication on the same 21 children is
  scorer robustness, not independent-sample confirmation.
- Hall is a separate historical cross-sectional sociolinguistic snapshot, not
  an 80th longitudinal child or causal SES study.
- CHILDES results are observational. Developmental association, adaptation,
  optimization, and causal learning mechanisms are not synonyms.

## What you must investigate externally

Conduct a deep, source-linked literature review using primary papers wherever
possible. At minimum, investigate:

1. Communicative efficiency and developmental change in children, including
   the Tal/Arnon line of work and work on adaptation to listeners or learners.
2. Efficient language production, Uniform Information Density, smooth signal
   redundancy, information density, and predictability-sensitive reduction.
3. Rate-distortion, information bottleneck, resource-rational, bounded-rational,
   and Rational Speech Act approaches to communication.
4. Dialogue grounding, common ground, repair, clarification, acknowledgement,
   contingent responding, and interactional success in child-caregiver talk.
5. Production effort, comprehension effort, joint/dyadic effort, and ways of
   avoiding invalid efficiency ratios.
6. Longitudinal and observational identification issues in CHILDES, including
   age/corpus support, within-child versus between-child effects, informative
   sampling, and developmental confirmation.
7. The validity and limitations of neural language-model surprisal in child
   language and psycholinguistics, including tokenization and domain effects.
8. Evaluation of generated response spaces, semantic equivalence, paraphrase
   sets, intended-meaning preservation, and listener-model utility.
9. Information-theoretic or predictive measures of how an utterance changes
   the distribution over a listener’s subsequent behavior.
10. Empirical precedents for treating actual next-turn behavior, repair, or
    task success as communicative utility.

Do not restrict the review to papers already named in the package. Search for
work that could falsify, reframe, or strengthen the project’s assumptions.
Clearly distinguish direct evidence, theoretical analogy, and your inference.
Use exact citations and links. Do not invent references.

## Questions to answer

### A. What has this project actually established?

Produce a claim-by-claim scientific assessment. For every major result, state:

- the estimand;
- sample and scorer;
- whether it is discovery, confirmation, robustness, descriptive, post hoc,
  contrary to prediction, pending, or deliberately stopped;
- the main estimate and uncertainty when important;
- the strongest defensible interpretation;
- the most important threat or alternative explanation.

Preserve null, mixed, and contrary results. Do not smooth them into a uniformly
positive developmental story.

### B. What should “communicative efficiency” mean here?

Compare several possible formalizations rather than selecting one by rhetoric.
For each candidate, specify:

- sender cost;
- listener or interactional benefit;
- contextual demand;
- unit of analysis;
- relevant comparison class or counterfactual;
- what the current data identify;
- what remains unobserved;
- whether developmental change is interpretable;
- what empirical result would support or contradict it.

Candidate families may include—but are not limited to—predictability at fixed
effort, utility at fixed effort, effort at fixed utility, Pareto/nondominance
approaches, rate-distortion formulations, information bottleneck measures,
resource-rational/RSA choice models, downstream behavioral predictive gain,
repair-adjusted joint cost, and multidimensional profiles. You are not required
to endorse any of these.

Determine whether a single scalar efficiency measure is scientifically useful
or whether the project should retain separate information, effort, contextual
support, and interactional-utility axes.

### C. Is the present evidence already enough for a strong paper?

Evaluate at least three publication strategies:

1. A focused paper on developmental predictability/conventionality of form at
   fixed measured effort.
2. A broader multidimensional paper combining predictability, effort
   adaptation, dyadic coupling, and downstream predictive utility.
3. Multiple papers separating the direct developmental result, generated
   response-space work, dyadic/downstream interaction, word-level effects, and
   Hall.

For each, identify the central claim, necessary figures/tables, results that
belong in appendices, likely reviewer objections, and whether any new work is a
submission blocker.

### D. Would another analysis materially solve the conceptual problem?

Only after assessing the existing evidence, identify analyses or measurements
that would materially change the scientific conclusion. Rank them by:

- conceptual value;
- identifiability;
- dependence on unvalidated assumptions;
- required new data or human annotation;
- computational cost;
- risk of researcher degrees of freedom;
- expected information gain;
- whether the analysis can be confirmatory given prior inspection.

Separate:

- analyses possible from existing audited compact products;
- analyses requiring the full local external tables;
- analyses requiring the 325-row human annotation;
- analyses requiring new generated alternatives or semantic validation;
- analyses requiring a new experiment or new corpus.

Do not recommend a large model grid simply because it is technically possible.
The package documents one correctly stopped 189-fit Bayesian program whose
projected cost exceeded its frozen resource ceiling.

### E. How should the project resolve the strongest conceptual objections?

Address these explicitly:

1. The observed child’s intended meaning is not known, and generated responses
   are not meaning-preserving counterfactuals.
2. The downstream predictive-gain measure uses an LM’s probability of the next
   caregiver string rather than human comprehension or success.
3. Older children’s language may simply become more conventional or more like
   model training data.
4. Age is entangled with corpus composition, recording density, session type,
   and linguistic development.
5. Word count is only one production-effort proxy.
6. The fixed-effort contextual effect is strong in discovery but does not meet
   the frozen primary frequentist confirmation gate in the other 58 children.
7. Context gain decreases rather than increases with age.
8. The immediate downstream utility proxy is positive, but its frozen
   developmental slope is not positive.
9. Scorers differ sharply in unconditional calibration and context use.
10. Naturalistic observational data may be unable to establish optimization.

For each objection, classify it as fatal to a particular claim, manageable by
reframing, testable with existing data, or requiring new evidence.

## Required final deliverable

Produce one integrated report with the following sections:

1. **Executive decision memo** — the clearest recommendation in no more than
   two pages.
2. **Reconstruction of the project** — a concise but accurate account of the
   data, measures, analyses, and evidential chronology.
3. **External literature landscape** — theories, empirical precedents,
   disagreements, and gaps, with primary-source citations.
4. **Construct and estimand map** — a formal comparison of candidate meanings
   of communicative efficiency.
5. **Claim-evidence audit** — what is supported, qualified, contrary,
   descriptive, pending, or not identified.
6. **Best scientific framing** — your recommended central contribution and
   why it is better than the alternatives.
7. **Publication architecture** — one-paper versus multi-paper recommendation,
   proposed title(s), research questions, section structure, figures, tables,
   and appendices.
8. **Prioritized next-work decision table** — including a defensible “no new
   analysis needed” option.
9. **If new work is recommended:** exact estimand, required variables,
   formula/model class, identification assumptions, sample split, validation
   gate, robustness checks, stopping rule, and interpretation limits. Do not
   provide vague suggestions such as “try a mixed model.”
10. **Adversarial peer review** — write the five strongest objections a top
    journal reviewer would raise and state how the project should respond.
11. **Faculty-verification list** — claims, citations, and decisions that must
    be checked by the human investigators.
12. **Source appendix** — external bibliography plus a list of package files
    actually consulted.

End with a ranked recommendation:

- what to do immediately;
- what to do only if resources allow;
- what not to do;
- the exact sentence you believe should become the project’s principal claim.

## Standards for reasoning and reporting

- Cite package evidence by relative filename and section/table when possible.
- Cite external factual and theoretical claims to primary sources.
- Mark your own synthesis as inference.
- Do not invent unavailable variables, labels, or experimental conditions.
- Do not interpret pilot coefficients from the stopped Bayesian program.
- Do not turn a sensitivity into the primary result because it is more
  favorable.
- Do not replace the registered clustered interval with a bootstrap interval
  without displaying and explaining both.
- Do not pool raw score magnitudes across tokenizers.
- Do not call Hall differences causal SES, race, ability, or deficit effects.
- Do not equate model prediction with human understanding.
- Prefer a smaller decisive study over an analysis zoo.
- Be ambitious about theory and conservative about evidence.
