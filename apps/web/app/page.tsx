"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import { usePostHog } from "posthog-js/react";

import {
  ApiError,
  ChatResponse,
  DatasetResponse,
  loadUciDataset,
  loadUrlDataset,
  sendChatMessage,
} from "../lib/api";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

const curatedDatasets = [
  { id: "iris", label: "Iris" },
  { id: "wine", label: "Wine" },
  { id: "auto_mpg", label: "Auto MPG" },
];

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export default function HomePage() {
  const posthog = usePostHog();
  const [sessionId, setSessionId] = useState<string>("");
  const [dataset, setDataset] = useState<DatasetResponse | null>(null);
  const [datasetError, setDatasetError] = useState<string | null>(null);
  const [datasetLoading, setDatasetLoading] = useState(false);
  const [urlInput, setUrlInput] = useState("");

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [plotResult, setPlotResult] = useState<ChatResponse | null>(null);
  const [graphDiv, setGraphDiv] = useState<HTMLElement | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    let stored = window.localStorage.getItem("vibe_plotter_session");
    if (!stored) {
      stored = window.crypto?.randomUUID() ?? `session-${Date.now()}`;
      window.localStorage.setItem("vibe_plotter_session", stored);
    }
    setSessionId(stored);
    posthog?.identify(stored);
  }, [posthog]);

  const plotJson = plotResult?.plot_json as
    | { data: unknown[]; layout?: Record<string, unknown>; frames?: unknown[] }
    | undefined;

  const previewRows = dataset?.rows ?? [];

  async function handleDatasetSelect(datasetId: string) {
    if (!sessionId) return;
    setDatasetLoading(true);
    setDatasetError(null);
    try {
      const response = await loadUciDataset(datasetId, sessionId);
      setDataset(response);
      setMessages([]);
      setPlotResult(null);
      posthog?.capture("dataset_loaded", {
        session_id: sessionId,
        dataset_type: "uci",
        dataset_id: datasetId,
        row_count: response.row_count,
        column_count: response.columns.length,
        $ai_session_id: sessionId,
      });
    } catch (error) {
      if (error instanceof ApiError) {
        setDatasetError(error.message);
      } else {
        setDatasetError("Failed to load dataset.");
      }
    } finally {
      setDatasetLoading(false);
    }
  }

  async function handleUrlLoad() {
    if (!sessionId || !urlInput) return;
    setDatasetLoading(true);
    setDatasetError(null);
    try {
      const response = await loadUrlDataset(urlInput, sessionId);
      setDataset(response);
      setMessages([]);
      setPlotResult(null);
      posthog?.capture("dataset_loaded", {
        session_id: sessionId,
        dataset_type: "url",
        source_url: urlInput,
        row_count: response.row_count,
        column_count: response.columns.length,
        $ai_session_id: sessionId,
      });
    } catch (error) {
      if (error instanceof ApiError) {
        setDatasetError(error.message);
      } else {
        setDatasetError("Failed to load dataset.");
      }
    } finally {
      setDatasetLoading(false);
    }
  }

  async function handleSendMessage() {
    if (!input.trim() || !sessionId || !dataset) return;
    const message = input.trim();
    setInput("");
    setChatLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: message }]);

    posthog?.capture("chat_message_sent", {
      session_id: sessionId,
      message_length: message.length,
      $ai_session_id: sessionId,
    });

    try {
      const response = await sendChatMessage(message, sessionId);
      setPlotResult(response);
      setMessages((prev) => [...prev, { role: "assistant", content: response.assistant_message }]);
      posthog?.capture("chart_rendered", {
        session_id: sessionId,
        title: response.title,
        $ai_session_id: sessionId,
      });
    } catch (error) {
      if (error instanceof ApiError) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: error.message },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Something went wrong. Try again." },
        ]);
      }
    } finally {
      setChatLoading(false);
    }
  }

  function downloadBlob(filename: string, blob: Blob) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  function buildHtmlExport() {
    if (!plotJson) return "";
    return `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>${plotResult?.title ?? "Vibe Plot"}</title>
  <script src="https://cdn.plot.ly/plotly-2.30.0.min.js"></script>
</head>
<body style="margin:0;background:#0e1116;color:#e7eefc;">
  <div id="plot" style="width:100vw;height:100vh;"></div>
  <script>
    const figure = ${JSON.stringify(plotJson)};
    Plotly.newPlot('plot', figure.data, figure.layout || {}, {responsive:true});
  </script>
</body>
</html>`;
  }

  async function handleDownload(type: "json" | "html" | "code" | "png") {
    if (!plotResult) return;

    if (type === "json" && plotJson) {
      downloadBlob("vibe-plot.json", new Blob([JSON.stringify(plotJson, null, 2)], { type: "application/json" }));
    }

    if (type === "html") {
      const html = buildHtmlExport();
      downloadBlob("vibe-plot.html", new Blob([html], { type: "text/html" }));
    }

    if (type === "code") {
      downloadBlob("vibe-plot.py", new Blob([plotResult.code ?? ""], { type: "text/plain" }));
    }

    if (type === "png" && graphDiv) {
      const Plotly = await import("plotly.js-dist-min");
      const plotly = (Plotly as unknown as { default?: typeof Plotly }).default ?? Plotly;
      const dataUrl = await plotly.toImage(graphDiv, { format: "png", width: 1200, height: 800 });
      const link = document.createElement("a");
      link.href = dataUrl;
      link.download = "vibe-plot.png";
      link.click();
    }

    posthog?.capture("export_clicked", {
      session_id: sessionId,
      export_type: type,
      $ai_session_id: sessionId,
    });
  }

  const datasetStats = useMemo(() => {
    if (!dataset) return null;
    return `${dataset.row_count} rows · ${dataset.columns.length} columns`;
  }, [dataset]);

  return (
    <div className="min-h-screen px-6 py-10 md:px-10">
      <header className="mx-auto flex max-w-6xl flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <div className="rounded-2xl bg-white/10 px-4 py-3 text-xl font-semibold tracking-tight text-white">
            Vibe Plotter
          </div>
          <span className="badge">LLM Analytics Demo</span>
        </div>
        <div className="text-sm text-white/70">
          Session <span className="font-mono text-white/90">{sessionId || "loading"}</span>
        </div>
      </header>

      <main className="mx-auto mt-10 grid max-w-6xl gap-8 lg:grid-cols-[360px_1fr]">
        <section className="flex flex-col gap-6">
          <details className="panel p-6" open>
            <summary className="panel-title cursor-pointer">Dataset Loader</summary>
            <div className="mt-5 flex flex-col gap-4">
              <div className="text-sm text-white/70">
                Pick a curated dataset or load a CSV URL. {datasetStats && (
                  <span className="text-white/90">Current: {datasetStats}</span>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {curatedDatasets.map((datasetItem) => (
                  <button
                    key={datasetItem.id}
                    className="btn-secondary"
                    onClick={() => handleDatasetSelect(datasetItem.id)}
                    disabled={datasetLoading}
                  >
                    {datasetItem.label}
                  </button>
                ))}
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-xs uppercase tracking-[0.2em] text-white/60">CSV URL</label>
                <div className="flex gap-2">
                  <input
                    value={urlInput}
                    onChange={(event) => setUrlInput(event.target.value)}
                    placeholder="https://example.com/data.csv"
                    className="w-full rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/40"
                  />
                  <button className="btn-primary" onClick={handleUrlLoad} disabled={datasetLoading}>
                    Load
                  </button>
                </div>
                {datasetError && <div className="text-sm text-flare">{datasetError}</div>}
              </div>
            </div>
          </details>

          <details className="panel p-6" open>
            <summary className="panel-title cursor-pointer">Data Preview</summary>
            <div className="mt-5 overflow-auto">
              {!dataset && <div className="text-sm text-white/60">No dataset loaded yet.</div>}
              {dataset && (
                <table className="table-grid">
                  <thead>
                    <tr>
                      {dataset.columns.map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewRows.map((row, idx) => (
                      <tr key={idx}>
                        {dataset.columns.map((col) => (
                          <td key={col}>{String(row[col] ?? "")}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </details>
        </section>

        <section className="flex flex-col gap-6">
          <div className="panel p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-semibold text-white">Ask for a chart</h2>
                <p className="text-sm text-white/60">Describe what you want to visualize.</p>
              </div>
              <div className="badge">Plot Agent</div>
            </div>
            <div className="mt-4 flex flex-col gap-3">
              <div className="max-h-64 space-y-3 overflow-auto rounded-2xl border border-white/10 bg-white/5 p-4">
                {messages.length === 0 && (
                  <div className="text-sm text-white/50">
                    No messages yet. Try: "Show a scatter of sepal length vs width colored by species."
                  </div>
                )}
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`rounded-xl px-3 py-2 text-sm ${
                      msg.role === "user"
                        ? "bg-splash/20 text-white"
                        : "bg-white/10 text-white/80"
                    }`}
                  >
                    <span className="mr-2 font-mono text-xs uppercase text-white/50">{msg.role}</span>
                    {msg.content}
                  </div>
                ))}
              </div>
              <div className="flex flex-col gap-2 md:flex-row">
                <input
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      handleSendMessage();
                    }
                  }}
                  disabled={!dataset}
                  placeholder="Ask for a visualization..."
                  className="flex-1 rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/40"
                />
                <button className="btn-primary" onClick={handleSendMessage} disabled={chatLoading || !dataset}>
                  {chatLoading ? "Working..." : "Send"}
                </button>
              </div>
            </div>
          </div>

          <div className="panel p-6">
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="text-xl font-semibold text-white">Plot Output</h3>
                <p className="text-sm text-white/60">Title, summary, and chart output.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button className="btn-secondary" onClick={() => handleDownload("json")} disabled={!plotResult}>
                  Download JSON
                </button>
                <button className="btn-secondary" onClick={() => handleDownload("html")} disabled={!plotResult}>
                  Download HTML
                </button>
                <button className="btn-secondary" onClick={() => handleDownload("png")} disabled={!plotResult}>
                  Download PNG
                </button>
                <button className="btn-secondary" onClick={() => handleDownload("code")} disabled={!plotResult}>
                  Download Code
                </button>
              </div>
            </div>
            <div className="mt-4 space-y-3">
              {!plotResult && <div className="text-sm text-white/50">No chart yet.</div>}
              {plotResult && (
                <>
                  <div>
                    <div className="text-lg font-semibold text-white">{plotResult.title}</div>
                    <div className="text-sm text-white/70">{plotResult.summary}</div>
                  </div>
                  {plotJson && (
                    <div className="rounded-2xl bg-white/5 p-3">
                      <Plot
                        data={plotJson.data}
                        layout={{
                          ...(plotJson.layout || {}),
                          paper_bgcolor: "rgba(0,0,0,0)",
                          plot_bgcolor: "rgba(0,0,0,0)",
                          font: { color: "#e7eefc" },
                        }}
                        frames={plotJson.frames}
                        config={{ displaylogo: false, responsive: true }}
                        onInitialized={(_figure: any, div: any) => setGraphDiv(div)}
                        onUpdate={(_figure: any, div: any) => setGraphDiv(div)}
                        style={{ width: "100%", height: "420px" }}
                      />
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
