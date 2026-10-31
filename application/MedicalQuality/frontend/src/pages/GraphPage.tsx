import { Component, useEffect, useRef, useState, type ReactNode } from "react";
import {
  ArrowLeft,
  Command as CommandIcon,
  Download,
  Expand,
  FileCode2,
  FileText,
  HelpCircle,
  Layers,
  Network,
  PanelLeftClose,
  Search,
  Upload,
  X,
} from "lucide-react";
import { api, command, navigate, post, type Data } from "../api";
import {
  Badge,
  ErrorBox,
  Loading,
  Modal,
  Notice,
  PdfEvidencePreview,
  useApi,
} from "../ui";
import { OntologyGraph } from "../vendor/ontology-playground/components/OntologyGraph";
import { InspectorPanel } from "../vendor/ontology-playground/components/InspectorPanel";
import { SearchFilter } from "../vendor/ontology-playground/components/SearchFilter";
import { PathFinderPanel } from "../vendor/ontology-playground/components/PathFinderPanel";
import { OntologyStatsPanel } from "../vendor/ontology-playground/components/OntologyStatsPanel";
import { QueryPlayground } from "../vendor/ontology-playground/components/QueryPlayground";
import { OntologyDesigner } from "../vendor/ontology-playground/components/OntologyDesigner";
import { CommandPalette } from "../vendor/ontology-playground/components/CommandPalette";
import { HelpModal } from "../vendor/ontology-playground/components/HelpModal";
import {
  useAppStore,
  themeClass,
  type ThemeId,
} from "../vendor/ontology-playground/store/appStore";
import { useDesignerStore } from "../vendor/ontology-playground/store/designerStore";
import { parseRDF } from "../vendor/ontology-playground/lib/rdf/parser";
import { serializeToRDF } from "../vendor/ontology-playground/lib/rdf/serializer";
import type { Ontology } from "../vendor/ontology-playground/data/ontology";
import "../vendor/ontology-playground/styles/app.css";

const blank: Ontology = {
  name: "",
  description: "",
  entityTypes: [],
  relationships: [],
};
// Keep the medical workspace preference separate from the upstream demo's
// legacy dark default, including browsers that already cached that default.
const medicalThemeKey = "mq.graph.theme";
let initialMedicalTheme: ThemeId = "light";
try {
  const saved = localStorage.getItem(medicalThemeKey);
  if (["light", "dark", "aurora", "crimson"].includes(saved || ""))
    initialMedicalTheme = saved as ThemeId;
} catch {
  // The light default also works when browser storage is unavailable.
}
useAppStore.getState().setTheme(initialMedicalTheme);

function chooseMedicalTheme(theme: ThemeId) {
  useAppStore.getState().setTheme(theme);
  try {
    localStorage.setItem(medicalThemeKey, theme);
  } catch {
    // The active theme remains usable without persistence.
  }
}
const kinds: Record<string, string> = {
  class: "本體類型",
  concept: "術語概念",
  instance: "病例實例",
  document: "文書版本",
  evidence: "原文證據",
  assertion: "來源斷言",
  rule: "規則版本",
  finding: "疑似問題",
  decision: "責任意見",
};

class GraphBoundary extends Component<
  { children: ReactNode; onFallback: () => void },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <div className="graph-error">
        <h3>圖譜暫時無法渲染</h3>
        <p>原文和結構化對象仍可查看；恢復後繼續當前版本。</p>
        <button onClick={this.props.onFallback}>查看對象列表</button>
        <button onClick={() => this.setState({ failed: false })}>
          重試圖譜
        </button>
      </div>
    ) : (
      this.props.children
    );
  }
}

