import { Placeholder } from "@/components/Placeholder";

const STATS = [
  { n: "01", label: "Calls scored" },
  { n: "02", label: "Sampled by hand" },
  { n: "03", label: "Possible breaches" },
  { n: "04", label: "Critical recall" },
];

export default function Wall() {
  return (
    <div className="space-y-6">
      <div>
        <div className="lab g">[ Thistle Bank · Call QA ]</div>
        <h1 className="mt-3 text-5xl">Every call, scored.</h1>
        <p className="mt-2 text-mute">Analysts review the AI&apos;s scorecard; every correction teaches it.</p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {STATS.map((s) => (
          <div key={s.n} className="panel p-4">
            <div className="lab">
              [ {s.n} ] {s.label}
            </div>
            <div className="mt-2 text-4xl text-mute-2">—</div>
          </div>
        ))}
      </div>

      <Placeholder label="Wall" title="One tile per call" note="5% sampled by hand today → 100% scored, coloured by risk tier." />

      <div className="grid gap-3 md:grid-cols-2">
        <Placeholder label="Queue" title="Breaches, uncertain calls and the audit sample" />
        <Placeholder label="Mubit" title="Corrections become a model you own" note="Trace panel, adapter status, playbook version." />
      </div>
    </div>
  );
}
