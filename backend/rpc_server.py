from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Callable

from backend.domain.errors import DomainError, ErrorCode
from backend.domain.state import AppState
from backend.repository.state_repository import StateRepository
from backend.licensing import LicenseManager
from backend.rpc.dispatcher import RpcDispatcher
from backend.application import (
    SubjectsService,
    LicensingService,
    ProctoringService,
    RoomsService,
    PrintingService,
    SystemService,
    DashboardService,
    UpdateGuard,
)

logger = logging.getLogger(__name__)


def _get_state_file() -> str:
    data_dir = (os.environ.get("EXAMFLOW_DATA_DIR") or os.environ.get("EXAMDESK_DATA_DIR") or "").strip()
    if data_dir:
        return os.path.join(data_dir, "data", "state.json")
    base = (
        os.environ.get("EXAMFLOW_APP_DIR")
        or os.environ.get("EXAMDESK_APP_DIR")
        or os.environ.get("EXAMFLOW_CERT_DIR")
        or os.environ.get("EXAMDESK_CERT_DIR")
        or ""
    ).strip()
    if base:
        return os.path.join(base, "data", "state.json")
    return os.path.join("data", "state.json")


def _reply_ok(result: Any) -> dict[str, Any]:
    return {"ok": True, "result": result}


def _reply_err(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message}


