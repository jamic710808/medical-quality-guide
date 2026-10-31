import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { AlertCircle, X, LoaderCircle, ArrowLeft } from "lucide-react";
import { api, navigate, statusNames } from "./api";

const scrollPositions = new Map<string, number>();
export function useScrollMemory<T extends HTMLElement>(
  key: string,
  ready: boolean,
) {
  const ref = useRef<T>(null);
  useLayoutEffect(() => {
    const element = ref.current;
    if (!ready || !element) return;
    element.scrollTop = scrollPositions.get(key) || 0;
    const save = () => {
      scrollPositions.set(key, element.scrollTop);
      if (scrollPositions.size > 50)
        scrollPositions.delete(scrollPositions.keys().next().value!);
    };
    element.addEventListener("scroll", save, { passive: true });
    return () => {
      save();
      element.removeEventListener("scroll", save);
    };
  }, [key, ready]);
  return ref;
}

export function useApi<T = any>(path: string | null, version = 0) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [settledKey, setSettledKey] = useState("");
  const requestKey = JSON.stringify([path, version]);
  useEffect(() => {
    if (!path) {
      setData(null);
      setError("");
      setSettledKey(requestKey);
      setLoading(false);
      return;
    }
    const abort = new AbortController();
    setLoading(true);
    setError("");
    setData(null);
    api<T>(path, { signal: abort.signal })
      .then((value) => {
        if (!abort.signal.aborted) {
          setData(value);
          setSettledKey(requestKey);
        }
      })
      .catch((e) => {
        if (!abort.signal.aborted && e.name !== "AbortError") {
          setError(e.message);
          setSettledKey(requestKey);
        }
      })
      .finally(() => {
        if (!abort.signal.aborted) setLoading(false);
      });
    return () => abort.abort();
  }, [path, version]);
  const current = settledKey === requestKey;
  return {
    data: current ? data : null,
    error: current ? error : "",
    loading: !!path && (!current || loading),
    setData,
  };
}
export function Badge({
  value,
  children,
}: {
  value: string;
  children?: ReactNode;
}) {
  return (
    <span className={"badge " + value}>
      {children || statusNames[value] || value}
    </span>
  );
}
export function ErrorBox({ message }: { message: string }) {
  return message ? (
    <div className="error-box" role="alert">
      <AlertCircle size={17} />
      {message}
    </div>
  ) : null;
}
export function Loading() {
  return (
    <div className="loading" role="status">
      <LoaderCircle size={22} className="spin" />
      正在讀取當前範圍…
    </div>
  );
}
export function Empty({
  title = "當前範圍暫無記錄",
  description = "調整篩選條件，或等待相應資料接入。",
  children,
}: {
  title?: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <div className="empty-icon">◎</div>
      <h3>{title}</h3>
      <p>{description}</p>
      {children}
    </div>
  );
}
export function PageTitle({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <header className="page-title">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {action && <div className="title-actions">{action}</div>}
    </header>
  );
}
export function Back({ to, label = "返回" }: { to: string; label?: string }) {
  return (
    <button className="text-button" onClick={() => navigate(to)}>
      <ArrowLeft size={16} />
      {label}
    </button>
  );
}
export function Modal({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const panel = useRef<HTMLElement>(null);
  const close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    const before = document.activeElement as HTMLElement;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const shell = document.querySelector<HTMLElement>(".mq-shell");
    const wasInert = shell?.inert;
    if (shell) shell.inert = true;
    const focusable = () =>
      Array.from(
        panel.current?.querySelectorAll<HTMLElement>(
          'button:not([disabled]),a[href],input:not([disabled]),textarea:not([disabled]),select:not([disabled]),[tabindex="0"]',
        ) || [],
      ).filter((e) => e.offsetParent !== null);
    const timer = requestAnimationFrame(() => focusable()[0]?.focus());
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        close.current();
      }
      if (e.key === "Tab") {
        const items = focusable();
        if (!items.length) return;
        const first = items[0],
          last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => {
      cancelAnimationFrame(timer);
      window.removeEventListener("keydown", handler);
      document.body.style.overflow = overflow;
      if (shell) shell.inert = wasInert || false;
      before?.focus();
    };
  }, []);
  return createPortal(
    <div className="modal-backdrop">
      <section
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={"modal " + (wide ? "wide" : "")}
      >
        <header>
          <h2>{title}</h2>
          <button className="icon-button" aria-label="關閉" onClick={onClose}>
            <X size={20} />
          </button>
        </header>
        <div className="modal-body">{children}</div>
      </section>
    </div>,
    document.body,
  );
}
export function Notice({ children }: { children: ReactNode }) {
  return (
    <div className="notice">
      <AlertCircle size={16} />
      <span>{children}</span>
    </div>
  );
}

export function PdfEvidencePreview({ id, page }: { id: string; page: number }) {
  const [open, setOpen] = useState(false);
  const [failed, setFailed] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [aspect, setAspect] = useState(1);
  return (
    <section className="pdf-evidence-preview">
      <button
        className="text-button"
        onClick={() => {
          setOpen((v) => !v);
          setFailed(false);
        }}
      >
        {open ? "收起原頁" : `查看第 ${page} 頁原圖與位置`}
      </button>
      {open && !failed && (
        <button
          className="text-button"
          onClick={() => setRotation((value) => (value + 270) % 360)}
        >
          向左旋轉視圖
        </button>
      )}
      {open &&
        (failed ? (
          <ErrorBox message="原頁暫不可用，請核對當前授權與來源版本後重試。" />
        ) : (
          <figure>
            <div
              className="pdf-page-frame"
              style={{ aspectRatio: rotation % 180 ? 1 / aspect : aspect }}
            >
              <img
                src={`/api/v1/evidence/${id}/page-image`}
                alt={`固定來源第 ${page} 頁的允許範圍，藍框標出證據位置`}
                onError={() => setFailed(true)}
                onLoad={(event) =>
                  setAspect(
                    event.currentTarget.naturalWidth /
                      event.currentTarget.naturalHeight,
                  )
                }
                data-view-rotation={rotation}
                style={{
                  width: rotation % 180 ? `${100 * aspect}%` : "100%",
                  transform: `translate(-50%, -50%) rotate(${rotation}deg)`,
                }}
              />
            </div>
            <figcaption>
              固定來源第 {page} 頁的允許範圍 · 藍框為當前證據位置；原圖與 OCR
              文字可分別核查。
            </figcaption>
          </figure>
        ))}
    </section>
  );
}