export function GraphPage({ session }: { session: Data }) {
  const query = new URLSearchParams(location.search);
  const kind = query.get("view") || "ontology";
  const scope = query.get("case") || query.get("rule") || "";
  const run = query.get("run") || "";
  const [releaseId, setReleaseId] = useState(
    query.get("release") || "semantic-v1",
  );
  const [revision, setRevision] = useState(0);
  const request =
    "/knowledge-graphs/views?" +
    new URLSearchParams({
      view_kind: kind,
      scope_ref: scope,
      release_id: releaseId,
      ...(run ? { run_id: run } : {}),
    });
  const { data, error, loading } = useApi<Data>(request, revision);
  const { data: cases } = useApi<Data>(
    session.permissions.includes("cases") ? "/cases?page_size=50" : null,
  );
  const { data: releases } = useApi<Data>("/semantic/releases");
  const [leftOpen, setLeftOpen] = useState(innerWidth >= 1360);
  const [focus, setFocus] = useState(false);
  const [listMode, setListMode] = useState(false);
  const [listQuery, setListQuery] = useState("");
  const [palette, setPalette] = useState(false);
  const [help, setHelp] = useState(false);
  const [sourceView, setSourceView] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [draftsOpen, setDraftsOpen] = useState(false);
  const [editor, setEditor] = useState(false);
  const [draft, setDraft] = useState<Data | null>(null);
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const [busy, setBusy] = useState(false);
  const [evidenceId, setEvidenceId] = useState("");
  const evidence = useApi<Data>(evidenceId ? "/evidence/" + evidenceId : null);
  const [detailTab, setDetailTab] = useState("definition");
  const [preview, setPreview] = useState(false);
  const [candidateMeta, setCandidateMeta] = useState<Data | null>(null);
  const selectedEntityId = useAppStore((s) => s.selectedEntityId),
    selectedRelationshipId = useAppStore((s) => s.selectedRelationshipId);
  const theme = useAppStore((s) => s.theme);
  const loadOntology = useAppStore((s) => s.loadOntology);
  const selectEntity = useAppStore((s) => s.selectEntity);
  const selectRelationship = useAppStore((s) => s.selectRelationship);
  const selected = selectedRelationshipId || selectedEntityId;
  const meta =
    data &&
    (selectedRelationshipId
      ? data.edge_meta[selectedRelationshipId]
      : data.node_meta[selectedEntityId || ""]);
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      loadOntology(blank, []);
      useDesignerStore.getState().resetDraft();
    };
  }, []);
  useEffect(() => {
    loadOntology(blank, []);
    setEvidenceId("");
    setPreview(false);
  }, [request]);
  useEffect(() => {
    if (data) {
      loadOntology(data.ontology, data.bindings);
      if (query.get("focus")) selectEntity(query.get("focus"));
    }
  }, [data]);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const input = (e.target as HTMLElement)?.closest("input,textarea,select");
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setPalette((v) => !v);
      }
      if (!input && e.key === "?") setHelp(true);
      if (e.key === "Escape") {
        setEvidenceId("");
        setPalette(false);
        setHelp(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  const changeView = (view: string, id = "") => {
    setEditor(false);
    setDraft(null);
    setNotice("");
    navigate(
      "/graph?" +
        new URLSearchParams({
          view,
          ...(view === "case" && id ? { case: id } : {}),
          ...(view === "rule" && id ? { rule: id } : {}),
          ...(query.get("return") ? { return: query.get("return")! } : {}),
        }),
    );
  };
  const authorize = async (exportKind: string) => {
    if (!data || preview) {
      setActionError("候選預覽需先保存並核對導出範圍。");
      return null;
    }
    try {
      return await post("/knowledge-graphs/export-authorizations", {
        kind: exportKind,
        view_kind: kind,
        scope_ref: scope || undefined,
        release_id: data.version_refs.semantic_release_id,
        run_id: run || undefined,
        projection_digest: data.projection_digest,
        purpose: "當前授權範圍內本地核查",
      });
    } catch (e) {
      setActionError((e as Error).message);
      return null;
    }
  };
  const download = (content: string, type: string, name: string) => {
    const url = URL.createObjectURL(new Blob([content], { type }));
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  };
  const exportJson = async () => {
    const permit = await authorize("projection_json");
    if (permit)
      download(
        JSON.stringify(permit.view, null, 2),
        "application/json",
        "醫療知識圖譜-顯示投影.json",
      );
  };
  const startEditor = () => {
    if (!data) return;
    if (!preview) {
      useDesignerStore.getState().loadDraft(data.ontology);
      setDraft(null);
      setCandidateMeta(null);
    }
    setEditor(true);
    setNotice("候選編輯與正式語義版本分離。保存不會直接發佈。");
  };
  const save = async () => {
    setBusy(true);
    setActionError("");
    try {
      const ontology = useDesignerStore.getState().ontology;
      const payload = {
        ontology,
        base_release_id: releaseId,
        metadata_map: candidateMeta || {
          node_meta: data?.node_meta || {},
          edge_meta: data?.edge_meta || {},
        },
        loss_report: candidateMeta?.loss_report || [],
      };
      const result = draft
        ? await api("/knowledge-graphs/drafts/" + draft.id, {
            method: "PATCH",
            body: JSON.stringify(
              command(draft.version, "保存本體定義候選", payload),
            ),
          })
        : await post("/knowledge-graphs/drafts", payload);
      setDraft(result);
      setNotice("候選已保存 · v" + result.version + "，尚未生效。");
      return result;
    } catch (e) {
      setActionError((e as Error).message);
      return null;
    } finally {
      setBusy(false);
    }
  };
  const submit = async () => {
    const saved = await save();
    if (!saved) return;
    try {
      const result = await post(
        "/knowledge-graphs/drafts/" + saved.id + "/submit",
        command(saved.version, "提交術語、關係與約束候選進行專業審核"),
      );
      setDraft(result);
      setNotice("已進入內部審核。正式本體和病例運行仍使用原基線。");
    } catch (e) {
      setActionError((e as Error).message);
    }
  };
  const validateDraft = () => {
    const o = useDesignerStore.getState().ontology;
    const ids = new Set(o.entityTypes.map((e) => e.id));
    const problems = o.entityTypes
      .filter((e) => !e.id || !e.name || !e.description)
      .map((e) => ({ message: "請補齊名稱、定義與穩定標識", entityId: e.id }));
    for (const edge of o.relationships) {
      if (!ids.has(edge.from) || !ids.has(edge.to))
        problems.push({ message: "關係端點缺失", entityId: edge.from });
    }
    useDesignerStore.setState({
      validationErrors: problems,
      _lastValidatedAt: Date.now(),
    });
    setNotice(
      problems.length
        ? "候選結構仍有缺口。"
        : "候選結構檢查完成；仍需 OWL/SHACL、專業定義及許可審核。",
    );
  };
  const exportRdf = async () => {
    const permit = await authorize("native_rdf");
    if (!permit) return;
    const o = structuredClone(permit.view.ontology);
    o.relationships = o.relationships.map((r: Data) => ({
      ...r,
      cardinalityKnown:
        permit.view.edge_meta[r.id]?.cardinality_status !== "unknown",
    }));
    download(
      serializeToRDF(o, permit.view.bindings),
      "application/rdf+xml",
      "醫療本體-原生可交換子集.rdf",
    );
    setNotice(
      "已導出原生支持子集；完整 OWL/SHACL 與未表示公理仍以正式包為準。",
    );
  };
  const exportDraft = async () => {
    const saved = await save();
    if (!saved) return;
    try {
      const result = await post("/knowledge-graphs/export-authorizations", {
        kind: "native_rdf",
        draft_id: saved.id,
        draft_version: saved.version,
      });
      const snapshot = structuredClone(result.draft.ontology);
      const edgeMeta = result.draft.metadata_map?.edge_meta || {};
      snapshot.relationships = snapshot.relationships.map((r: Data) => ({
        ...r,
        cardinalityKnown:
          edgeMeta[r.id]?.cardinality_status === "unknown"
            ? false
            : r.cardinalityKnown,
      }));
      download(
        serializeToRDF(snapshot, []),
        "application/rdf+xml",
        "醫療本體-未批准候選.rdf",
      );
      setNotice("候選已導出；包含未批准標識，不代表完整正式本體包。");
    } catch (e) {
      setActionError((e as Error).message);
    }
  };
  const exportPackage = async () => {
    try {
      const response = await fetch(
        "/api/v1/semantic/releases/" +
          encodeURIComponent(
            data?.version_refs.semantic_release_id || releaseId,
          ) +
          "/package",
        { credentials: "same-origin" },
      );
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || "本體包導出失敗");
      }
      const url = URL.createObjectURL(await response.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = "醫療質控-完整本體包.zip";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setActionError((e as Error).message);
    }
  };
  const commands = [
    {
      id: "search",
      label: "搜索實體與關係",
      icon: <Search size={16} />,
      action: () => setLeftOpen(true),
    },
    {
      id: "fit",
      label: "進入 / 退出專注視圖",
      icon: <Expand size={16} />,
      action: () => setFocus((v) => !v),
    },
    {
      id: "source",
      label: "查看 RDF/XML 源碼",
      icon: <FileCode2 size={16} />,
      action: () => setSourceView(true),
    },
    {
      id: "designer",
      label: "設計本體候選",
      icon: <Network size={16} />,
      action: startEditor,
      hidden: !data?.capabilities.edit,
    },
    {
      id: "help",
      label: "快捷鍵與原生圖譜幫助",
      icon: <HelpCircle size={16} />,
      action: () => setHelp(true),
    },
  ];
  const onExitEditor = () => {
    const changed =
      !draft ||
      JSON.stringify(useDesignerStore.getState().ontology) !==
        JSON.stringify(draft.ontology);
    if (changed && !confirm("當前候選有未保存修改。放棄此次編輯並返回圖譜？"))
      return;
    setEditor(false);
    setRevision((r) => r + 1);
  };
  return (
    <div className={"knowledge-page " + (focus ? "focus-mode" : "")}>
      <header className="graph-page-heading">
        <div>
          {query.get("return") && (
            <button
              className="text-button"
              onClick={() => navigate(query.get("return")!)}
            >
              <ArrowLeft size={16} />
              返回原任務
            </button>
          )}
          <div className="eyebrow">KNOWLEDGE WORKSPACE</div>
          <h1>知識圖譜</h1>
          <p>理解術語，連接證據，回到每一條判斷的來源。</p>
        </div>
        <div className="title-actions">
          {session.permissions.includes("draft") && (
            <button
              className="secondary compact"
              onClick={() => setDraftsOpen(true)}
            >
              候選與審核
            </button>
          )}
          <button
            className="secondary compact"
            onClick={() => setPalette(true)}
          >
            <CommandIcon size={16} />
            快捷操作
          </button>
          <button
            className="secondary compact"
            onClick={() => setImportOpen(true)}
            disabled={!session.permissions.includes("draft")}
          >
            <Upload size={16} />
            導入候選
          </button>
          <button
            className="primary compact"
            disabled={!data?.capabilities.edit || busy}
            onClick={startEditor}
          >
            <Network size={16} />
            設計本體
          </button>
        </div>
      </header>
      <ErrorBox message={actionError || error} />
      {error && (
        <button className="secondary" onClick={() => setRevision((v) => v + 1)}>
          重試當前圖譜
        </button>
      )}
      {notice && (
        <div className="graph-notice" role="status">
          {notice}
          <button onClick={() => setNotice("")} aria-label="關閉提示">
            <X size={14} />
          </button>
        </div>
      )}
      <div className={"native-workspace app-container " + themeClass(theme)}>
        <div className="graph-workspace-toolbar">
          <div className="graph-tabs">
            {[
              ["ontology", "本體與術語"],
              ["case", "病例證據"],
              ["rule", "規則影響"],
            ].map(([key, name]) => (
              <button
                key={key}
                className={kind === key ? "active" : ""}
                disabled={
                  key === "case" && !session.permissions.includes("cases")
                }
                onClick={() =>
                  changeView(
                    key,
                    key === "case" ? cases?.items[0]?.id || "" : "",
                  )
                }
              >
                {name}
              </button>
            ))}
          </div>
          <div className="graph-toolbar-actions">
            {kind === "case" && (
              <select
                aria-label="圖譜病例"
                value={scope}
                onChange={(e) => changeView("case", e.target.value)}
              >
                {cases?.items.map((c: Data) => (
                  <option key={c.id} value={c.id}>
                    {c.display_name} · {c.encounter_id}
                  </option>
                ))}
              </select>
            )}
            <select
              aria-label="語義版本"
              value={releaseId}
              onChange={(e) => setReleaseId(e.target.value)}
            >
              {releases?.items.map((r: Data) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
            <select
              aria-label="圖譜主題"
              value={theme}
              onChange={(e) =>
                chooseMedicalTheme(e.target.value as ThemeId)
              }
            >
              <option value="light">淺色</option>
              <option value="dark">深色</option>
              <option value="aurora">極光</option>
              <option value="crimson">緋紅</option>
            </select>
            <button title="擴大圖譜" onClick={() => setFocus((v) => !v)}>
              <Expand size={17} />
            </button>
            <button title="圖譜幫助" onClick={() => setHelp(true)}>
              <HelpCircle size={17} />
            </button>
          </div>
        </div>
        {editor ? (
          <div className="medical-designer">
            <div className="draft-banner">
              <Badge value={draft?.status || "draft"} />
              <span>
                {draft
                  ? "候選 " + draft.id.slice(0, 8) + " · v" + draft.version
                  : "基於 " + releaseId + " 的新候選"}
              </span>
              <span>原生可視化設計器 · 不直接發佈</span>
            </div>
            <OntologyDesigner
              route={{ page: "designer" }}
              medical={{
                onBack: onExitEditor,
                onSave: () => void save(),
                onSubmit: () => void submit(),
                onValidate: validateDraft,
                onExport: () => void exportDraft(),
                onPreview: () => {
                  loadOntology(useDesignerStore.getState().ontology, []);
                  setEditor(false);
                  setPreview(true);
                  setNotice("正在查看候選預覽，正式語義版本未改變。");
                },
              }}
            />
          </div>
        ) : loading ? (
          <Loading />
        ) : data ? (
          <>
            <div
              className={
                "graph-split " +
                (leftOpen ? "" : "left-collapsed") +
                (evidenceId ? " evidence-open" : "") +
                (!selected && !evidenceId ? " inspector-collapsed" : "")
              }
            >
              <aside className="graph-explorer">
                <div className="explorer-heading">
                  <h2>探索關係</h2>
                  <button title="收起探索欄" onClick={() => setLeftOpen(false)}>
                    <PanelLeftClose size={16} />
                  </button>
                </div>
                <SearchFilter
                  medical
                  entityLabel={kind === "ontology" ? "概念類型" : "對象"}
                />
                <PathFinderPanel medical />
                <OntologyStatsPanel medical />
                <details className="native-query">
                  <summary>
                    圖譜查詢 <span>當前已加載範圍</span>
                  </summary>
                  <QueryPlayground medical />
                </details>
                <div className="graph-explorer-footer">
                  <button onClick={() => setListMode((v) => !v)}>
                    <Layers size={15} />
                    {listMode ? "回到畫布" : "全部對象列表"}
                  </button>
                  <button onClick={() => setSourceView(true)}>
                    <FileCode2 size={15} />
                    RDF 源碼
                  </button>
                </div>
              </aside>
              <section className="graph-stage">
                <div className="canvas-topline">
                  {!leftOpen && (
                    <button
                      title="打開探索欄"
                      onClick={() => setLeftOpen(true)}
                    >
                      <Search size={16} />
                      搜索與路徑
                    </button>
                  )}
                  <span>
                    <span className="graph-live-dot" />
                    {preview
                      ? "候選預覽"
                      : kind === "ontology"
                        ? "本體類型關係"
                        : kind === "case"
                          ? "病例證據關係"
                          : "規則與概念關係"}
                  </span>
                  <span className="canvas-hint">拖動探索 · 雙擊聚焦鄰域</span>
                </div>
                {listMode ? (
                  <div className="graph-object-list">
                    <input
                      aria-label="搜索全部圖對象"
                      placeholder="搜索中文名稱、定義或標識"
                      value={listQuery}
                      onChange={(e) => setListQuery(e.target.value)}
                    />
                    {[
                      ...data.ontology.entityTypes,
                      ...data.ontology.relationships,
                    ]
                      .filter((x: Data) =>
                        (x.name + " " + x.description + " " + x.id)
                          .toLowerCase()
                          .includes(listQuery.toLowerCase()),
                      )
                      .map((x: Data) => (
                        <button
                          key={x.id}
                          onClick={() => {
                            x.from
                              ? selectRelationship(x.id)
                              : selectEntity(x.id);
                            setListMode(false);
                          }}
                        >
                          <span style={{ color: x.color }}>
                            {x.icon || "↗"}
                          </span>
                          <strong>{x.name}</strong>
                          <small>
                            {x.from
                              ? "關係"
                              : kinds[data.node_meta[x.id]?.semantic_kind] ||
                                "對象"}
                          </small>
                        </button>
                      ))}
                  </div>
                ) : (
                  <GraphBoundary onFallback={() => setListMode(true)}>
                    <OntologyGraph
                      medicalLayout
                      legendTitle={
                        kind === "ontology" ? "本體類型" : "證據與業務對象"
                      }
                      authorizeDownload={async () =>
                        Boolean(await authorize("png"))
                      }
                    />
                  </GraphBoundary>
                )}
              </section>
              {evidenceId ? (
                <aside className="graph-evidence">
                  <header>
                    <strong>固定版本原文</strong>
                    <button
                      aria-label="關閉原文"
                      onClick={() => setEvidenceId("")}
                    >
                      <X size={18} />
                    </button>
                  </header>
                  {evidence.loading ? (
                    <Loading />
                  ) : evidence.error ? (
                    <ErrorBox message={evidence.error} />
                  ) : (
                    <>
                      <h3>{evidence.data?.document?.title || "來源記錄"}</h3>
                      {evidence.data?.evidence.envelope.locator.type ===
                        "pdf" && (
                        <PdfEvidencePreview
                          id={evidenceId}
                          page={evidence.data.evidence.envelope.locator.page}
                        />
                      )}
                      <div className="source-lines">
                        {(
                          evidence.data?.document?.content ||
                          evidence.data?.evidence.envelope.content.text ||
                          ""
                        )
                          .split("\n")
                          .map((line: string, i: number) => (
                            <div
                              key={i}
                              className={
                                evidence.data?.evidence.envelope.locator
                                  .line_start ===
                                i + 1
                                  ? "highlighted-line"
                                  : ""
                              }
                            >
                              <span>{i + 1}</span>
                              <p>{line}</p>
                            </div>
                          ))}
                      </div>
                    </>
                  )}
                </aside>
              ) : (
                <aside className="graph-inspector">
                  <div className="inspector-tabs">
                    {[
                      ["definition", "對象詳情"],
                      ["provenance", "來源與版本"],
                    ].map(([key, title]) => (
                      <button
                        key={key}
                        className={detailTab === key ? "active" : ""}
                        onClick={() => setDetailTab(key)}
                      >
                        {title}
                      </button>
                    ))}
                  </div>
                  {detailTab === "definition" ? (
                    <>
                      <InspectorPanel
                        metadata={{ ...data.node_meta, ...data.edge_meta }}
                      />
                      {meta && (
                        <div className="medical-inspector">
                          <div className="metadata-kind">
                            {kinds[meta.semantic_kind] || "關係依據"}
                          </div>
                          {meta.assertion && (
                            <>
                              <h3>斷言語境</h3>
                              <dl>
                                <dt>主體</dt>
                                <dd>
                                  {{
                                    patient: "患者",
                                    family: "家屬",
                                    other: "其他",
                                    unknown: "未知",
                                  }[meta.assertion.subject as string] ||
                                    meta.assertion.subject}
                                </dd>
                                <dt>極性</dt>
                                <dd>
                                  {
                                    {
                                      affirmed: "肯定記載",
                                      negated: "否定記載",
                                      uncertain: "不確定",
                                      hypothetical: "假設",
                                    }[meta.assertion.polarity as string]
                                  }
                                </dd>
                                <dt>時間</dt>
                                <dd>{meta.assertion.temporality}</dd>
                              </dl>
                              <Notice>
                                原文中的主張，不自動等同患者事實。
                              </Notice>
                            </>
                          )}
                          {meta.evidence_id && (
                            <button
                              className="inspector-primary"
                              onClick={() => setEvidenceId(meta.evidence_id)}
                            >
                              <FileText size={15} />
                              並列查看原文
                            </button>
                          )}
                          {meta.assertion?.evidence_ids?.map((eid: string) => (
                            <button
                              key={eid}
                              className="inspector-primary"
                              onClick={() => setEvidenceId(eid)}
                            >
                              查看支持原文
                            </button>
                          ))}
                          {meta.support_refs
                            ?.filter(
                              (id: string) => data.node_meta[id]?.evidence_id,
                            )
                            .map((id: string) => (
                              <button
                                key={id}
                                className="inspector-primary"
                                onClick={() => setEvidenceId(id)}
                              >
                                查看關係證據
                              </button>
                            ))}
                          {meta.rule_id && (
                            <button
                              className="inspector-primary"
                              onClick={() =>
                                navigate("/rules?rule=" + meta.rule_id)
                              }
                            >
                              查看規則與依據
                            </button>
                          )}
                          {meta.case_id && (
                            <button
                              className="inspector-primary"
                              onClick={() => navigate("/cases/" + meta.case_id)}
                            >
                              返回病例處理
                            </button>
                          )}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="medical-inspector">
                      <h3>{selected ? "當前選中對象" : "當前圖譜基線"}</h3>
                      <dl>
                        {Object.entries(meta || data.version_refs)
                          .filter(
                            ([k]) => !["assertion", "support_refs"].includes(k),
                          )
                          .map(([k, v]) => (
                            <div key={k}>
                              <dt>
                                {(
                                  {
                                    original_iri: "原始 IRI",
                                    source_ref: "來源依據",
                                    approval_status: "審核狀態",
                                    version: "版本",
                                    semantic_kind: "對象類型",
                                    source_role: "來源類別",
                                    cardinality_status: "基數狀態",
                                  } as Data
                                )[k] || k}
                              </dt>
                              <dd>
                                {typeof v === "object"
                                  ? JSON.stringify(v)
                                  : String(v)}
                              </dd>
                            </div>
                          ))}
                      </dl>
                      <h3>固定版本集合</h3>
                      <pre>{JSON.stringify(data.version_refs, null, 2)}</pre>
                      {data.gaps.length > 0 && (
                        <Notice>{data.gaps.join("；")}</Notice>
                      )}
                      <p>圖的位置與最短路徑不表示臨床因果或診斷結果。</p>
                    </div>
                  )}
                </aside>
              )}
            </div>
            <footer className="graph-statusbar">
              <span>
                {data.loaded_counts.nodes} 個節點 · {data.loaded_counts.edges}{" "}
                條關係
              </span>
              <span>
                {kind === "case" ? "固定病例範圍" : "已加載語義範圍"} ·{" "}
                {data.version_refs.semantic_release_id}
              </span>
              <div>
                <button onClick={() => void exportJson()}>
                  <Download size={14} />
                  顯示投影
                </button>
                {kind === "ontology" && (
                  <>
                    <button onClick={() => void exportRdf()}>RDF 子集</button>
                    <button onClick={() => void exportPackage()}>
                      完整本體包
                    </button>
                  </>
                )}
                <span>Ontology-Playground 原生渲染</span>
              </div>
            </footer>
          </>
        ) : null}
      </div>
      <CommandPalette
        open={palette}
        onClose={() => setPalette(false)}
        commands={commands}
      />
      {help && (
        <div className={"native-modal-scope " + themeClass(theme)}>
          <HelpModal medical onClose={() => setHelp(false)} />
        </div>
      )}
      {sourceView && (
        <Modal
          title="原生 RDF/XML · 顯示子集"
          wide
          onClose={() => setSourceView(false)}
        >
          <Notice>
            {kind !== "ontology"
              ? "當前圖中包含業務實例，禁止序列化成 OWL 類；下面展示完整顯示投影。"
              : "本視圖用於核對原生可交換子集；複雜 OWL/SHACL 以正式包為準。"}
          </Notice>
          <pre className="code-view">
            {kind !== "ontology"
              ? JSON.stringify(data, null, 2)
              : serializeToRDF(
                  useAppStore.getState().currentOntology,
                  useAppStore.getState().dataBindings,
                )}
          </pre>
        </Modal>
      )}
      {draftsOpen && (
        <DraftQueue
          session={session}
          onClose={() => setDraftsOpen(false)}
          onOpen={(d) => {
            setDraft(d);
            setCandidateMeta({ ...d.metadata_map, loss_report: d.loss_report });
            useDesignerStore.getState().loadDraft(d.ontology);
            setEditor(true);
            setDraftsOpen(false);
            setNotice("已恢復保存的候選 v" + d.version + "。");
          }}
          onPublished={(id) => {
            setDraftsOpen(false);
            setReleaseId(id);
            setRevision((v) => v + 1);
            setEditor(false);
            setNotice("本體版本已形成；已有病例運行仍保持原固定基線。");
          }}
        />
      )}
      {importOpen && (
        <ImportDialog
          onClose={() => setImportOpen(false)}
          onImport={async (result) => {
            setCandidateMeta({
              node_meta: result.node_meta || {},
              edge_meta: result.edge_meta || {},
              original_ref: result.original_ref,
              original_digest: result.original_digest,
              loss_report: result.loss_report || [],
            });
            useDesignerStore.getState().loadDraft(result.ontology);
            setDraft(null);
            setEditor(true);
            setImportOpen(false);
            setNotice(
              result.loss_report?.length
                ? "導入存在未表達語義，需核對原始包；不能直接發佈。"
                : "導入為候選，尚未生效。",
            );
          }}
        />
      )}
    </div>
  );
}

function ImportDialog({
  onClose,
  onImport,
}: {
  onClose: () => void;
  onImport: (data: Data) => void;
}) {
  const [text, setText] = useState("");
  const [format, setFormat] = useState("xml");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <Modal title="導入本體候選" wide onClose={onClose}>
      <Notice>
        原生 RDF/XML 與 JSON 子集保留；Turtle
        通過域內正式解析器轉換，語義損失會單獨報告。導入不會覆蓋正式版本。
      </Notice>
      <label>
        讀取文件
        <input
          type="file"
          accept=".rdf,.owl,.xml,.ttl,.json"
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (!f) return;
            if (f.size > 5 * 1024 * 1024) {
              setError("文件超過 5 MiB。");
              return;
            }
            setText(await f.text());
            setFormat(
              f.name.endsWith(".ttl")
                ? "turtle"
                : f.name.endsWith(".json")
                  ? "json"
                  : "xml",
            );
          }}
        />
      </label>
      <label>
        格式
        <select value={format} onChange={(e) => setFormat(e.target.value)}>
          <option value="xml">RDF/XML · 原生支持子集</option>
          <option value="json">原生 JSON</option>
          <option value="turtle">Turtle · 正式適配</option>
        </select>
      </label>
      <textarea
        className="code-editor"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="粘貼本體內容，或從本地選擇文件"
      />
      <ErrorBox message={error} />
      <div className="modal-actions">
        <button className="secondary" onClick={onClose}>
          取消
        </button>
        <button
          className="primary"
          disabled={busy || !text}
          onClick={async () => {
            setBusy(true);
            setError("");
            try {
              const result = await post("/knowledge-graphs/import", {
                content: text,
                format,
              });
              if (format === "xml") {
                const native = parseRDF(text, true);
                result.ontology = native.ontology;
                result.bindings = native.bindings;
                result.node_meta = Object.fromEntries(
                  native.ontology.entityTypes.map((n) => [
                    n.id,
                    {
                      semantic_kind: "class",
                      original_iri: n.iri,
                      source_ref: result.original_ref,
                      approval_status: "candidate",
                    },
                  ]),
                );
                result.edge_meta = Object.fromEntries(
                  native.ontology.relationships.map((r) => [
                    r.id,
                    {
                      predicate_ref: r.iri,
                      cardinality_status:
                        r.cardinalityKnown === false ? "unknown" : "declared",
                      source_ref: result.original_ref,
                    },
                  ]),
                );
              }
              onImport(result);
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          {busy ? "正在核對…" : "讀取為候選"}
        </button>
      </div>
    </Modal>
  );
}

function DraftQueue({
  session,
  onClose,
  onOpen,
  onPublished,
}: {
  session: Data;
  onClose: () => void;
  onOpen: (d: Data) => void;
  onPublished: (id: string) => void;
}) {
  const [revision, setRevision] = useState(0);
  const { data, error, loading } = useApi<Data>(
    "/knowledge-graphs/drafts",
    revision,
  );
  const [selected, setSelected] = useState<Data | null>(null);
  const [reason, setReason] = useState("");
  const [failure, setFailure] = useState("");
  const [busy, setBusy] = useState(false);
  async function review(decision: string) {
    if (!selected || !reason.trim()) return;
    setBusy(true);
    try {
      const result = await post(
        "/knowledge-graphs/drafts/" + selected.id + "/review",
        command(selected.version, reason, { decision }),
      );
      if (result.semantic_release_id) onPublished(result.semantic_release_id);
      else {
        setSelected(null);
        setRevision((v) => v + 1);
      }
    } catch (e) {
      setFailure((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title="本體候選與責任審核" wide onClose={onClose}>
      <Notice>
        本地審核記錄屬於工程驗證。完整形式檢查成功後生成獨立版本；不會替換歷史運行或自動獲得臨床批准。
      </Notice>
      <ErrorBox message={error || failure} />
      {loading ? (
        <Loading />
      ) : data?.items.length ? (
        <table className="data-table">
          <thead>
            <tr>
              <th>候選</th>
              <th>狀態 / 版本</th>
              <th>責任</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data.items.map((d: Data) => (
              <tr key={d.id}>
                <td>
                  <strong>{d.ontology.name}</strong>
                  <small className="cell-sub">基於 {d.base_release_id}</small>
                </td>
                <td>
                  <Badge value={d.status} /> v{d.version}
                </td>
                <td>
                  {d.review.reviewer_name || d.review.reviewer_id || "尚未提交"}
                </td>
                <td>
                  {d.actor_id === session.actor.id && d.status === "draft" ? (
                    <button className="text-button" onClick={() => onOpen(d)}>
                      繼續編輯
                    </button>
                  ) : (
                    <button
                      className="text-button"
                      onClick={() => setSelected(d)}
                    >
                      查看與審核
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="muted">暫無本人候選或獲派審核事項。</p>
      )}
      {selected && (
        <section className="draft-review-detail">
          <h3>
            {selected.ontology.name} · v{selected.version}
          </h3>
          <p>
            {selected.ontology.entityTypes.length} 個類型 ·{" "}
            {selected.ontology.relationships.length} 條關係
          </p>
          <details>
            <summary>核查定義與原生數據</summary>
            <pre className="code-view">
              {JSON.stringify(selected.ontology, null, 2)}
            </pre>
          </details>
          {selected.loss_report.length > 0 && (
            <Notice>
              存在未解決的轉換損失：{JSON.stringify(selected.loss_report)}
            </Notice>
          )}
          {selected.review.reviewer_id === session.actor.id &&
            selected.status === "in_review" && (
              <>
                <label>
                  審核依據與責任意見
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </label>
                <div className="modal-actions">
                  <button
                    className="secondary"
                    disabled={!reason.trim() || busy}
                    onClick={() => void review("reject")}
                  >
                    退回維護者
                  </button>
                  <button
                    className="primary"
                    disabled={!reason.trim() || busy}
                    onClick={() => void review("approve")}
                  >
                    {busy ? "正在執行形式檢查…" : "記錄審核並構建版本"}
                  </button>
                </div>
              </>
            )}
          {selected.review.history?.map((r: Data, i: number) => (
            <p className="muted" key={i}>
              {r.actor_name}：{r.reason} ·{" "}
              {r.identity_mode === "local" ? "工程身份" : "已認證身份"}
            </p>
          ))}
        </section>
      )}
    </Modal>
  );
}
