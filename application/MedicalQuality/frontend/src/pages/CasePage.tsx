import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  Check,
  ChevronRight,
  Clock3,
  FileText,
  Network,
  Play,
  Shield,
  UserRound,
} from "lucide-react";
import {
  command,
  navigate,
  post,
  riskNames,
  statusNames,
  when,
  type Data,
} from "../api";
import {
  Back,
  Badge,
  Empty,
  ErrorBox,
  Loading,
  Modal,
  Notice,
  PageTitle,
  useApi,
} from "../ui";

const actions: Record<string, string> = {
  accept: "確認問題並派發",
  reject: "駁回誤報",
  revise: "提交整改版本",
  appeal: "提交申訴",
  arbitrate: "保存專業裁決",
  recheck: "執行再次核驗",
  confirm: "確認核驗結果",
  return: "退回醫生補充",
  assign: "調整責任醫生",
  extend: "調整截止時間",
  sign: "簽署當前範圍",
  reopen: "重新建立核驗鏈",
};

export function CasePage({ id, session }: { id: string; session: Data }) {
  const [revision, setRevision] = useState(0);
  const { data, error, loading } = useApi<Data>("/cases/" + id, revision);
  const params = new URLSearchParams(location.search);
  const back = params.get("return") || "/";
  const [runOpen, setRunOpen] = useState(false);
  const tab = ["evidence", "versions", "history"].includes(
    params.get("tab") || "",
  )
    ? params.get("tab")!
    : "evidence";
  const requestedTask = params.get("task") || "";
  const selected = data?.tasks.some((task: Data) => task.id === requestedTask)
    ? requestedTask
    : data?.tasks[0]?.id || "";
  const updateView = (key: string, value: string) => {
    const next = new URLSearchParams(location.search);
    next.set(key, value);
    history.replaceState({}, "", location.pathname + "?" + next.toString());
    window.dispatchEvent(new PopStateEvent("popstate"));
  };
  const [action, setAction] = useState("");
  const [feedback, setFeedback] = useState("");
  const [evidenceId, setEvidenceId] = useState("");
  const evidenceView = useApi<Data>(
    evidenceId ? "/evidence/" + evidenceId : null,
  );
  useEffect(() => {
    if (
      !data?.runs.some((r: Data) => ["queued", "running"].includes(r.status)) &&
      !data?.tasks.some((t: Data) => t.state === "verifying")
    )
      return;
    const timer = setInterval(() => setRevision((r) => r + 1), 2000);
    return () => clearInterval(timer);
  }, [data]);
  if (loading && !data) return <Loading />;
  if (error) return <ErrorBox message={error} />;
  if (!data) return null;
  const actorName = (key: string) =>
    data.actors?.find((a: Data) => a.id === key)?.name || key;
  const c = data.case;
  const task = data.tasks.find((t: Data) => t.id === selected);
  const finding =
    task && data.findings.find((f: Data) => f.id === task.finding_id);
  const choices = getActions(task, session.actor);
  const activeRun = data.runs[0];
  const graph = () =>
    navigate(
      "/graph?view=case&case=" +
        encodeURIComponent(id) +
        (finding?.run_id || activeRun?.id
          ? "&run=" + (finding?.run_id || activeRun?.id)
          : "") +
        (finding ? "&focus=" + finding.id : "") +
        "&return=" +
        encodeURIComponent(
          location.pathname +
            "?" +
            new URLSearchParams({
              ...Object.fromEntries(params),
              tab,
              ...(selected ? { task: selected } : {}),
            }).toString(),
        ),
    );

  return (
    <div className="case-page">
      <Back
        to={back}
        label={back.startsWith("/sources") ? "返回資料目錄" : "返回病例隊列"}
      />
      <PageTitle
        eyebrow={c.encounter_id + " · " + c.department}
        title={c.display_name + "的病歷質控"}
        description={`${c.details.age ?? "未知"} 歲 · ${c.details.sex ?? "未知"} · ${c.details.bed ?? "—"} 床 · ${c.group_id}`}
        action={
          <>
            <button className="secondary" onClick={graph}>
              <Network size={17} />
              查看證據關係
            </button>
            {session.permissions.includes("run") && (
              <button className="primary" onClick={() => setRunOpen(true)}>
                <Play size={16} />
                執行質控
              </button>
            )}
          </>
        }
      />
      <div className="case-summary-bar">
        <Badge value={c.status} />
        <Badge value={c.details.no_active_issue ? "success" : c.risk}>
          {c.details.no_active_issue ? "無待處理問題" : riskNames[c.risk]}
        </Badge>
        <span>
          <FileText size={15} />
          {data.documents.length} 份當前文書
        </span>
        <span>
          <Shield size={15} />
          {c.data_kind === "synthetic"
            ? "合成工程病例"
            : c.data_kind === "literature"
              ? "文獻病例"
              : "來源資料"}
        </span>
        <span className="muted">當前版本 v{c.version}</span>
      </div>
      {feedback && (
        <div className="success-message" role="status">
          {feedback}
        </div>
      )}
      <div className="steps">
        {[
          "疑似問題",
          "質控複核",
          "醫生整改 / 申訴",
          "再次核驗",
          "責任簽字",
        ].map((s, i) => (
          <div key={s} className={stage(task?.state) >= i ? "reached" : ""}>
            <span>{stage(task?.state) > i ? <Check size={13} /> : i + 1}</span>
            {s}
            {i < 4 && <ChevronRight size={15} />}
          </div>
        ))}
      </div>
      <div className="page-tabs">
        {[
          ["evidence", "證據複核"],
          ["versions", "整改與版本"],
          ["history", "操作記錄"],
        ].map(([key, label]) => (
          <button
            key={key}
            className={tab === key ? "active" : ""}
            aria-pressed={tab === key}
            onClick={() => updateView("tab", key)}
          >
            {label}
          </button>
        ))}
        <div className="case-sticky-context">
          <strong>{c.display_name}</strong>
          <span>{c.encounter_id}</span>
        </div>
      </div>
      {tab === "evidence" ? (
        <div className="case-workspace">
          <aside className="panel findings-panel">
            <div className="panel-heading">
              <h2>
                待核查問題 <span className="count">{data.tasks.length}</span>
              </h2>
            </div>
            {data.tasks.length ? (
              data.tasks.map((t: Data) => {
                const f = data.findings.find(
                  (x: Data) => x.id === t.finding_id,
                );
                return (
                  <button
                    key={t.id}
                    className={
                      "finding-item " + (selected === t.id ? "selected" : "")
                    }
                    onClick={() => {
                      updateView("task", t.id);
                      setEvidenceId("");
                    }}
                  >
                    <div>
                      <Badge value={f?.severity}>
                        {riskNames[f?.severity] || "待判斷"}
                      </Badge>
                      <span>{statusNames[t.state] || t.state}</span>
                    </div>
                    <strong>{f?.title || "待核查問題"}</strong>
                    <small>{f?.details.rule_key}</small>
                  </button>
                );
              })
            ) : (
              <Empty
                title="尚無候選問題"
                description="執行質控後，在此查看固定輸入與檢查結果。"
              />
            )}
          </aside>
          <section className="panel evidence-panel">
            {finding ? (
              <>
                <div className="panel-heading">
                  <div>
                    <span className="eyebrow">
                      {finding.layer === "model_inference"
                        ? "模型推斷 · 未確認"
                        : "規則判斷 · 待複核"}
                    </span>
                    <h2>{finding.title}</h2>
                  </div>
                  <button className="text-button" onClick={graph}>
                    在圖中查看
                    <ArrowUpRight size={15} />
                  </button>
                </div>
                <p className="finding-reason">{finding.reason}</p>
                {finding.details.blocking && (
                  <Notice>
                    此項仍有依據或適用性缺口，需要補齊後才能推進。
                  </Notice>
                )}
                {finding.details.model_candidates?.length > 0 && (
                  <div className="model-inference">
                    <span className="eyebrow">模型推斷 · 待專業複核</span>
                    {finding.details.model_candidates.map(
                      (m: Data, i: number) => (
                        <p key={i}>{m.reason}</p>
                      ),
                    )}
                    <small>
                      引用已核對屬於本次輸入；醫學支持性仍由獲權人員確認。
                    </small>
                  </div>
                )}
                <h3 className="section-label">來源原文</h3>
                <div className="evidence-quotes">
                  {finding.evidence_ids.length ? (
                    finding.evidence_ids.map((eid: string) => {
                      const ev = data.evidence.find((e: Data) => e.id === eid);
                      const doc = [
                        ...data.documents,
                        ...(data.document_versions || []),
                      ].find((d: Data) => d.id === ev?.document_id);
                      return (
                        <button
                          key={eid}
                          className={
                            "evidence-quote " +
                            (evidenceId === eid ? "active" : "")
                          }
                          onClick={() => {
                            setEvidenceId(eid);
                          }}
                        >
                          <span>
                            <FileText size={14} />
                            {doc?.title || "歷史文書"} · v{doc?.version ?? "—"}
                            <small>
                              第 {ev?.envelope.locator.line_start ?? "—"} 行
                            </small>
                          </span>
                          <blockquote>
                            {ev?.envelope.content.text ||
                              "當前版本未提供此證據，請回查歷史運行。"}
                          </blockquote>
                          <span className="quote-link">
                            定位原文 <ArrowUpRight size={13} />
                          </span>
                        </button>
                      );
                    })
                  ) : (
                    <p className="muted">
                      尚未獲得可支持的精確原文位置，系統不補造引用。
                    </p>
                  )}
                </div>
                <div className="suggestion">
                  <h3>整改建議</h3>
                  <p>{finding.suggestion}</p>
                </div>
                <div className="responsibility-card">
                  <div>
                    <UserRound size={17} />
                    <span>當前責任節點</span>
                    <Badge value={task.state} />
                  </div>
                  <p>
                    <Clock3 size={15} />
                    截止 {when(task.deadline)}
                    {new Date(task.deadline).getTime() < Date.now() && (
                      <Badge value="high">已逾期</Badge>
                    )}
                  </p>
                  <p>
                    責任醫生：{actorName(task.doctor_id)} · 複核人：
                    {actorName(task.reviewer_id)}
                  </p>
                  <div className="action-row">
                    {choices.length ? (
                      choices.map((a) => (
                        <button
                          key={a}
                          className={
                            [
                              "accept",
                              "revise",
                              "confirm",
                              "sign",
                              "arbitrate",
                            ].includes(a)
                              ? "primary"
                              : "secondary"
                          }
                          onClick={() => setAction(a)}
                        >
                          {actions[a]}
                        </button>
                      ))
                    ) : (
                      <span className="muted">
                        等待對應崗位處理；當前身份沒有此節點的操作權限。
                      </span>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <Empty
                title="先選擇一個問題"
                description="對照原文、規則與專業意見，再繼續處理。"
              />
            )}
          </section>
        </div>
      ) : tab === "versions" ? (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>文書與固定版本</h2>
              <p>整改形成新版本，原始文書和歷史責任記錄保留。</p>
            </div>
          </div>
          <div className="document-grid">
            {data.documents.map((d: Data) => (
              <div className="document-card" key={d.id}>
                <div>
                  <FileText size={20} />
                  <h3>{d.title}</h3>
                  <Badge value="version">v{d.version}</Badge>
                </div>
                <pre>{d.content}</pre>
                <small>
                  {d.parent_id ? "父版本：" + d.parent_id : "來源初始版本"} ·{" "}
                  {when(d.created_at)}
                </small>
              </div>
            ))}
          </div>
          <div className="panel-heading">
            <h2>責任簽署記錄</h2>
          </div>
          {data.signatures.length ? (
            data.signatures.map((s: Data) => (
              <div className="signature-row" key={s.id}>
                <Shield size={18} />
                <strong>
                  {s.role === "doctor" ? "責任醫生" : "質控複核人"}
                </strong>
                <span>{actorName(s.actor_id)}</span>
                <small>
                  {when(s.created_at)} ·{" "}
                  {s.mode === "local_engineering"
                    ? "本地工程身份記錄"
                    : "認證責任記錄"}
                </small>
                <code>{s.scope_digest.slice(0, 12)}</code>
              </div>
            ))
          ) : (
            <Empty
              title="尚無簽署記錄"
              description="完成當前範圍核驗與人工確認後，兩崗位分別簽署。"
            />
          )}
        </section>
      ) : (
        <section className="panel">
          <div className="panel-heading">
            <h2>責任操作時間線</h2>
          </div>
          {data.decisions.length ? (
            <div className="timeline">
              {data.decisions.map((d: Data) => (
                <article key={d.id}>
                  <span className="timeline-dot" />
                  <time>{when(d.created_at)}</time>
                  <h3>
                    {actions[d.action] || d.action}
                    <small>
                      {d.manifest.actor_snapshot?.name || actorName(d.actor_id)}
                    </small>
                  </h3>
                  <p>{d.reason}</p>
                  <div>
                    <Badge value={d.before_state} />
                    <ChevronRight size={13} />
                    <Badge value={d.after_state} />
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <Empty
              title="尚無人工責任操作"
              description="系統檢查不會自動生成醫生意見或責任簽字。"
            />
          )}
          <div className="panel-heading">
            <h2>質控執行軌跡</h2>
          </div>
          {data.runs.map((r: Data) => (
            <details className="run-detail" key={r.id}>
              <summary>
                <Badge value={r.status} />
                <span>{when(r.created_at)}</span>
                <small>{r.id.slice(0, 12)}</small>
              </summary>
              <ol>
                {r.trace.map((s: string) => (
                  <li key={s}>{s}</li>
                ))}
              </ol>
              <Notice>
                模型狀態：{r.coverage.model?.status || "尚未執行"}
                ；臨床效果：尚未評估。各規則的未知項保持在覆蓋分母中。
              </Notice>
            </details>
          ))}
        </section>
      )}
      {evidenceId && (
        <Modal title="固定版本原文" wide onClose={() => setEvidenceId("")}>
          <ErrorBox message={evidenceView.error} />
          {evidenceView.loading ? (
            <Loading />
          ) : (
            <div className="source-document">
              <h3>
                {evidenceView.data?.document?.title} · v
                {evidenceView.data?.document?.version}
              </h3>
              <div className="source-lines">
                {evidenceView.data?.document?.content
                  .split("\n")
                  .map((line: string, i: number) => (
                    <div
                      className={
                        evidenceView.data?.evidence.envelope.locator
                          .line_start ===
                        i + 1
                          ? "highlighted-line"
                          : ""
                      }
                      key={i}
                    >
                      <span>{i + 1}</span>
                      <p>{line}</p>
                    </div>
                  ))}
              </div>
              <p className="muted">
                來源版本 {evidenceView.data?.evidence.source_version} ·
                原文定位與展示文本保持一致。
              </p>
            </div>
          )}
        </Modal>
      )}
      {runOpen && (
        <RunDialog
          data={data}
          onClose={() => setRunOpen(false)}
          onDone={() => {
            setRunOpen(false);
            setRevision((v) => v + 1);
            setFeedback("已按所選固定基線受理檢查。");
          }}
        />
      )}
      {action && task && (
        <ActionDialog
          action={action}
          task={task}
          data={data}
          session={session}
          onClose={() => setAction("")}
          onDone={() => {
            setAction("");
            setRevision((r) => r + 1);
            setFeedback("操作已保存，責任狀態與審計同步更新。");
          }}
        />
      )}
    </div>
  );
}

function stage(state: string) {
  return ["signed", "sign"].includes(state)
    ? 4
    : ["verifying", "verify_ready", "verification_pending"].includes(state)
      ? 3
      : ["doctor", "appeal", "disputed"].includes(state)
        ? 2
        : 1;
}
function getActions(task: Data, actor: Data): string[] {
  if (!task) return [];
  const s = task.state;
  if (actor.role === "qc" && actor.id === task.reviewer_id) {
    if (s === "review") return ["accept", "reject", "assign", "extend"];
    if (["verification_pending", "blocked", "doctor"].includes(s))
      return ["recheck", "return", "extend"];
    if (s === "verify_ready") return ["confirm", "return"];
    if (s === "sign") return ["sign"];
    if (["signed", "closed_false_positive"].includes(s)) return ["reopen"];
  }
  if (actor.role === "doctor" && actor.id === task.doctor_id) {
    if (s === "doctor") return ["revise", "appeal"];
    if (s === "blocked") return ["revise"];
    if (s === "sign") return ["sign", "revise"];
    if (s === "signed") return ["revise"];
  }
  if (
    actor.role === "expert" &&
    actor.id === task.expert_id &&
    ["appeal", "disputed"].includes(s)
  )
    return ["arbitrate"];
  return [];
}

function ActionDialog({
  action,
  task,
  data,
  session,
  onClose,
  onDone,
}: {
  action: string;
  task: Data;
  data: Data;
  session: Data;
  onClose: () => void;
  onDone: () => void;
}) {
  const [initialVersion] = useState(task.version);
  const [reason, setReason] = useState("");
  const [docId, setDocId] = useState(data.documents.at(-1)?.id || "");
  const doc = data.documents.find((d: Data) => d.id === docId);
  const [content, setContent] = useState(doc?.content || "");
  const [verdict, setVerdict] = useState("revision_required");
  const [deadline, setDeadline] = useState("");
  const [doctor, setDoctor] = useState("doctor1");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <Modal title={actions[action]} wide={action === "revise"} onClose={onClose}>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          let payload: Data = {};
          if (action === "revise") {
            const fields = { ...doc.fields };
            const read = (label: string) =>
              content
                .match(new RegExp(label + "[：:]([^。\\n]*)"))?.[1]
                ?.trim();
            const encounter = read("就診標識"),
              diagnosis = read("診斷描述"),
              course = read("病情變化與診療經過"),
              time = read("記錄時間"),
              dose = read("用藥記錄");
            if (encounter) fields.encounter_id = encounter;
            if (diagnosis) fields.diagnosis_text = diagnosis;
            if (course && course !== "未填寫") fields.course_summary = course;
            if (time) fields.recorded_at = time;
            if (dose && !dose.includes("未記錄")) fields.dose_unit = dose;
            fields.author = session.actor.name;
            fields.source_signature = "工作臺內新版本提交記錄";
            payload = { document_id: docId, content, fields };
          }
          if (action === "arbitrate")
            payload = { verdict, next_expert_id: "expert3" };
          if (action === "extend")
            payload = {
              deadline: deadline ? new Date(deadline).toISOString() : "",
            };
          if (action === "assign") payload = { doctor_id: doctor };
          if (action === "appeal") payload = { expert_id: "expert3" };
          try {
            await post(
              "/tasks/" + task.id + "/" + action,
              command(initialVersion, reason, payload),
            );
            onDone();
          } catch (err) {
            setError((err as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <ErrorBox message={error} />
        {action === "revise" && (
          <>
            <label>
              要修改的當前文書
              <select
                value={docId}
                onChange={(e) => {
                  setDocId(e.target.value);
                  setContent(
                    data.documents.find((d: Data) => d.id === e.target.value)
                      .content,
                  );
                }}
              >
                {data.documents.map((d: Data) => (
                  <option key={d.id} value={d.id}>
                    {d.title} · v{d.version}
                  </option>
                ))}
              </select>
            </label>
            <label>
              新的文書內容
              <textarea
                className="document-editor"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
              />
            </label>
            <Notice>
              提交會生成有父版本的新文書，不覆蓋原件，不回寫
              HIS。請僅依據已核實資料修改。
            </Notice>
          </>
        )}
        {action === "arbitrate" && (
          <label>
            裁決出口
            <select
              value={verdict}
              onChange={(e) => setVerdict(e.target.value)}
            >
              <option value="revision_required">要求整改</option>
              <option value="not_a_problem">問題不成立</option>
              <option value="escalate">升級爭議</option>
            </select>
          </label>
        )}
        {action === "extend" && (
          <label>
            新的截止時間
            <input
              type="datetime-local"
              required
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
            />
          </label>
        )}
        {action === "assign" && (
          <label>
            責任醫生
            <select value={doctor} onChange={(e) => setDoctor(e.target.value)}>
              <option value="doctor1">林辰 · A組</option>
              <option value="doctor2">蘇禾 · B組</option>
            </select>
          </label>
        )}
        {action === "sign" && (
          <Notice>
            只簽署當前任務綁定的文書、規則、核驗與語義版本；本地工程身份記錄不冒充生產電子簽名。
          </Notice>
        )}
        <label>
          處理意見 / 理由
          <textarea
            required
            minLength={1}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="說明本次判斷依據和必要的處理意見"
          />
        </label>
        <div className="modal-actions">
          <button type="button" className="secondary" onClick={onClose}>
            取消
          </button>
          <button className="primary" disabled={busy}>
            {busy ? "正在保存…" : actions[action]}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function RunDialog({
  data,
  onClose,
  onDone,
}: {
  data: Data;
  onClose: () => void;
  onDone: () => void;
}) {
  const rules = useApi<Data>("/rules");
  const releases = useApi<Data>("/semantic/releases");
  const [semantic, setSemantic] = useState(
    data.case.details.semantic_release_id || "semantic-v1",
  );
  const [selection, setSelection] = useState<Data>(() =>
    Object.fromEntries(
      (
        data.case.details.rule_ids ||
        Array.from(
          { length: 8 },
          (_, i) => `MQC-DOC-${String(i + 1).padStart(3, "0")}-v1`,
        )
      ).map((id: string) => [id.split("-v")[0], id]),
    ),
  );
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const keys = Array.from(
    { length: 8 },
    (_, i) => "MQC-DOC-" + String(i + 1).padStart(3, "0"),
  );
  return (
    <Modal title="選擇檢查範圍與固定依據" wide onClose={onClose}>
      <Notice>
        檢查當前文書版本。候選規則僅用於允許的工程驗證，選擇新版本不會改寫舊結果或繼承舊簽字。
      </Notice>
      <label>
        醫療語義基線
        <select value={semantic} onChange={(e) => setSemantic(e.target.value)}>
          {releases.data?.items.map((r: Data) => (
            <option key={r.id} value={r.id}>
              {r.name} · {statusNames[r.status] || r.status}
            </option>
          ))}
        </select>
      </label>
      <div className="rule-baseline-grid">
        {keys.map((key) => (
          <label key={key}>
            {rules.data?.items.find((r: Data) => r.rule_key === key)?.name ||
              key}
            <select
              value={selection[key] || ""}
              onChange={(e) =>
                setSelection((v) => ({ ...v, [key]: e.target.value }))
              }
            >
              <option value="">請選擇匹配版本</option>
              {rules.data?.items
                .filter(
                  (r: Data) =>
                    r.rule_key === key &&
                    r.semantic_release_id === semantic &&
                    ["candidate", "approved"].includes(r.status),
                )
                .map((r: Data) => (
                  <option key={r.id} value={r.id}>
                    {key} · v{r.version} · {statusNames[r.status]}
                  </option>
                ))}
            </select>
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
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              await post(
                "/cases/" + data.case.id + "/quality-runs",
                command(
                  data.case.version,
                  "在所選固定文書、規則和本體範圍內執行輔助質控",
                  {
                    semantic_release_id: semantic,
                    rule_ids: keys.map((k) => selection[k]),
                  },
                ),
              );
              onDone();
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          {busy ? "正在受理…" : "按此基線執行檢查"}
        </button>
      </div>
    </Modal>
  );
}
