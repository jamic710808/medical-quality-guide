import { useEffect, useState } from "react";
import {
  Activity,
  LayoutDashboard,
  Network,
  BookOpen,
  ShieldCheck,
  Database,
  ClipboardCheck,
  Package,
  LogOut,
  ChevronRight,
  Search,
  ArrowUpRight,
  X,
} from "lucide-react";
import {
  api,
  navigate,
  post,
  riskNames,
  statusNames,
  when,
  type Data,
} from "./api";
import {
  Badge,
  Empty,
  ErrorBox,
  Loading,
  PageTitle,
  useApi,
  useScrollMemory,
} from "./ui";
import { CasePage } from "./pages/CasePage";
import { GraphPage } from "./pages/GraphPage";
import {
  SourcesPage,
  RulesPage,
  EvaluationPage,
  ReleasePage,
  GovernancePage,
  AssetsPage,
  OperationsPage,
} from "./pages/OperationsPages";

const nav = [
  ["/", "質控工作臺", LayoutDashboard, "cases"],
  ["/sources", "資料接入", Database, "sources"],
  ["/rules", "規則與依據", BookOpen, "knowledge"],
  ["/graph", "知識圖譜", Network, "graph"],
  ["/evaluation", "專家評測", ClipboardCheck, "evaluation"],
  ["/release", "評測與准入", ShieldCheck, "release"],
  ["/assets", "交付資產", Package, "export_assets"],
  ["/governance", "權限與審計", Activity, "audit"],
  ["/operations", "運行狀態", Activity, "operations"],
] as const;

