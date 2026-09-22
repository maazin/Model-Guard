import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { API_BASE, REPO_URL, STATIC_DEMO, get } from "../lib/api";
import { Badge, Loading } from "./ui";

function stripFrontMatter(md: string) {
  if (!md.startsWith("---")) return md;
  const end = md.indexOf("\n---", 3);
  return end === -1 ? md : md.slice(end + 4);
}

export function DocumentViewer({ versionId, type }: { versionId: string; type: string }) {
  const q = useQuery({ queryKey: ["doc", versionId, type], queryFn: () => get(`/api/v1/model-versions/${versionId}/documents/${type}`) });
  if (q.isLoading) return <Loading />;
  if (!q.data) return null;
  const d = q.data;
  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
        <Badge value={d.status} />
        <span className="muted">v{d.version}</span>
        <code className="faint">{d.content_hash.slice(0, 12)}</code>
        <span className="faint">{d.path}</span>
        <a className="btn ml-auto" href={STATIC_DEMO ? `${REPO_URL}/blob/main/${d.path}` : `${API_BASE}/api/v1/model-versions/${versionId}/documents/${type}/download`} target="_blank" rel="noreferrer">
          {STATIC_DEMO ? "View .md on GitHub" : "Download .md"}
        </a>
      </div>
      <div className="prose-doc max-h-[60vh] overflow-auto rounded border p-3" style={{ borderColor: "var(--border)" }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{stripFrontMatter(d.content)}</ReactMarkdown>
      </div>
    </div>
  );
}
