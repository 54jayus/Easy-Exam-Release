# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Language

**IMPORTANT**: Always communicate with the user in Chinese (中文). All responses, explanations, and conversations should be in Chinese unless the user explicitly requests otherwise.

## Project Overview

**Easy Exam (智能考务系统)** — A desktop application for exam administration. It manages exam room arrangement, proctoring schedules, printing of exam materials, and student registration. Built as an Electron app with a Vue 3 frontend and a Python backend communicating via JSON-RPC over stdin/stdout.

## Architecture

### Two-Process Model

The app runs two processes:

1. **Electron + Vue 3 frontend** (`frontend/`) — UI layer. Spawns the Python backend as a child process on startup.
2. **Python backend** (`backend/`) — Business logic engine. Communicates with the frontend via newline-delimited JSON-RPC over stdin/stdout.

The RPC protocol: frontend sends `{"id": "1", "method": "method_name", "params": {...}}\n`, backend replies `{"ok": true, "result": ..., "id": "1"}\n` or `{"ok": false, "error": "...", "id": "1"}\n`.

### Frontend (`frontend/src/`)

- **Framework**: Vue 3 + TypeScript + Vite + Electron
- **UI**: Element Plus + Tailwind CSS + lucide-vue-next icons
- **State**: Pinia (`stores/license.ts`)
- **Routing**: Vue Router with hash history (`router.ts`) — pages: dashboard, registration, subjects, proctoring, rooms, printing, help, assistant
- **Backend bridge**: `lib/pythonBackend.ts` — `PythonBackendClient` singleton (`pythonBackend`) that manages the child process lifecycle and maps RPC calls to promises
- **Electron IPC**: `electron/main.ts` handles `spawn_python`, `write_python`, `kill_python`, `dialog:open`, `dialog:save`, `open_path`, `assistant:open/close/move/resize` etc. `electron/preload.ts` exposes `window.electron`

### Backend (`backend/`)

- **Entry**: `backend/__main__.py` → `backend/rpc_server.py:main()`
- **RPC dispatch**: `rpc_server.py` — single large file containing all RPC method handlers and in-memory state. All state (subjects, rooms, students, proctoring schedule, config) lives here and is persisted to `data/state.json`
- **Modules**:
  - `examroom/` — exam room arrangement logic (`core/arrangement.py`: `ExamArrangement`)
  - `proctoring/` — proctoring schedule generation (`core/models.py`: `Teacher`, `Schedule`, `Exam`; `schedule_export.py`, `schedule_import.py`, `teacher_import.py`)
  - `printing/` — document generation (corner papers, desk labels, admission tickets, exam bag labels, student info tables). Uses `core/factory.py` + `core/config.py` + `core/generators/`
  - `subjects/` — exam subject management (`core.py`, `excel.py`)
  - `assistant/` — AI assistant using ZhipuAI API (`core/assistant_engine.py`, `core/zhipu_client.py`)
  - `licensing/` — machine-code-based license verification (`core.py`, `cert_store.py`)
- **Persistence**: State saved to `data/state.json`. Path determined by env vars `EXAMFLOW_DATA_DIR` / `EXAMDESK_DATA_DIR`, falling back to `data/state.json` relative to CWD.

### AI Assistant

A secondary Electron window (`/assistant` route, `AssistantWindow.vue`) that opens as a frameless floating panel. It calls the Python backend's `assistant.*` RPC methods, which use the ZhipuAI API. The main window sends UI context to the assistant via IPC (`update-ui-context` / `get-ui-context`).

## Development Commands

All frontend commands run from `frontend/`:

```bash
# Start dev server (Electron + Vite hot reload)
cd frontend
npm run dev

# Type-check only
cd frontend
npx vue-tsc -p tsconfig.json --noEmit

# Build frontend (no Electron packaging)
cd frontend
npm run build

# Build + package as Windows installer (output: frontend/release_v6/)
cd frontend
npm run electron:build
```

Run the Python backend directly (for debugging without Electron):

```bash
D:/ANACONDA/envs/exam_scheduler/python.exe -m backend
```

### Building the Python Engine (PyInstaller)

The Python backend is bundled as `engine.exe` using PyInstaller. Use the spec file at `frontend/engine.spec`:

```bash
# From project root
D:/ANACONDA/envs/exam_scheduler/python.exe -m PyInstaller --clean --noconfirm frontend/engine.spec
# Output goes to frontend/python-dist/engine/
```

The root-level `engine.spec` is an older variant; prefer `frontend/engine.spec`.

## Key Environment Variables

| Variable | Purpose |
|---|---|
| `EXAMFLOW_DATA_DIR` / `EXAMDESK_DATA_DIR` | Where `data/state.json` is stored |
| `EXAMFLOW_APP_DIR` / `EXAMDESK_APP_DIR` | App exe directory (for cert path fallback) |
| `EXAMFLOW_CERT_DIR` / `EXAMDESK_CERT_DIR` | Where `license.cert` is stored |

In Electron mode, the main process sets `EXAMDESK_APP_DIR` and `EXAMDESK_CERT_DIR` to `path.dirname(app.getPath('exe'))` before spawning the Python process.

## License Certificate Path

- **Dev mode (via Electron)**: `frontend/node_modules/electron/dist/license.cert`
- **Installed app**: same directory as `Easy Exam.exe`
- **Direct Python run** (no env vars): `<project_root>/backend/license.cert`

## Python Environment

Conda env: `D:/ANACONDA/envs/exam_scheduler`

Key dependencies: `pandas`, `openpyxl`, `xlrd`, `xlsxwriter`, `PyInstaller`

## RPC Server Pattern

All business logic is dispatched through `build_dispatch()` in `rpc_server.py`, which returns a dict mapping method names to handler functions. In-memory state variables (subjects, rooms, students, schedule, config) are captured as closures. The `main()` function reads JSON lines from stdin and writes JSON replies to stdout.

When adding a new RPC method: add a handler function inside `build_dispatch()` and register it in the returned dict.
