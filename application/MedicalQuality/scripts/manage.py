#!/usr/bin/env python3
"""本項目獨立的本地運行環境，不訪問其他項目數據庫或憑據。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import subprocess
import time
import urllib.request
import urllib.error
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime"
BACKEND = ROOT / "backend"
PYTHON = BACKEND / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
if os.name == "nt":
    os.environ["PATH"] = str(RUNTIME / "tools/pgsql/bin") + os.pathsep + os.environ.get("PATH", "")
PGPORT = 55443
APIPORT = 8180


def run(argv, **kwargs):
    return subprocess.run([str(x) for x in argv], check=True, **kwargs)


def write_private(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)
    path.chmod(0o600)


def config():
    return json.loads((RUNTIME / "config.json").read_text())


def postgres_start():
    pg = shutil.which("pg_ctl")
    if not pg:
        raise SystemExit(
            "需要 PostgreSQL 17 / pgvector；見 README 的容器或本機準備方法。"
        )
    status = subprocess.run(
        [pg, "-D", str(RUNTIME / "postgres"), "status"], capture_output=True
    )
    if status.returncode == 0:
        return
    run(
        [
            pg,
            "-D",
            RUNTIME / "postgres",
            "-l",
            RUNTIME / "logs/postgres.log",
            "start",
            "-w",
        ],
        stdout=subprocess.DEVNULL,
    )


def setup():
    RUNTIME.mkdir(exist_ok=True, mode=0o700)
    (RUNTIME / "logs").mkdir(exist_ok=True)
    (ROOT / "artifacts").mkdir(exist_ok=True)
    if not (RUNTIME / "config.json").exists():
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", PGPORT)) == 0:
                raise SystemExit("項目數據庫端口已佔用，未修改已有服務。")
        passwords = {
            role: secrets.token_urlsafe(30)
            for role in ["mq_bootstrap", "mq_app", "mq_worker", "mq_checkpoint"]
        }

        def url(role, driver=False):
            protocol = "postgresql+psycopg" if driver else "postgresql"
            return f"{protocol}://{role}:{quote(passwords[role])}@127.0.0.1:{PGPORT}/medical_quality"

        conf = {
            "mode": "local",
            "database_url": url("mq_app", True),
            "worker_database_url": url("mq_worker", True),
            "checkpoint_url": url("mq_checkpoint"),
            "migration_url": url("mq_bootstrap", True),
            "session_secret": secrets.token_urlsafe(48),
            "passwords": passwords,
        }
        write_private(RUNTIME / "config.json", json.dumps(conf, indent=2))
        pwfile = RUNTIME / "init-password"
        write_private(pwfile, passwords["mq_bootstrap"])
        try:
            run(
                [
                    "initdb",
                    "-D",
                    RUNTIME / "postgres",
                    "--username=mq_bootstrap",
                    "--auth=scram-sha-256",
                    f"--pwfile={pwfile}",
                    "--encoding=UTF8",
                    "--locale=C",
                ],
                stdout=subprocess.DEVNULL,
            )
        finally:
            pwfile.unlink(missing_ok=True)
        with (RUNTIME / "postgres/postgresql.conf").open("a") as stream:
            stream.write(
                f"\nlisten_addresses = '127.0.0.1'\nport = {PGPORT}\nmax_connections = 40\nshared_buffers = '128MB'\n" + ("" if os.name == 'nt' else f"unix_socket_directories = '{RUNTIME}'\n")
            )
    postgres_start()
    conf = config()
    env = {**os.environ, "PGPASSWORD": conf["passwords"]["mq_bootstrap"]}
    # Send generated credentials through stdin; never put them in command arguments/logs.
    sql = []
    for role in ["mq_app", "mq_worker", "mq_checkpoint"]:
        password = conf["passwords"][role]
        sql.append(
            f"SELECT 'CREATE ROLE {role} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD ''{password}''' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname='{role}')\\gexec"
        )
    sql.append(
        "SELECT 'CREATE DATABASE medical_quality' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname='medical_quality')\\gexec"
    )
    run(
        [
            "psql",
            "-h",
            "127.0.0.1",
            "-p",
            PGPORT,
            "-U",
            "mq_bootstrap",
            "-d",
            "postgres",
            "-v",
            "ON_ERROR_STOP=1",
        ],
        input="\n".join(sql),
        text=True,
        env=env,
        stdout=subprocess.DEVNULL,
    )
    run(
        [
            "psql",
            "-h",
            "127.0.0.1",
            "-p",
            PGPORT,
            "-U",
            "mq_bootstrap",
            "-d",
            "medical_quality",
            "-v",
            "ON_ERROR_STOP=1",
        ],
        input="CREATE SCHEMA IF NOT EXISTS checkpoints AUTHORIZATION mq_checkpoint;\nALTER ROLE mq_checkpoint SET search_path TO checkpoints;",
        text=True,
        env=env,
        stdout=subprocess.DEVNULL,
    )
    run(
        [PYTHON, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND,
        env={**os.environ, "MQ_MIGRATION_URL": conf["migration_url"]},
    )
    print("項目 PostgreSQL 17 / pgvector 與業務遷移已就緒。")


def pid_alive(pid):
    if os.name != "nt":
        os.kill(pid, 0)
        return
    import ctypes
    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        raise ProcessLookupError(pid)
    code = ctypes.c_ulong()
    try:
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value != 259:
            raise ProcessLookupError(pid)
    finally:
        kernel.CloseHandle(handle)


def start():
    postgres_start()
    current_config = config()
    if not current_config.get("model_key"):
        current_config["model_key"] = secrets.token_urlsafe(32)
        write_private(RUNTIME / "config.json", json.dumps(current_config, indent=2))
    write_private(RUNTIME / "model-api-key", current_config["model_key"])
    binaries = list((RUNTIME / "tools/llama").glob("*/llama-server.exe" if os.name == "nt" else "*/llama-server"))
    weights = ROOT / "artifacts/models/qwen3-4b/Qwen3-4B-Q4_K_M.gguf"
    model_pid = RUNTIME / "model.pid"
    model_running = False
    if model_pid.exists():
        try:
            pid_alive(int(model_pid.read_text()))
            model_running = True
        except ProcessLookupError:
            model_pid.unlink()
    if os.environ.get("MQ_ENABLE_LOCAL_MODEL") == "1" and binaries and weights.exists() and not model_running:
        with (RUNTIME / "logs/model.log").open("ab") as stream:
            process = subprocess.Popen(
                [
                    str(binaries[0]),
                    "-m",
                    str(weights),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8191",
                    "-c",
                    "8192",
                    "-np",
                    "1",
                    "-ngl",
                    "99",
                    "-t",
                    "4",
                    "--jinja",
                    "--chat-template-kwargs",
                    '{"enable_thinking":false}',
                    "--no-webui",
                    "--no-ui-mcp-proxy",
                    "--no-context-shift",
                    "--api-key-file",
                    str(RUNTIME / "model-api-key"),
                ],
                cwd=ROOT,
                stdout=stream,
                stderr=stream,
                start_new_session=(os.name != "nt"),
                creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
            )
        model_pid.write_text(str(process.pid))
    for name, module in [
        ("api", "medical_quality.app"),
        ("worker", "medical_quality.worker"),
    ]:
        pidfile = RUNTIME / (name + ".pid")
        if pidfile.exists():
            try:
                pid_alive(int(pidfile.read_text()))
                print(name, "已經運行")
                continue
            except ProcessLookupError:
                pidfile.unlink()
        argv = [str(PYTHON), "-m", module]
        env = dict(os.environ)
        if name == "worker":
            env["MQ_DATABASE_URL"] = config()["worker_database_url"]
        with (RUNTIME / "logs" / (name + ".log")).open("ab") as stream:
            process = subprocess.Popen(
                argv,
                cwd=BACKEND,
                env=env,
                stdout=stream,
                stderr=stream,
                start_new_session=(os.name != "nt"),
                creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
            )
        pidfile.write_text(str(process.pid))
    for attempt in range(60):
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{APIPORT}/api/health", timeout=1
            ) as response:
                if response.status == 200:
                    print(f"本地工作臺：http://127.0.0.1:{APIPORT}")
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.25)
    raise SystemExit(
        "應用尚未通過健康檢查，請查看 .runtime/logs/api.log；未宣稱啟動成功。"
    )


def stop():
    for name in ["api", "worker", "model"]:
        path = RUNTIME / (name + ".pid")
        if path.exists():
            pid = int(path.read_text())
            if os.name == "nt":
                command = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", f"(Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}').CommandLine"],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW,
                ).stdout
            else:
                command = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True).stdout
            expected = (
                "llama-server"
                if name == "model"
                else f"medical_quality.{'app' if name == 'api' else 'worker'}"
            )
            if expected in command and (os.name != "nt" or str(ROOT).lower() in command.lower()):
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False) if os.name == "nt" else os.kill(pid, signal.SIGTERM)
            path.unlink()
    if (RUNTIME / "postgres/PG_VERSION").exists():
        subprocess.run(
            ["pg_ctl", "-D", str(RUNTIME / "postgres"), "stop", "-m", "fast"],
            capture_output=True,
        )
    print("本項目服務已停止；業務數據保留。")


def status():
    for port, label in [(PGPORT, "PostgreSQL"), (APIPORT, "工作臺 API")]:
        with socket.socket() as probe:
            print(
                label,
                "運行中" if probe.connect_ex(("127.0.0.1", port)) == 0 else "未運行",
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["setup", "start", "stop", "status", "seed"])
    args = parser.parse_args()
    if args.action == "seed":
        run(
            [PYTHON, "-m", "medical_quality.seed"],
            cwd=BACKEND,
            env={**os.environ, "MQ_DATABASE_URL": config()["migration_url"]},
        )
    else:
        globals()[args.action]()