export function App() {
  const [session, setSession] = useState<Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [route, setRoute] = useState(location.pathname + location.search);
  useEffect(() => {
    api("/session")
      .then(setSession)
      .catch(() => {})
      .finally(() => setLoading(false));
    const back = () => setRoute(location.pathname + location.search);
    const expired = () => setSession(null);
    window.addEventListener("popstate", back);
    window.addEventListener("mq-session-expired", expired);
    return () => {
      window.removeEventListener("popstate", back);
      window.removeEventListener("mq-session-expired", expired);
    };
  }, []);
  useEffect(() => {
    if (!session) return;
    const stream = new EventSource("/api/v1/events");
    stream.addEventListener("authorization_revoked", () => {
      stream.close();
      setSession(null);
    });
    return () => stream.close();
  }, [session?.actor.id]);
  if (loading) return <Loading />;
  if (!session)
    return (
      <Login
        onLogin={(s) => {
          setSession(s);
          navigate("/");
        }}
      />
    );
  const current = route.split("?")[0];
  const perms = session.permissions as string[];
  const visible = nav.filter(
    (n) =>
      perms.includes(n[3]) ||
      (n[0] === "/evaluation" && perms.includes("evaluation_report")) ||
      (n[0] === "/release" &&
        ["qc", "doctor", "info"].includes(session.actor.role)),
  );
  let page;
  if (current.startsWith("/cases/"))
    page = <CasePage id={current.split("/")[2]} session={session} />;
  else if (current === "/graph") page = <GraphPage session={session} />;
  else if (current === "/sources") page = <SourcesPage />;
  else if (current === "/rules") page = <RulesPage session={session} />;
  else if (current === "/evaluation")
    page = <EvaluationPage session={session} />;
  else if (current === "/release") page = <ReleasePage session={session} />;
  else if (current === "/governance")
    page = <GovernancePage session={session} />;
  else if (current === "/assets") page = <AssetsPage />;
  else if (current === "/operations") page = <OperationsPage />;
  else
    page = perms.includes("cases") ? (
      <Dashboard route={route} />
    ) : (
      <Overview session={session} visible={visible} />
    );
  return (
    <div className="mq-shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="/"
          onClick={(e) => {
            e.preventDefault();
            navigate("/");
          }}
        >
          <img src="/brand/ff-logo.png" alt="FF - 醫療病歷質控 Logo" />
          <div>
            <strong>FF 醫療質控</strong>
            <span>Medical Quality</span>
          </div>
        </a>
        <div className="workspace-label">
          內科一病區 <span>一期</span>
        </div>
        <nav>
          {visible.map(([path, name, Icon]) => (
            <a
              key={path}
              href={path}
              className={
                current === path ||
                (path === "/" && current.startsWith("/cases/"))
                  ? "active"
                  : ""
              }
              aria-current={
                current === path ||
                (path === "/" && current.startsWith("/cases/"))
                  ? "page"
                  : undefined
              }
              onClick={(e) => {
                e.preventDefault();
                navigate(path);
              }}
            >
              <Icon size={19} />
              <span>{name}</span>
              {path === "/graph" && <span className="nav-new">圖譜</span>}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="scope-note">
            <span className="status-dot" />
            本地工作區 · 數據不出域
          </div>
          <button
            className="account"
            title="退出當前賬號"
            onClick={async () => {
              await post("/auth/logout", {});
              setSession(null);
            }}
          >
            <div className="avatar">{session.actor.name.slice(0, 1)}</div>
            <span>
              <strong>{session.actor.name.split(" · ")[0]}</strong>
              <small>{session.actor.name.split(" · ")[1] || "當前崗位"}</small>
            </span>
            <LogOut size={16} />
          </button>
          <div className="signature">@賦範空間 獨家研發</div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            醫療病歷質控 <ChevronRight size={14} />
            <strong>
              {visible.find((n) => n[0] === current)?.[1] ||
                (current.startsWith("/cases/") ? "病例詳情" : "工作區")}
            </strong>
          </div>
          <div className="topbar-right">
            <span className="environment-pill">
              {session.identity_mode === "local"
                ? "本地工程驗證"
                : "授權工作區"}
            </span>
            <span className="today">
              {new Date().toLocaleDateString("zh-CN", {
                month: "long",
                day: "numeric",
                weekday: "long",
              })}
            </span>
          </div>
        </header>
        <main
          key={current}
          className={
            "main-content" +
            (current === "/graph"
              ? " graph-content"
              : current === "/sources"
                ? " sources-content"
                : current === "/" && perms.includes("cases")
                  ? " dashboard-content"
                  : "")
          }
        >
          <div className="page-scroll">{page}</div>
        </main>
      </div>
    </div>
  );
}

function Login({ onLogin }: { onLogin: (s: Data) => void }) {
  const { data, error, loading } = useApi<Data>("/auth/options");
  const [selected, setSelected] = useState("qc1");
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  return (
    <div className="login-page">
      <div className="login-art">
        <div className="login-orbit one" />
        <div className="login-orbit two" />
        <div className="login-orbit three" />
        <div className="login-emblem">
          <Activity size={52} />
        </div>
        <div className="login-caption">
          <span>FF MEDICAL QUALITY</span>
          <h1>
            讓每一條質控意見
            <br />
            都能回到證據。
          </h1>
          <p>病歷質控 · 證據定位 · 整改協同</p>
        </div>
      </div>
      <section className="login-panel">
        <img className="login-logo" src="/brand/ff-logo.png" />
        <h2>進入醫療質控工作區</h2>
        <p>從當前崗位開始，接續同一項工作。</p>
        <ErrorBox message={error || failure} />
        {loading ? (
          <Loading />
        ) : data?.mode === "local" ? (
          <>
            <label>
              本地試用身份
              <select
                value={selected}
                onChange={(e) => setSelected(e.target.value)}
              >
                {data.actors.map((a: Data) => (
                  <option key={a.id} value={a.id}>
                    {a.name} · {a.role_name}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="primary large"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  await post("/auth/local", { actor_id: selected });
                  onLogin(await api("/session"));
                } catch (e) {
                  setFailure((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              {busy ? "正在建立會話…" : "進入工作區"}
              <ArrowUpRight size={18} />
            </button>
            <div className="login-boundary">
              本地賬號用於工程驗證；病例來源分別標註。這裡的操作不會被當作真實醫院身份、臨床驗收或生產電子簽名。
            </div>
          </>
        ) : (
          <a className="primary" href={data?.login_url}>
            使用醫院身份登錄
          </a>
        )}
        <small className="login-footer">@賦範空間 獨家研發</small>
      </section>
    </div>
  );
}

function Dashboard({ route }: { route: string }) {
  const params = new URLSearchParams(route.split("?")[1]);
  const q = params.get("q") || "",
    state = params.get("state") || "",
    risk = params.get("risk") || "",
    page = Math.max(1, Math.floor(Number(params.get("page")) || 1));
  const [revision, setRevision] = useState(0);
  const { data, error, loading } = useApi<Data>(
    "/cases?" +
      new URLSearchParams({
        q,
        state,
        risk,
        page: String(page),
        page_size: "8",
      }),
    revision,
  );
  const stats = useApi<Data>("/dashboard");
  const [search, setSearch] = useState(q);
  const listRef = useScrollMemory<HTMLDivElement>(
    "cases:" + route,
    !loading && !!data,
  );
  const filtered = !!(q || state || risk);
  useEffect(() => setSearch(q), [q]);
  const update = (key: string, value: string) => {
    const next = new URLSearchParams(location.search);
    value ? next.set(key, value) : next.delete(key);
    if (key !== "page") next.set("page", "1");
    navigate("/?" + next.toString());
  };
  useEffect(() => {
    if (data && page > Math.max(1, Math.ceil(data.total / 8)))
      update("page", String(Math.max(1, Math.ceil(data.total / 8))));
  }, [data, page]);
  const reset = () => {
    setSearch("");
    navigate("/");
  };
  return (
    <div className="dashboard-page">
      <PageTitle
        eyebrow="臨床文書 · 當前授權範圍"
        title="質控工作臺"
        description="從疑似問題到責任確認，持續追蹤每一次處理。"
        action={
          <button className="secondary" onClick={() => navigate("/graph")}>
            <Network size={17} />
            查看知識圖譜
          </button>
        }
      />
      <section className="stat-strip">
        {[
          ["當前病例", stats.data?.case_count, "份"],
          ["待處理病例", stats.data?.pending, "份"],
          ["高風險關注", stats.data?.high_risk, "份"],
          ["當前範圍簽字", stats.data?.signed, "份"],
        ].map(([name, value, unit], i) => (
          <div key={String(name)} className={i === 2 ? "stat caution" : "stat"}>
            <span>{name}</span>
            <strong>
              {value ?? "—"}
              <small>{unit}</small>
            </strong>
            <div className="stat-explanation">
              {i === 2
                ? "依據當前問題風險分層"
                : i === 3
                  ? "不代表全病歷專業合格"
                  : i === 1
                    ? "複核、整改與待補充"
                    : "來源與權限共同限定"}
            </div>
          </div>
        ))}
      </section>
      <div className="workbench-layout">
        <section className="panel case-list">
          <div className="panel-heading">
            <div>
              <h2>
                病例隊列 <span className="count">{data?.total ?? 0}</span>
              </h2>
              <p>定位當前責任範圍，進入原文與處理任務。</p>
            </div>
          </div>
          <div className="toolbar">
            <form
              className="search-box"
              onSubmit={(e) => {
                e.preventDefault();
                update("q", search);
              }}
            >
              <Search size={17} />
              <input
                aria-label="搜索病例"
                placeholder="搜索姓名、就診號或來源標識"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              {search && (
                <button
                  type="button"
                  className="search-clear"
                  aria-label="清除搜索"
                  onClick={() => {
                    setSearch("");
                    if (q) update("q", "");
                  }}
                >
                  <X size={16} />
                </button>
              )}
              <button type="submit" className="search-submit">
                搜索
              </button>
            </form>
            <select
              aria-label="篩選狀態"
              value={state}
              onChange={(e) => update("state", e.target.value)}
            >
              <option value="">全部狀態</option>
              {[
                "review",
                "doctor",
                "appeal",
                "disputed",
                "blocked",
                "verification_pending",
                "verifying",
                "verify_ready",
                "sign",
                "signed",
                "checked",
                "closed_false_positive",
              ].map((value) => (
                <option key={value} value={value}>
                  {statusNames[value]}
                </option>
              ))}
            </select>
            <select
              aria-label="篩選風險"
              value={risk}
              onChange={(e) => update("risk", e.target.value)}
            >
              <option value="">全部風險</option>
              <option value="high">高風險</option>
              <option value="medium">中風險</option>
              <option value="low">低風險</option>
              <option value="unknown">待判斷</option>
            </select>
          </div>
          {filtered && (
            <div className="active-filters">
              <span>
                當前篩選：
                {[
                  q && `“${q}”`,
                  state && statusNames[state],
                  risk && riskNames[risk],
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </span>
              <button className="text-button reset-filters" onClick={reset}>
                清除篩選
              </button>
            </div>
          )}
          {loading ? (
            <Loading />
          ) : error ? (
            <div className="queue-feedback">
              <ErrorBox message={error} />
              <button
                className="secondary"
                onClick={() => setRevision((value) => value + 1)}
              >
                重新加載病例
              </button>
            </div>
          ) : data?.items.length ? (
            <>
              <div
                className="table-scroll"
                ref={listRef}
                role="region"
                tabIndex={0}
                aria-label="病例隊列，可滾動瀏覽"
              >
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>病例 / 就診</th>
                      <th>責任組</th>
                      <th>風險</th>
                      <th>當前進度</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((c: Data) => (
                      <tr
                        key={c.id}
                        onClick={() =>
                          navigate(
                            "/cases/" +
                              c.id +
                              "?return=" +
                              encodeURIComponent(
                                location.pathname + location.search,
                              ),
                          )
                        }
                      >
                        <td>
                          <div className="person-cell">
                            <div className="patient-avatar">
                              {c.display_name[0]}
                            </div>
                            <div>
                              <strong title={c.display_name}>
                                {c.display_name}
                              </strong>
                              <span>
                                {c.details.age !== undefined
                                  ? c.details.age + " 歲"
                                  : "年齡未提供"}{" "}
                                ·{" "}
                                {c.details.bed
                                  ? c.details.bed + " 床"
                                  : "床位未關聯"}
                              </span>
                              <small>
                                {c.details.encounter_identity === "unlinked"
                                  ? "來源記錄 · " + c.details.origin_record_id
                                  : c.encounter_id}
                              </small>
                            </div>
                          </div>
                        </td>
                        <td>
                          {c.group_id}
                          <small className="cell-sub">{c.department}</small>
                        </td>
                        <td>
                          <Badge
                            value={
                              c.details.no_active_issue ? "success" : c.risk
                            }
                          >
                            {c.details.no_active_issue
                              ? "無待處理問題"
                              : riskNames[c.risk]}
                          </Badge>
                        </td>
                        <td>
                          <Badge value={c.status} />
                        </td>
                        <td>
                          <button
                            className="row-open"
                            aria-label={"打開病例 " + c.display_name}
                          >
                            <ChevronRight size={18} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="pagination">
                <span>
                  第 {(page - 1) * 8 + 1}–{Math.min(page * 8, data.total)}{" "}
                  條，共 {data.total} 條
                </span>
                <div>
                  <button
                    disabled={page === 1}
                    onClick={() => update("page", String(page - 1))}
                  >
                    上一頁
                  </button>
                  <span>
                    {page} / {Math.max(1, Math.ceil(data.total / 8))}
                  </span>
                  <button
                    disabled={page * 8 >= data.total}
                    onClick={() => update("page", String(page + 1))}
                  >
                    下一頁
                  </button>
                </div>
              </div>
            </>
          ) : (
            <Empty
              title={filtered ? "沒有符合篩選條件的病例" : "當前暫無可處理病例"}
              description={
                filtered
                  ? "可以調整搜索內容或清除篩選，返回全部病例。"
                  : "獲授權資料接入後，會在這裡形成待處理記錄。"
              }
            >
              {filtered && (
                <button className="secondary" onClick={reset}>
                  清除篩選，查看全部
                </button>
              )}
            </Empty>
          )}
        </section>
        <aside className="context-rail">
          <section className="rail-card recent-card">
            <h3>近期執行</h3>
            <div
              className="recent-events"
              tabIndex={0}
              aria-label="近期執行記錄，可滾動瀏覽"
            >
              {stats.data?.jobs?.length ? (
                stats.data.jobs.map((j: Data) => (
                  <div className="mini-event" key={j.id}>
                    <span className={"event-dot " + j.status} />
                    <div>
                      <strong>
                        {(
                          {
                            quality: "病歷質控",
                            parse: "資料解析",
                            index: "知識索引",
                            human_wait: "等待責任人處理",
                            human_resume: "責任流程接續",
                          } as Data
                        )[j.kind] || "後臺作業"}
                      </strong>
                      <span>{when(j.created_at)}</span>
                    </div>
                    <Badge
                      value={j.kind === "human_wait" ? "pending" : j.status}
                    >
                      {j.kind === "human_wait" ? "待人工處理" : undefined}
                    </Badge>
                  </div>
                ))
              ) : (
                <p>尚無執行記錄</p>
              )}
            </div>
          </section>
          <section className="rail-note">
            <ShieldCheck size={18} />
            <p>
              系統提供輔助檢查與證據。存在缺口或爭議時，保留人工複核和責任確認。
            </p>
          </section>
        </aside>
      </div>
    </div>
  );
}

function Overview({
  session,
  visible,
}: {
  session: Data;
  visible: readonly any[];
}) {
  return (
    <>
      <PageTitle
        eyebrow="崗位工作區"
        title={"你好，" + session.actor.name.split(" · ")[0]}
        description="按當前崗位權限，查看資料、知識與責任記錄。"
      />
      <div className="overview-grid">
        {visible
          .filter((n) => n[0] !== "/")
          .map(([path, name, Icon]) => (
            <button
              className="overview-item"
              key={path}
              onClick={() => navigate(path)}
            >
              <Icon size={30} />
              <h2>{name}</h2>
              <span>
                進入工作區
                <ArrowUpRight size={16} />
              </span>
            </button>
          ))}
      </div>
    </>
  );
}
