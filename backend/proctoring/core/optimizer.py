#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optimization helpers for proctoring scheduling."""

import logging


logger = logging.getLogger(__name__)


def optimize_duration_postprocess(schedule, max_passes=5, enable_smoothing=True, smoothing_passes=20):
    """
    后处理均衡（两阶段）
    - 第一阶段：重载优先（压低峰值：先总时长，再本次时长）
    - 第二阶段：轻载平滑（在不抬升峰值前提下降低方差）

    Returns:
        dict: 优化报告，包含交换次数、前后最大总时长/本次时长、交换记录
    """
    progress_cb = schedule.get_constraint("progress_callback", None)
    log_swaps = bool(schedule.get_constraint("log_optimization_swaps", False))

    def variance(values):
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)

    def current_minutes(teacher):
        return teacher.supervision_duration or 0

    def overall_minutes(teacher):
        return (teacher.supervision_duration or 0) + (teacher.previous_supervision_duration or 0)

    def snapshot_metrics():
        cur = [current_minutes(teacher) for teacher in schedule.teachers]
        overall = [overall_minutes(teacher) for teacher in schedule.teachers]
        return {
            "max_current": max(cur) if cur else 0,
            "max_overall": max(overall) if overall else 0,
            "var_current": variance(cur),
            "var_overall": variance(overall),
        }

    report = {
        "swaps": [],
        "before": snapshot_metrics(),
    }
    total_steps = max_passes + (smoothing_passes if enable_smoothing else 0)
    if callable(progress_cb):
        try:
            progress_cb(f"计划轮次 {total_steps}", 0)
        except Exception:
            pass

    try:
        if log_swaps:
            logger.info(
                f"[二次均衡] 初始指标：最大总时长={report['before']['max_overall']}, "
                f"最大本次时长={report['before']['max_current']}, "
                f"总时长方差={report['before']['var_overall']:.4f}, "
                f"本次时长方差={report['before']['var_current']:.4f}"
            )
    except Exception:
        pass

    patience = int(schedule.get_constraint("early_stop_patience", 5))
    no_improve_count = 0
    last_swap_sig = None
    pass_idx = 0
    for _ in range(max_passes):
        pass_idx += 1
        teachers_desc = sorted(schedule.teachers, key=overall_minutes, reverse=True)
        teachers_asc = sorted(schedule.teachers, key=overall_minutes)
        before = snapshot_metrics()
        variance_weight = float(schedule.get_constraint("variance_weight", 1.5))
        if callable(progress_cb):
            try:
                progress = (
                    int(100 * (pass_idx - 1) / max_passes)
                    if total_steps == max_passes
                    else int(100 * (pass_idx - 1) / total_steps)
                )
                progress_cb("均衡优化中：", progress)
            except Exception:
                pass

        candidates = []
        for heavy in teachers_desc:
            heavy_overall = overall_minutes(heavy)
            heavy_current = current_minutes(heavy)
            if not heavy.assigned_sessions:
                continue
            for (sub1, room1) in list(heavy.assigned_sessions):
                idx1 = schedule._find_teacher_index(sub1, room1, heavy)
                if idx1 is None:
                    continue
                if schedule.get_constraint("lock_imported") and schedule.is_position_imported(sub1, room1, idx1):
                    continue
                d1 = schedule._get_subject_duration(sub1)

                for light in teachers_asc:
                    if light is heavy:
                        continue
                    if not light.assigned_sessions:
                        continue
                    light_overall = overall_minutes(light)
                    if light_overall >= heavy_overall:
                        continue
                    for (sub2, room2) in list(light.assigned_sessions):
                        idx2 = schedule._find_teacher_index(sub2, room2, light)
                        if idx2 is None:
                            continue
                        if schedule.get_constraint("lock_imported") and schedule.is_position_imported(
                            sub2, room2, idx2
                        ):
                            continue
                        d2 = schedule._get_subject_duration(sub2)
                        if d2 >= d1:
                            continue

                        heavy_overall_after = heavy_overall - d1 + d2
                        light_overall_after = light_overall - d2 + d1
                        others_overall = [
                            overall_minutes(teacher)
                            for teacher in schedule.teachers
                            if teacher not in (heavy, light)
                        ]
                        after_max_overall = (
                            max([heavy_overall_after, light_overall_after] + others_overall)
                            if others_overall
                            else max(heavy_overall_after, light_overall_after)
                        )

                        heavy_current_after = heavy_current - d1 + d2
                        light_current = current_minutes(light)
                        light_current_after = light_current - d2 + d1
                        others_current = [
                            current_minutes(teacher)
                            for teacher in schedule.teachers
                            if teacher not in (heavy, light)
                        ]
                        after_max_current = (
                            max([heavy_current_after, light_current_after] + others_current)
                            if others_current
                            else max(heavy_current_after, light_current_after)
                        )

                        if after_max_current > before["max_current"]:
                            continue
                        if not (
                            after_max_overall < before["max_overall"]
                            or (
                                after_max_overall == before["max_overall"]
                                and after_max_current <= before["max_current"]
                            )
                        ):
                            continue

                        cur_after = [heavy_current_after, light_current_after] + [
                            current_minutes(teacher)
                            for teacher in schedule.teachers
                            if teacher not in (heavy, light)
                        ]
                        overall_after = [heavy_overall_after, light_overall_after] + [
                            overall_minutes(teacher)
                            for teacher in schedule.teachers
                            if teacher not in (heavy, light)
                        ]
                        var_cur_after = variance(cur_after)
                        var_overall_after = variance(overall_after)
                        var_score = var_overall_after + variance_weight * var_cur_after

                        candidates.append(
                            {
                                "score": (after_max_overall, after_max_current, var_score),
                                "swap": ((sub1, room1, idx1), (sub2, room2, idx2)),
                                "from": {"subject": sub1, "room": room1, "duration": d1},
                                "to": {"subject": sub2, "room": room2, "duration": d2},
                                "heavy": heavy.name,
                                "light": light.name,
                            }
                        )

        if not candidates:
            if callable(progress_cb):
                try:
                    progress = int(100 * (max_passes if total_steps == max_passes else pass_idx) / total_steps)
                    progress_cb(f"第 {pass_idx} 轮：无可行候选，提前结束", progress)
                except Exception:
                    pass
            break

        candidates.sort(key=lambda candidate: candidate["score"])
        applied = False
        for candidate in candidates:
            try:
                if last_swap_sig and set(candidate["swap"]) == set(last_swap_sig):
                    continue
            except Exception:
                pass
            session1, session2 = candidate["swap"]
            ok, _msg = schedule.swap_teachers(session1, session2)
            if ok:
                post = snapshot_metrics()
                improved_strict = (post["max_overall"] < before["max_overall"]) or (
                    post["max_overall"] == before["max_overall"]
                    and post["max_current"] < before["max_current"]
                )
                epsilon = float(schedule.get_constraint("variance_improve_epsilon", 0.5))
                improved_variance = (post["var_overall"] < before["var_overall"] - epsilon) or (
                    post["var_current"] < before["var_current"] - epsilon
                )
                improved = improved_strict or improved_variance
                try:
                    if log_swaps:
                        logger.info(
                            f"[二次均衡] 交换{len(report['swaps']) + 1}：最大总时长={post['max_overall']}, "
                            f"最大本次时长={post['max_current']}, "
                            f"总时长方差={post['var_overall']:.4f}, "
                            f"本次时长方差={post['var_current']:.4f}; "
                            f"重载教师={candidate['heavy']} 的科目{candidate['from']['subject']}考场"
                            f"{candidate['from']['room']}({candidate['from']['duration']}分钟) -> "
                            f"轻载教师={candidate['light']} 的科目{candidate['to']['subject']}考场"
                            f"{candidate['to']['room']}({candidate['to']['duration']}分钟)"
                        )
                except Exception:
                    pass
                report["swaps"].append(
                    {
                        "index": len(report["swaps"]) + 1,
                        "heavy": candidate["heavy"],
                        "light": candidate["light"],
                        "from": candidate["from"],
                        "to": candidate["to"],
                        "note": "steepest: 优先 max_overall；其次 max_current；再次 variance（不抬升本次峰值）",
                        "max_overall": post["max_overall"],
                        "max_current": post["max_current"],
                        "var_overall": post["var_overall"],
                        "var_current": post["var_current"],
                        "improved": improved,
                    }
                )
                if improved:
                    no_improve_count = 0
                else:
                    no_improve_count += 1
                last_swap_sig = (session1, session2)
                applied = True
                break
        if not applied:
            if callable(progress_cb):
                try:
                    progress = int(100 * (max_passes if total_steps == max_passes else pass_idx) / total_steps)
                    progress_cb(f"第 {pass_idx} 轮：未应用交换，提前结束", progress)
                except Exception:
                    pass
            break
        if no_improve_count >= patience:
            reason = (
                f"连续{no_improve_count}次交换未降低最大总时长或最大本次时长，"
                "且方差也未改善（判定为当前算法均衡瓶颈）"
            )
            previous = report.get("early_stop_reason")
            report["early_stop_reason"] = f"{previous}; {reason}" if previous else reason
            try:
                if log_swaps:
                    logger.info(f"[二次均衡] 提前结束：{reason}")
            except Exception:
                pass
            break

    if enable_smoothing and smoothing_passes > 0:
        variance_weight = float(schedule.get_constraint("variance_weight", 1.5))
        epsilon = float(schedule.get_constraint("variance_improve_epsilon", 0.5))
        smooth_patience = int(schedule.get_constraint("smoothing_patience", 5))
        no_var_improve_count = 0
        try:
            if log_swaps:
                logger.info(f"[方差平滑] 阶段开始：预计轮次={smoothing_passes}，遵循不抬升峰值约束")
        except Exception:
            pass
        for smoothing_index in range(smoothing_passes):
            if callable(progress_cb):
                try:
                    progress_cb("均衡优化中：", int(100 * (max_passes + smoothing_index) / total_steps))
                except Exception:
                    pass
            baseline = snapshot_metrics()
            base_score = baseline["var_overall"] + variance_weight * baseline["var_current"]

            candidates = []
            teachers_asc = sorted(schedule.teachers, key=overall_minutes)
            for light in teachers_asc:
                if not light.assigned_sessions:
                    continue
                light_overall = overall_minutes(light)
                light_current = current_minutes(light)
                for (sub2, room2) in list(light.assigned_sessions):
                    idx2 = schedule._find_teacher_index(sub2, room2, light)
                    if idx2 is None:
                        continue
                    if schedule.get_constraint("lock_imported") and schedule.is_position_imported(sub2, room2, idx2):
                        continue
                    d2 = schedule._get_subject_duration(sub2)

                    for mid in schedule.teachers:
                        if mid is light:
                            continue
                        if not mid.assigned_sessions:
                            continue
                        mid_overall = overall_minutes(mid)
                        if mid_overall <= light_overall:
                            continue
                        mid_current = current_minutes(mid)
                        for (sub1, room1) in list(mid.assigned_sessions):
                            idx1 = schedule._find_teacher_index(sub1, room1, mid)
                            if idx1 is None:
                                continue
                            if schedule.get_constraint("lock_imported") and schedule.is_position_imported(
                                sub1, room1, idx1
                            ):
                                continue
                            d1 = schedule._get_subject_duration(sub1)
                            if d1 <= d2:
                                continue

                            mid_overall_after = mid_overall - d1 + d2
                            light_overall_after = light_overall - d2 + d1
                            mid_current_after = mid_current - d1 + d2
                            light_current_after = light_current - d2 + d1
                            others_overall = [
                                overall_minutes(teacher)
                                for teacher in schedule.teachers
                                if teacher not in (mid, light)
                            ]
                            after_max_overall = (
                                max([mid_overall_after, light_overall_after] + others_overall)
                                if others_overall
                                else max(mid_overall_after, light_overall_after)
                            )
                            others_current = [
                                current_minutes(teacher)
                                for teacher in schedule.teachers
                                if teacher not in (mid, light)
                            ]
                            after_max_current = (
                                max([mid_current_after, light_current_after] + others_current)
                                if others_current
                                else max(mid_current_after, light_current_after)
                            )

                            if after_max_overall > baseline["max_overall"]:
                                continue
                            if after_max_current > baseline["max_current"]:
                                continue

                            cur_after = [mid_current_after, light_current_after] + [
                                current_minutes(teacher)
                                for teacher in schedule.teachers
                                if teacher not in (mid, light)
                            ]
                            overall_after = [mid_overall_after, light_overall_after] + [
                                overall_minutes(teacher)
                                for teacher in schedule.teachers
                                if teacher not in (mid, light)
                            ]
                            var_cur_after = variance(cur_after)
                            var_overall_after = variance(overall_after)
                            var_score = var_overall_after + variance_weight * var_cur_after
                            if var_score >= base_score - epsilon:
                                continue

                            candidates.append(
                                {
                                    "score": var_score,
                                    "swap": ((sub1, room1, idx1), (sub2, room2, idx2)),
                                    "from": {"subject": sub1, "room": room1, "duration": d1},
                                    "to": {"subject": sub2, "room": room2, "duration": d2},
                                    "heavy": mid.name,
                                    "light": light.name,
                                }
                            )

            if not candidates:
                reason = "轻载平滑阶段：无可行候选，提前结束"
                previous = report.get("early_stop_reason")
                report["early_stop_reason"] = f"{previous}; {reason}" if previous else reason
                try:
                    if log_swaps:
                        logger.info(f"[方差平滑] 提前结束：{reason}")
                except Exception:
                    pass
                break

            candidates.sort(key=lambda candidate: candidate["score"])
            applied = False
            for candidate in candidates:
                session1, session2 = candidate["swap"]
                ok, _msg = schedule.swap_teachers(session1, session2)
                if ok:
                    post = snapshot_metrics()
                    try:
                        if log_swaps:
                            logger.info(
                                f"[方差平滑] 交换{len(report['swaps']) + 1}：最大总时长={post['max_overall']}, "
                                f"最大本次时长={post['max_current']}, "
                                f"总时长方差={post['var_overall']:.4f}, "
                                f"本次时长方差={post['var_current']:.4f}; "
                                f"重载教师={candidate['heavy']} 的科目{candidate['from']['subject']}考场"
                                f"{candidate['from']['room']}({candidate['from']['duration']}分钟) -> "
                                f"轻载教师={candidate['light']} 的科目{candidate['to']['subject']}考场"
                                f"{candidate['to']['room']}({candidate['to']['duration']}分钟)"
                            )
                    except Exception:
                        pass
                    report["swaps"].append(
                        {
                            "index": len(report["swaps"]) + 1,
                            "heavy": candidate["heavy"],
                            "light": candidate["light"],
                            "from": candidate["from"],
                            "to": candidate["to"],
                            "note": "smoothing: 方差平滑（不抬升峰值）",
                            "max_overall": post["max_overall"],
                            "max_current": post["max_current"],
                            "var_overall": post["var_overall"],
                            "var_current": post["var_current"],
                            "improved": True,
                        }
                    )
                    applied = True
                    no_var_improve_count = 0
                    break
            if not applied:
                no_var_improve_count += 1
                if no_var_improve_count >= smooth_patience:
                    reason = f"轻载平滑阶段：连续{no_var_improve_count}次未找到方差改善，提前结束"
                    previous = report.get("early_stop_reason")
                    report["early_stop_reason"] = f"{previous}; {reason}" if previous else reason
                    try:
                        if log_swaps:
                            logger.info(f"[方差平滑] 提前结束：{reason}")
                    except Exception:
                        pass
                    break

    report["after"] = snapshot_metrics()
    if callable(progress_cb):
        try:
            progress_cb("优化完成", 100)
        except Exception:
            pass
    report["swap_count"] = len(report["swaps"])
    return report
