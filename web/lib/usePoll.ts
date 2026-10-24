"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/** Fetch now and every `ms` milliseconds. Returns [data, error, refresh]. */
export function usePoll<T>(fn: () => Promise<T>, ms: number, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fnRef = useRef(fn);
  useEffect(() => {
    fnRef.current = fn;
  });
  const refresh = useCallback(
    () =>
      fnRef
        .current()
        .then((d) => {
          setData(d);
          setError(null);
        })
        .catch((e: Error) => setError(e.message)),
    [],
  );
  useEffect(() => {
    let alive = true;
    const tick = () =>
      fnRef
        .current()
        .then((d) => alive && (setData(d), setError(null)))
        .catch((e: Error) => alive && setError(e.message));
    tick();
    const id = ms > 0 ? setInterval(tick, ms) : undefined;
    return () => {
      alive = false;
      if (id) clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ms, ...deps]);
  return [data, error, refresh] as const;
}
