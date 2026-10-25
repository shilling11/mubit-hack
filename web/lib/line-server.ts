/**
 * The phone line, server side (route handlers in app/api/line). LiveKit itself holds the state: who is in
 * the room right now. That way the phone pages work from Vercel, with no link back to the laptop.
 *   closed → waiting (the laptop's recorder is in) → calling (Ellen rang) → connected (Sam answered)
 */
import { AccessToken, RoomServiceClient } from "livekit-server-sdk";

export type Role = "customer" | "agent" | "recorder";
export type LineState = "closed" | "waiting" | "calling" | "connected";

export const ROOM = process.env.LIVEKIT_ROOM ?? "thistle-line";
const LK_URL = process.env.LIVEKIT_URL ?? "";
const KEY = process.env.LIVEKIT_API_KEY ?? "";
const SECRET = process.env.LIVEKIT_API_SECRET ?? "";

export const configured = () => Boolean(LK_URL && KEY && SECRET);
export const NOT_SET_UP = "LiveKit isn't set up: add LIVEKIT_URL, LIVEKIT_API_KEY and LIVEKIT_API_SECRET to web/.env.local";

/** Identities in the room now ("recorder", "customer", "agent"). No room yet means nobody is on the line. */
export async function onLine(): Promise<string[]> {
  try {
    const people = await new RoomServiceClient(LK_URL.replace(/^ws/, "http"), KEY, SECRET).listParticipants(ROOM);
    return people.map((p) => p.identity);
  } catch (e) {
    if ((e as { code?: string }).code === "not_found") return [];
    throw e;
  }
}

export function stateOf(ids: string[]): LineState {
  if (ids.includes("customer")) return ids.includes("agent") ? "connected" : "calling";
  return ids.includes("recorder") ? "waiting" : "closed";
}

/** The laptop's recorder only listens; the phones publish their mics. */
export async function tokenFor(role: Role): Promise<{ url: string; token: string }> {
  const at = new AccessToken(KEY, SECRET, { identity: role, ttl: "1h" });
  at.addGrant({ room: ROOM, roomJoin: true, canPublish: role !== "recorder", canSubscribe: true, canPublishData: false });
  return { url: LK_URL, token: await at.toJwt() };
}
