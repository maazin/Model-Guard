import { Link } from "react-router-dom";
import { Card, PageHeader } from "../components/ui";

const STEPS: [string, string][] = [
  ["Build and test", "A data scientist trains the model and measures how well it ranks risk on borrowers it has never seen. Every setting, seed and data file is recorded so the result can be reproduced."],
  ["Gather the evidence", "Before anyone can approve the model, eight requirements must be met: where the data came from, what the model is for, how it was tested, how it will be watched, whether it treats groups alike, which safeguards exist, and who signed off. Missing items are listed by name, not hidden behind a red light."],
  ["A person decides", "Only a model risk reviewer can approve or reject, and must give a reason. The decision, and every step before it, is written to a record that cannot be quietly edited."],
  ["Keep watching", "After approval, each new batch of borrowers is checked: is the data clean, have the borrowers changed, are the model's answers still accurate? Problems become alerts with an owner and a due date."],
];

export function About() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Why this exists"
        lede="Banks and lenders use statistical models to estimate how likely a borrower is to miss payments. Those models influence who gets credit and at what price, so they need the same discipline as any other important decision: evidence before use, a named person accountable, and ongoing checks afterwards."
      />
      <Card title="The problem">
        <div className="space-y-3 text-[15px]">
          <p>
            A model is only ever as good as the day it was built. The borrowers it sees change, the economy changes, and a model that was accurate last year can quietly stop being accurate. It can also be unfair to a group of people without anyone intending it, or be
            approved on a slide deck that no one can trace back to the actual data.
          </p>
          <p>
            In most organisations the evidence that would answer these questions is scattered: results in a notebook, the approval in an email, the monitoring in a spreadsheet, the documentation out of date. When a regulator, an auditor or a risk committee asks
            <em> “how do you know this model is still safe to use?”</em>, assembling the answer takes weeks.
          </p>
        </div>
      </Card>
      <Card title="What ModelGuard does" subtitle="One place where a model goes from idea to approval to retirement, and the evidence is collected along the way rather than reconstructed afterwards.">
        <ol className="grid gap-4 md:grid-cols-2">
          {STEPS.map(([title, body], i) => (
            <li key={title} className="rounded-xl p-4" style={{ background: "var(--surface-2)" }}>
              <div className="flex items-center gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-semibold" style={{ background: "var(--accent)", color: "var(--accent-ink)" }}>{i + 1}</span>
                <h3 className="font-semibold">{title}</h3>
              </div>
              <p className="muted mt-2 text-sm">{body}</p>
            </li>
          ))}
        </ol>
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Who it is for">
          <dl className="space-y-3 text-sm">
            <div><dt className="font-medium">Risk leaders and committees</dt><dd className="muted">Read the <Link className="underline" to="/versions/pd-credit-v2.0.0/executive">one-page summary</Link>: what the model is for, how healthy it is, the top risks, and a recommendation.</dd></div>
            <div><dt className="font-medium">Model risk reviewers</dt><dd className="muted">Check the <Link className="underline" to="/versions/pd-credit-v1.1.0/governance">evidence list</Link>, read the documents, and approve or reject with a reason that is kept on record.</dd></div>
            <div><dt className="font-medium">Data scientists</dt><dd className="muted">Train, test and document a model, and see exactly what a reviewer will ask for before submitting it.</dd></div>
            <div><dt className="font-medium">Auditors</dt><dd className="muted">Follow the <Link className="underline" to="/versions/pd-credit-v2.0.0">trail from data file to decision</Link>, including a tamper-evident log of every change.</dd></div>
          </dl>
        </Card>
        <Card title="What you are looking at">
          <div className="space-y-3 text-sm">
            <p>
              A working demonstration with four model versions. Three were built on a synthetic dataset to show the whole journey: one is approved and being monitored, one is waiting for a reviewer, and one is deliberately incomplete so you can see the approval gate
              refuse it. The fourth, <Link className="underline" to="/versions/pd-credit-v2.0.0/executive">pd-credit-v2.0.0</Link>, was built on a real, openly licensed public dataset of 30,000 credit-card accounts.
            </p>
            <p>Try it: pick a model at the top, switch <em>View as</em> to “Model risk reviewer”, open <em>Approval</em>, and approve or reject the version that is waiting. Then look at the audit log on <em>Details</em>.</p>
            <p className="muted">Every technical term on the site is shown in everyday words with the technical name beside it, and each page ends with an explanation of how the two connect.</p>
          </div>
        </Card>
      </div>
      <Card title="What it is not">
        <ul className="list-disc space-y-1.5 pl-5 text-sm">
          <li>Not a real lending system. No real borrower is scored and no decision about anyone is made.</li>
          <li>Not credit advice, and not a claim that any regulation is satisfied. The approval steps simulate good practice; they are not a legal standard.</li>
          <li>Not a product. It is a portfolio project built to show, end to end, what responsible use of a credit model looks like.</li>
        </ul>
      </Card>
      <p className="muted text-sm">
        Ready to explore? Start with <Link className="underline" to="/">all models</Link>.
      </p>
    </div>
  );
}
