export type Status = "queued" | "processing" | "completed" | "failed";

export interface Job {
  id: string;
  document_id: string;
  status: Status;
  progress: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExtractedResult {
  id: number;
  document_id: string;
  title: string;
  category: string;
  summary: string;
  keywords: string[];
  finalized: boolean;
}

export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  size: number;
  status: Status;
  created_at: string;
  updated_at: string;
  latest_job?: Job;
}

export interface DocumentDetail extends DocumentItem {
  extracted_result?: ExtractedResult;
}

export interface JobEvent {
  job_id: string;
  status: string;
  progress: number;
  message: string;
  timestamp: string;
}

export interface JobEventRecord {
  id: number;
  job_id: string;
  status: string;
  progress: number;
  message: string;
  timestamp: string;
}
