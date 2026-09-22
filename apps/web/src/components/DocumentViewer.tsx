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
        <span className="muted">revision {d.version}</span>
        <span className="faint hidden sm:inline">{d.path}</span>
        <a className="btn ml-auto" href={STATIC_DEMO ? `${REPO_URL}/blob/main/${d.path}` : `${API_BASE}/api/v1/model-versions/${versionId}/documents/${type}/download`} target="_blank" rel="noreferrer">
          {STATIC_DEMO ? "Open on GitHub" : "Download"}
        </a>
      </div>
      <div className="prose-doc max-h-[60vh] overflow-auto rounded-xl border p-4 hairline">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{stripFrontMatter(d.content)}</ReactMarkdown>
      </div>
    </div>
  );
}
