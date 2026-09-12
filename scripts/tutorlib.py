"""AI Tutor V5 文件协议。仅使用 Python 标准库，不读取旧版课程。"""

import contextlib
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

VERSION = "5"
SCHEMA_VERSION = 3
MODES = {"learn", "solve", "act", "review"}
ACTIVITIES = {"intake", "explain", "demonstrate", "practice", "check", "feedback",
              "plan", "execute", "reflect", "paused", "complete"}
STATUSES = {"introduced", "assisted", "provisional", "retained", "transferred", "mastered"}
RESULTS = {"reported", "revealed", "not_passed", "assisted", "provisional", "retained", "transferred"}
QUALIFIED = {"provisional", "retained", "transferred"}
SOURCE_TYPES = {"law_or_regulation", "official_standard", "official_filing", "official_guidance",
                "original_work", "original_data", "academic_research", "textbook",
                "professional_analysis", "news", "open_web", "user_material"}
SOURCE_USES = {"supporting", "contextual", "discovery_only", "conflicting"}
ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{0,79}\Z")
PROGRESS = "学习进度_progress.md"
BEGIN, END = "<!-- tutor:begin -->", "<!-- tutor:end -->"
SETTINGS_RELATIVE = Path(".config/ai-tutor-v5/settings.json")
DEFAULT_DATA_ROOT = "AI-Tutor-V5-学习记录"


class TutorError(ValueError):
    pass


class Nullable:
    def __init__(self, inner):
        self.inner = inner


class Mapping:
    def __init__(self, inner):
        self.inner = inner


