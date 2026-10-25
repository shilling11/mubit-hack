import { configured, NOT_SET_UP, onLine, ROOM, stateOf } from "@/lib/line-server";

export const dynamic = "force-dynamic";

/** The phones poll this: is the line open, is someone calling? */
export async function GET() {
  if (!configured()) return Response.json({ state: "closed", error: NOT_SET_UP });
  return Response.json({ state: stateOf(await onLine()), room: ROOM });
}
