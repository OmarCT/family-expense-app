import { sha256 } from "./sha256";

const SEPARATOR = "\u001f";

/** Clave de desempate del largest remainder (ADR-0002): SHA-256 de item, U+001F y user en UTF-8. */
export function tiebreakKey(itemId: string, userId: string): Uint8Array {
  return sha256(new TextEncoder().encode(`${itemId}${SEPARATOR}${userId}`));
}

function compareBytes(a: Uint8Array, b: Uint8Array): number {
  for (let i = 0; i < a.length; i++) {
    const diff = (a[i] as number) - (b[i] as number);
    if (diff !== 0) return diff;
  }
  return 0;
}

/** Participantes de menor a mayor clave: el primero recibe antes el centavo sobrante. */
export function orderByTiebreak(itemId: string, userIds: readonly string[]): string[] {
  if (new Set(userIds).size !== userIds.length) throw new Error("user_ids duplicados");
  return userIds
    .map((userId) => ({ userId, key: tiebreakKey(itemId, userId) }))
    .sort((x, y) => compareBytes(x.key, y.key))
    .map((entry) => entry.userId);
}
