#!/usr/bin/env bash
# Easy Exam 运行时环境解析（macOS / Linux）
# 用法: source tools/runtime-env.sh

_get_project_root() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$script_dir/.." && pwd
}

# 读取 .env.runtime.local 或 .env.runtime.example 配置
_read_runtime_config() {
    local project_root="$1"
    local config_file=""

    if [[ -f "$project_root/.env.runtime.local" ]]; then
        config_file="$project_root/.env.runtime.local"
    elif [[ -f "$project_root/.env.runtime.example" ]]; then
        config_file="$project_root/.env.runtime.example"
    fi

    if [[ -z "$config_file" ]]; then
        return
    fi

    while IFS= read -r line; do
        # 跳过空行和注释
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        # 去掉行首尾空白
        line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [[ -z "$line" ]] && continue
        # 解析 key=value
        local key="${line%%=*}"
        local value="${line#*=}"
        key="$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        value="$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//;s/^["'\'']\(.*\)["'\'']/\1/')"
        [[ -n "$key" ]] && export "EXAM_CFG_${key}=${value}"
    done < "$config_file"
}

# 解析 Python 命令并输出到 stdout
# 用法: resolve_python_command [python_args...]
resolve_python_command() {
    local project_root
    project_root="$(_get_project_root)"

    # 清除旧的配置变量
    unset EXAM_CFG_EXAM_PYTHON_EXE EXAM_CFG_EXAM_PYTHON_MODE EXAM_CFG_EXAM_CONDA_ENV EXAM_CFG_EXAM_CONDA_EXE

    _read_runtime_config "$project_root"

    local explicit_python="${EXAM_CFG_EXAM_PYTHON_EXE:-}"
    if [[ -n "$explicit_python" ]]; then
        echo "$explicit_python $*"
        return
    fi

    local mode="${EXAM_CFG_EXAM_PYTHON_MODE:-}"
    local conda_env="${EXAM_CFG_EXAM_CONDA_ENV:-}"

    if [[ "$mode" == "conda" || -n "$conda_env" ]]; then
        if [[ -z "$conda_env" ]]; then
            echo "错误: 运行环境配置缺少 EXAM_CONDA_ENV" >&2
            exit 1
        fi
        local conda_exe="${EXAM_CFG_EXAM_CONDA_EXE:-conda}"
        [[ -z "$conda_exe" ]] && conda_exe="conda"
        echo "$conda_exe run --no-capture-output -n $conda_env python $*"
        return
    fi

    echo "python $*"
}

# 执行 Python 命令
# 用法: invoke_project_python [python_args...]
invoke_project_python() {
    local project_root
    project_root="$(_get_project_root)"

    unset EXAM_CFG_EXAM_PYTHON_EXE EXAM_CFG_EXAM_PYTHON_MODE EXAM_CFG_EXAM_CONDA_ENV EXAM_CFG_EXAM_CONDA_EXE
    _read_runtime_config "$project_root"

    local explicit_python="${EXAM_CFG_EXAM_PYTHON_EXE:-}"
    if [[ -n "$explicit_python" ]]; then
        echo "Using Python runtime: EXAM_PYTHON_EXE=$explicit_python" >&2
        exec "$explicit_python" "$@"
    fi

    local mode="${EXAM_CFG_EXAM_PYTHON_MODE:-}"
    local conda_env="${EXAM_CFG_EXAM_CONDA_ENV:-}"

    if [[ "$mode" == "conda" || -n "$conda_env" ]]; then
        if [[ -z "$conda_env" ]]; then
            echo "错误: 运行环境配置缺少 EXAM_CONDA_ENV" >&2
            exit 1
        fi
        local conda_exe="${EXAM_CFG_EXAM_CONDA_EXE:-conda}"
        [[ -z "$conda_exe" ]] && conda_exe="conda"
        echo "Using Python runtime: $conda_exe run -n $conda_env python" >&2
        exec "$conda_exe" run --no-capture-output -n "$conda_env" python "$@"
    fi

    echo "Using Python runtime: python" >&2
    exec python "$@"
}
