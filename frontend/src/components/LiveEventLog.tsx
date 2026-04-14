import { useEffect, useMemo, useRef } from "react";

import { JobEvent } from "@/services/types";

interface LiveEventLogProps {
  events: JobEvent[];
}

interface ProcessingTimelineProps {
  events: JobEvent[];
  currentStatus?: string;
  currentStepIndex?: number;
}

interface TimelineStep {
  key: string;
  label: string;
}

const steps: TimelineStep[] = [
  { key: "job_queued", label: "Job Queued" },
  { key: "job_started", label: "Job Started" },
  { key: "document_parsing_started", label: "Parsing Started" },
  { key: "document_parsing_completed", label: "Parsing Completed" },
  { key: "field_extraction_started", label: "Extraction Started" },
  { key: "field_extraction_completed", label: "Extraction Completed" },
  { key: "final_result_stored", label: "Final Result Stored" },
  { key: "job_terminal", label: "Job Completed" },
];

const statusToStepIndex: Record<string, number> = {
  job_queued: 0,
  job_started: 1,
  document_parsing_started: 2,
  document_parsing_completed: 3,
  field_extraction_started: 4,
  field_extraction_completed: 5,
  final_result_stored: 6,
  job_completed: 7,
};

function stepIndexFromProgress(progress: number): number {
  if (progress >= 100) return 7;
  if (progress >= 95) return 6;
  if (progress >= 90) return 5;
  if (progress >= 60) return 4;
  if (progress >= 30) return 3;
  if (progress >= 10) return 2;
  if (progress >= 5) return 1;
  return 0;
}

function resolveCurrentStepIndex(
  latestStatus: string | undefined,
  latestProgress: number | undefined,
  currentStepIndex: number | undefined,
): number {
  if (typeof currentStepIndex === "number") {
    return Math.max(0, Math.min(steps.length - 1, currentStepIndex));
  }
  if (latestStatus && latestStatus in statusToStepIndex) {
    return statusToStepIndex[latestStatus];
  }
  return stepIndexFromProgress(latestProgress ?? 0);
}

function formatEventTime(timestamp: string): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return "--:--:--";
  }
  return date.toLocaleTimeString();
}

export function LiveEventLog({ events }: LiveEventLogProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  const ordered = useMemo(
    () => [...events].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()),
    [events],
  );

  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.scrollTop = containerRef.current.scrollHeight;
  }, [ordered.length]);

  if (!ordered.length) {
    return <p className="subdued">Waiting for processing...</p>;
  }

  return (
    <div className="event-log" ref={containerRef} aria-live="polite">
      {ordered.map((event, idx) => (
        <div key={`${event.timestamp}-${idx}`} className="event-row">
          <span className="event-time">{formatEventTime(event.timestamp)}</span>
          <span className="event-message">[{event.progress}%] {event.message}</span>
        </div>
      ))}
    </div>
  );
}

export function ProcessingTimeline({
  events,
  currentStatus,
  currentStepIndex,
}: ProcessingTimelineProps) {
  if (!events.length) {
    return <p className="subdued">Waiting for processing...</p>;
  }

  const ordered = [...events].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );
  const latest = ordered[ordered.length - 1];
  const isFailed = latest.status === "job_failed" || currentStatus === "failed";
  const isCompleted = latest.status === "job_completed" || currentStatus === "completed";
  const activeIndex = resolveCurrentStepIndex(latest.status, latest.progress, currentStepIndex);

  return (
    <ol className="timeline-list" aria-label="Processing timeline">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1;
        let state: "completed" | "current" | "pending" | "failed" = "pending";
        let label = step.label;

        if (isCompleted) {
          state = "completed";
        } else if (isFailed) {
          if (step.key === "job_terminal") {
            state = "failed";
            label = "Job Failed";
          } else if (index < activeIndex) {
            state = "completed";
          }
        } else if (index < activeIndex) {
          state = "completed";
        } else if (index === activeIndex) {
          state = "current";
        }

        const marker =
          state === "completed" ? "\u2714" : state === "current" ? "\u25cf" : state === "failed" ? "\u2716" : "\u25cb";

        return (
          <li key={step.key} className={`timeline-item timeline-${state} ${isLast ? "timeline-tail" : ""}`}>
            <span className="timeline-marker" aria-hidden="true">{marker}</span>
            <span className="timeline-label">{label}</span>
          </li>
        );
      })}
    </ol>
  );
}