def identifier(value):
    return isinstance(value, str) and bool(ID_PATTERN.fullmatch(value))


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def timestamp(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return "T" in value and parsed.tzinfo is not None and parsed.utcoffset() is not None
    except ValueError:
        return False


def parse_time(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def score(value):
    return type(value) is int and 0 <= value <= 2


def hint(value):
    return type(value) is int and 0 <= value <= 4


def check_shape(value, spec, path="state", errors=None):
    errors = [] if errors is None else errors
    if isinstance(spec, Nullable):
        if value is not None:
            check_shape(value, spec.inner, path, errors)
    elif isinstance(spec, Mapping):
        if not isinstance(value, dict):
            errors.append(f"{path}: 必须是对象")
        else:
            for key, item in value.items():
                if not identifier(key):
                    errors.append(f"{path}.{key}: 非法 ID")
                check_shape(item, spec.inner, f"{path}.{key}", errors)
    elif isinstance(spec, dict):
        if not isinstance(value, dict):
            errors.append(f"{path}: 必须是对象")
        else:
            for key in sorted(set(value) - set(spec)):
                errors.append(f"{path}.{key}: 不支持的字段；不会静默丢弃")
            for key, rule in spec.items():
                if key not in value:
                    errors.append(f"{path}.{key}: 缺少字段")
                else:
                    check_shape(value[key], rule, f"{path}.{key}", errors)
    elif isinstance(spec, list):
        if not isinstance(value, list):
            errors.append(f"{path}: 必须是数组")
        else:
            for index, item in enumerate(value):
                check_shape(item, spec[0], f"{path}[{index}]", errors)
    elif isinstance(spec, set):
        if not isinstance(value, str) or value not in spec:
            errors.append(f"{path}: 必须是 {', '.join(sorted(spec))} 之一")
    elif isinstance(spec, type):
        if type(value) is not spec:
            errors.append(f"{path}: 类型应为 {spec.__name__}")
    elif callable(spec):
        if not spec(value):
            errors.append(f"{path}: 不符合 {spec.__name__} 规则")
    return errors


STATE_SPEC = {
    "schema_version": int, "skill_version": str, "course_id": identifier,
    "created_at": timestamp, "updated_at": timestamp,
    "topic": {"title": nonempty, "slug": identifier, "scope": str},
    "goal": {"purpose": str, "observable_outcome": str, "success_criteria": [nonempty], "time_constraints": str},
    "mode": MODES, "activity": ACTIVITIES, "storage_mode": {"off", "progress", "full"},
    "storage_consent": {"source": {"none", "user"}, "progress_authorized_at": Nullable(timestamp), "full_authorized_at": Nullable(timestamp)},
    "current_unit": Nullable(identifier),
    "curriculum": [{"id": identifier, "title": nonempty, "outcome": nonempty}],
    "mastery": Mapping({"status": STATUSES, "evidence_ids": [identifier]}),
    "weak_points": [nonempty],
    "review_queue": [{"concept_id": identifier, "due_at": timestamp, "basis_id": identifier}],
    "task": Nullable({"description": nonempty, "success_criteria": [nonempty],
        "status": {"open", "planned", "in_progress", "reported_done", "verified", "blocked"},
        "plan": [nonempty], "actual_result": str, "source": {"none", "user_report", "observed", "artifact_verified"}, "verification": str}),
    "checkpoint": {"resume_activity": ACTIVITIES - {"paused"}, "task_prompt": str,
        "response_so_far": str, "response_status": {"none", "partial", "complete"},
        "pending_question": str, "hint_level": hint, "scaffold_level": {"L0", "L1", "L2", "L3"}, "next_action": str},
    "insight_capture": {"enabled": bool, "authorized_at": Nullable(timestamp)},
}

ASSESSMENT_SPEC = {
    "id": identifier, "course_id": identifier, "concept_id": identifier, "occurred_at": timestamp,
    "kind": {"immediate", "retention", "transfer"}, "task": nonempty, "answer_excerpt": str,
    "evidence_source": {"observed_response", "user_report", "artifact_verified"}, "source_ref": str,
    "scores": {"accuracy": score, "reasoning": score, "transfer": score, "independence": score},
    "hint_level": hint, "scaffold_level": {"L0", "L1", "L2", "L3"},
    "answer_revealed": bool, "critical_error": bool, "aligned": bool, "success_criteria_met": bool,
    "new_context": Nullable(nonempty), "prior_assessment_id": Nullable(identifier),
    "feedback": nonempty, "result": RESULTS,
}

INSIGHT_SPEC = {
    "id": identifier, "course_id": identifier, "occurred_at": timestamp,
    "kind": {"fact", "self_report", "hypothesis", "preference", "learning_evidence"},
    "summary": nonempty, "source": {"kind": {"user", "assistant", "document", "observation"},
        "reference": nonempty, "time": timestamp}, "conditions": str, "uncertainty": str,
    "evidence_refs": [identifier],
}

SOURCE_SPEC = {
    "id": identifier, "course_id": identifier, "title": nonempty,
    "author_or_institution": nonempty, "source_type": SOURCE_TYPES,
    "publication_or_version": str, "effective_or_data_period": str,
    "retrieved_at": timestamp, "location": nonempty, "relevant_section": str,
    "used_for": [identifier], "use_status": SOURCE_USES, "supports": nonempty,
    "authority_basis": nonempty, "limitations": str,
    "supersedes": Nullable(identifier),
}


def fail(errors):
    if errors:
        raise TutorError("\n".join(errors))


def validate_state(state, records=None):
    errors = check_shape(state, STATE_SPEC)
    if errors:
        return errors
    if state["schema_version"] != SCHEMA_VERSION or state["skill_version"] != VERSION:
        errors.append("state: 仅接受 V5 / schema 3；不读取或迁移旧课程内容，请另建课程")
    if parse_time(state["updated_at"]) < parse_time(state["created_at"]):
        errors.append("state.updated_at: 不能早于 created_at")
    consent = state["storage_consent"]
    if state["storage_mode"] != "off" and (consent["source"] != "user" or not consent["progress_authorized_at"]):
        errors.append("state.storage_consent: progress/full 需要明确保存授权")
    if state["storage_mode"] == "full" and not consent["full_authorized_at"]:
        errors.append("state.storage_consent.full_authorized_at: 完整档案需要单独授权")
    if state["insight_capture"]["enabled"] and not state["insight_capture"]["authorized_at"]:
        errors.append("state.insight_capture.authorized_at: 洞见库需要单独授权")
    ids = [unit["id"] for unit in state["curriculum"]]
    if len(ids) != len(set(ids)):
        errors.append("state.curriculum: 单元 ID 重复")
    if state["current_unit"] is not None and state["current_unit"] not in ids:
        errors.append("state.current_unit: 必须引用 curriculum 中的单元")
    point = state["checkpoint"]
    if state["activity"] != "paused" and point["resume_activity"] != state["activity"]:
        errors.append("state.checkpoint.resume_activity: 非暂停时必须等于 activity")
    if point["resume_activity"] == "check":
        if not point["task_prompt"].strip():
            errors.append("state.checkpoint.task_prompt: 检测恢复点必须保存完整题目")
        elif len(point["task_prompt"]) < 10:
            errors.append("state.checkpoint.task_prompt: 检测题目过短，可能缺少关键标准或完整题面")
    if point["response_status"] in {"partial", "complete"} and not point["response_so_far"].strip():
        errors.append("state.checkpoint.response_so_far: 缺少实际作答")
    if state["activity"] == "paused" and not point["next_action"].strip():
        errors.append("state.checkpoint.next_action: 暂停时必须有具体恢复动作")
    task = state["task"]
    if task and task["status"] in {"reported_done", "verified"}:
        if not task["actual_result"].strip() or task["source"] == "none":
            errors.append("state.task: 完成状态需要实际结果和来源")
        if task["status"] == "verified" and (task["source"] not in {"observed", "artifact_verified"} or not task["verification"].strip() or not task["success_criteria"]):
            errors.append("state.task.verified: 需要已核验来源、成功标准和核验依据；用户自述不够")
    if records is not None:
        record_errors = validate_assessments(records, state["course_id"])
        errors.extend(record_errors)
        if not record_errors:
            if state["mastery"] != derive_mastery(records):
                errors.append("state.mastery: 与评估日志不一致；核对日志后运行 sync 重建派生掌握状态")
            indexed = {record["id"]: record for record in records}
            for index, review in enumerate(state["review_queue"]):
                basis = indexed.get(review["basis_id"])
                if not basis or basis["concept_id"] != review["concept_id"] or basis["result"] not in QUALIFIED:
                    errors.append(f"state.review_queue[{index}].basis_id: 缺少同概念有效独立评估")
    return errors


def simple_similarity(text1, text2):
    """简单启发式检查：两个任务是否只有数字不同"""
    import re
    # 提取所有数字
    nums1 = re.findall(r'\d+\.?\d*', text1)
    nums2 = re.findall(r'\d+\.?\d*', text2)
    # 移除所有数字后比较
    stripped1 = re.sub(r'\d+\.?\d*', '', text1.lower().strip())
    stripped2 = re.sub(r'\d+\.?\d*', '', text2.lower().strip())
    if not stripped1 or not stripped2 or len(stripped1) < 15:
        return False  # 文本太短，不适用此检查
    # 如果去数字后完全相同，原文不同，且至少有 2 个数字变化
    if stripped1 == stripped2 and text1.strip() != text2.strip():
        # 要求至少有 2 个数字，且数字确实不同
        return len(nums1) >= 2 and len(nums2) >= 2 and nums1 != nums2
    return False


def assessment_result(record, previous):
    if record["answer_revealed"] or record["hint_level"] == 4:
        return "revealed"
    if record["evidence_source"] == "user_report":
        return "reported"
    scores = record["scores"]
    passing = (sum(scores.values()) >= 6 and scores["accuracy"] == 2
               and not record["critical_error"] and record["aligned"] and record["success_criteria_met"])
    if not passing:
        return "not_passed"
    if record["hint_level"] > 0 or record["scaffold_level"] != "L0" or scores["independence"] < 2:
        return "assisted"
    if record["kind"] == "immediate":
        return "provisional"
    prior = next((item for item in previous if item["id"] == record["prior_assessment_id"]), None)
    if not prior or prior["concept_id"] != record["concept_id"] or prior["result"] not in QUALIFIED:
        raise TutorError("prior_assessment_id: 需要此前同概念的独立通过证据")
    prior_index = previous.index(prior)
    if any(item["concept_id"] == record["concept_id"] and item["result"] == "not_passed" for item in previous[prior_index + 1:]):
        raise TutorError("prior_assessment_id: 不能引用最近一次未通过之前的证据来升级")
    if record["kind"] == "retention":
        if parse_time(record["occurred_at"]) - parse_time(prior["occurred_at"]) < dt.timedelta(hours=24):
            raise TutorError("occurred_at: 保持证据须有至少 24 小时真实间隔")
        if record["task"].strip() == prior["task"].strip():
            raise TutorError("task: 保持检测需要等价新题，不能重复原题")
        if simple_similarity(record["task"], prior["task"]):
            raise TutorError("task: 保持检测疑似仅换数字，未改变题目结构；需改变表达、条件、求解方向或情境之一")
        return "retained"
    if not record["new_context"] or scores["transfer"] != 2:
        raise TutorError("new_context: 迁移需要明确新场景差异，且迁移评分为 2")
    if record["task"].strip() == prior["task"].strip():
        raise TutorError("task: 迁移不能重复此前原题")
    return "transferred"


def validate_assessments(records, course_id):
    errors, previous, seen = [], [], set()
    for index, record in enumerate(records):
        path = f"assessments[{index}]"
        shape = check_shape(record, ASSESSMENT_SPEC, path)
        errors.extend(shape)
        if shape:
            continue
        if record["id"] in seen:
            errors.append(f"{path}.id: 重复 ID")
        seen.add(record["id"])
        if record["course_id"] != course_id:
            errors.append(f"{path}.course_id: 不属于当前课程")
        if parse_time(record["occurred_at"]) > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=2):
            errors.append(f"{path}.occurred_at: 不能提前记录尚未发生的评估")
        if previous and parse_time(record["occurred_at"]) < parse_time(previous[-1]["occurred_at"]):
            errors.append(f"{path}.occurred_at: 日志必须按真实发生时间顺序追加")
        if record["evidence_source"] != "user_report" and not record["answer_excerpt"].strip():
            errors.append(f"{path}.answer_excerpt: 缺少可评估的实际作答或产出片段")
        if record["evidence_source"] == "artifact_verified" and not record["source_ref"].strip():
            errors.append(f"{path}.source_ref: 核验产出需要来源引用")
        if (record["hint_level"] > 0 or record["scaffold_level"] != "L0") and record["scores"]["independence"] == 2:
            errors.append(f"{path}.scores.independence: 有支持不能记为完全独立")
        if (record["answer_revealed"] or record["hint_level"] == 4) and record["scores"]["independence"] != 0:
            errors.append(f"{path}.scores.independence: 看过答案时独立性应为 0")
        try:
            expected = assessment_result(record, previous)
            if record["result"] != expected:
                errors.append(f"{path}.result: 应为 {expected}，不能写成 {record['result']}")
        except TutorError as exc:
            errors.append(f"{path}.{exc}")
        previous.append(record)
    return errors


def derive_mastery(records):
    result, successes = {}, {}
    for record in records:
        outcome, concept = record["result"], record["concept_id"]
        if outcome in {"reported", "revealed"}:
            continue
        item = result.setdefault(concept, {"status": "introduced", "evidence_ids": []})
        if outcome == "not_passed":
            item.update(status="introduced", evidence_ids=[record["id"]])
            successes[concept] = set()
            continue
        item["evidence_ids"].append(record["id"])
        if outcome == "assisted":
            if item["status"] == "introduced":
                item["status"] = "assisted"
            continue
        flags = successes.setdefault(concept, set())
        flags.add(outcome)
        if {"retained", "transferred"} <= flags:
            item["status"] = "mastered"
        elif "retained" in flags:
            item["status"] = "retained"
        elif "transferred" in flags:
            item["status"] = "transferred"
        else:
            item["status"] = "provisional"
    return result


def validate_insights(records, course_id, assessments):
    errors, seen = [], set()
    evidence_ids = {record["id"] for record in assessments}
    for index, record in enumerate(records):
        path = f"insights[{index}]"
        shape = check_shape(record, INSIGHT_SPEC, path)
        errors.extend(shape)
        if shape:
            continue
        if record["course_id"] != course_id:
            errors.append(f"{path}.course_id: 不属于当前课程")
        if record["id"] in seen:
            errors.append(f"{path}.id: 重复 ID")
        seen.add(record["id"])
        if record["kind"] == "fact" and record["source"]["kind"] in {"user", "assistant"}:
            errors.append(f"{path}.kind: 自述或判断不能直接标为 fact，需观察或文档核验来源")
        if record["kind"] == "learning_evidence" and not record["evidence_refs"]:
            errors.append(f"{path}.evidence_refs: 学习证据必须引用真实评估")
        if any(item not in evidence_ids for item in record["evidence_refs"]):
            errors.append(f"{path}.evidence_refs: 评估引用不存在")
    return errors


def validate_sources(records, course_id):
    errors, seen, previous = [], set(), []
    for index, record in enumerate(records):
        path = f"sources[{index}]"
        shape = check_shape(record, SOURCE_SPEC, path)
        errors.extend(shape)
        if shape:
            continue
        if record["course_id"] != course_id:
            errors.append(f"{path}.course_id: 不属于当前课程")
        if record["id"] in seen:
            errors.append(f"{path}.id: 重复 ID")
        if parse_time(record["retrieved_at"]) > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=2):
            errors.append(f"{path}.retrieved_at: 不能提前记录尚未取得的资料")
        if previous and parse_time(record["retrieved_at"]) < parse_time(previous[-1]["retrieved_at"]):
            errors.append(f"{path}.retrieved_at: 日志必须按真实获取时间顺序追加")
        if record["supersedes"] is not None and record["supersedes"] not in seen:
            errors.append(f"{path}.supersedes: 必须引用当前日志中更早的来源记录")
        seen.add(record["id"])
        previous.append(record)
    return errors


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise TutorError(f"JSON 字段重复：{key}")
        value[key] = item
    return value


