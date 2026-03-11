import React, { useMemo, useState } from "react";
import { useResolveWorkspaceEntry, useWorkspaceEntries, useWorkspaceSummary } from "../hooks/useWorkspace";
import type { WorkspaceEntry } from "../api/workspaceTypes";

type Props = {
  workspaceId: string;
  className?: string;
};

const sections = [
  { key: "facts", label: "Facts" },
  { key: "hypotheses", label: "Hypotheses" },
  { key: "questions", label: "Questions" },
  { key: "decisions", label: "Decisions" },
  { key: "artifacts", label: "Artifacts" },
  { key: "notes", label: "Notes" },
] as const;

function EntryCard({ entry, onResolve }: { entry: WorkspaceEntry; onResolve?: (id: string) => void }) {
  return (
    <div className="rounded-2xl border p-3 bg-white shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-medium">{entry.source_agent || "system"} · {entry.status}</div>
          <div className="text-xs text-slate-500">confidence {(entry.confidence * 100).toFixed(0)}%</div>
        </div>
        {entry.entry_type === "question" && entry.status !== "resolved" && onResolve && (
          <button onClick={() => onResolve(entry.memory_id)} className="rounded-lg border px-2 py-1 text-xs hover:bg-slate-50">
            Resolve
          </button>
        )}
      </div>
      <pre className="mt-3 whitespace-pre-wrap text-xs overflow-auto">{JSON.stringify(entry.content, null, 2)}</pre>
    </div>
  );
}

export function WorkspaceInspector({ workspaceId, className }: Props) {
  const [showSummary, setShowSummary] = useState(false);
  const { data, isLoading, isError, error } = useWorkspaceEntries(workspaceId);
  const resolveMutation = useResolveWorkspaceEntry(workspaceId);
  const summaryMutation = useWorkspaceSummary(workspaceId);

  const groupedSections = useMemo(() => {
    if (!data) return [];
    return sections.map((section) => ({
      ...section,
      entries: (data as any)[section.key] as WorkspaceEntry[],
    }));
  }, [data]);

  return (
    <div className={className || "space-y-4"}>
      <div className="rounded-2xl border p-4 bg-white shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Shared Cognitive Workspace</h2>
            <p className="text-sm text-slate-600">Inspect what agents know, what they believe, what remains unresolved, and why decisions were made.</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => setShowSummary(v => !v)} className="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50">
              {showSummary ? "Hide Summary" : "Summarize"}
            </button>
            {showSummary && (
              <button onClick={() => summaryMutation.mutate()} className="rounded-xl bg-black px-3 py-2 text-sm text-white">
                Generate Summary
              </button>
            )}
          </div>
        </div>

        {showSummary && (
          <div className="mt-4 rounded-xl border bg-slate-50 p-3">
            {summaryMutation.isPending && <div className="text-sm text-slate-600">Summarizing workspace…</div>}
            {summaryMutation.data && (
              <>
                <div className="text-sm font-medium mb-1">Workspace Summary</div>
                <div className="text-sm text-slate-700 whitespace-pre-wrap">{summaryMutation.data.summary}</div>
              </>
            )}
          </div>
        )}
      </div>

      {isLoading && <div className="rounded-2xl border p-6 bg-white">Loading workspace…</div>}
      {isError && <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{(error as Error)?.message || "Failed to load workspace."}</div>}

      {!isLoading && !isError && groupedSections.map((section) => (
        <div key={section.key} className="rounded-2xl border p-4 bg-white shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-base font-semibold">{section.label}</h3>
            <span className="rounded-full border px-2 py-1 text-xs text-slate-600">{section.entries.length}</span>
          </div>

          {section.entries.length === 0 ? (
            <div className="rounded-xl border border-dashed p-4 text-sm text-slate-500">No {section.label.toLowerCase()} yet.</div>
          ) : (
            <div className="grid gap-3">
              {section.entries.map((entry) => (
                <EntryCard key={entry.memory_id} entry={entry} onResolve={(id) => resolveMutation.mutate(id)} />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
