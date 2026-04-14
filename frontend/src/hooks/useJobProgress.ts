import { useEffect, useRef, useState } from "react";

import { getJobEvents, jobWebSocketUrl } from "@/services/api";
import { JobEvent, Status } from "@/services/types";

function statusFromEvent(stage: string, current: Status): Status {
  if (stage === "job_failed") return "failed";
  if (stage === "job_completed") return "completed";
  if (stage === "job_queued") return "queued";
  if (stage === "job_retrying") return "processing";
  if (stage.includes("started") || stage.includes("completed") || stage === "final_result_stored") {
    return "processing";
  }
  return current;
}

function normalizeEvent(payload: Partial<JobEvent>, fallbackJobId: string): JobEvent {
  return {
    job_id: payload.job_id || fallbackJobId,
    status: payload.status || "job_queued",
    progress: typeof payload.progress === "number" ? payload.progress : 0,
    message: payload.message || "Waiting for processing...",
    timestamp: payload.timestamp || new Date().toISOString(),
  };
}

function mergeEvent(existing: JobEvent[], next: JobEvent): JobEvent[] {
  const duplicate = existing.some(
    (item) =>
      item.timestamp === next.timestamp &&
      item.status === next.status &&
      item.message === next.message &&
      item.progress === next.progress,
  );
  if (duplicate) return existing;
  return [...existing, next].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );
}

interface UseJobProgressOptions {
  includeHistory?: boolean;
}

export function useJobProgress(
  jobId?: string,
  initialProgress = 0,
  initialMessage = "Waiting",
  initialStatus: Status = "queued",
  options: UseJobProgressOptions = {},
) {
  const [progress, setProgress] = useState(initialProgress);
  const [statusMessage, setStatusMessage] = useState(initialMessage);
  const [status, setStatus] = useState<Status>(initialStatus);
  const [events, setEvents] = useState<JobEvent[]>([]);
  const reconnectRef = useRef<number>(0);
  const stopRef = useRef(false);
  const includeHistory = options.includeHistory ?? false;

  useEffect(() => {
    setProgress(initialProgress);
    setStatusMessage(initialMessage);
    setStatus(initialStatus);
    setEvents([]);
  }, [jobId, initialProgress, initialMessage, initialStatus]);

  useEffect(() => {
    if (!jobId) {
      return;
    }

    stopRef.current = false;
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;

    if (includeHistory) {
      getJobEvents(jobId)
        .then((history) => {
          const normalized = history.map((item) => normalizeEvent(item, jobId));
          setEvents(normalized);
          const latest = normalized[normalized.length - 1];
          if (latest) {
            setProgress(latest.progress);
            setStatusMessage(latest.message);
            setStatus((current: Status) => statusFromEvent(latest.status, current));
          }
        })
        .catch(() => {
          // Keep websocket-only updates if history fetch fails.
        });
    }

    const connect = () => {
      if (stopRef.current) return;

      ws = new WebSocket(jobWebSocketUrl(jobId));

      ws.onopen = () => {
        reconnectRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const payload = normalizeEvent(JSON.parse(event.data) as JobEvent, jobId);
          setProgress(payload.progress);
          setStatusMessage(payload.message);
          setStatus((current: Status) => statusFromEvent(payload.status, current));
          setEvents((current) => mergeEvent(current, payload));
        } catch {
          // Ignore malformed event payloads and keep last known values.
        }
      };

      ws.onerror = () => {
        ws?.close();
      };

      ws.onclose = () => {
        if (stopRef.current) return;
        const attempt = reconnectRef.current + 1;
        reconnectRef.current = attempt;
        const delay = Math.min(5000, 500 * attempt);
        reconnectTimer = setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      stopRef.current = true;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      ws?.close();
    };
  }, [jobId, includeHistory]);

  return { progress, statusMessage, status, events };
}