def decode(text, label):
    try:
        return json.loads(text, object_pairs_hook=unique_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(TutorError(f"非法 JSON 常量：{value}")))
    except (ValueError, TypeError) as exc:
        raise TutorError(f"{label}: {exc}") from exc


def read_json(path):
    return decode(Path(path).read_text(encoding="utf-8"), str(path))


def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def safe_path(root, name):
    root = Path(root).absolute()
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise TutorError("文件名必须是课程内相对路径")
    if root.is_symlink():
        raise TutorError(f"课程目录不能是软链接：{root}")
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise TutorError(f"拒绝通过软链接读取或写入课程数据：{cursor}")
    return cursor


def read_log(root, name):
    path = safe_path(root, name)
    if not path.exists():
        return []
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            records.append(decode(line, f"{name}:{number}"))
    return records


def log_text(records):
    return "".join(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n" for record in records)


def load_course(root, cross_check=True):
    state = read_json(safe_path(root, "state.json"))
    if not isinstance(state, dict) or state.get("schema_version") != SCHEMA_VERSION or state.get("skill_version") != VERSION:
        raise TutorError("不是 V5 / schema 3 课程；停止读取其余内容，不迁移、不覆盖，请另建课程")
    fail(validate_state(state))
    records = read_log(root, "assessments.jsonl")
    fail(validate_assessments(records, state["course_id"]))
    sources = read_log(root, "sources.jsonl")
    fail(validate_sources(sources, state["course_id"]))
    if cross_check:
        fail(validate_state(state, records))
    return state, records


def require_storage(state, full=False, insights=False):
    if state["storage_mode"] == "off":
        raise TutorError("storage_mode=off：未写入任何课程文件")
    if full and state["storage_mode"] != "full":
        raise TutorError("完整记录或课件需要 full 明确授权")
    if insights and not state["insight_capture"]["enabled"]:
        raise TutorError("洞见库尚未单独授权")


@contextlib.contextmanager
def course_lock(root):
    path = safe_path(root, ".tutor-write.lock")
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        # 检查锁是否过期（进程不存在）
        stale = False
        try:
            content = path.read_text(encoding="utf-8").strip()
            if content.isdigit():
                pid = int(content)
                try:
                    os.kill(pid, 0)  # 检查进程是否存在
                except OSError:
                    stale = True
        except (OSError, ValueError, UnicodeError):
            pass
        if stale:
            try:
                path.unlink()
                descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except (OSError, FileExistsError):
                raise TutorError("课程正被写入；请稍后重试。异常遗留锁须确认没有写入进程后再移走") from exc
        else:
            raise TutorError("课程正被写入；请稍后重试。异常遗留锁须确认没有写入进程后再移走") from exc
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        path.unlink(missing_ok=True)


def atomic_write(path, content):
    path = Path(path)
    if path.is_symlink():
        raise TutorError(f"拒绝写入软链接：{path}")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        if path.read_text(encoding="utf-8") != content:
            raise TutorError(f"文件回读不一致：{path}")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def data_root_settings_path(home=None):
    base = Path.home() if home is None else Path(home)
    return base.expanduser().absolute() / SETTINGS_RELATIVE


def normalize_data_root(value):
    if not nonempty(value):
        raise TutorError("data_root: 必须是非空路径")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise TutorError("data_root: 必须是绝对路径或以 ~ 开头，不能依赖当前工作目录的 ./data")
    path = path.absolute()
    skill_root = Path(__file__).resolve().parents[1]
    if path == skill_root or skill_root in path.parents:
        raise TutorError("data_root: 学习数据不能放进技能安装目录")
    return path


def resolve_data_root(override=None, home=None, settings_path=None):
    home_path = (Path.home() if home is None else Path(home)).expanduser().absolute()
    config = data_root_settings_path(home_path) if settings_path is None else Path(settings_path).expanduser().absolute()
    if override is not None:
        root, source = normalize_data_root(override), "override"
    elif config.exists() or config.is_symlink():
        if config.is_symlink() or not config.is_file():
            raise TutorError(f"数据根目录设置必须是普通 JSON 文件：{config}")
        settings = read_json(config)
        if not isinstance(settings, dict) or set(settings) != {"data_root"}:
            raise TutorError("数据根目录设置只接受 data_root 字段")
        root, source = normalize_data_root(settings["data_root"]), "config"
    else:
        root, source = normalize_data_root(str(home_path / "Documents" / DEFAULT_DATA_ROOT)), "default"
    return {"data_root": str(root), "source": source, "settings_path": str(config),
            "exists": root.is_dir() and not root.is_symlink()}


def configure_data_root(value, home=None, settings_path=None):
    root = normalize_data_root(value)
    config = data_root_settings_path(home) if settings_path is None else Path(settings_path).expanduser().absolute()
    if config.is_symlink():
        raise TutorError(f"拒绝覆盖软链接设置：{config}")
    config.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(config, encode({"data_root": str(root)}))
    result = resolve_data_root(home=home, settings_path=config)
    if result["data_root"] != str(root):
        raise TutorError("数据根目录设置回读不一致")
    return result


def discover_courses(data_root):
    root = normalize_data_root(str(data_root))
    if not root.exists():
        return {"data_root": str(root), "exists": False, "courses": [], "ignored": []}
    if root.is_symlink() or not root.is_dir():
        raise TutorError(f"数据根目录必须是普通目录：{root}")
    courses, ignored = [], []
    for folder in sorted(root.iterdir(), key=lambda item: item.name):
        if folder.name.startswith(".") or not folder.is_dir() or folder.is_symlink():
            continue
        state_path = folder / "state.json"
        if not state_path.is_file() or state_path.is_symlink():
            continue
        try:
            state = read_json(state_path)
            if not isinstance(state, dict) or state.get("schema_version") != SCHEMA_VERSION or state.get("skill_version") != VERSION:
                raise TutorError("不是 V5 / schema 3 课程")
            fail(validate_state(state))
            courses.append({"path": str(folder), "course_id": state["course_id"],
                            "title": state["topic"]["title"], "updated_at": state["updated_at"],
                            "mode": state["mode"], "activity": state["activity"]})
        except (OSError, UnicodeError, TutorError) as exc:
            ignored.append({"path": str(folder), "reason": str(exc)})
    courses.sort(key=lambda item: parse_time(item["updated_at"]), reverse=True)
    return {"data_root": str(root), "exists": True, "courses": courses, "ignored": ignored}


def now_after(previous=None):
    current = dt.datetime.now(dt.timezone.utc)
    if previous:
        current = max(current, parse_time(previous) + dt.timedelta(microseconds=1))
    return current.isoformat(timespec="microseconds").replace("+00:00", "Z")


def progress_text(state, old=""):
    point = state["checkpoint"]
    names = {"learn": "学习", "solve": "解决问题", "act": "行动", "review": "复习"}
    lines = [BEGIN, f"# {state['topic']['title']} · 学习进度", "",
             f"更新：{state['updated_at']}", f"模式：{names[state['mode']]}｜活动：{state['activity']}",
             f"目标：{state['goal']['observable_outcome'] or '待明确'}", "", "## 当前恢复点", "",
             f"任务：{point['task_prompt'] or '尚未进入具体任务'}",
             f"已答部分：{point['response_so_far'] or '无'}", f"待答部分：{point['pending_question'] or '无'}",
             f"支持：提示 {point['hint_level']}；支架 {point['scaffold_level']}",
             f"下一步：{point['next_action'] or '按用户当前请求继续'}", "", "## 能力证据", ""]
    lines.extend(f"- {key}：{value['status']}；依据：{', '.join(value['evidence_ids'])}" for key, value in state["mastery"].items())
    if not state["mastery"]:
        lines.append("尚无可据以升级的评估证据。")
    if state["weak_points"]:
        lines.extend(["", "## 当前缺口", ""] + [f"- {value}" for value in state["weak_points"]])
    task = state["task"]
    if task:
        lines.extend(["", "## 当前实际任务", "", task["description"], f"状态：{task['status']}",
                      f"实际结果：{task['actual_result'] or '尚无'}", f"来源：{task['source']}"])
    lines += ["", "本区由 state.json 和评估日志生成；个人补充写在自动区外。", END]
    block = "\n".join(lines)
    if not old:
        return block + "\n\n## 个人补充\n\n"
    if old.count(BEGIN) != 1 or old.count(END) != 1 or old.index(BEGIN) >= old.index(END):
        raise TutorError("学习进度文件缺少唯一自动区边界；保留原文件，人工核对后再更新")
    return old[:old.index(BEGIN)] + block + old[old.index(END) + len(END):]


def commit(root, state, records, logs=None):
    state = copy.deepcopy(state)
    state["updated_at"] = now_after(state["updated_at"])
    state["mastery"] = derive_mastery(records)
    fail(validate_state(state, records))
    state_path = safe_path(root, "state.json")
    progress_path = safe_path(root, PROGRESS)
    progress = progress_text(state, progress_path.read_text(encoding="utf-8") if progress_path.exists() else "")
    outputs = [(safe_path(root, name), log_text(items)) for name, items in (logs or {}).items()]
    outputs += [(state_path, encode(state)), (progress_path, progress)]
    written = []
    try:
        for path, content in outputs:
            atomic_write(path, content)
            written.append(path.name)
    except (OSError, TutorError) as exc:
        raise TutorError(f"保存未全部完成，已写入 {written}；原有日志不会截断。核对后运行 sync 恢复派生状态。原因：{exc}") from exc
    load_course(root)
    return state


def append_record(root, incoming, kind):
    if kind not in {"assessment", "insight", "source"}:
        raise TutorError("记录类型必须是 assessment、insight 或 source")
    state, _ = load_course(root, cross_check=False)
    require_storage(state, insights=kind == "insight")
    with course_lock(root):
        state, assessments = load_course(root, cross_check=False)
        require_storage(state, insights=kind == "insight")
        record = copy.deepcopy(incoming)
        names = {"assessment": "assessments.jsonl", "insight": "insights.jsonl", "source": "sources.jsonl"}
        name = names[kind]
        records = assessments if kind == "assessment" else read_log(root, name)
        if kind == "insight":
            fail(validate_insights(records, state["course_id"], assessments))
        if kind == "source":
            fail(validate_sources(records, state["course_id"]))
        if kind == "assessment" and isinstance(record, dict) and "result" not in record:
            candidate = dict(record, result="reported")
            fail(check_shape(candidate, ASSESSMENT_SPEC, "assessment"))
            record["result"] = assessment_result(candidate, assessments)
        specs = {"assessment": ASSESSMENT_SPEC, "insight": INSIGHT_SPEC, "source": SOURCE_SPEC}
        spec = specs[kind]
        fail(check_shape(record, spec, kind))
        duplicate = next((item for item in records if item["id"] == record["id"]), None)
        if duplicate:
            if duplicate != record:
                raise TutorError("重复 ID 对应不同内容；未覆盖原记录")
            return {"status": "unchanged", "id": record["id"], "note": "同一记录已存在；若上次写入中断，运行 sync 核对恢复"}
        proposed = records + [record]
        if kind == "assessment":
            fail(validate_assessments(proposed, state["course_id"]))
            assessments = proposed
        elif kind == "insight":
            fail(validate_insights(proposed, state["course_id"], assessments))
        else:
            fail(validate_sources(proposed, state["course_id"]))
        saved = commit(root, state, assessments, {name: proposed})
        return {"status": "saved", "id": record["id"], "updated_at": saved["updated_at"]}


def save_state(root, proposed, expected_update, authorize_full=False, authorize_insights=False):
    fail(validate_state(proposed))
    require_storage(proposed)
    old, _ = load_course(root, cross_check=False)
    require_storage(old)
    with course_lock(root):
        old, records = load_course(root, cross_check=False)
        require_storage(old)
        if old["updated_at"] != expected_update:
            raise TutorError("updated_at 已改变；重新读取并合并，不得覆盖其他会话的更新")
        if proposed["updated_at"] != expected_update:
            raise TutorError("候选状态须保留读到的 updated_at；实际更新时间由保存工具生成")
        for field in ["course_id", "created_at"]:
            if proposed[field] != old[field]:
                raise TutorError(f"state.{field}: 不能变更当前课程身份")
        if proposed["topic"]["slug"] != old["topic"]["slug"]:
            raise TutorError("topic.slug: 稳定标识不能随中文标题或目录改名")
        if proposed["storage_mode"] == "full" and old["storage_mode"] != "full" and not authorize_full:
            raise TutorError("切换 full 需要确认已有用户明确授权，并传 --authorize-full")
        if proposed["insight_capture"]["enabled"] and not old["insight_capture"]["enabled"] and not authorize_insights:
            raise TutorError("启用洞见库需已有用户授权，并传 --authorize-insights")
        fail(validate_state(proposed, records))
        return commit(root, proposed, records)


def sync_course(root):
    state, _ = load_course(root, cross_check=False)
    require_storage(state)
    with course_lock(root):
        state, records = load_course(root, cross_check=False)
        require_storage(state)
        return commit(root, state, records)


def save_session(root, content, name, kind):
    if Path(name).name != name or not name.endswith(".md") or name.startswith("."):
        raise TutorError("记录文件名必须是单个可见 Markdown 文件名")
    state, _ = load_course(root)
    require_storage(state, full=kind in {"full", "unit"})
    folder = "学习资料_units" if kind == "unit" else "学习记录_sessions"
    with course_lock(root):
        state, _ = load_course(root)
        require_storage(state, full=kind in {"full", "unit"})
        path = safe_path(root, f"{folder}/{name}")
        if path.exists():
            raise TutorError("同名记录已存在；请核对后使用新的记录名，不覆盖原文")
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(path, content)
    return {"status": "saved", "path": str(path), "sha256": hashlib.sha256(content.encode()).hexdigest()}
