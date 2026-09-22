/** Plain-language definitions shown next to technical terms. Written for a risk committee, not a data scientist. */
export const GLOSSARY: Record<string, { term: string; short: string; long: string }> = {
  auc: {
    term: "Ranking accuracy (AUC)",
    short: "How reliably the model puts riskier borrowers above safer ones.",
    long: "Take one borrower who later defaulted and one who did not. AUC is how often the model gave the defaulter the higher risk score. 0.5 is a coin toss; 1.0 is perfect. Credit models typically land between 0.70 and 0.85.",
  },
  ks: {
    term: "Separation (KS)",
    short: "The widest gap between defaulters and non-defaulters across the score range.",
    long: "The Kolmogorov–Smirnov statistic measures how far apart the score distributions of defaulters and non-defaulters are at their most different point. Higher means the model separates the two groups more cleanly.",
  },
  brier: {
    term: "Forecast error (Brier score)",
    short: "Average gap between the predicted probability and what actually happened. Lower is better.",
    long: "Each prediction is a probability; each outcome is 0 or 1. The Brier score is the average squared difference between them, so it rewards probabilities that are both well-ranked and honest.",
  },
  ece: {
    term: "Calibration error (ECE)",
    short: "Whether a '20% risk' really means about 20% default. Lower is better.",
    long: "Borrowers are grouped by predicted risk; in each group the predicted rate is compared with the observed default rate. Expected calibration error is the average of those gaps, weighted by group size.",
  },
  ci: {
    term: "95% confidence interval",
    short: "The range the true figure most likely sits in, given the size of the test sample.",
    long: "The test sample is re-drawn with replacement hundreds of times (bootstrap) and the metric recomputed each time. Two models whose intervals overlap are not reliably different.",
  },
  holdout: {
    term: "Held-out test data",
    short: "Borrowers the model never saw during training, used for a fair check.",
    long: "Performance is always reported on data set aside before training. Where the data has dates, the test set is the most recent period (a temporal split); otherwise a random, stratified sample is held out and that limitation is recorded.",
  },
  champion: {
    term: "Champion and baseline",
    short: "The candidate model versus a simple reference model.",
    long: "The baseline is a logistic regression: transparent and easy to explain. The champion is a gradient-boosted tree model that can capture interactions. Both are trained the same way and compared on the same held-out data; nothing is promoted automatically.",
  },
  importance: {
    term: "Feature importance",
    short: "How much each input contributes to the model's accuracy.",
    long: "Each input is scrambled in turn and the drop in ranking accuracy is measured (permutation importance). Larger drops mean the model leans on that input more. Correlated inputs share credit, so treat the ordering as indicative.",
  },
  threshold: {
    term: "Illustrative cut-off",
    short: "A score above which a borrower would be flagged, chosen only to illustrate trade-offs.",
    long: "The cut-off maximises the balance of precision and recall on the validation data. It is not a lending policy: a real policy would weigh business costs and be set by the business, not the model.",
  },
  precision: {
    term: "Precision and recall",
    short: "Of those flagged, how many defaulted; of those who defaulted, how many were flagged.",
    long: "Raising the cut-off flags fewer borrowers (higher precision, lower recall). Lowering it catches more defaulters at the cost of flagging more good borrowers.",
  },
  fairness: {
    term: "Fairness diagnostics",
    short: "Whether the model behaves similarly for different groups of borrowers.",
    long: "Selection-rate ratio compares how often each group is flagged (a common rule of thumb is to look closer below 0.80). True- and false-positive-rate differences compare error rates across groups. These are diagnostics for discussion, never a legal determination, and the grouping field is never used as a model input.",
  },
  psi: {
    term: "Population shift (PSI)",
    short: "How far the mix of incoming borrowers has moved away from the data the model learned from.",
    long: "The Population Stability Index compares the distribution of each input today with its distribution at training time. Project defaults: below 0.10 stable; 0.10–0.25 worth investigating; above 0.25 a material shift that needs action. The thresholds are configurable, not regulatory.",
  },
  scoreDrift: {
    term: "Score drift",
    short: "Whether the model's own risk scores are shifting compared with training.",
    long: "The same stability index applied to the predicted probabilities. A shift here means the model is seeing different borrowers, changing its verdicts, or both.",
  },
  readiness: {
    term: "Readiness checks",
    short: "Eight evidence requirements a model must meet before a reviewer can approve it.",
    long: "Data lineage, documentation, validation results, a monitoring plan, a fairness assessment, controls, security checks and reviewer sign-off. The checks are deterministic: the same evidence always gives the same answer, and every gap is named.",
  },
  controls: {
    term: "Controls",
    short: "The safeguards around the model, each with an owner, a frequency and evidence that it works.",
    long: "Examples: a data-quality gate before training, reproducible training settings, a human approval gate, monitoring alerts, and an audit log. A control without an owner or test evidence fails the readiness check.",
  },
  audit: {
    term: "Audit log",
    short: "A permanent, tamper-evident record of every change and decision.",
    long: "Events are appended, never edited. Each event carries a cryptographic fingerprint that includes the previous event's fingerprint, so altering history breaks the chain and is detectable.",
  },
  lineage: {
    term: "Lineage",
    short: "The traceable path from data source to model version.",
    long: "Which dataset (and license), which snapshot (with a checksum of the file), which training run (with its seed and settings) produced this version. It allows anyone to reproduce the result.",
  },
  checksum: {
    term: "Checksum",
    short: "A fingerprint of a file; if the file changes, the fingerprint changes.",
    long: "A SHA-256 hash recorded when data is imported and again when a model is trained, proving the same file was used.",
  },
  modelCard: {
    term: "Model card",
    short: "The one-document summary of what the model is for, how it was built, how well it works and where it fails.",
    long: "A standard format for documenting a model's purpose, data, methods, results, limitations and approvals so that people other than its author can review it.",
  },
  hypothesis: {
    term: "Statistical test",
    short: "A formal check of whether two groups of borrowers differ by more than chance.",
    long: "A two-sample Kolmogorov–Smirnov test compares one input's distribution between the training data and a comparison group. A small p-value says the difference is unlikely to be chance; the effect size says whether it is large enough to matter.",
  },
  lifecycle: {
    term: "Lifecycle state",
    short: "Where a model version is on the path from draft to retirement.",
    long: "Draft → Validated → Awaiting review → Approved → In monitoring → Retired. A reviewer can reject at review or withdraw an approval; a rejected version can be reopened as a draft. Nothing is modifiable once submitted for review.",
  },
  batch: {
    term: "Monitoring batch",
    short: "A dated set of new borrowers scored by the approved model and checked for problems.",
    long: "Each batch is checked for data quality, population shift, score drift and, when outcomes are known, accuracy and calibration. Problems raise alerts with an owner and a due date.",
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
