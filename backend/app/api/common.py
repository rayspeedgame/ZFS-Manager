from __future__ import annotations

from app.schemas.task import TaskCommandLog


def build_single_result_task_message(
    *,
    success: bool,
    success_text: str,
    failure_text: str,
    refresh_error: str | None,
) -> str:
    message = success_text if success else failure_text
    if refresh_error:
        return f"{message} State refresh warning: {refresh_error}"
    return message


def build_multi_result_task_message(
    *,
    success_count: int,
    total_count: int,
    refresh_error: str | None,
    noun: str,
) -> str:
    message = f"Applied {success_count}/{total_count} {noun}."
    if refresh_error:
        return f"{message} State refresh warning: {refresh_error}"
    return message


def task_log_from_single_result(*, label: str, result) -> TaskCommandLog:
    return TaskCommandLog(
        label=label,
        success=bool(getattr(result, "success", False)),
        message=str(getattr(result, "message", "")),
        command=getattr(result, "command", None),
        exit_status=getattr(result, "exit_status", None),
        stdout=getattr(result, "stdout", None),
        stderr=getattr(result, "stderr", None),
    )


def task_log_from_multi_result(label: str, result) -> TaskCommandLog:
    return TaskCommandLog(
        label=label,
        success=bool(getattr(result, "success", False)),
        message=str(getattr(result, "message", "")),
        command=getattr(result, "command", None),
        exit_status=getattr(result, "exit_status", None),
        stdout=getattr(result, "stdout", None),
        stderr=getattr(result, "stderr", None),
    )
