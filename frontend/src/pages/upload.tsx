import { FormEvent, useState } from "react";
import { useRouter } from "next/router";

import { DnsHelpNotice } from "@/components/DnsHelpNotice";
import { Layout } from "@/components/Layout";
import { uploadFiles } from "@/services/api";

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const router = useRouter();

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!files.length) return;

    setBusy(true);
    setMessage(null);
    try {
      await uploadFiles(files);
      setMessage("Upload successful. Jobs queued.");
      setTimeout(() => router.push("/"), 1000);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Layout title="Upload Documents">
      <section className="panel narrow">
        <form onSubmit={onSubmit} className="stacked-form">
          <input
            type="file"
            multiple
            onChange={(e) => setFiles(Array.from(e.target.files || []))}
          />
          <button type="submit" disabled={busy || !files.length}>
            {busy ? "Uploading..." : "Upload and Process"}
          </button>
          {message ? <p>{message}</p> : null}
          <DnsHelpNotice errorMessage={message} />
        </form>
      </section>
    </Layout>
  );
}
