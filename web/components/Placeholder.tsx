/** A labelled empty panel, standing in for a section that isn't built yet. */
export function Placeholder({ label, title, note, className }: { label: string; title: string; note?: string; className?: string }) {
  return (
    <section className={`panel p-5 ${className ?? ""}`}>
      <div className="lab">[ {label} ]</div>
      <h3 className="mt-2 text-xl">{title}</h3>
      {note && <p className="mt-2 text-sm text-mute">{note}</p>}
    </section>
  );
}
