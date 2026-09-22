/**
 * Every technical term used in the dashboard, three ways:
 *  - plain: the everyday label shown in the UI
 *  - jargon: the exact technical name and abbreviation a data scientist would use
 *  - technical: how it is actually computed
 *  - bridge: how the plain label maps onto the technical measure, so a reader can move between the two
 */
export interface GlossaryEntry {
  plain: string;
  jargon: string;
  abbr: string;
  short: string;
  technical: string;
  bridge: string;
}

export const GLOSSARY: Record<string, GlossaryEntry> = {
  auc: {
    plain: "Ranking accuracy",
    jargon: "Area under the ROC curve",
    abbr: "AUC",
    short: "How reliably the model puts riskier borrowers above safer ones.",
    technical:
      "The ROC curve plots the true-positive rate against the false-positive rate at every possible score cut-off. AUC is the area beneath that curve, from 0.5 (random) to 1.0 (perfect). It equals the probability that a randomly chosen defaulter receives a higher score than a randomly chosen non-defaulter.",
    bridge:
      "“Ranking accuracy” is that probability read literally: an AUC of 0.79 means that in 79 of 100 defaulter/non-defaulter pairs, the model ranks the defaulter as riskier. It says nothing about whether the probabilities themselves are right — that is calibration.",
  },
  ks: {
    plain: "Separation",
    jargon: "Kolmogorov–Smirnov statistic",
    abbr: "KS",
    short: "The widest gap between defaulters and non-defaulters across the score range.",
    technical:
      "Sort borrowers by score. At each cut-off, compute the cumulative share of defaulters caught minus the cumulative share of non-defaulters flagged (TPR − FPR). KS is the maximum of that difference, between 0 and 1.",
    bridge:
      "“Separation” is the point on the score scale where the two groups are most different. A KS of 0.44 means there is a cut-off at which 44 percentage points more defaulters than non-defaulters fall above it. Credit teams often quote KS alongside AUC because it points at a usable cut-off.",
  },
  brier: {
    plain: "Forecast error",
    jargon: "Brier score",
    abbr: "Brier",
    short: "Average gap between the predicted probability and what actually happened. Lower is better.",
    technical:
      "The mean squared difference between each predicted probability p and the outcome y ∈ {0, 1}: mean((p − y)²). A model that always predicts the base default rate scores roughly rate × (1 − rate); 0 is perfect.",
    bridge:
      "“Forecast error” is the same idea as scoring a weather forecast: if you said 20% and it rained, you are charged (0.2 − 1)². It penalises both bad ranking and over-confident probabilities, so it complements AUC.",
  },
  ece: {
    plain: "Calibration error",
    jargon: "Expected calibration error",
    abbr: "ECE",
    short: "Whether a ‘20% risk’ really means about 20% default. Lower is better.",
    technical:
      "Predictions are bucketed into equal-width probability bins (ten here). In each bin the mean predicted probability is compared with the observed default rate; ECE is the absolute gap averaged across bins, weighted by how many borrowers fall in each.",
    bridge:
      "“Calibration” is honesty of the numbers. The calibration chart is the same computation drawn out: each dot is a bin; dots on the diagonal mean the model’s stated risk matches reality. ECE summarises how far the dots sit from that line.",
  },
  ci: {
    plain: "Likely range",
    jargon: "95% bootstrap confidence interval",
    abbr: "95% CI",
    short: "The range the true figure most likely sits in, given the size of the test sample.",
    technical:
      "The held-out sample is re-drawn with replacement several hundred times and the metric recomputed each time. The 2.5th and 97.5th percentiles of those recomputed values form the interval.",
    bridge:
      "A single number hides sampling noise. If two models’ ranges overlap, the data cannot tell them apart with confidence — which is why ModelGuard never promotes a model on a metric alone.",
  },
  holdout: {
    plain: "Held-out test data",
    jargon: "Temporal (out-of-time) or stratified holdout",
    abbr: "holdout",
    short: "Borrowers the model never saw during training, used for a fair check.",
    technical:
      "The data is split 60/20/20 into training, validation and test partitions. With a date field the cut is chronological (temporal split) so the test set is the most recent period. Without one, a random split stratified on the default rate is used and the limitation is recorded.",
    bridge:
      "Testing on unseen borrowers is what makes the quality figures credible. “Out-of-time” is the stronger test because it mimics deployment: the model is judged on people who applied after it was built.",
  },
  champion: {
    plain: "Candidate and reference model",
    jargon: "Champion / baseline (challenger framework)",
    abbr: "champion vs. baseline",
    short: "The candidate model versus a simple reference model.",
    technical:
      "Baseline: L2-regularised logistic regression. Champion candidate: scikit-learn HistGradientBoostingClassifier. Both share one preprocessing pipeline (median imputation, scaling, one-hot encoding) and the same split, seed and evaluation code.",
    bridge:
      "The reference model is deliberately simple and explainable; the candidate is allowed to be more complex. Comparing them on identical data shows whether the extra complexity buys real accuracy.",
  },
  importance: {
    plain: "Which inputs matter most",
    jargon: "Permutation feature importance",
    abbr: "importance",
    short: "How much each input contributes to the model’s accuracy.",
    technical:
      "For each input, its values are shuffled across borrowers (breaking its link to the outcome) and the drop in AUC is measured, repeated ten times with a fixed seed. Larger drops mean greater reliance on that input.",
    bridge:
      "“Scrambling” an input and watching accuracy fall is a direct test of how much the model uses it. Inputs that are correlated share credit, so the chart is an ordering, not an exact attribution.",
  },
  threshold: {
    plain: "Illustrative cut-off",
    jargon: "Decision threshold",
    abbr: "threshold",
    short: "A score above which a borrower would be flagged, chosen only to illustrate trade-offs.",
    technical:
      "The probability above which a borrower is classed as “flagged”. Here it is set to the value that maximises F1 (the harmonic mean of precision and recall) on the validation partition.",
    bridge:
      "The model outputs a probability, not a decision. A cut-off turns it into one. The one shown is a mathematical convenience; a real policy would be set by the business after weighing the cost of each kind of mistake.",
  },
  precision: {
    plain: "Flagged who defaulted / defaulters caught",
    jargon: "Precision and recall (confusion matrix)",
    abbr: "precision / recall",
    short: "Of those flagged, how many defaulted; of those who defaulted, how many were flagged.",
    technical:
      "At a cut-off, the confusion matrix counts true positives (TP), false positives (FP), false negatives (FN) and true negatives (TN). Precision = TP / (TP + FP); recall (true-positive rate) = TP / (TP + FN); specificity = TN / (TN + FP).",
    bridge:
      "The 2 × 2 table on the quality page is the confusion matrix with the cells labelled in words: “caught”, “missed”, “flagged in error”, “correctly cleared”. Precision and recall are just ratios of those cells.",
  },
  fairness: {
    plain: "Treats groups alike",
    jargon: "Fairness diagnostics: selection-rate ratio, TPR/FPR difference, group calibration",
    abbr: "fairness",
    short: "Whether the model behaves similarly for different groups of borrowers.",
    technical:
      "Selection-rate ratio = min(flag rate) / max(flag rate) across groups (the “four-fifths” rule of thumb looks closer below 0.80). TPR and FPR differences compare error rates across groups at the same cut-off. Group calibration compares predicted and observed default rates within each group.",
    bridge:
      "“Flag-rate ratio” is the selection-rate ratio; “defaulters caught, gap” is the TPR difference; “flagged in error, gap” is the FPR difference. The grouping field is never a model input; these figures inform a discussion and are not a legal finding.",
  },
  psi: {
    plain: "Population shift",
    jargon: "Population Stability Index",
    abbr: "PSI",
    short: "How far the mix of incoming borrowers has moved away from the data the model learned from.",
    technical:
      "Each input is binned (ten quantile bins fixed at training time). PSI = Σ (actual% − expected%) × ln(actual% / expected%) across bins. Project defaults: < 0.10 stable, 0.10–0.25 investigate, > 0.25 alert; these are configurable, not regulatory.",
    bridge:
      "PSI is a single number for “how different does this batch look from the training data on this input”. The batch-by-batch table shows it per input; the trend chart shows the largest one per batch.",
  },
  scoreDrift: {
    plain: "Score drift",
    jargon: "Prediction-score PSI",
    abbr: "score PSI",
    short: "Whether the model’s own risk scores are shifting compared with training.",
    technical:
      "The same PSI formula applied to the model’s predicted probabilities, using ten equal-width bins on [0, 1] fixed at training time, plus the shift in mean predicted probability.",
    bridge:
      "Input shift asks whether the borrowers changed; score drift asks whether the model’s verdicts changed. Both can move for different reasons, so both are tracked.",
  },
  readiness: {
    plain: "Evidence requirements",
    jargon: "Deterministic readiness engine (approval gate)",
    abbr: "readiness checks",
    short: "Eight evidence requirements a model must meet before a reviewer can approve it.",
    technical:
      "Eight checks — dataset lineage, documentation, validation, monitoring plan, fairness assessment, controls, security, sign-off — each evaluated from registry records and document contents by fixed rules. Submission for review requires the first seven; approval also records the eighth.",
    bridge:
      "“Requirements met” on the cards is the count of passing checks. Because the rules are deterministic, the same evidence always yields the same list of named gaps, which is what the “missing evidence” lists show.",
  },
  controls: {
    plain: "Safeguards",
    jargon: "Risk-control matrix",
    abbr: "controls",
    short: "The safeguards around the model, each with an owner, a frequency and evidence that it works.",
    technical:
      "A register of controls with name, owner, frequency, status (planned / implemented / tested / effective), evidence URI and test evidence. The readiness engine requires at least three, each fully populated and not merely planned.",
    bridge:
      "“Control” is audit language for a safeguard. The matrix answers who is responsible, how often it runs, and how we know it works — the questions a reviewer asks.",
  },
  audit: {
    plain: "Permanent record of changes",
    jargon: "Append-only, hash-chained audit log",
    abbr: "audit log",
    short: "A tamper-evident record of every change and decision.",
    technical:
      "Every event stores a SHA-256 fingerprint of its own content combined with the previous event’s fingerprint (event_hash = sha256(previous_hash + payload)). Verification recomputes the chain; any edited or removed event breaks every fingerprint after it.",
    bridge:
      "The short hexadecimal “fingerprint” beside each entry is that hash. You cannot read anything from it directly; its value is that it changes if history is altered.",
  },
  lineage: {
    plain: "Where the data came from",
    jargon: "Data lineage (source → snapshot → training run → model version)",
    abbr: "lineage",
    short: "The traceable path from data source to model version.",
    technical:
      "Registry records link a data source (licence, retrieval date) to a snapshot (file, row count, SHA-256 checksum, quality results), to a training run (seed, features, hyperparameters, package versions, code version) and to the registered model version.",
    bridge:
      "Lineage lets anyone re-run the exact training that produced a result and confirm that the same data was used. It is the difference between “trust me” and “check for yourself”.",
  },
  checksum: {
    plain: "File fingerprint",
    jargon: "SHA-256 checksum",
    abbr: "checksum",
    short: "A fingerprint of a file; if the file changes, the fingerprint changes.",
    technical:
      "A 64-character hexadecimal hash of the file’s bytes, computed on import and stored with the training run.",
    bridge:
      "Matching checksums on the snapshot and the training run prove the model was trained on exactly the file that was quality-checked.",
  },
  modelCard: {
    plain: "Model card",
    jargon: "Model card (Mitchell et al., 2019 format)",
    abbr: "model card",
    short: "The one-document summary of what the model is for, how it was built, how well it works and where it fails.",
    technical:
      "Twelve required sections: name and version, purpose, out-of-scope uses, data and licence, target and approach, features and exclusions, split and reproducibility, results, limitations, monitoring, controls, approval state. Measured sections are generated from the registry; narrative sections are written by the data scientist.",
    bridge:
      "It is the document a committee reads first. The readiness engine refuses to accept it while any section is still a placeholder.",
  },
  hypothesis: {
    plain: "Are the two groups really different?",
    jargon: "Two-sample Kolmogorov–Smirnov test",
    abbr: "KS test",
    short: "A formal check of whether two groups of borrowers differ by more than chance.",
    technical:
      "Compares the empirical distributions of one input in two samples. The statistic D is the largest gap between their cumulative distributions; the p-value is the probability of a gap that large if both came from the same distribution. Cohen’s d is reported as an effect size.",
    bridge:
      "A small p-value says “not chance”; the effect size says “but is it big enough to matter”. With thousands of borrowers, even trivial differences become “significant”, so both are shown.",
  },
  lifecycle: {
    plain: "Where a version is on its journey",
    jargon: "Lifecycle state machine",
    abbr: "lifecycle",
    short: "Where a model version is on the path from draft to retirement.",
    technical:
      "States: DRAFT → VALIDATED → PENDING_REVIEW → APPROVED → MONITORING → RETIRED, with REJECTED reachable from review or approval and REOPEN back to draft. Transitions are role-gated (only a reviewer can approve, reject or retire) and each one is an audit event.",
    bridge:
      "“Awaiting review” is PENDING_REVIEW; “In monitoring” is MONITORING. Nothing about a version can be edited once it is submitted, which is why the pill next to the title matters.",
  },
  batch: {
    plain: "Batch of new borrowers",
    jargon: "Monitoring batch (dated scoring cohort)",
    abbr: "batch",
    short: "A dated set of new borrowers scored by the approved model and checked for problems.",
    technical:
      "A snapshot imported for monitoring, scored with the stored pipeline and evaluated for data quality, PSI per input, score PSI and, when the target is present, AUC, KS, Brier, ECE and fairness. Findings above thresholds create alerts with severity, owner and due date.",
    bridge:
      "Each column in the batch table is one such cohort. “Outcomes known” means defaults have been observed, so accuracy could be measured, not just drift.",
  },
};

export type GlossaryKey = keyof typeof GLOSSARY;

export const STATE_LABEL: Record<string, string> = {
  DRAFT: "Draft",
  VALIDATED: "Validated",
  PENDING_REVIEW: "Awaiting review",
  APPROVED: "Approved",
  MONITORING: "In monitoring",
  REJECTED: "Rejected",
  RETIRED: "Retired",
};

export const HEALTH_LABEL: Record<string, string> = {
  healthy: "Healthy",
  watch: "Watch",
  at_risk: "At risk",
  retired: "Retired",
};
