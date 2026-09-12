"""仅使用合成资料验证数据不变量与恢复，不读取用户课程。"""

import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import tutorlib as lib


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ai-tutor-v5-test-")
        self.base = Path(self.temporary.name)
        self.course = self.base / "测试课程"
        result = self.cli("init", self.course, "--title", "测试主题", "--slug", "test-topic", "--storage", "progress", "--authorize-progress")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.course_id = self.state()["course_id"]

    def tearDown(self):
        self.temporary.cleanup()

    def cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(ROOT / "scripts/tutor.py"), *map(str, args)], text=True, capture_output=True)

    def state(self):
        return lib.read_json(self.course / "state.json")

    def snapshot(self):
        return {str(path.relative_to(self.course)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.course.rglob("*") if path.is_file() and not path.is_symlink()}

    def event(self, event_id="a1", **changes):
        item = lib.read_json(ROOT / "assets/templates/assessment.json")
        item.update(id=event_id, course_id=self.course_id, concept_id="causality", occurred_at="2020-01-01T08:00:00Z",
                    task=f"合成题目 {event_id}：请给出判断与理由。", answer_excerpt="给出了正确判断、依据与必要边界。",
                    scores={"accuracy": 2, "reasoning": 2, "transfer": 0, "independence": 2},
                    aligned=True, success_criteria_met=True, feedback="依据实际作答通过当前检测。")
        item.pop("result")
        item.update(changes)
        return item

    def append(self, event=None):
        return lib.append_record(self.course, event or self.event(), "assessment")

    def authorize_insights(self):
        state = self.state()
        state["insight_capture"] = {"enabled": True, "authorized_at": state["updated_at"]}
        lib.save_state(self.course, state, state["updated_at"], authorize_insights=True)

    def insight(self, record_id="i1"):
        item = lib.read_json(ROOT / "assets/templates/insight.json")
        item.update(id=record_id, course_id=self.course_id, summary="用户自述可能理解了，但新题仍会卡住。")
        return item

    def source(self, record_id="s1", **changes):
        item = lib.read_json(ROOT / "assets/templates/source.json")
        item.update(id=record_id, course_id=self.course_id, title="企业会计准则示例",
                    author_or_institution="正式发布机构", retrieved_at="2020-01-01T08:00:00Z",
                    location="https://example.invalid/official-source",
                    used_for=["causality"], supports="支持本课程示例中的具体规则。",
                    authority_basis="这是该规则的正式发布文本。")
        item.update(changes)
        return item

    def test_init_off_leaves_no_files(self):
        target = self.base / "不保存"
        result = self.cli("init", target, "--title", "一次解释", "--slug", "one-time")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["status"], "not_saved")
        self.assertFalse(target.exists())

    def test_init_requires_real_choice_flags(self):
        for storage, flags in [("progress", []), ("full", ["--authorize-progress"])]:
            with self.subTest(storage=storage):
                target = self.base / storage
                result = self.cli("init", target, "--title", "测试", "--slug", "test", "--storage", storage, *flags)
                self.assertEqual(result.returncode, 1)
                self.assertFalse(target.exists())

    def test_init_refuses_existing_directory(self):
        before = self.snapshot()
        result = self.cli("init", self.course, "--title", "覆盖", "--slug", "overwrite", "--storage", "progress", "--authorize-progress")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(before, self.snapshot())

    def test_data_root_resolution_is_stable_and_does_not_create_course_storage(self):
        home = self.base / "home"; home.mkdir()
        default = lib.resolve_data_root(home=home)
        self.assertEqual(default["data_root"], str(home / "Documents" / "AI-Tutor-V5-学习记录"))
        self.assertEqual(default["source"], "default")
        self.assertFalse((home / "Documents").exists())

        configured_root = self.base / "自定义学习记录"
        configured = lib.configure_data_root(str(configured_root), home=home)
        self.assertEqual(configured["source"], "config")
        self.assertEqual(configured["data_root"], str(configured_root))
        self.assertFalse(configured_root.exists())

        override = self.base / "本次覆盖"
        resolved = lib.resolve_data_root(str(override), home=home)
        self.assertEqual(resolved["source"], "override")
        self.assertEqual(resolved["data_root"], str(override))
        for invalid in ["./data", str(ROOT)]:
            with self.subTest(invalid=invalid), self.assertRaises(lib.TutorError):
                lib.resolve_data_root(invalid, home=home)

    def test_course_discovery_reads_only_direct_compatible_v5_states(self):
        second = self.base / "第二课程"
        result = self.cli("init", second, "--title", "第二主题", "--slug", "second", "--storage", "progress", "--authorize-progress")
        self.assertEqual(result.returncode, 0, result.stdout)
        old = self.base / "旧版课程"; old.mkdir()
        old_state = self.state(); old_state.update(skill_version="4.0.0", schema_version=1)
        (old / "state.json").write_text(lib.encode(old_state))
        broken = self.base / "损坏课程"; broken.mkdir()
        (broken / "state.json").write_text('{"broken":\n')

        found = lib.discover_courses(self.base)
        self.assertEqual([item["title"] for item in found["courses"]], ["第二主题", "测试主题"])
        self.assertEqual({Path(item["path"]).name for item in found["ignored"]}, {"旧版课程", "损坏课程"})

    def test_root_and_courses_cli_are_read_only(self):
        target = self.base / "尚未创建的数据根目录"
        root = self.cli("root", "--data-root", target)
        self.assertEqual(root.returncode, 0, root.stdout)
        self.assertFalse(json.loads(root.stdout)["exists"])
        courses = self.cli("courses", "--data-root", target)
        self.assertEqual(courses.returncode, 0, courses.stdout)
        self.assertEqual(json.loads(courses.stdout)["courses"], [])
        self.assertFalse(target.exists())

    def test_schema_wrong_types_are_errors_not_exceptions(self):
        cases = [("mode", []), ("mode", {}), ("activity", []), ("storage_mode", {}),
                 ("topic", "主题"), ("schema_version", True), ("mastery", []), ("review_queue", None)]
        for field, wrong in cases:
            with self.subTest(field=field, wrong=wrong):
                state = self.state(); state[field] = wrong
                self.assertTrue(lib.validate_state(state, []))
        for wrong in [12, [], {}, None, True]:
            state = self.state(); state["topic"]["slug"] = wrong
            self.assertTrue(lib.validate_state(state))

    def test_unknown_fields_fail_without_silent_loss(self):
        state = self.state(); state["messages"] = ["不应进入状态"]
        before = self.snapshot()
        with self.assertRaises(lib.TutorError):
            lib.save_state(self.course, state, state["updated_at"])
        self.assertEqual(before, self.snapshot())

    def test_old_version_rejected_before_other_course_files(self):
        state = self.state(); state.update(skill_version="4.0.0", schema_version=1)
        (self.course / "state.json").write_text(lib.encode(state))
        with mock.patch.object(lib, "read_log", side_effect=AssertionError("不应读取旧版日志")):
            with self.assertRaises(lib.TutorError):
                lib.load_course(self.course)

    def test_six_points_can_pass_without_testing_transfer(self):
        self.append()
        self.assertEqual(self.state()["mastery"]["causality"]["status"], "provisional")

    def test_accuracy_gate_overrides_high_total(self):
        self.append(self.event(scores={"accuracy": 1, "reasoning": 2, "transfer": 2, "independence": 2}))
        self.assertEqual(self.state()["mastery"]["causality"]["status"], "introduced")

    def test_hint_and_scaffold_cannot_claim_independent(self):
        for support in [{"hint_level": 1}, {"scaffold_level": "L2"}]:
            with self.subTest(support=support):
                item = self.event(**support)
                with self.assertRaises(lib.TutorError):
                    self.append(item)
                item["scores"] = {"accuracy": 2, "reasoning": 2, "transfer": 2, "independence": 1}
                self.append(item)
                self.assertEqual(self.state()["mastery"]["causality"]["status"], "assisted")
                # 每个变式使用独立课程快照。
                (self.course / "assessments.jsonl").unlink()
                lib.sync_course(self.course)

    def test_revealed_answer_does_not_upgrade(self):
        item = self.event(answer_revealed=True, hint_level=4, scores={"accuracy": 2, "reasoning": 2, "transfer": 2, "independence": 0})
        self.append(item)
        self.assertEqual(self.state()["mastery"], {})
        self.assertEqual(lib.read_log(self.course, "assessments.jsonl")[0]["result"], "revealed")

    def test_self_report_does_not_upgrade(self):
        self.append(self.event(evidence_source="user_report", answer_excerpt="我应该会了"))
        self.assertEqual(self.state()["mastery"], {})

    def test_mastered_requires_both_retention_and_transfer(self):
        self.append()
        retained = self.event("a2", kind="retention", occurred_at="2020-01-02T08:00:00Z", prior_assessment_id="a1")
        self.append(retained)
        self.assertEqual(self.state()["mastery"]["causality"]["status"], "retained")
        transfer = self.event("a3", kind="transfer", occurred_at="2020-01-02T09:00:00Z", prior_assessment_id="a1",
                              new_context="从自然季节案例换为产品实验数据，独立识别选择偏差。",
                              scores={"accuracy": 2, "reasoning": 2, "transfer": 2, "independence": 2})
        self.append(transfer)
        self.assertEqual(self.state()["mastery"]["causality"]["status"], "mastered")

    def test_delay_and_timezones_are_real(self):
        self.append()
        item = self.event("a2", kind="retention", occurred_at="2020-01-02T15:59:00+08:00", prior_assessment_id="a1")
        before = self.snapshot()
        with self.assertRaises(lib.TutorError):
            self.append(item)
        self.assertEqual(before, self.snapshot())
        item["occurred_at"] = "2020-01-02T16:00:00+08:00"
        self.append(item)
        self.assertEqual(self.state()["mastery"]["causality"]["status"], "retained")

    def test_future_assessment_rejected(self):
        future = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat()
        with self.assertRaises(lib.TutorError):
            self.append(self.event(occurred_at=future))

    def test_transfer_needs_context_and_valid_prior(self):
        self.append()
        item = self.event("a2", kind="transfer", occurred_at="2020-01-02T08:00:00Z", prior_assessment_id="a1",
                          scores={"accuracy": 2, "reasoning": 2, "transfer": 2, "independence": 2})
        with self.assertRaises(lib.TutorError):
            self.append(item)
        item.update(new_context="新领域中的独立判断", concept_id="different-concept")
        with self.assertRaises(lib.TutorError):
            self.append(item)

    def test_repeating_same_task_does_not_prove_retention_or_transfer(self):
        original = self.event(); self.append(original)
        for kind in ["retention", "transfer"]:
            item = self.event("a2", kind=kind, task=original["task"], occurred_at="2020-01-03T08:00:00Z", prior_assessment_id="a1",
                              new_context="声称是新场景", scores={"accuracy": 2, "reasoning": 2, "transfer": 2, "independence": 2})
            with self.assertRaises(lib.TutorError):
                self.append(item)

    def test_new_failure_invalidates_older_promotion_basis(self):
        self.append()
        self.append(self.event("a2", occurred_at="2020-01-02T08:00:00Z", critical_error=True))
        self.assertEqual(self.state()["mastery"]["causality"]["status"], "introduced")
        with self.assertRaises(lib.TutorError):
            self.append(self.event("a3", kind="retention", occurred_at="2020-01-03T08:00:00Z", prior_assessment_id="a1"))

    def test_forged_result_and_mastery_rejected(self):
        with self.assertRaises(lib.TutorError):
            self.append(self.event(result="retained"))
        state = self.state(); state["mastery"] = {"causality": {"status": "mastered", "evidence_ids": []}}
        with self.assertRaises(lib.TutorError):
            lib.save_state(self.course, state, state["updated_at"])

    def test_append_repairs_missing_final_newline(self):
        self.append()
        path = self.course / "assessments.jsonl"
        path.write_text(path.read_text().rstrip("\n"))
        self.append(self.event("a2", occurred_at="2020-01-01T09:00:00Z"))
        self.assertEqual(len(lib.read_log(self.course, "assessments.jsonl")), 2)
        self.assertTrue(path.read_bytes().endswith(b"\n"))
        lib.load_course(self.course)

    def test_same_record_retry_is_idempotent(self):
        self.append(); before = self.snapshot()
        self.assertEqual(self.append()["status"], "unchanged")
        self.assertEqual(before, self.snapshot())
        with self.assertRaises(lib.TutorError):
            self.append(self.event(answer_excerpt="不同内容"))
        self.assertEqual(before, self.snapshot())

    def test_damaged_log_is_preserved(self):
        (self.course / "assessments.jsonl").write_text('{"broken":\n')
        before = self.snapshot()
        with self.assertRaises(lib.TutorError):
            self.append()
        self.assertEqual(before, self.snapshot())

    def test_malformed_record_shapes_are_diagnostic(self):
        for wrong in [[], None, "text", {"id": []}]:
            (self.course / "assessments.jsonl").write_text(json.dumps(wrong) + "\n")
            with self.assertRaises(lib.TutorError):
                lib.load_course(self.course)

    def test_duplicate_json_keys_and_nan_rejected(self):
        for raw in ['{"mode":"learn","mode":"act"}', '{"value":NaN}']:
            with self.assertRaises(lib.TutorError):
                lib.decode(raw, "test")

    def test_concurrent_state_update_is_not_overwritten(self):
        stale = self.state(); self.append(); before = self.snapshot()
        stale["weak_points"] = ["某个缺口"]
        with self.assertRaises(lib.TutorError):
            lib.save_state(self.course, stale, stale["updated_at"])
        self.assertEqual(before, self.snapshot())

    def test_off_blocks_all_course_writes(self):
        state = self.state(); state["storage_mode"] = "off"
        (self.course / "state.json").write_text(lib.encode(state))
        before = self.snapshot()
        operations = [lambda: self.append(), lambda: lib.sync_course(self.course),
                      lambda: lib.save_session(self.course, "内容", "记录.md", "progress"),
                      lambda: lib.save_state(self.course, state, state["updated_at"]),
                      lambda: lib.append_record(self.course, self.insight(), "insight"),
                      lambda: lib.append_record(self.course, self.source(), "source")]
        for operation in operations:
            with self.assertRaises(lib.TutorError):
                operation()
            self.assertEqual(before, self.snapshot())
            self.assertFalse((self.course / ".tutor-write.lock").exists())

    def test_symlink_log_cannot_modify_external_data(self):
        target = self.base / "外部资料.jsonl"; target.write_text("私人资料")
        (self.course / "assessments.jsonl").symlink_to(target)
        with self.assertRaises(lib.TutorError):
            self.append()
        self.assertEqual(target.read_text(), "私人资料")

    def test_symlink_session_directory_rejected(self):
        target = self.base / "外部目录"; target.mkdir()
        (self.course / "学习记录_sessions").symlink_to(target)
        with self.assertRaises(lib.TutorError):
            lib.save_session(self.course, "内容", "记录.md", "progress")
        self.assertEqual(list(target.iterdir()), [])

    def test_partial_write_is_reported_and_recoverable(self):
        original = lib.atomic_write
        def interrupted(path, content):
            if Path(path).name == "state.json":
                raise OSError("模拟断电")
            original(path, content)
        with mock.patch.object(lib, "atomic_write", side_effect=interrupted):
            with self.assertRaisesRegex(lib.TutorError, "未全部完成"):
                self.append()
        self.assertEqual(len(lib.read_log(self.course, "assessments.jsonl")), 1)
        with self.assertRaises(lib.TutorError):
            lib.load_course(self.course)
        lib.sync_course(self.course)
        self.assertEqual(self.append()["status"], "unchanged")
        self.assertEqual(len(lib.read_log(self.course, "assessments.jsonl")), 1)
        lib.load_course(self.course)

    def test_user_progress_notes_survive_update(self):
        path = self.course / lib.PROGRESS
        path.write_text(path.read_text() + "用户补充：我自己的例子。\n")
        self.append()
        self.assertIn("用户补充：我自己的例子。", path.read_text())

    def test_unmanaged_progress_file_is_not_overwritten(self):
        (self.course / lib.PROGRESS).write_text("用户自建的进度内容")
        before = self.snapshot()
        with self.assertRaises(lib.TutorError):
            self.append()
        self.assertEqual(before, self.snapshot())

    def test_full_session_requires_full_permission_and_preserves_existing(self):
        with self.assertRaises(lib.TutorError):
            lib.save_session(self.course, "逐字内容", "档案.md", "full")
        state = self.state(); state["storage_mode"] = "full"
        state["storage_consent"]["full_authorized_at"] = state["updated_at"]
        with self.assertRaises(lib.TutorError):
            lib.save_state(self.course, state, state["updated_at"])
        lib.save_state(self.course, state, state["updated_at"], authorize_full=True)
        lib.save_session(self.course, "实际原文", "档案.md", "full")
        with self.assertRaises(lib.TutorError):
            lib.save_session(self.course, "新原文", "档案.md", "full")
        self.assertEqual((self.course / "学习记录_sessions/档案.md").read_text(), "实际原文")

    def test_insight_requires_separate_opt_in(self):
        with self.assertRaises(lib.TutorError):
            lib.append_record(self.course, self.insight(), "insight")
        self.authorize_insights()
        lib.append_record(self.course, self.insight(), "insight")
        self.assertEqual(len(lib.read_log(self.course, "insights.jsonl")), 1)

    def test_insight_newline_idempotency_and_fact_boundary(self):
        self.authorize_insights()
        lib.append_record(self.course, self.insight(), "insight")
        path = self.course / "insights.jsonl"; path.write_text(path.read_text().rstrip("\n"))
        lib.append_record(self.course, self.insight("i2"), "insight")
        self.assertEqual(len(lib.read_log(self.course, "insights.jsonl")), 2)
        self.assertEqual(lib.append_record(self.course, self.insight("i2"), "insight")["status"], "unchanged")
        wrong = self.insight("i3"); wrong["kind"] = "fact"
        with self.assertRaises(lib.TutorError):
            lib.append_record(self.course, wrong, "insight")

    def test_insight_rejects_dialogue_and_missing_evidence(self):
        self.authorize_insights()
        for change in [{"messages": ["闲聊"]}, {"kind": "learning_evidence"}, {"evidence_refs": ["missing"]}]:
            item = self.insight(); item.update(change)
            with self.assertRaises(lib.TutorError):
                lib.append_record(self.course, item, "insight")

    def test_source_log_is_lazy_traceable_and_idempotent(self):
        path = self.course / "sources.jsonl"
        self.assertFalse(path.exists())
        record = self.source()
        result = lib.append_record(self.course, record, "source")
        self.assertEqual(result["status"], "saved")
        self.assertEqual(lib.read_log(self.course, "sources.jsonl"), [record])
        self.assertEqual(lib.append_record(self.course, record, "source")["status"], "unchanged")
        self.assertEqual(len(lib.read_log(self.course, "sources.jsonl")), 1)
        lib.load_course(self.course)

    def test_source_validation_preserves_history_and_boundaries(self):
        lib.append_record(self.course, self.source(), "source")
        cases = [
            self.source("s2", course_id="other-course", retrieved_at="2020-01-01T09:00:00Z"),
            self.source("s2", retrieved_at=(dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat()),
            self.source("s2", retrieved_at="2020-01-01T09:00:00Z", source_type="unknown"),
            dict(self.source("s2", retrieved_at="2020-01-01T09:00:00Z"), messages=["不应进入来源日志"]),
            self.source("s2", retrieved_at="2020-01-01T09:00:00Z", supersedes="missing"),
        ]
        for record in cases:
            with self.subTest(record=record):
                before = self.snapshot()
                with self.assertRaises(lib.TutorError):
                    lib.append_record(self.course, record, "source")
                self.assertEqual(before, self.snapshot())
        replacement = self.source("s2", retrieved_at="2020-01-01T09:00:00Z",
                                  publication_or_version="修订版", supersedes="s1")
        lib.append_record(self.course, replacement, "source")
        self.assertEqual(len(lib.read_log(self.course, "sources.jsonl")), 2)

    def test_damaged_source_log_blocks_course_without_rewriting_it(self):
        path = self.course / "sources.jsonl"
        path.write_text('{"broken":\n')
        before = path.read_bytes()
        with self.assertRaises(lib.TutorError):
            lib.load_course(self.course)
        self.assertEqual(path.read_bytes(), before)

    def test_checkpoint_roundtrip_keeps_partial_answer(self):
        state = self.state(); state.update(mode="learn", activity="paused")
        state["checkpoint"].update(resume_activity="check", task_prompt="判断相关与因果，并提出需要的证据。",
                                   response_so_far="相关不能直接证明因果，可能有第三变量。", response_status="partial",
                                   pending_question="还需要什么证据？", next_action="继续回答后半题。", hint_level=1)
        saved = lib.save_state(self.course, state, state["updated_at"])
        loaded, _ = lib.load_course(self.course)
        self.assertEqual(loaded["checkpoint"], state["checkpoint"])
        self.assertEqual(saved["mode"], "learn")
        empty = copy.deepcopy(saved); empty["checkpoint"]["task_prompt"] = ""
        self.assertTrue(lib.validate_state(empty, []))

    def test_reported_action_is_not_verified_result(self):
        state = self.state()
        state["task"] = {"description": "发送实验介绍", "success_criteria": ["实际发送并观察回复"], "status": "verified",
                         "plan": ["明天发送"], "actual_result": "我觉得解决了", "source": "user_report", "verification": "用户认为"}
        self.assertTrue(lib.validate_state(state, []))
        state["task"].update(status="planned", actual_result="", source="none", verification="")
        self.assertEqual(lib.validate_state(state, []), [])

    def test_lock_prevents_parallel_mutation(self):
        with lib.course_lock(self.course):
            before = self.snapshot()
            with self.assertRaises(lib.TutorError):
                self.append()
            self.assertEqual(before, self.snapshot())

    def test_symlinked_course_root_is_rejected(self):
        real = self.base / "真实目录"; real.mkdir()
        linked = self.base / "链接目录"; linked.symlink_to(real)
        with self.assertRaises(lib.TutorError):
            lib.safe_path(linked, "state.json")


if __name__ == "__main__":
    unittest.main()
