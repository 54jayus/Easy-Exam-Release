# Proctoring Stress Report

| Case | Expected | Observed | Time(s) | Notes |
| --- | --- | --- | ---: | --- |
| `case01_single_dense_default_rooms` | success | success | 13.046 | unassigned=0; solver=FEASIBLE |
| `case02_double_mixed_constraints` | success | success | 7.885 | unassigned=0; solver=FEASIBLE |
| `case03_variable_rooms_overlap` | success | success | 20.060 | unassigned=0; solver=FEASIBLE |
| `case04_capacity_shortfall` | error | error | 0.000 | 全局监考名额不足：需要 48 人次，只有 20 人次。 |
| `case05_pairing_impossible` | error | error | 0.000 | 科目1在‘性别+本外校’约束下，合法配对最多 2 对，不足以覆盖 10 个考场。 |
| `case06_dirty_teacher_import` | teacher_import_error | teacher_import_error | 0.000 | errors=5; warnings=1; 教师姓名存在重复，不允许导入：['Teacher-01']。建议在重复姓名后加数字1、2区分 / 教师 Teacher-03 的最大监考段数不是数字：abc / 教师 Teacher-04 的不监考科目中存在无法识别的项: ['UnknownSubject']。请使用[1..4]的编号或已导入的科目名称 / 教师 Teacher-04 的不监考科目中存在越界编号: ['999']（有效范围1..4） / 教师 Teacher-04 的历次监考时长不能为负数：-30 |
| `case07_locked_conflict_continue` | error | error | 0.012 | 导入的锁定安排存在冲突：Teacher-01 同时被锁定在 科目01 和 科目02，两场考试时间重叠，无法同时监考。 |
| `case08_feasible_continue_partial_preset` | success | success | 4.008 | unassigned=0; solver=FEASIBLE |
| `case09_double_gender_only` | success | success | 0.191 | unassigned=0; solver=OPTIMAL |
| `case10_double_internal_only` | success | success | 0.164 | unassigned=0; solver=OPTIMAL |
| `case11_room_repeat_fixed` | success | success | 0.291 | unassigned=0; solver=OPTIMAL |
| `case12_room_repeat_different` | success | success | 1.325 | unassigned=0; solver=OPTIMAL |
| `case13_invalid_preset_warning_success` | success | success | 0.074 | warnings=2; unassigned=0; solver=OPTIMAL |
| `case14_import_schedule_complete` | success | success | 0.008 | unassigned=0; solver=None |
| `case15_swap_success` | success | success | 0.008 | unassigned=0; solver=None |
| `case16_swap_blocked_by_preset` | error | error | 0.008 | 教师 Teacher-01 预设房间为 1，不能交换到考场 2 |
