import { configured, NOT_SET_UP, onLine, ROOM, stateOf, tokenFor, type Role } from "@/lib/line-server";

const fail = (status: number, detail: string) => Response.json({ detail }, { status });

/** A phone (or the laptop's recorder) asks to join the line; returns a LiveKit token. */
export async function POST(req: Request) {
  const { role } = (await req.json().catch(() => ({}))) as { role?: Role };
  if (role !== "customer" && role !== "agent" && role !== "recorder") return fail(422, "role must be customer, agent or recorder");
  if (!configured()) return fail(400, NOT_SET_UP);
  // The phone pages are public on Vercel; only the laptop's own server hands out the listening token
  if (role === "recorder" && process.env.VERCEL) return fail(403, "Open the line from the laptop (localhost)");
  const ids = await onLine();
  if (role === "customer" && !ids.includes("recorder")) return fail(409, "The line is closed: open it on the laptop first");
  if (role === "agent" && !ids.includes("customer")) return fail(409, "Nobody is calling yet");
  return Response.json({ state: stateOf(ids), room: ROOM, ...(await tokenFor(role)) });
}
