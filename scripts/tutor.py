#!/usr/bin/env python3
"""课程文件命令入口；授权标志只表达已有授权，不替代真实用户选择。"""

import argparse
import copy
import json
import os
from pathlib import Path
import sys
import uuid

from tutorlib import (TutorError, MODES, PROGRESS, append_record, atomic_write,
                      configure_data_root, discover_courses, encode, fail, load_course,
                      now_after, progress_text, read_json, read_log, resolve_data_root,
                      save_session, save_state, sync_course, validate_insights,
                      validate_sources, validate_state)


def init_course(args):
    template = Path(__file__).resolve().parents[1] / "assets/templates/state.json"
    state = copy.deepcopy(read_json(template))
    now = now_after()
    state.update(course_id=f"{args.slug[:60]}-{uuid.uuid4().hex[:8]}", created_at=now,
                 updated_at=now, mode=args.mode, storage_mode=args.storage)
    state["topic"].update(title=args.title, slug=args.slug)
    state["goal"]["observable_outcome"] = args.goal
    if args.storage != "off":
        if not args.authorize_progress:
            raise TutorError("须已有用户保存进度授权，并传 --authorize-progress；尚未建档")
        state["storage_consent"].update(source="user", progress_authorized_at=now)
    if args.storage == "full":
        if not args.authorize_full:
            raise TutorError("full 需要明确完整档案授权，并传 --authorize-full；尚未建档")
        state["storage_consent"]["full_authorized_at"] = now
    if args.authorize_insights:
        state["insight_capture"].update(enabled=True, authorized_at=now)
    fail(validate_state(state, []))
    if args.storage == "off":
        return {"status": "not_saved", "note": "仅返回会话内状态，没有创建文件", "state": state}
    root = Path(args.course).absolute()
    if root.exists() or root.is_symlink():
        raise TutorError("目标已存在；新课程必须使用独立新目录，不覆盖或迁移原课程")
    root.mkdir(parents=True)
    try:
        atomic_write(root / "state.json", encode(state))
        atomic_write(root / PROGRESS, progress_text(state))
        load_course(root)
    except (OSError, TutorError) as exc:
        raise TutorError(f"建档未全部完成，请检查 {root} 后恢复，不要反复覆盖。原因：{exc}") from exc
    return {"status": "created", "course": str(root), "course_id": state["course_id"], "updated_at": now}


def parser():
    root = argparse.ArgumentParser(description="AI Tutor V5：明确授权后管理当前版本的课程文件")
    commands = root.add_subparsers(dest="command", required=True)
    show_root = commands.add_parser("root", help="显示数据根目录；不创建目录")
    show_root.add_argument("--data-root")
    configure_root = commands.add_parser("configure-root", help="设置本机数据根目录；不创建课程")
    configure_root.add_argument("--data-root", required=True)
    courses = commands.add_parser("courses", help="列出数据根目录中的兼容 V5 课程")
    courses.add_argument("--data-root")
    init = commands.add_parser("init", help="在新目录建档；off 不创建文件")
    init.add_argument("course")
    init.add_argument("--title", required=True)
    init.add_argument("--slug", required=True)
    init.add_argument("--goal", default="")
    init.add_argument("--mode", choices=sorted(MODES), default="learn")
    init.add_argument("--storage", choices=["off", "progress", "full"], default="off")
    init.add_argument("--authorize-progress", action="store_true")
    init.add_argument("--authorize-full", action="store_true")
    init.add_argument("--authorize-insights", action="store_true")
    for name in ["validate", "sync"]:
        sub = commands.add_parser(name)
        sub.add_argument("course")
    save = commands.add_parser("save")
    save.add_argument("course")
    save.add_argument("--input", required=True)
    save.add_argument("--expected-update", required=True)
    save.add_argument("--authorize-full", action="store_true")
    save.add_argument("--authorize-insights", action="store_true")
    for name in ["assessment", "insight", "source"]:
        sub = commands.add_parser(name)
        sub.add_argument("course")
        sub.add_argument("--input", required=True)
    session = commands.add_parser("session")
    session.add_argument("course")
    session.add_argument("--input", required=True)
    session.add_argument("--name", required=True)
    session.add_argument("--kind", choices=["progress", "full", "unit"], default="progress")
    return root


def main():
    args = parser().parse_args()
    try:
        if args.command == "root":
            result = resolve_data_root(args.data_root)
        elif args.command == "configure-root":
            result = configure_data_root(args.data_root)
        elif args.command == "courses":
            resolved = resolve_data_root(args.data_root)
            result = dict(resolved, **discover_courses(resolved["data_root"]))
        elif args.command == "init":
            result = init_course(args)
        elif args.command == "validate":
            state, records = load_course(args.course)
            insights = read_log(args.course, "insights.jsonl")
            sources = read_log(args.course, "sources.jsonl")
            fail(validate_insights(insights, state["course_id"], records))
            fail(validate_sources(sources, state["course_id"]))
            result = {"status": "valid", "assessments": len(records), "sources": len(sources),
                      "insights": len(insights), "version": state["skill_version"]}
        elif args.command == "save":
            state = save_state(args.course, read_json(args.input), args.expected_update,
                               args.authorize_full, args.authorize_insights)
            result = {"status": "saved", "updated_at": state["updated_at"]}
        elif args.command in {"assessment", "insight", "source"}:
            result = append_record(args.course, read_json(args.input), args.command)
        elif args.command == "sync":
            state = sync_course(args.course)
            result = {"status": "synced", "updated_at": state["updated_at"]}
        else:
            result = save_session(args.course, Path(args.input).read_text(encoding="utf-8"), args.name, args.kind)
        print(encode(result), end="")
        return 0
    except (TutorError, OSError, UnicodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
