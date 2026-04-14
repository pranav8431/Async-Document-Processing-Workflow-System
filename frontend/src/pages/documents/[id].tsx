import { useRouter } from "next/router";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { DnsHelpNotice } from "@/components/DnsHelpNotice";
import { Layout } from "@/components/Layout";
import { LiveEventLog, ProcessingTimeline } from "@/components/LiveEventLog";
import { ProgressBar } from "@/components/ProgressBar";
import { useJobProgress } from "@/hooks/useJobProgress";
import {
  exportDocumentUrl,
  finalizeDocument,
  getDocument,
  retryJob,
  updateDocument,
} from "@/services/api";
import { DocumentDetail, Status } from "@/services/types";

function initialJobMessage(status?: Status, errorMessage?: string | null): string {
  if (errorMessage) return errorMessage;
  if (status === "completed") return "Job completed successfully";
  if (status === "failed") return "Job failed";
  if (status === "processing") return "Processing";
  if (status === "queued") return "Job queued";
  return "Waiting";
}

export default function DocumentDetailPage() {
  const router = useRouter();
  const documentId = useMemo(() => (typeof router.query.id === "string" ? router.query.id : ""), [router.query.id]);

  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const { progress, statusMessage, status, events } = useJobProgress(
    document?.latest_job?.id,
    document?.latest_job?.progress ?? 0,
    initialJobMessage(document?.latest_job?.status, document?.latest_job?.error_message),
    document?.status ?? "queued",
    { includeHistory: true },
  );

  useEffect(() => {
    if (!documentId) return;

    getDocument(documentId)
      .then(setDocument)
      .catch((err: Error) => setError(err.message));
  }, [documentId]);

  async function saveEdits(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!document) return;

    const form = new FormData(e.currentTarget);
    const payload = {
      title: String(form.get("title") || ""),
      category: String(form.get("category") || ""),
      summary: String(form.get("summary") || ""),
      keywords: String(form.get("keywords") || "")
        .split(",")
        .map((k) => k.trim())
        .filter(Boolean),
    };

    setBusy(true);
    setError(null);
    try {
      const updated = await updateDocument(document.id, payload);
      setDocument(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update document");
    } finally {
      setBusy(false);
    }
  }

  async function finalize() {
    if (!document) return;
    setBusy(true);
    try {
      const updated = await finalizeDocument(document.id);
      setDocument(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to finalize");
    } finally {
      setBusy(false);
    }
  }

  async function retry() {
    if (!document?.latest_job) return;
    setBusy(true);
    try {
      await retryJob(document.latest_job.id);
      const refreshed = await getDocument(document.id);
      setDocument(refreshed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Retry failed");
    } finally {
      setBusy(false);
    }
  }

  if (!documentId) {
    return null;
  }

  return (
    <Layout title="Document Detail">
      <section className="panel narrow">
        {error ? <p className="error-text">{error}</p> : null}
        <DnsHelpNotice errorMessage={error} />
        {document ? (
          <>
            <p><strong>Filename:</strong> {document.filename}</p>
            <p><strong>Status:</strong> {status}</p>
            <ProgressBar value={status === "completed" ? 100 : progress} />
            <p className="subdued">{statusMessage}</p>

            <div className="job-live-grid">
              <section className="panel timeline-panel">
                <h3>Processing Timeline</h3>
                <ProcessingTimeline events={events} currentStatus={status} />
              </section>
              <section className="panel event-panel">
                <h3>Live Event Log</h3>
                <LiveEventLog events={events} />
              </section>
            </div>

            <section className="panel extracted-panel">
              <h3>Extracted Fields</h3>

              <form onSubmit={saveEdits} className="stacked-form">
                <label>
                  Title
                  <input name="title" defaultValue={document.extracted_result?.title || ""} />
                </label>
                <label>
                  Category
                  <input name="category" defaultValue={document.extracted_result?.category || ""} />
                </label>
                <label>
                  Summary
                  <textarea name="summary" defaultValue={document.extracted_result?.summary || ""} rows={4} />
                </label>
                <label>
                  Keywords (comma separated)
                  <input
                    name="keywords"
                    defaultValue={(document.extracted_result?.keywords || []).join(", ")}
                  />
                </label>
                <button type="submit" disabled={busy}>Save Edits</button>
              </form>
            </section>

            <div className="action-row">
              <button onClick={finalize} disabled={busy}>Finalize</button>
              {document.status === "failed" ? (
                <button onClick={retry} disabled={busy}>Retry Job</button>
              ) : null}
              <a href={exportDocumentUrl(document.id, "json")}>Export JSON</a>
              <a href={exportDocumentUrl(document.id, "csv")}>Export CSV</a>
            </div>
          </>
        ) : (
          <p>Loading...</p>
        )}
      </section>
    </Layout>
  );
}
