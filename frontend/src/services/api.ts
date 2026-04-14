import { DocumentDetail, DocumentItem, JobEventRecord } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const fallback = `Request failed with status ${response.status}`;
    let detail = fallback;
    try {
      const payload = await response.json();
      detail = payload?.detail || fallback;
    } catch {
      detail = fallback;
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export async function uploadFiles(files: File[]): Promise<DocumentItem[]> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  return request<DocumentItem[]>("/upload", {
    method: "POST",
    body: formData,
  });
}

export async function listDocuments(params: {
  search?: string;
  status?: string;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}): Promise<DocumentItem[]> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.status && params.status !== "all") query.set("status", params.status);
  if (params.sortBy) query.set("sort_by", params.sortBy);
  if (params.sortOrder) query.set("sort_order", params.sortOrder);

  return request<DocumentItem[]>(`/documents?${query.toString()}`);
}

export async function getDocument(documentId: string): Promise<DocumentDetail> {
  return request<DocumentDetail>(`/documents/${documentId}`);
}

export async function updateDocument(documentId: string, payload: Partial<DocumentDetail["extracted_result"]>): Promise<DocumentDetail> {
  return request<DocumentDetail>(`/documents/${documentId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function finalizeDocument(documentId: string): Promise<DocumentDetail> {
  return request<DocumentDetail>(`/documents/${documentId}/finalize`, {
    method: "POST",
  });
}

export async function retryJob(jobId: string) {
  return request(`/jobs/${jobId}/retry`, {
    method: "POST",
  });
}

export async function deleteDocument(documentId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/documents/${documentId}`, {
    method: "DELETE",
  });
}

export function exportDocumentUrl(documentId: string, format: "json" | "csv"): string {
  return `${API_BASE}/documents/${documentId}/export?format=${format}`;
}

export async function getJobEvents(jobId: string): Promise<JobEventRecord[]> {
  return request<JobEventRecord[]>(`/jobs/${jobId}/events`);
}

export function jobWebSocketUrl(jobId: string): string {
  const apiUrl = new URL(API_BASE);
  const protocol = apiUrl.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${apiUrl.host}/ws/jobs/${jobId}`;
}
