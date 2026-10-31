import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Download,
  FileText,
  FolderInput,
  LockKeyhole,
  Network,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Upload,
  X,
} from "lucide-react";
import {
  api,
  command,
  navigate,
  post,
  riskNames,
  roleNames,
  statusNames,
  when,
  type Data,
} from "../api";
import {
  Badge,
  Empty,
  ErrorBox,
  Loading,
  Modal,
  Notice,
  PageTitle,
  PdfEvidencePreview,
  useApi,
} from "../ui";

export function SourcesPage() {
  const sourceParams = new URLSearchParams(location.search);
  const [revision, setRevision] = useState(0);
  const { data, error, loading } = useApi<Data>("/sources", revision);
  const catalogue = useApi<Data>("/sources/catalogue");
  const [open, setOpen] = useState(false);
  const [failure, setFailure] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");
  const [selected, setSelected] = useState<Data | null>(null);
  const [schema, setSchema] = useState<Data | null>(null);
  const [evidenceSource, setEvidenceSource] = useState<Data | null>(null);
  const [structuredSource, setStructuredSource] = useState<Data | null>(null);
  const [query, setQuery] = useState(sourceParams.get("q") || "");
  const [format, setFormat] = useState(sourceParams.get("format") || "");
  const [page, setPage] = useState(
    Math.max(1, Math.floor(Number(sourceParams.get("page")) || 1)),
  );
  useEffect(() => {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (format) params.set("format", format);
    if (page > 1) params.set("page", String(page));
    history.replaceState(
      {},
      "",
      "/sources" + (params.size ? "?" + params : ""),
    );
  }, [query, format, page]);
  const filtered = (data?.items || []).filter(
    (source: Data) =>
      (!format || source.format === format) &&
      (source.name + " " + source.namespace)
        .toLowerCase()
        .includes(query.trim().toLowerCase()),
  );
  const pages = Math.max(1, Math.ceil(filtered.length / 8));
  const currentPage = Math.min(page, pages);
  const visible = filtered.slice((currentPage - 1) * 8, currentPage * 8);
  async function register(key: string) {
    setBusy(key);
    setFailure("");
    try {
      await post("/sources", { catalogue_key: key });
      setRevision((v) => v + 1);
      setMessage("資料來源與固定版本已登記。");
    } catch (e) {
      setFailure((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function parse(source: Data) {
    setBusy(source.id);
    setFailure("");
    try {
      const job = await post(
        "/source-versions/" + source.id + "/parse-runs",
        command(source.version, "在當前聲明範圍讀取結構與證據", {
          limit: 100,
          max_pages: 20,
        }),
      );
      setMessage("作業已受理；只統計聲明範圍，未覆蓋部分會保留。");
      let completed = false;
      for (let n = 0; n < 60; n++) {
        await new Promise((r) => setTimeout(r, 1000));
        const current = await api("/jobs/" + job.id);
        if (["completed", "failed"].includes(current.status)) {
          completed = true;
          setMessage(
            current.status === "completed"
              ? "處理已完成，可查看覆蓋、證據及缺口。"
              : "處理失敗：" + current.error_code,
          );
          break;
        }
      }
      if (!completed) setMessage("作業仍在後臺處理，稍後刷新查看。");
      setRevision((v) => v + 1);
    } catch (e) {
      setFailure((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  return (
    <div className="sources-page">
      <PageTitle
        eyebrow="數據準備 · 原始資料保持只讀"
        title="資料接入"
        description="登記來源、固定版本，保留結構、定位與未覆蓋內容。"
        action={
          <>
            <button
              className="secondary"
              onClick={() => setRevision((v) => v + 1)}
            >
              <RefreshCw size={16} />
              刷新
            </button>
            <button className="primary" onClick={() => setOpen(true)}>
              <Plus size={17} />
              登記資料
            </button>
          </>
        }
      />
      <ErrorBox message={error || failure} />
      {data?.coverage_summary && (
        <p className="muted">
          當前登記 {data.coverage_summary.expected_total} 項來源；
          {data.coverage_summary.counts.success} 項讀取完成，
          {data.coverage_summary.counts.partial}{" "}
          項部分完成，其餘保持失敗、阻斷或待處理狀態。按來源計數，不代表病例數或專業通過。
        </p>
      )}
      {message && <div className="success-message">{message}</div>}
      <section className="panel source-list">
        <div className="panel-heading">
          <h2>
            來源目錄 <span className="count">{data?.items.length ?? 0}</span>
          </h2>
          <span className="muted">登記成功不等於解析或醫學驗證通過</span>
        </div>
        <div className="toolbar">
          <label className="search-box">
            <Search size={17} />
            <input
              aria-label="篩選資料名稱"
              placeholder="按資料名稱或來源查找"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(1);
              }}
            />
          </label>
          <select
            aria-label="篩選資料格式"
            value={format}
            onChange={(event) => {
              setFormat(event.target.value);
              setPage(1);
            }}
          >
            <option value="">全部格式</option>
            {Array.from(
              new Set<string>(
                (data?.items || []).map((source: Data) => source.format),
              ),
            )
              .sort()
              .map((value) => (
                <option key={value} value={value}>
                  {value.toUpperCase()}
                </option>
              ))}
          </select>
          {(query || format) && (
            <button
              className="text-button"
              onClick={() => {
                setQuery("");
                setFormat("");
                setPage(1);
              }}
            >
              清除篩選
            </button>
          )}
        </div>
        {loading ? (
          <Loading />
        ) : visible.length ? (
          <div
            className="table-scroll"
            key={currentPage + query + format}
            role="region"
            tabIndex={0}
            aria-label="來源目錄，可滾動瀏覽"
          >
            <table className="data-table">
              <thead>
                <tr>
                  <th>資料名稱</th>
                  <th>來源 / 格式</th>
                  <th>版本</th>
                  <th>處理狀態</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((s: Data) => (
                  <tr key={s.id}>
                    <td>
                      <strong>{s.name}</strong>
                      <small className="cell-sub">{s.namespace}</small>
                    </td>
                    <td>
                      <span className="format-tag">
                        {s.format.toUpperCase()}
                      </span>
                      <small className="cell-sub">
                        {s.data_kind === "synthetic"
                          ? "合成工程資料"
                          : s.data_kind === "literature"
                            ? "文獻病例"
                            : s.data_kind === "public_deidentified"
                              ? "公開脫敏資料"
                              : s.data_kind === "unknown"
                                ? "來源待確認"
                                : "公開研究資料"}
                      </small>
                    </td>
                    <td>
                      v{s.version}
                      <small className="cell-sub mono">
                        {s.digest.slice(0, 10)}
                      </small>
                    </td>
                    <td>
                      <Badge value={s.status} />
                      {s.details.last_parse && (
                        <small className="cell-sub">
                          {s.details.last_parse.evidence_count} 項證據
                        </small>
                      )}
                    </td>
                    <td>
                      <div className="inline-actions">
                        <button
                          className="text-button"
                          onClick={() => setSelected(s)}
                        >
                          查看
                        </button>
                        {s.format === "sqlite" && (
                          <button
                            className="text-button"
                            onClick={() => setStructuredSource(s)}
                          >
                            就診查詢
                          </button>
                        )}
                        {s.format === "sqlite" && (
                          <button
                            className="text-button"
                            onClick={async () => {
                              try {
                                setSchema(
                                  await api("/sources/" + s.id + "/schema"),
                                );
                              } catch (e) {
                                setFailure((e as Error).message);
                              }
                            }}
                          >
                            結構
                          </button>
                        )}
                        <button
                          className="secondary small"
                          disabled={!!busy}
                          onClick={() => void parse(s)}
                        >
                          {busy === s.id ? "正在處理…" : "讀取與解析"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty
            title={query || format ? "未找到符合條件的資料" : "尚未登記來源"}
            description={
              query || format
                ? "調整名稱或格式篩選，查看其他已登記來源。"
                : "選擇已有本地資料，或上傳有權處理的文件。"
            }
          />
        )}
        <div className="pagination">
          <span>
            {filtered.length
              ? `第 ${(currentPage - 1) * 8 + 1}–${Math.min(currentPage * 8, filtered.length)} 條，共 ${filtered.length} 條`
              : "共 0 條"}
          </span>
          <div>
            <button
              disabled={currentPage === 1 || loading}
              onClick={() => setPage(currentPage - 1)}
            >
              上一頁
            </button>
            <span>
              {currentPage} / {pages}
            </span>
            <button
              disabled={currentPage === pages || loading}
              onClick={() => setPage(currentPage + 1)}
            >
              下一頁
            </button>
          </div>
        </div>
      </section>
      {open && (
        <Modal title="登記本地資料" wide onClose={() => setOpen(false)}>
          <Notice>
            原始數據保持只讀，參考標註與留出答案不進入建設/運行管線。
          </Notice>
          <div className="catalogue-list">
            {catalogue.data?.items.map((s: Data) => (
              <div key={s.key}>
                <FolderInput size={21} />
                <span>
                  <strong>{s.name}</strong>
                  <small>
                    {s.format} · {s.license}
                  </small>
                </span>
                <button
                  className="secondary small"
                  disabled={!!busy}
                  onClick={() => void register(s.key)}
                >
                  {busy === s.key ? "登記中…" : "登記"}
                </button>
              </div>
            ))}
          </div>
          <label className="upload-box">
            <Upload size={23} />
            <strong>上傳 PDF、Markdown、CSV、JSON 等資料</strong>
            <span>單文件 20 MiB；上傳後保持來源未確認狀態</span>
            <input
              type="file"
              onChange={async (e) => {
                const f = e.target.files?.[0];
                if (!f) return;
                const body = new FormData();
                body.append("file", f);
                setBusy("upload");
                try {
                  await api("/sources/upload", { method: "POST", body });
                  setRevision((v) => v + 1);
                  setOpen(false);
                } catch (err) {
                  setFailure((err as Error).message);
                } finally {
                  setBusy("");
                }
              }}
            />
          </label>
        </Modal>
      )}
      {selected && (
        <Modal title={selected.name} wide onClose={() => setSelected(null)}>
          <dl className="details-grid">
            <dt>來源版本</dt>
            <dd>v{selected.version}</dd>
            <dt>來源類型</dt>
            <dd>{selected.data_kind}</dd>
            <dt>允許用途</dt>
            <dd>{selected.purpose}</dd>
            <dt>許可說明</dt>
            <dd>{selected.license}</dd>
            <dt>內容摘要</dt>
            <dd className="mono">{selected.digest}</dd>
          </dl>
          <button
            className="secondary"
            onClick={() => {
              setEvidenceSource(selected);
              setSelected(null);
            }}
          >
            查看解析證據與病例接入
          </button>
          <h3>覆蓋與處理記錄</h3>
          <pre className="code-view">
            {JSON.stringify(
              selected.details.last_parse || { status: "尚未執行" },
              null,
              2,
            )}
          </pre>
        </Modal>
      )}
      {structuredSource && (
        <StructuredSource
          source={structuredSource}
          onClose={() => setStructuredSource(null)}
        />
      )}{" "}
      {evidenceSource && (
        <SourceEvidence
          source={evidenceSource}
          onClose={() => setEvidenceSource(null)}
        />
      )}{" "}
      {schema && (
        <Modal
          title="數據庫結構目錄 · 只讀"
          wide
          onClose={() => setSchema(null)}
        >
          <p>{schema.tables.length} 張表，源字段類型及主鍵按原結構保留。</p>
          <div className="schema-list">
            {schema.tables.map((t: Data) => (
              <details key={t.table}>
                <summary>
                  {t.table}
                  <span>{t.columns.length} 個字段</span>
                </summary>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>字段</th>
                      <th>原類型</th>
                      <th>主鍵</th>
                    </tr>
                  </thead>
                  <tbody>
                    {t.columns.map((c: Data) => (
                      <tr key={c.name}>
                        <td>{c.name}</td>
                        <td>{c.type}</td>
                        <td>{c.pk ? "是" : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            ))}
          </div>
        </Modal>
      )}
    </div>
  );
}

function StructuredSource({
  source,
  onClose,
}: {
  source: Data;
  onClose: () => void;
}) {
  const [result, setResult] = useState<Data | null>(null);
  const [detail, setDetail] = useState<Data | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(true);
  useEffect(() => {
    post("/sources/" + source.id + "/structured-query", {
      operation: "list_encounters",
      parameters: { namespace: "mimic_iv_demo", limit: 20 },
    })
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setBusy(false));
  }, [source.id]);
  return (
    <Modal title="源結構化就診 · 受控只讀查詢" wide onClose={onClose}>
      <Notice>
        患者、住院和檢驗事件分別計數。日期保持來源脫敏偏移；無就診歸屬的事件不強行合併，不產生診斷。
      </Notice>
      <ErrorBox message={error} />
      {busy ? (
        <Loading />
      ) : (
        result && (
          <>
            <p>
              當前來源：{result.encounter_count} 個住院標識 ·{" "}
              {result.patient_count} 個患者標識。展示前 {result.items.length}{" "}
              項。
            </p>
            <table className="data-table">
              <thead>
                <tr>
                  <th>來源就診號</th>
                  <th>來源患者號</th>
                  <th>入院時間（來源值）</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {result.items.map((row: Data) => (
                  <tr key={row._source_record_number}>
                    <td>{row.hadm_id}</td>
                    <td>{row.subject_id}</td>
                    <td>{row.admittime}</td>
                    <td>
                      <button
                        className="text-button"
                        onClick={async () => {
                          try {
                            setDetail(
                              await post(
                                "/sources/" + source.id + "/structured-query",
                                {
                                  operation: "encounter_context",
                                  parameters: {
                                    namespace: "mimic_iv_demo",
                                    encounter_id: row.hadm_id,
                                    limit: 15,
                                  },
                                },
                              ),
                            );
                          } catch (e) {
                            setError((e as Error).message);
                          }
                        }}
                      >
                        回查上下文
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )
      )}
      {detail && (
        <>
          <h3>住院範圍與原始檢驗值</h3>
          <p>
            關聯檢驗 {detail.observation_count} 項；同源患者另有{" "}
            {detail.unlinked_observation_count_for_subject} 項未明確就診歸屬。
          </p>
          <pre className="code-view">{JSON.stringify(detail, null, 2)}</pre>
        </>
      )}
    </Modal>
  );
}

function SourceEvidence({
  source,
  onClose,
}: {
  source: Data;
  onClose: () => void;
}) {
  const [page, setPage] = useState(1);
  const { data, error, loading } = useApi<Data>(
    "/sources/" + source.id + "/evidence?page=" + page,
  );
  const [failure, setFailure] = useState("");
  const [busy, setBusy] = useState("");
  return (
    <Modal title={source.name + " · 解析證據"} wide onClose={onClose}>
      <Notice>
        原始字段、定位與來源性質保留。接入病例敘述不會自動確認患者身份、就診關係或成人肺炎適用範圍。
      </Notice>
      <ErrorBox message={error || failure} />
      {loading ? (
        <Loading />
      ) : !error && !data?.items.length ? (
        <Empty
          title="當前來源沒有可瀏覽的解析結果"
          description="返回資料目錄運行讀取與解析；已接入病例的原文也可從對應病例查看。"
        >
          <button className="secondary" onClick={onClose}>
            返回資料目錄
          </button>
        </Empty>
      ) : (
        data?.items.map((e: Data) => {
          const locator = e.envelope.locator;
          const position =
            locator.type === "pdf"
              ? `第 ${locator.page} 頁`
              : locator.type === "text"
                ? `第 ${locator.line_start}–${locator.line_end} 行`
                : locator.record_number
                  ? `第 ${locator.record_number} 條記錄`
                  : locator.type === "database"
                    ? `數據表 ${locator.table}`
                    : locator.type === "spreadsheet"
                      ? `工作表 ${locator.sheet}`
                      : "來源附件";
          const kind =
            (
              {
                text: "文本段落",
                table: "表格",
                record: "數據記錄",
                schema: "結構目錄",
                image: "圖像附件",
                waveform: "波形附件",
              } as Data
            )[e.envelope.kind] || "解析內容";
          return (
            <article className="source-record" key={e.id}>
              <div>
                <Badge value={e.envelope.quality.status} />
                <small>
                  {kind} · {position} · 來源 v{e.source_version}
                </small>
              </div>
              <pre>
                {e.envelope.content.text?.slice(0, 900) ||
                  JSON.stringify(
                    e.envelope.content.value ??
                      e.envelope.content.columns ??
                      e.envelope.content.rows ??
                      e.envelope.content.metadata ??
                      {},
                    null,
                    2,
                  ).slice(0, 900)}
              </pre>
              <details className="evidence-location">
                <summary>定位詳情</summary>
                <pre>{JSON.stringify(e.envelope.locator, null, 2)}</pre>
              </details>
              {e.envelope.quality.issues?.includes(
                "rotated_table_requires_structure_review",
              ) && (
                <Notice>
                  旋轉頁的表頭與行列關係需要複核。原生矩陣已保留，當前不用於自動結構化判斷，請對照原圖。
                </Notice>
              )}
              {e.envelope.locator.type === "pdf" && (
                <PdfEvidencePreview id={e.id} page={e.envelope.locator.page} />
              )}
              {e.envelope.content.text &&
                source.data_role === "business_evidence" && (
                  <button
                    className="secondary small"
                    disabled={!!busy}
                    onClick={async () => {
                      setBusy(e.id);
                      try {
                        const result = await post(
                          "/evidence/" + e.id + "/case",
                          command(
                            1,
                            "將當前來源原文登記為待核查資料，不推定就診身份",
                            { owner_id: "doctor1" },
                          ),
                        );
                        navigate(
                          "/cases/" +
                            result.id +
                            "?return=" +
                            encodeURIComponent(
                              location.pathname + location.search,
                            ),
                        );
                        onClose();
                      } catch (err) {
                        setFailure((err as Error).message);
                      } finally {
                        setBusy("");
                      }
                    }}
                  >
                    {busy === e.id
                      ? "正在登記…"
                      : e.case_id
                        ? "打開已關聯病例"
                        : "登記為待核查病例"}
                  </button>
                )}
            </article>
          );
        })
      )}
      {data && (
        <div className="pagination">
          <span>共 {data.total} 項證據</span>
          <div>
            <button disabled={page === 1} onClick={() => setPage((v) => v - 1)}>
              上一頁
            </button>
            <span>{page}</span>
            <button
              disabled={page * 20 >= data.total}
              onClick={() => setPage((v) => v + 1)}
            >
              下一頁
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}

export function RulesPage({ session }: { session: Data }) {
  const [revision, setRevision] = useState(0);
  const { data, error, loading } = useApi<Data>("/rules", revision);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(
    new URLSearchParams(location.search).get("rule") || "",
  );
  const [result, setResult] = useState<Data | null>(null);
  const [failure, setFailure] = useState("");
  const [reason, setReason] = useState("");
  const [versionOpen, setVersionOpen] = useState(false);
  const [newContent, setNewContent] = useState("");
  const [reviewOpen, setReviewOpen] = useState(false);
  const [decision, setDecision] = useState("approve");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (data && !selected) setSelected(data.items[0]?.id || "");
  }, [data]);
  const item = data?.items.find((r: Data) => r.id === selected);
  const visible =
    data?.items.filter((r: Data) =>
      (r.name + r.rule_key + r.content).includes(search),
    ) || [];
  return (
    <>
      <PageTitle
        eyebrow="一期規則包 · 8 類文書檢查"
        title="規則與依據"
        description="明確適用範圍、專業資格與引用版本，保留每一條判斷的依據。"
        action={
          <button
            className="secondary"
            onClick={() => navigate("/graph?view=rule")}
          >
            <Network size={17} />
            查看規則關係
          </button>
        }
      />
      <ErrorBox message={error || failure} />
      <form
        className="knowledge-search"
        onSubmit={async (e) => {
          e.preventDefault();
          try {
            setResult(
              await api("/knowledge/search?q=" + encodeURIComponent(search)),
            );
          } catch (err) {
            setFailure((err as Error).message);
          }
        }}
      >
        <Search size={20} />
        <input
          placeholder="按規則編號、術語或問題查找依據"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button className="primary">檢索依據</button>
      </form>
      {result && (
        <section className="panel retrieval-results">
          <header>
            <strong>檢索結果 · {result.results.length} 條</strong>
            <span>
              {result.mode === "exact_id"
                ? "編號精確定位"
                : result.mode === "hybrid"
                  ? "詞法 + 語義混合檢索"
                  : "詞法檢索"}
            </span>
            <button
              className="icon-button"
              onClick={() => setResult(null)}
              aria-label="關閉檢索結果"
            >
              <X size={17} />
            </button>
          </header>
          {result.gaps.length > 0 && (
            <Notice>
              語義覆蓋尚有限制：{result.gaps.join("、")}
              。排序分數不代表醫學確定性。
            </Notice>
          )}
          {result.results.map((r: Data) => (
            <button
              key={r.id || r.rule.id}
              className="retrieval-hit"
              onClick={() => setSelected(r.rule.id)}
            >
              <span>{r.rule.rule_key}</span>
              <strong>{r.rule.name}</strong>
              <p>{r.text || r.rule.content}</p>
            </button>
          ))}
        </section>
      )}
      {loading ? (
        <Loading />
      ) : (
        <div className="rules-layout">
          <aside className="panel rules-list">
            {visible.map((r: Data) => (
              <button
                key={r.id}
                className={selected === r.id ? "selected" : ""}
                onClick={() => setSelected(r.id)}
              >
                <div>
                  <BookOpen size={18} />
                  <span>{r.rule_key}</span>
                  <Badge value={r.status} />
                </div>
                <strong>{r.name}</strong>
                <small>
                  {r.category} · v{r.version}
                </small>
              </button>
            ))}
          </aside>
          <section className="panel rule-detail">
            {item ? (
              <>
                <div className="rule-detail-heading">
                  <div>
                    <span className="eyebrow">{item.rule_key}</span>
                    <h2>{item.name}</h2>
                  </div>
                  <Badge value={item.severity}>
                    {riskNames[item.severity]}
                  </Badge>
                </div>
                <Notice>
                  當前為工程候選規則；尚未取得目標醫院專業適用性審核，不能用於生產放行。
                </Notice>
                <h3>檢查與依據</h3>
                <p>{item.content}</p>
                <dl className="details-grid">
                  <dt>適用範圍</dt>
                  <dd>{item.specification.scope}</dd>
                  <dt>判斷方式</dt>
                  <dd>{item.specification.method}</dd>
                  <dt>規則版本</dt>
                  <dd>
                    v{item.version} ·{" "}
                    {item.status === "candidate" ? "候選" : "已停用"}
                  </dd>
                  <dt>語義基線</dt>
                  <dd>{item.semantic_release_id}</dd>
                  <dt>來源</dt>
                  <dd>{item.provenance.source}</dd>
                </dl>
                <h3>關聯概念</h3>
                <div className="concept-tags">
                  {item.specification.concepts.map((c: string) => (
                    <button
                      key={c}
                      onClick={() => navigate("/graph?focus=" + c)}
                    >
                      {c}
                      <ArrowUpRight size={12} />
                    </button>
                  ))}
                </div>
                <button
                  className="primary"
                  onClick={() =>
                    navigate(
                      "/graph?view=rule&rule=" +
                        item.id +
                        "&return=" +
                        encodeURIComponent("/rules?rule=" + item.id),
                    )
                  }
                >
                  <Network size={17} />
                  查看規則關聯
                </button>
                <div className="action-row">
                  {session.permissions.includes("knowledge_edit") && (
                    <>
                      <button
                        className="secondary"
                        onClick={() => {
                          setNewContent(item.content);
                          setVersionOpen(true);
                        }}
                      >
                        提出新版本
                      </button>
                      <button
                        className="secondary"
                        onClick={async () => {
                          try {
                            await post(
                              "/knowledge/indices",
                              command(1, "根據當前固定規則和本體建立知識索引", {
                                release_id: item.semantic_release_id,
                              }),
                            );
                            setFailure("");
                            setResult({
                              mode: "pending",
                              results: [],
                              gaps: [
                                "索引作業已受理；完成後使用新的完整索引版本。",
                              ],
                            });
                          } catch (e) {
                            setFailure((e as Error).message);
                          }
                        }}
                      >
                        建立當前知識索引
                      </button>
                    </>
                  )}
                  {session.actor.role === "expert" && (
                    <button
                      className="secondary"
                      onClick={() => setReviewOpen(true)}
                    >
                      記錄審核意見
                    </button>
                  )}
                </div>
                {session.permissions.includes("knowledge_edit") && (
                  <details className="rule-maintenance">
                    <summary>候選資格維護</summary>
                    <label>
                      變更理由
                      <input
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        placeholder="說明停用或重新登記的原因"
                      />
                    </label>
                    <button
                      className="secondary"
                      disabled={!reason.trim()}
                      onClick={async () => {
                        try {
                          await post(
                            "/rules/" + item.id + "/status",
                            command(item.policy_version, reason, {
                              status:
                                item.status === "retired"
                                  ? "candidate"
                                  : "retired",
                            }),
                          );
                          setRevision((v) => v + 1);
                          setReason("");
                        } catch (e) {
                          setFailure((e as Error).message);
                        }
                      }}
                    >
                      {item.status === "retired"
                        ? "恢復候選資格"
                        : "停用此候選"}
                    </button>
                  </details>
                )}
              </>
            ) : (
              <Empty title="未找到規則" />
            )}
          </section>
        </div>
      )}
      {versionOpen && item && (
        <Modal
          title="提出規則新版本"
          wide
          onClose={() => setVersionOpen(false)}
        >
          <Notice>
            新版本保持候選狀態，不覆蓋舊版本，不自動替換舊運行依據。改變執行含義後需要重新評估對應檢查器。
          </Notice>
          <label>
            候選規則說明
            <textarea
              className="document-editor"
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
            />
          </label>
          <label>
            變更理由
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </label>
          <div className="modal-actions">
            <button className="secondary" onClick={() => setVersionOpen(false)}>
              取消
            </button>
            <button
              className="primary"
              disabled={!reason.trim() || busy}
              onClick={async () => {
                setBusy(true);
                try {
                  const result = await post(
                    "/rules/" + item.id + "/versions",
                    command(item.version, reason, { content: newContent }),
                  );
                  setSelected(result.id);
                  setRevision((v) => v + 1);
                  setVersionOpen(false);
                  setReason("");
                } catch (e) {
                  setFailure((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              保存候選新版本
            </button>
          </div>
        </Modal>
      )}
      {reviewOpen && item && (
        <Modal title="規則審核意見" onClose={() => setReviewOpen(false)}>
          <Notice>
            本地工程身份的審核僅用於驗證流程；不會將候選規則標成臨床批准。
          </Notice>
          <label>
            審核結果
            <select
              value={decision}
              onChange={(e) => setDecision(e.target.value)}
            >
              <option value="approve">工程核對通過</option>
              <option value="reject">退回 / 停用</option>
            </select>
          </label>
          <label>
            審核依據與理由
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </label>
          <div className="modal-actions">
            <button className="secondary" onClick={() => setReviewOpen(false)}>
              取消
            </button>
            <button
              className="primary"
              disabled={!reason.trim() || busy}
              onClick={async () => {
                setBusy(true);
                try {
                  await post(
                    "/rules/" + item.id + "/review",
                    command(item.policy_version, reason, { decision }),
                  );
                  setRevision((v) => v + 1);
                  setReviewOpen(false);
                  setReason("");
                } catch (e) {
                  setFailure((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              記錄本崗位審核
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}

export function EvaluationPage({ session }: { session: Data }) {
  const [revision, setRevision] = useState(0);
  const { data, error, loading } = useApi<Data>(
    "/evaluation-batches",
    revision,
  );
  const [selected, setSelected] = useState("");
  const [create, setCreate] = useState(false);
  const [failure, setFailure] = useState("");
  const [sample, setSample] = useState<Data | null>(null);
  const [protocolOpen, setProtocolOpen] = useState(false);
  const [thresholds, setThresholds] = useState<Data>({});
  const [protocolReason, setProtocolReason] = useState("");
  const [compareWith, setCompareWith] = useState("");
  const [comparison, setComparison] = useState<Data | null>(null);
  const report = useApi<Data>(
    selected ? "/evaluation-batches/" + selected + "/report" : null,
    revision,
  );
  useEffect(() => {
    if (data?.items.length && !selected) setSelected(data.items[0].id);
  }, [data]);
  return (
    <>
      <PageTitle
        eyebrow="專業評測 · 原判與仲裁分離"
        title="專家評測"
        description="固定樣本和版本，分別記錄兩份獨立原判，再處理分歧。"
        action={
          session.permissions.includes("evaluation") &&
          session.actor.role !== "expert" ? (
            <button className="primary" onClick={() => setCreate(true)}>
              <Plus size={17} />
              創建評測批次
            </button>
          ) : undefined
        }
      />
      <ErrorBox message={error || report.error || failure} />
      {loading ? (
        <Loading />
      ) : !data?.items.length ? (
        <Empty
          title="尚未建立評測批次"
          description="選擇固定質控運行，指派兩名原判者和一名仲裁者。工程樣本不用於生產准入。"
        />
      ) : (
        <>
          <div className="batch-selector">
            <label>
              評測批次
              <select
                value={selected}
                onChange={(e) => {
                  setSelected(e.target.value);
                  setComparison(null);
                  setCompareWith("");
                }}
              >
                {data.items.map((b: Data) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </label>
            <Badge value={report.data?.status || "not_evaluated"} />
            <span>樣本與輸入版本已凍結</span>
          </div>
          {report.loading ? (
            <Loading />
          ) : (
            report.data && (
              <>
                <section className="stat-strip eval-stats">
                  {[
                    ["凍結樣本", report.data.metrics.total],
                    [
                      "參照可判斷",
                      report.data.metrics.positive_reference +
                        report.data.metrics.negative_reference,
                    ],
                    [
                      "高風險漏報",
                      report.data.metrics.high_risk_false_negatives.length,
                    ],
                    [
                      "待判 / 未決",
                      report.data.samples.filter(
                        (s: Data) =>
                          !["positive", "negative"].includes(s.reference) ||
                          report.data!.metrics.unresolved_high_risk.includes(
                            s.id,
                          ),
                      ).length,
                    ],
                  ].map(([label, value], i) => (
                    <div
                      className={"stat " + (i === 2 ? "caution" : "")}
                      key={label}
                    >
                      <span>{label}</span>
                      <strong>{value}</strong>
                    </div>
                  ))}
                </section>
                <Notice>
                  零次觀察到漏報不代表可以上線。當前資格：
                  {report.data.qualification === "engineering_only"
                    ? "工程身份評測"
                    : "待專業責任接受"}
                  {report.data.thresholds
                    ? "；已記錄固定閾值，臨床資格須另行核驗。"
                    : "；正式閾值尚需凍結。"}
                </Notice>
                <div className="evaluation-grid">
                  <section className="panel">
                    <div className="panel-heading">
                      <h2>樣本與獨立判斷</h2>
                      {["expert", "manager"].includes(session.actor.role) ? (
                        <button
                          className="text-button"
                          onClick={() => setProtocolOpen(true)}
                        >
                          凍結評測口徑
                        </button>
                      ) : (
                        <span className="muted">
                          按風險、規則和來源保留分層
                        </span>
                      )}
                    </div>
                    <div className="table-scroll">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>樣本 / 規則</th>
                            <th>風險</th>
                            <th>兩份原判</th>
                            <th>分歧 / 仲裁</th>
                            <th />
                          </tr>
                        </thead>
                        <tbody>
                          {report.data.samples.map((s: Data) => (
                            <tr key={s.id}>
                              <td>
                                <strong>{s.title}</strong>
                                <small className="cell-sub">
                                  {s.case_id} · {s.rule_key}
                                </small>
                              </td>
                              <td>
                                <Badge value={s.severity}>
                                  {riskNames[s.severity]}
                                </Badge>
                              </td>
                              <td>{s.judgment_count} / 2</td>
                              <td>
                                {s.disagreement
                                  ? s.arbitrated
                                    ? "已仲裁"
                                    : "待仲裁"
                                  : "—"}
                              </td>
                              <td>
                                <button
                                  className="text-button"
                                  onClick={() => setSample(s)}
                                >
                                  查看與評價
                                  <ChevronRight size={14} />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>
                  <aside className="panel metric-panel">
                    <h2>指標與分母</h2>
                    {[
                      ["end_to_end_recall", "端到端召回"],
                      ["precision", "精確率"],
                      ["false_positive_rate", "誤報率"],
                      ["abstention", "棄答 / 無法判斷"],
                    ].map(([key, label]) => {
                      const m = report.data!.metrics[key];
                      return (
                        <div className="metric-row" key={key}>
                          <span>{label}</span>
                          <strong>
                            {m.value === null
                              ? "未定義"
                              : (m.value * 100).toFixed(1) + "%"}
                          </strong>
                          <small>
                            {m.numerator} / {m.denominator}
                          </small>
                        </div>
                      );
                    })}
                    <h3>原始一致性</h3>
                    <p>
                      {report.data.agreement.observed === null
                        ? "尚無成對原判"
                        : (report.data.agreement.observed * 100).toFixed(1) +
                          "%"}
                      <small className="cell-sub">
                        {report.data.agreement.pairs} 對原判；不以仲裁覆蓋
                      </small>
                    </p>
                    <p className="muted">
                      困難樣本、失敗和棄答保留在對應分母中。尚未運行的項目不填成績。
                    </p>
                  </aside>
                </div>
                <section className="panel evaluation-supplement">
                  <div className="panel-heading">
                    <h2>證據與建議分項</h2>
                    <span className="muted">
                      按獨立原判計數，無法判斷與缺判單列
                    </span>
                  </div>
                  <div className="table-scroll">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>評價項</th>
                          <th>通過 / 已判斷</th>
                          <th>未通過</th>
                          <th>無法判斷</th>
                          <th>尚未評價</th>
                        </tr>
                      </thead>
                      <tbody>
                        {[
                          ["location", "位置正確"],
                          ["support", "主張支持"],
                          ["explanation", "解釋可用"],
                          ["suggestion", "建議可用"],
                        ].map(([key, label]) => {
                          const r = report.data!.rubrics[key];
                          return (
                            <tr key={key}>
                              <td>{label}</td>
                              <td>
                                {r.numerator} / {r.denominator}
                              </td>
                              <td>{r.counts.fail}</td>
                              <td>{r.counts.unable}</td>
                              <td>{r.counts.unreviewed}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  <div className="panel-heading">
                    <h3>按風險分層</h3>
                    <span className="muted">
                      不同來源的樣本保留來源性質，不推算總體發生率
                    </span>
                  </div>
                  <div className="table-scroll">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>風險</th>
                          <th>樣本</th>
                          <th>端到端召回分子 / 分母</th>
                          <th>高風險漏報</th>
                          <th>參照未定</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(report.data.strata.severity).map(
                          ([key, value]) => {
                            const m = value as Data;
                            return (
                              <tr key={key}>
                                <td>{riskNames[key]}</td>
                                <td>{m.total}</td>
                                <td>
                                  {m.end_to_end_recall.numerator} /{" "}
                                  {m.end_to_end_recall.denominator}
                                </td>
                                <td>{m.high_risk_false_negatives.length}</td>
                                <td>{m.counts.U_ref}</td>
                              </tr>
                            );
                          },
                        )}
                      </tbody>
                    </table>
                  </div>
                </section>
                <section className="panel evaluation-supplement evaluation-comparison">
                  <div className="panel-heading">
                    <h2>固定樣本的版本比較</h2>
                  </div>
                  <div className="batch-selector">
                    <label>
                      對比批次
                      <select
                        value={compareWith}
                        onChange={(e) => {
                          setCompareWith(e.target.value);
                          setComparison(null);
                        }}
                      >
                        <option value="">選擇另一批次</option>
                        {data.items
                          .filter((b: Data) => b.id !== selected)
                          .map((b: Data) => (
                            <option key={b.id} value={b.id}>
                              {b.name}
                            </option>
                          ))}
                      </select>
                    </label>
                    <button
                      className="secondary"
                      disabled={!compareWith}
                      onClick={async () => {
                        setFailure("");
                        try {
                          setComparison(
                            await api(
                              `/evaluation-batches/${selected}/compare/${compareWith}`,
                            ),
                          );
                        } catch (e) {
                          setComparison(null);
                          setFailure((e as Error).message);
                        }
                      }}
                    >
                      比較同一範圍
                    </button>
                  </div>
                  {comparison ? (
                    <div className="table-scroll">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>規則</th>
                            <th>原批次</th>
                            <th>對比批次</th>
                            <th>參照 / 未決</th>
                          </tr>
                        </thead>
                        <tbody>
                          {comparison.pairs.map((p: Data, i: number) => (
                            <tr key={i}>
                              <td>{p.rule_key}</td>
                              <td>
                                {(
                                  {
                                    issue: "疑似問題",
                                    pass: "未發現",
                                    unknown: "無法判斷",
                                  } as Data
                                )[p.before] || p.before}
                              </td>
                              <td>
                                {(
                                  {
                                    issue: "疑似問題",
                                    pass: "未發現",
                                    unknown: "無法判斷",
                                  } as Data
                                )[p.after] || p.after}
                              </td>
                              <td>
                                {p.unresolved
                                  ? "仍有未決"
                                  : p.reference === "positive"
                                    ? "存在問題"
                                    : "不存在問題"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="muted">
                      樣本、文書、規則範圍、參照或閾值不同會拒絕配對，不能將口徑變化當作效果改善。
                    </p>
                  )}
                </section>
              </>
            )
          )}
        </>
      )}
      {protocolOpen && report.data && (
        <Modal
          title="凍結評測口徑與門檻"
          onClose={() => setProtocolOpen(false)}
        >
          <Notice>
            系統不提供默認合格線。原判開始後不能修改門檻來提高分數；本地記錄不構成醫院專業批准。
          </Notice>
          {[
            ["min_end_to_end_recall", "端到端召回下限"],
            ["max_false_positive_rate", "誤報率上限"],
            ["min_reference_coverage", "參照覆蓋下限"],
          ].map(([key, label]) => (
            <label key={key}>
              {label}（0–1）
              <input
                type="number"
                min="0"
                max="1"
                step="0.001"
                value={thresholds[key] ?? ""}
                onChange={(e) =>
                  setThresholds((v) => ({
                    ...v,
                    [key]: e.target.value === "" ? "" : Number(e.target.value),
                  }))
                }
              />
            </label>
          ))}
          <label>
            口徑與責任依據
            <textarea
              value={protocolReason}
              onChange={(e) => setProtocolReason(e.target.value)}
            />
          </label>
          <div className="modal-actions">
            <button
              className="secondary"
              onClick={() => setProtocolOpen(false)}
            >
              取消
            </button>
            <button
              className="primary"
              disabled={!protocolReason.trim()}
              onClick={async () => {
                try {
                  await post(
                    "/evaluation-batches/" +
                      report.data!.batch.id +
                      "/protocol",
                    command(report.data!.batch.version, protocolReason, {
                      thresholds,
                    }),
                  );
                  setProtocolOpen(false);
                  setRevision((v) => v + 1);
                } catch (e) {
                  setFailure((e as Error).message);
                }
              }}
            >
              記錄並凍結
            </button>
          </div>
        </Modal>
      )}
      {create && (
        <CreateBatch
          onClose={() => setCreate(false)}
          onDone={(id) => {
            setCreate(false);
            setSelected(id);
            setRevision((v) => v + 1);
          }}
        />
      )}
      {sample && report.data && (
        <JudgmentDialog
          sample={sample}
          report={report.data}
          session={session}
          onClose={() => setSample(null)}
          onDone={() => {
            setSample(null);
            setRevision((v) => v + 1);
          }}
        />
      )}
    </>
  );
}

function CreateBatch({
  onClose,
  onDone,
}: {
  onClose: () => void;
  onDone: (id: string) => void;
}) {
  const { data } = useApi<Data>("/cases?page_size=50");
  const people = useApi<Data>("/access/actors");
  const [raters, setRaters] = useState(["expert1", "expert2"]);
  const [arbitrator, setArbitrator] = useState("expert3");
  const [name, setName] = useState("成人肺炎文書 · 第一輪工程評測");
  const [selected, setSelected] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <Modal title="創建固定版本評測批次" wide onClose={onClose}>
      <label>
        批次名稱
        <input value={name} onChange={(e) => setName(e.target.value)} />
      </label>
      <Notice>
        只納入固定質控運行。明確指派會授予所選專家對應病例的複核範圍並留下審計；本地身份不代表真實專家資格。
      </Notice>
      <div className="form-columns">
        {[0, 1].map((index) => (
          <label key={index}>
            原判專家 {index + 1}
            <select
              value={raters[index]}
              onChange={(e) =>
                setRaters((previous) =>
                  previous.map((value, i) =>
                    i === index ? e.target.value : value,
                  ),
                )
              }
            >
              {people.data?.items
                .filter(
                  (person: Data) => person.role === "expert" && person.enabled,
                )
                .map((person: Data) => (
                  <option key={person.id} value={person.id}>
                    {person.name}
                  </option>
                ))}
            </select>
          </label>
        ))}
      </div>
      <label>
        仲裁專家
        <select
          value={arbitrator}
          onChange={(e) => setArbitrator(e.target.value)}
        >
          {people.data?.items
            .filter(
              (person: Data) => person.role === "expert" && person.enabled,
            )
            .map((person: Data) => (
              <option key={person.id} value={person.id}>
                {person.name}
              </option>
            ))}
        </select>
      </label>
      <div className="case-picks">
        {data?.items
          .filter((c: Data) => c.details.current_run_id)
          .map((c: Data) => (
            <label key={c.id}>
              <input
                type="checkbox"
                checked={selected.includes(c.details.current_run_id)}
                onChange={(e) =>
                  setSelected((v) =>
                    e.target.checked
                      ? [...v, c.details.current_run_id]
                      : v.filter((x) => x !== c.details.current_run_id),
                  )
                }
              />
              <span>
                {c.display_name} · {c.encounter_id}
              </span>
              <Badge value={c.risk}>{riskNames[c.risk]}</Badge>
            </label>
          ))}
      </div>
      <ErrorBox message={error} />
      <div className="modal-actions">
        <button className="secondary" onClick={onClose}>
          取消
        </button>
        <button
          className="primary"
          disabled={
            !selected.length ||
            busy ||
            new Set([...raters, arbitrator]).size !== 3
          }
          onClick={async () => {
            setBusy(true);
            try {
              const result = await post("/evaluation-batches", {
                name,
                run_ids: selected,
                raters,
                arbitrator,
              });
              onDone(result.id);
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          凍結樣本並創建
        </button>
      </div>
    </Modal>
  );
}

function JudgmentDialog({
  sample,
  report,
  session,
  onClose,
  onDone,
}: {
  sample: Data;
  report: Data;
  session: Data;
  onClose: () => void;
  onDone: () => void;
}) {
  const [verdict, setVerdict] = useState("");
  const [severity, setSeverity] = useState(sample.severity);
  const [reason, setReason] = useState("");
  const [rubric, setRubric] = useState<Data>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const detail = useApi<Data>(
    "/evaluation-batches/" + report.batch.id + "/samples/" + sample.id,
  );
  const arb = report.batch.assignments.arbitrator === session.actor.id;
  const assigned = report.batch.assignments.raters.includes(session.actor.id);
  const own = report.judgments.find(
    (j: Data) => j.sample_id === sample.id && j.actor_id === session.actor.id,
  );
  return (
    <Modal title={sample.title} wide onClose={onClose}>
      <div className="modal-context">
        <span>
          {sample.case_id} · {sample.rule_key}
        </span>
        <Badge value={sample.severity}>{riskNames[sample.severity]}</Badge>
      </div>
      {detail.error && <ErrorBox message={detail.error} />}
      <div className="sample-evidence">
        {sample.evidence_ids.map((id: string) => {
          const e = detail.data?.evidence.find((v: Data) => v.id === id);
          return (
            <blockquote key={id}>
              {e?.envelope.content.text || "固定證據需從對應運行回查"}
            </blockquote>
          );
        })}
      </div>
      <div className="judgment-history">
        {report.judgments
          .filter((j: Data) => j.sample_id === sample.id)
          .map((j: Data) => (
            <div key={j.id}>
              <strong>{j.actor_id}</strong>
              <Badge value={j.verdict}>
                {
                  (
                    {
                      positive: "存在問題",
                      negative: "問題不成立",
                      unable: "無法判斷",
                    } as Data
                  )[j.verdict]
                }
              </Badge>
              <p>{j.reason}</p>
            </div>
          ))}
      </div>
      {(assigned && !own) || arb ? (
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            try {
              await post(
                "/evaluation-batches/" +
                  report.batch.id +
                  (arb ? "/arbitrations" : "/judgments"),
                command(report.batch.version, reason, {
                  sample_id: sample.id,
                  verdict,
                  severity,
                  rubric,
                }),
              );
              onDone();
            } catch (err) {
              setError((err as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <div className="form-columns">
            <label>
              {arb ? "仲裁結論" : "獨立原判"}
              <select
                required
                value={verdict}
                onChange={(e) => setVerdict(e.target.value)}
              >
                <option value="">請選擇你的判斷</option>
                <option value="positive">存在文書問題</option>
                <option value="negative">問題不成立</option>
                <option value="unable">依據不足 / 無法判斷</option>
              </select>
            </label>
            <label>
              專業風險分層
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
              >
                <option value="high">高風險</option>
                <option value="medium">中風險</option>
                <option value="low">低風險</option>
                <option value="unknown">無法判斷</option>
              </select>
            </label>
          </div>
          {!arb && (
            <div className="rubric-grid">
              {[
                ["location", "位置是否準確"],
                ["support", "原文是否支持"],
                ["explanation", "解釋是否可用"],
                ["suggestion", "建議是否越界"],
              ].map(([key, label]) => (
                <label key={key}>
                  {label}
                  <select
                    value={rubric[key] || ""}
                    onChange={(e) =>
                      setRubric((v) => ({ ...v, [key]: e.target.value }))
                    }
                  >
                    <option value="">未評價</option>
                    <option value="pass">符合</option>
                    <option value="fail">不符合</option>
                    <option value="unable">無法判斷</option>
                  </select>
                </label>
              ))}
            </div>
          )}
          <label>
            判斷依據
            <textarea
              required
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="圍繞原文、適用規則與版本說明，不復制另一人的判斷。"
            />
          </label>
          <ErrorBox message={error} />
          <div className="modal-actions">
            <button type="button" className="secondary" onClick={onClose}>
              關閉
            </button>
            <button className="primary" disabled={busy || !verdict}>
              {arb ? "追加仲裁記錄" : "提交獨立原判"}
            </button>
          </div>
        </form>
      ) : (
        <Notice>
          {own
            ? "你的原判已保存，不可被後續仲裁覆蓋。"
            : "當前身份未承擔此樣本原判或仲裁。"}
        </Notice>
      )}
    </Modal>
  );
}

export function ReleasePage({ session }: { session: Data }) {
  const [revision, setRevision] = useState(0);
  const { data, error, loading } = useApi<Data>("/release-requests", revision);
  const batches = useApi<Data>(
    session.actor.role === "manager" ? "/evaluation-batches" : null,
  );
  const rules = useApi<Data>("/rules");
  const [selected, setSelected] = useState("");
  const [open, setOpen] = useState(false);
  const [stage, setStage] = useState("shadow");
  const [batchIds, setBatchIds] = useState<string[]>([]);
  const [reason, setReason] = useState("");
  const [failure, setFailure] = useState("");
  useEffect(() => {
    if (data?.items.length && !selected) setSelected(data.items[0].id);
  }, [data]);
  const current = data?.items.find((r: Data) => r.id === selected);
  async function perform(action: string) {
    if (!reason.trim()) {
      setFailure("請填寫責任意見或檢查理由。");
      return;
    }
    try {
      await post(
        "/release-requests/" + current.id + "/" + action,
        command(current.version, reason),
      );
      setRevision((v) => v + 1);
      setReason("");
    } catch (e) {
      setFailure((e as Error).message);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="逐步放權 · 一項高風險漏報即可否決"
        title="評測與准入"
        description="從離線驗證到影子運行，再到有人確認的輔助決策。"
        action={
          session.actor.role === "manager" ? (
            <button className="primary" onClick={() => setOpen(true)}>
              <Plus size={17} />
              建立准入申請
            </button>
          ) : undefined
        }
      />
      <div className="release-stages">
        <div className="current">
          <CheckCircle2 size={23} />
          <strong>離線驗證</strong>
          <span>當前工作階段</span>
        </div>
        <ChevronRight />
        <div>
          <ShieldCheck size={23} />
          <strong>限定影子運行</strong>
          <span>業務證據與責任前置</span>
        </div>
        <ChevronRight />
        <div>
          <ClipboardCheck size={23} />
          <strong>輔助決策</strong>
          <span>專業確認與持續觀察</span>
        </div>
      </div>
      <ErrorBox message={error || failure} />
      {loading ? (
        <Loading />
      ) : !data?.items.length ? (
        <Empty
          title="尚無准入申請"
          description="技術運行成功不等於業務放權。先固定評測、授權與責任證據。"
        />
      ) : (
        <>
          <div className="batch-selector">
            <label>
              申請基線
              <select
                value={selected}
                onChange={(e) => setSelected(e.target.value)}
              >
                {data.items.map((r: Data) => (
                  <option key={r.id} value={r.id}>
                    {r.stage === "shadow" ? "影子運行" : "輔助決策"} ·{" "}
                    {when(r.created_at)}
                  </option>
                ))}
              </select>
            </label>
            <Badge value={current?.status || "pending"} />
          </div>
          {current && (
            <div className="release-grid">
              <section className="panel">
                <div className="panel-heading">
                  <h2>必要條件清單</h2>
                  <span>
                    {
                      current.conditions.filter((c: Data) => c.status === "met")
                        .length
                    }{" "}
                    / {current.conditions.length} 項滿足
                  </span>
                </div>
                {current.conditions.map((c: Data) => (
                  <div key={c.key} className="gate-condition">
                    <div className={"condition-icon " + c.status}>
                      {c.status === "met" ? (
                        <Check size={16} />
                      ) : (
                        <LockKeyhole size={16} />
                      )}
                    </div>
                    <div>
                      <strong>{c.label}</strong>
                      <p>{c.reason}</p>
                    </div>
                    <Badge value={c.status === "met" ? "success" : "blocked"}>
                      {c.status === "met" ? "已滿足" : "未滿足"}
                    </Badge>
                  </div>
                ))}
              </section>
              <aside className="panel responsibility-acceptance">
                <h2>關鍵崗位責任接受</h2>
                <Notice>
                  缺失的責任條件不會被默認勾選；本地身份只產生工程記錄。
                </Notice>
                {current.acceptances.map((a: Data, i: number) => (
                  <div className="acceptance-record" key={i}>
                    <strong>
                      {a.actor_id} · {a.role}
                    </strong>
                    <p>{a.reason}</p>
                    <small>
                      {a.identity_mode === "local"
                        ? "本地工程身份"
                        : "實際認證身份"}
                    </small>
                  </div>
                ))}
                <label>
                  本次責任意見
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="說明當前範圍、證據與責任條件"
                  />
                </label>
                <div className="stack-actions">
                  <button
                    className="secondary"
                    onClick={() => void perform("acceptances")}
                  >
                    記錄本崗位責任意見
                  </button>
                  {session.actor.role === "manager" && (
                    <>
                      <button
                        className="primary"
                        onClick={() => void perform("decisions")}
                      >
                        核對全部條件並記錄決定
                      </button>
                      <button
                        className="text-button danger"
                        onClick={() => void perform("stop")}
                      >
                        停止當前範圍並要求重驗
                      </button>
                    </>
                  )}
                </div>
              </aside>
            </div>
          )}
        </>
      )}
      {open && (
        <Modal title="建立固定基線准入申請" onClose={() => setOpen(false)}>
          <label>
            目標階段
            <select value={stage} onChange={(e) => setStage(e.target.value)}>
              <option value="shadow">限定影子運行</option>
              <option value="assisted">人確認的輔助決策</option>
            </select>
          </label>
          <h3>關聯評測批次</h3>
          {batches.data?.items.length ? (
            batches.data.items.map((b: Data) => (
              <label className="check-option" key={b.id}>
                <input
                  type="checkbox"
                  checked={batchIds.includes(b.id)}
                  onChange={(e) =>
                    setBatchIds((v) =>
                      e.target.checked
                        ? [...v, b.id]
                        : v.filter((x) => x !== b.id),
                    )
                  }
                />
                {b.name}
              </label>
            ))
          ) : (
            <Notice>尚無批次。可以建立申請查看缺項，不能因此放行。</Notice>
          )}
          <div className="modal-actions">
            <button className="secondary" onClick={() => setOpen(false)}>
              取消
            </button>
            <button
              className="primary"
              onClick={async () => {
                try {
                  const result = await post("/release-requests", {
                    stage,
                    baseline: {
                      batch_ids: batchIds,
                      rule_ids:
                        rules.data?.items
                          .filter((r: Data) => r.status !== "superseded")
                          .map((r: Data) => r.id) || [],
                      semantic_release_id: "semantic-v1",
                    },
                  });
                  setSelected(result.id);
                  setRevision((v) => v + 1);
                  setOpen(false);
                } catch (e) {
                  setFailure((e as Error).message);
                }
              }}
            >
              創建並檢查缺項
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}

export function GovernancePage({ session }: { session: Data }) {
  const [revision, setRevision] = useState(0);
  const [page, setPage] = useState(1);
  const audits = useApi<Data>("/audit-events?page=" + page, revision);
  const actors = useApi<Data>("/access/actors", revision);
  const [tab, setTab] = useState("audit");
  const [target, setTarget] = useState<Data | null>(null);
  const [expiry, setExpiry] = useState("");
  const [reason, setReason] = useState("");
  const [failure, setFailure] = useState("");
  return (
    <>
      <PageTitle
        eyebrow="最小權限 · 當前對象與用途"
        title="權限與審計"
        description="角色決定可執行動作，對象範圍決定可訪問資料；責任記錄持續可追溯。"
      />
      <div className="page-tabs">
        <button
          className={tab === "audit" ? "active" : ""}
          onClick={() => setTab("audit")}
        >
          操作審計
        </button>
        <button
          className={tab === "access" ? "active" : ""}
          onClick={() => setTab("access")}
        >
          崗位與授權
        </button>
      </div>
      <ErrorBox message={audits.error || actors.error || failure} />
      {tab === "audit" ? (
        <section className="panel">
          <div className="panel-heading">
            <h2>全鏈路責任軌跡</h2>
            <button
              className="text-button"
              onClick={() => setRevision((v) => v + 1)}
            >
              <RefreshCw size={15} />
              刷新
            </button>
          </div>
          {audits.loading ? (
            <Loading />
          ) : (
            <>
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>時間</th>
                      <th>主體 / 崗位</th>
                      <th>動作</th>
                      <th>結果</th>
                      <th>對象 / 理由</th>
                    </tr>
                  </thead>
                  <tbody>
                    {audits.data?.items.map((a: Data) => (
                      <tr key={a.id}>
                        <td>{when(a.created_at)}</td>
                        <td>
                          {a.actor_id}
                          <small className="cell-sub">
                            {roleNames[a.role] || a.role}
                          </small>
                        </td>
                        <td>
                          <span className="audit-action">{a.action}</span>
                        </td>
                        <td>
                          <Badge
                            value={
                              a.outcome === "denied" ? "blocked" : "success"
                            }
                          >
                            {a.outcome === "denied" ? "已拒絕" : "已記錄"}
                          </Badge>
                        </td>
                        <td>
                          <small className="mono">
                            {a.resource_id.slice(0, 16)}
                          </small>
                          <p className="audit-reason">{a.reason || "—"}</p>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="pagination">
                <span>普通日誌不復制病歷全文或憑據</span>
                <div>
                  <button
                    disabled={page === 1}
                    onClick={() => setPage((v) => v - 1)}
                  >
                    上一頁
                  </button>
                  <span>{page}</span>
                  <button
                    disabled={(audits.data?.items.length || 0) < 30}
                    onClick={() => setPage((v) => v + 1)}
                  >
                    下一頁
                  </button>
                </div>
              </div>
            </>
          )}
        </section>
      ) : (
        <section className="panel">
          <div className="panel-heading">
            <h2>當前主體與對象範圍</h2>
          </div>
          <Notice>
            此處顯示本地工程身份配置。生產接入需醫院 OIDC 映射和實際責任授權。
          </Notice>
          <table className="data-table">
            <thead>
              <tr>
                <th>主體</th>
                <th>崗位</th>
                <th>責任組 / 指派</th>
                <th>有效性</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {actors.data?.items.map((a: Data) => (
                <tr key={a.id}>
                  <td>
                    <strong>{a.name}</strong>
                    <small className="cell-sub">{a.id}</small>
                  </td>
                  <td>{roleNames[a.role] || a.role}</td>
                  <td>
                    {a.groups.join("、") || "按對象指派"}
                    <small className="cell-sub">
                      {a.case_ids.length
                        ? `${a.case_ids.length} 個指定病例`
                        : ""}
                    </small>
                  </td>
                  <td>
                    <Badge value={a.enabled ? "success" : "blocked"}>
                      {a.enabled ? "有效" : "已撤銷"}
                    </Badge>
                  </td>
                  <td>
                    {session.permissions.includes("manage_access") &&
                      a.id !== session.actor.id && (
                        <button
                          className={
                            "text-button " + (a.enabled ? "danger" : "")
                          }
                          onClick={() => setTarget(a)}
                        >
                          {a.enabled ? "撤銷授權" : "恢復原授權"}
                        </button>
                      )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
      {target && (
        <Modal
          title={target.enabled ? "撤銷當前主體授權" : "恢復原對象範圍授權"}
          onClose={() => setTarget(null)}
        >
          <Notice>
            {target.enabled
              ? "撤銷後停止後續資料、任務與圖譜訪問，並使已有會話失效；歷史責任記錄保留。"
              : "按既有崗位和對象範圍恢復，必須明確截止時間並重新登錄；不會擴大病例訪問範圍。"}
          </Notice>
          <h3>{target.name}</h3>
          {!target.enabled && (
            <label>
              明確授權截止時間
              <input
                type="datetime-local"
                value={expiry}
                onChange={(e) => setExpiry(e.target.value)}
              />
            </label>
          )}
          <label>
            操作理由
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
            />
          </label>
          <div className="modal-actions">
            <button className="secondary" onClick={() => setTarget(null)}>
              取消
            </button>
            <button
              className="primary"
              disabled={!reason.trim()}
              onClick={async () => {
                try {
                  await post(
                    "/access/actors/" +
                      target.id +
                      (target.enabled ? "/revoke" : "/restore"),
                    command(
                      target.version,
                      reason,
                      target.enabled
                        ? {}
                        : {
                            expires_at: expiry
                              ? new Date(expiry).toISOString()
                              : "",
                          },
                    ),
                  );
                  setRevision((v) => v + 1);
                  setTarget(null);
                  setReason("");
                } catch (e) {
                  setFailure((e as Error).message);
                }
              }}
            >
              {target.enabled ? "記錄並撤銷" : "按原範圍恢復"}
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}

export function AssetsPage() {
  const [revision, setRevision] = useState(0);
  const { data, error, loading } = useApi<Data>("/exports", revision);
  const releases = useApi<Data>("/release-requests");
  const [selected, setSelected] = useState("");
  const [failure, setFailure] = useState("");
  const [busy, setBusy] = useState(false);
  const [detail, setDetail] = useState<Data | null>(null);
  return (
    <>
      <PageTitle
        eyebrow="同一交付基線 · 許可與資格保真"
        title="交付資產"
        description="固化規則、本體、權限和評測資產，保留適用範圍與未滿足條件。"
      />
      <Notice>
        交付包不含原始患者資料、參考答案、憑據或身份映射；導出不會改變臨床准入資格。
      </Notice>
      <ErrorBox message={error || failure} />
      <section className="panel export-builder">
        <div>
          <h2>建立工程交接包</h2>
          <p>選擇已有準入或未放行基線，一併保存真實狀態。</p>
        </div>
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">選擇交付基線</option>
          {releases.data?.items.map((r: Data) => (
            <option key={r.id} value={r.id}>
              {when(r.created_at)} · {statusNames[r.status]}
            </option>
          ))}
        </select>
        <button
          className="primary"
          disabled={!selected || busy}
          onClick={async () => {
            setBusy(true);
            try {
              await post("/exports", { release_request_id: selected });
              setRevision((v) => v + 1);
            } catch (e) {
              setFailure((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <Download size={16} />
          {busy ? "正在生成…" : "生成交接包"}
        </button>
      </section>
      <section className="panel">
        <div className="panel-heading">
          <h2>可接手資產</h2>
        </div>
        {loading ? (
          <Loading />
        ) : data?.items.length ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>交付包</th>
                <th>生成時間</th>
                <th>資格狀態</th>
                <th>完整性</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data.items.map((x: Data) => (
                <tr key={x.id}>
                  <td>
                    <strong>醫療質控工程資產</strong>
                    <small className="cell-sub">
                      {x.manifest.included.length} 項文件
                    </small>
                  </td>
                  <td>{when(x.created_at)}</td>
                  <td>
                    <Badge value="candidate">
                      {x.manifest.gate_status === "approved"
                        ? "按批准範圍"
                        : "未獲臨床放行"}
                    </Badge>
                  </td>
                  <td>
                    <span className="mono">{x.digest.slice(0, 12)}</span>
                  </td>
                  <td>
                    <div className="inline-actions">
                      <button
                        className="text-button"
                        onClick={() => setDetail(x)}
                      >
                        清單
                      </button>
                      <a
                        className="secondary small"
                        href={"/api/v1/exports/" + x.id + "/download"}
                      >
                        下載
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <Empty
            title="尚無交接包"
            description="先建立固定基線，再生成可檢查的資產清單。"
          />
        )}
      </section>
      {detail && (
        <Modal title="交付清單與邊界" wide onClose={() => setDetail(null)}>
          <Notice>{detail.manifest.instructions}</Notice>
          <h3>包含文件</h3>
          <ul className="manifest-files">
            {detail.manifest.included.map((i: Data) => (
              <li key={i.path}>
                <FileText size={15} />
                <span>{i.path}</span>
                <small>{i.bytes} B</small>
              </li>
            ))}
          </ul>
          <h3>明確排除</h3>
          <p>{detail.manifest.excluded.join("、")}</p>
        </Modal>
      )}
    </>
  );
}

export function OperationsPage() {
  const { data, error, loading } = useApi<Data>("/operations/status");
  return (
    <>
      <PageTitle
        eyebrow="受限運行診斷"
        title="運行狀態"
        description="查看服務與固定資源狀態；運行支持身份不默認取得病例正文。"
      />
      <ErrorBox message={error} />
      {loading ? (
        <Loading />
      ) : (
        data && (
          <section className="panel" style={{ padding: 26 }}>
            <div className="status-service">
              <span className="status-dot" />
              <h2>應用服務可訪問</h2>
              <Badge value="success">本地運行</Badge>
            </div>
            <dl className="details-grid">
              <dt>應用版本</dt>
              <dd>{data.application_version}</dd>
              <dt>業務數據庫</dt>
              <dd>{data.database}</dd>
              <dt>運行角色</dt>
              <dd>{data.database_role} · 非所有者業務角色</dd>
              <dt>原件訪問</dt>
              <dd>只讀，不回寫源庫與原件</dd>
              <dt>語義能力</dt>
              <dd>{data.ontology}</dd>
              <dt>OCR 資源</dt>
              <dd>
                {data.ocr_resources_prepared ? "已準備主路線資源" : "尚未準備"}
              </dd>
              <dt>本地模型</dt>
              <dd>
                {data.model.model} · {data.model.quantization} ·{" "}
                {data.model.prepared ? "權重已準備" : "權重缺失"}
              </dd>
              <dt>醫院身份</dt>
              <dd>
                {data.identity_provider_configured
                  ? "已配置，仍需目標環境核驗"
                  : "尚未配置；本地工程身份獨立"}
              </dd>
            </dl>
            <Notice>
              {data.diagnostic_scope}
              。臨床資格與生產准入仍需正式評測和責任接受。
            </Notice>
          </section>
        )
      )}
    </>
  );
}
