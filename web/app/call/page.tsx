import { Placeholder } from "@/components/Placeholder";

export default function LiveCall() {
  return (
    <div className="space-y-6">
      <div>
        <div className="lab g">[ Live call · recording ]</div>
        <h1 className="mt-3 text-5xl">Live call</h1>
        <p className="mt-2 text-mute">Redress records both sides. The scorecard appears when the call ends.</p>
      </div>

      <div className="grid gap-3 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <Placeholder label="Transcript" title="Every word, as it's said" note="Colleague and customer on separate lanes." />
        <Placeholder label="Scorecard" title="C1–C4 critical · S1–S5 scored" note="Answer, quote with timestamp, confidence, routing reason." />
      </div>
    </div>
  );
}
