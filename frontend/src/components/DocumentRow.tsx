import Link from "next/link";

import { useJobProgress } from "@/hooks/useJobProgress";
import { DocumentItem } from "@/services/types";

import { ProgressBar } from "./ProgressBar";
import { StatusBadge } from "./StatusBadge";

interface DocumentRowProps {
  document: DocumentItem;
  onRetry: (jobId: string) => void;
  onDelete: (documentId: string) => void;
  isDeleting: boolean;
}

export function DocumentRow({ document, onRetry, onDelete, isDeleting }: DocumentRowProps) {
  const initialMessage = document.latest_job?.error_message || document.latest_job?.status || "Waiting";
  const { progress, statusMessage, status } = useJobProgress(
    document.latest_job?.id,
    document.latest_job?.progress ?? 0,
    initialMessage,
    document.status,
  );
  const failedJobId = status === "failed" ? document.latest_job?.id : undefined;
  const deleteDisabled = status === "processing" || isDeleting;

  return (
    <tr>
      <td>{document.filename}</td>
      <td><StatusBadge status={status} /></td>
      <td>
        <ProgressBar value={status === "completed" ? 100 : progress} />
      </td>
      <td>{statusMessage}</td>
      <td>
        <div className="table-actions">
          <Link href={`/documents/${document.id}`}>View</Link>
          {failedJobId ? (
            <button type="button" className="button-secondary" onClick={() => onRetry(failedJobId)}>
              Retry
            </button>
          ) : null}
          <button
            type="button"
            className="button-danger"
            disabled={deleteDisabled}
            title={status === "processing" ? "Cannot delete while processing" : "Delete document"}
            onClick={() => onDelete(document.id)}
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </button>
        </div>
      </td>
    </tr>
  );
}