def build_dispatcher() -> RpcDispatcher:
    """构建 RPC 调度器"""
    # 构建依赖
    state = AppState()
    repo = StateRepository(_get_state_file())
    repo.load(state)
    update_guard = UpdateGuard()
    update_guard.refresh()

    # 创建 Services
    subjects_svc = SubjectsService(state, repo)
    licensing_svc = LicensingService(LicenseManager())
    proctoring_svc = ProctoringService(state, repo)
    rooms_svc = RoomsService(state, repo)
    printing_svc = PrintingService(state, repo)
    system_svc = SystemService(state, repo, update_guard=update_guard)
    dashboard_svc = DashboardService(state)

    # 注册路由
    dispatcher = RpcDispatcher()

    # System
    dispatcher.register("system.resetData", system_svc.reset_data)
    dispatcher.register("system.exportState", system_svc.export_state)
    dispatcher.register("system.importState", system_svc.import_state)
    dispatcher.register("system.getHelpManual", system_svc.get_help_manual)
    dispatcher.register("system.getUpdateGuardStatus", system_svc.get_update_guard_status)
    dispatcher.register("system.refreshUpdateGuard", system_svc.refresh_update_guard)

    # Licensing
    dispatcher.register("licensing.machineCode", licensing_svc.machine_code)
    dispatcher.register("licensing.verify", licensing_svc.verify)
    dispatcher.register("licensing.register", licensing_svc.register)

    # Dashboard
    dispatcher.register("dashboard.getStats", dashboard_svc.get_stats)

    # Subjects
    dispatcher.register("subjects.list", subjects_svc.list)
    dispatcher.register("subjects.update", subjects_svc.update)
    dispatcher.register("subjects.import", subjects_svc.import_from_excel)
    dispatcher.register("subjects.export", subjects_svc.export)
    dispatcher.register("subjects.template", subjects_svc.template)
    dispatcher.register("subjects.validate", subjects_svc.validate)

    # Proctoring
    dispatcher.register("proctoring.getState", proctoring_svc.get_state)
    dispatcher.register("proctoring.saveConfig", proctoring_svc.save_config)
    dispatcher.register("proctoring.startSolverJob", proctoring_svc.start_solver_job)
    dispatcher.register("proctoring.getJobStatus", proctoring_svc.get_job_status)
    dispatcher.register("proctoring.clearState", proctoring_svc.clear_state)
    dispatcher.register("proctoring.importTeachers", proctoring_svc.import_teachers)
    dispatcher.register("proctoring.generateSchedule", proctoring_svc.generate_schedule)
    dispatcher.register("proctoring.template", proctoring_svc.template)
    dispatcher.register("proctoring.export", proctoring_svc.export)
    dispatcher.register("proctoring.continue", proctoring_svc.continue_schedule)
    dispatcher.register("proctoring.importSchedule", proctoring_svc.import_schedule)
    dispatcher.register("proctoring.swap", proctoring_svc.swap)
    dispatcher.register("proctoring.export_empty_preset", proctoring_svc.export_empty_preset)
    dispatcher.register("proctoring.import_preset", proctoring_svc.import_preset)

    # Rooms
    dispatcher.register("rooms.resetState", rooms_svc.reset_state)
    dispatcher.register("rooms.getState", rooms_svc.get_state)
    dispatcher.register("rooms.saveState", rooms_svc.save_state)
    dispatcher.register("rooms.getSubjectPriority", rooms_svc.get_subject_priority)
    dispatcher.register("rooms.setSubjectPriority", rooms_svc.set_subject_priority)
    dispatcher.register("rooms.getGaokaoTimeSettings", rooms_svc.get_gaokao_time_settings)
    dispatcher.register("rooms.setGaokaoTimeSettings", rooms_svc.set_gaokao_time_settings)
    dispatcher.register("rooms.generateTemplate", rooms_svc.generate_template)
    dispatcher.register("rooms.importSettings", rooms_svc.import_settings)
    dispatcher.register("rooms.importStudents", rooms_svc.import_students)
    dispatcher.register("rooms.arrange", rooms_svc.arrange)
    dispatcher.register("rooms.export", rooms_svc.export)
    dispatcher.register("rooms.importResults", rooms_svc.import_results)

    # Printing
    dispatcher.register("printing.getState", printing_svc.get_state)
    dispatcher.register("printing.saveConfig", printing_svc.save_config)
    dispatcher.register("printing.resetState", printing_svc.reset_state)
    dispatcher.register("printing.readHeaders", printing_svc.read_headers)
    dispatcher.register("printing.previewData", printing_svc.preview_data)
    dispatcher.register("printing.loadFromSchedule", printing_svc.load_from_schedule)
    dispatcher.register("printing.previewPdf", printing_svc.preview_pdf)
    dispatcher.register("printing.generate", printing_svc.generate)

    return dispatcher


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    stdin_buffer = sys.stdin.buffer
    dispatcher = build_dispatcher()

    while True:
        try:
            raw_bytes = stdin_buffer.readline()
        except Exception:
            break

        if not raw_bytes:
            break

        try:
            line = raw_bytes.decode("utf-8-sig").strip()
        except UnicodeDecodeError as e:
            logger.warning("UTF-8 解码失败: %s 原始字节: %s", e, raw_bytes[:100])
            continue

        if not line:
            continue

        try:
            req = json.loads(line)
        except Exception as e:
            err_msg = f"收到无效 JSON。错误: {str(e)}。内容: {repr(line)[:1000]}"
            logger.warning("%s", err_msg)
            sys.stdout.write(json.dumps(_reply_err(err_msg), ensure_ascii=False) + "\n")
            sys.stdout.flush()
            continue

        req_id = req.get("id", None)
        method = req.get("method")
        params = req.get("params") or {}
        if not isinstance(params, dict):
            params = {}

        if not dispatcher.has_method(method):
            reply = _reply_err(f"未知方法: {method}")
            if req_id is not None:
                reply["id"] = req_id
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            continue

        try:
            result = dispatcher.dispatch(method, params)
            reply = _reply_ok(result)
            if req_id is not None:
                reply["id"] = req_id
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except DomainError as e:
            # 业务错误，返回结构化错误信息
            reply = {"ok": False, "error": e.to_dict()}
            if req_id is not None:
                reply["id"] = req_id
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except ValueError as e:
            # 参数错误
            logger.warning("参数错误: %s", e)
            reply = {
                "ok": False,
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR.value,
                    "message": f"参数错误: {str(e)}",
                    "details": {}
                }
            }
            if req_id is not None:
                reply["id"] = req_id
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except FileNotFoundError as e:
            # 文件不存在
            logger.warning("文件不存在: %s", e)
            reply = {
                "ok": False,
                "error": {
                    "code": ErrorCode.FILE_IO_ERROR.value,
                    "message": f"文件不存在: {e.filename if hasattr(e, 'filename') else '未知'}",
                    "details": {"filename": e.filename if hasattr(e, 'filename') else None}
                }
            }
            if req_id is not None:
                reply["id"] = req_id
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except PermissionError as e:
            # 权限错误
            logger.warning("权限不足: %s", e)
            reply = {
                "ok": False,
                "error": {
                    "code": ErrorCode.FILE_IO_ERROR.value,
                    "message": "权限不足，请检查文件访问权限",
                    "details": {}
                }
            }
            if req_id is not None:
                reply["id"] = req_id
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except OSError as e:
            logger.warning("文件读写失败: %s", e)
            reply = {
                "ok": False,
                "error": {
                    "code": ErrorCode.FILE_IO_ERROR.value,
                    "message": str(e) or "文件读写失败",
                    "details": {}
                }
            }
            if req_id is not None:
                reply["id"] = req_id
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except Exception as e:
            # 未预期的错误，记录详细信息但返回通用消息
            logger.exception("未预期异常: %s", e)
            reply = {
                "ok": False,
                "error": {
                    "code": ErrorCode.UNKNOWN_ERROR.value,
                    "message": "系统内部错误，请联系管理员",
                    "details": {}
                }
            }
            if req_id is not None:
                reply["id"] = req_id
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()

    return 0
