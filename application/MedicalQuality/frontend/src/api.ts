export type Data = Record<string, any>;
export class ApiError extends Error {
  status: number;
  code: string;
  constructor(message: string, status: number, code: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}
export async function api<T = Data>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const csrf =
    document.cookie
      .split("; ")
      .find((c) => c.startsWith("mq_csrf="))
      ?.split("=")[1] || "";
  const response = await fetch("/api/v1" + path, {
    ...options,
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      "X-CSRF-Token": decodeURIComponent(csrf),
      ...options.headers,
    },
    credentials: "same-origin",
  });
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401)
      window.dispatchEvent(new CustomEvent("mq-session-expired"));
    throw new ApiError(
      data.error?.message || "請求未完成，請稍後重試。",
      response.status,
      data.error?.code || "request_failed",
    );
  }
  return data;
}
export function post<T = Data>(path: string, body: unknown) {
  return api<T>(path, { method: "POST", body: JSON.stringify(body) });
}
export function command(version: number, reason: string, payload: Data = {}) {
  return {
    expected_version: version,
    idempotency_key: crypto.randomUUID(),
    reason,
    payload,
    purpose: "engineering",
  };
}
export function navigate(path: string) {
  history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
export const statusNames: Record<string, string> = {
  pending: "待檢查",
  queued: "等待執行",
  running: "正在檢查",
  review: "待質控複核",
  needs_review: "待人工複核",
  doctor: "待醫生處理",
  appeal: "申訴待裁決",
  disputed: "爭議升級",
  blocked: "待補充依據",
  partial: "部分完成",
  empty: "聲明範圍為空",
  checked: "已檢查",
  verification_pending: "待再次核驗",
  verifying: "正在再核驗",
  verify_ready: "待人工確認",
  sign: "待責任簽字",
  signed: "當前範圍已簽字",
  closed_false_positive: "問題不成立",
  candidate: "候選",
  approved: "已批准",
  engineering_ready: "工程基線",
  retired: "已停用",
  draft: "草稿",
  in_review: "待專業審核",
  engineering_released: "工程版本已形成",
  failed: "執行失敗",
  completed: "已完成",
  success: "讀取成功",
  registered: "已登記",
  frozen: "已凍結",
  not_evaluated: "尚未評測",
  stopped: "已停用",
};
export const riskNames: Record<string, string> = {
  high: "高風險",
  medium: "中風險",
  low: "低風險",
  unknown: "待判斷",
};
export const roleNames: Record<string, string> = {
  qc: "質控人員",
  doctor: "責任醫生",
  expert: "複核專家",
  info: "信息科",
  manager: "管理部門",
  support: "運行支持",
};
export function when(value: string) {
  return value
    ? new Date(value).toLocaleString("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";
}
