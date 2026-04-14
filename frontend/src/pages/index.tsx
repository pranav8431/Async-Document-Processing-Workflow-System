import { ChangeEvent, useEffect, useState } from "react";

import { DocumentRow } from "@/components/DocumentRow";
import { Layout } from "@/components/Layout";
import { deleteDocument, listDocuments, retryJob } from "@/services/api";
import { DocumentItem } from "@/services/types";

export default function DashboardPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function refreshDocuments() {
    const items = await listDocuments({ search, status, sortBy, sortOrder });
    setDocuments(items);
  }

  useEffect(() => {
    setError(null);
    refreshDocuments()
      .catch((err: Error) => setError(err.message));
  }, [search, status, sortBy, sortOrder]);

  async function handleRetry(jobId: string) {
    try {
      setSuccess(null);
      await retryJob(jobId);
      await refreshDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to retry job");
    }
  }

  async function handleDelete(documentId: string) {
    const confirmed = window.confirm("Are you sure you want to delete this document?");
    if (!confirmed) return;

    try {
      setError(null);
      setSuccess(null);
      setDeletingId(documentId);
      const result = await deleteDocument(documentId);
      setSuccess(result.message);
      await refreshDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete document");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <Layout title="Document Workflow Dashboard">
      <section className="panel">
        <div className="toolbar">
          <input
            placeholder="Search filename"
            value={search}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
          />
          <select value={status} onChange={(e: ChangeEvent<HTMLSelectElement>) => setStatus(e.target.value)}>
            <option value="all">All</option>
            <option value="queued">Queued</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
          <select value={sortBy} onChange={(e: ChangeEvent<HTMLSelectElement>) => setSortBy(e.target.value)}>
            <option value="created_at">Created</option>
            <option value="updated_at">Updated</option>
            <option value="filename">Filename</option>
            <option value="size">Size</option>
            <option value="status">Status</option>
          </select>
          <select
            value={sortOrder}
            onChange={(e: ChangeEvent<HTMLSelectElement>) => setSortOrder(e.target.value as "asc" | "desc")}
          >
            <option value="desc">Desc</option>
            <option value="asc">Asc</option>
          </select>
        </div>

        {error ? <p className="error-text">{error}</p> : null}
        {success ? <p className="success-text">{success}</p> : null}

        <table className="doc-table">
          <thead>
            <tr>
              <th>Filename</th>
              <th>Status</th>
              <th>Progress</th>
              <th>Latest Event</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <DocumentRow
                key={doc.id}
                document={doc}
                onRetry={handleRetry}
                onDelete={handleDelete}
                isDeleting={deletingId === doc.id}
              />
            ))}
          </tbody>
        </table>
      </section>
    </Layout>
  );
}
