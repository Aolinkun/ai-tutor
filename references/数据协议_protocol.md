# 数据协议 3 · 两种发行形态共同遵守

仅用于 AI Tutor V5 新课程；不要把 V4 或其他状态协议当作本模板。原目录保持原样，本版不提供迁移器。首次只识别状态版号，非本版停止读取其余课程内容。

读取本节及相应 JSON 模板后再建档或保存。所有 JSON 使用 UTF-8、标准 JSON；JSONL 每行一个对象，以换行结尾。保留数组／对象类型，不能把 `topic` 改成字符串、把 `goal` 改成 `goals`，也不能省略模板字段。

## state.json

从 state 模板复制，替换示例主题、ID 和日期；模板的 2000 年时间只是占位示例，不能原样当作真实记录时间。所有时间采用含时区的 ISO 8601，例如真实 UTC 时间的 `YYYY-MM-DDTHH:mm:ssZ`。不知道历史时间就不声称有延迟证据。

字段严格保持模板结构，不新增任意字段。不认识的字段先报错并保留原数据，不静默丢弃。ID 使用小写英文字母、数字、下划线或连字符，最长 80 位，首字符为字母或数字。

| 字段 | 内容与约束 |
|---|---|
| schema_version / skill_version | 固定 3 / `5` |
| course_id / topic | 稳定课程 ID；topic 是 title、slug、scope 三个字符串组成的对象，title 非空，slug 是稳定 ID |
| created_at / updated_at | 真实建档与最近写入时间；更新不能早于创建 |
| goal | purpose、observable_outcome、time_constraints 为字符串；success_criteria 是字符串数组 |
| mode | `learn`、`solve`、`act`、`review` |
| activity | `intake`、`explain`、`demonstrate`、`practice`、`check`、`feedback`、`plan`、`execute`、`reflect`、`paused`、`complete` |
| storage_mode / storage_consent | off/progress/full；source 为 none/user；progress/full 需真实 progress_authorized_at，full 另需 full_authorized_at |
| current_unit / curriculum | 当前单元 ID 或 null；curriculum 为 `{id,title,outcome}` 对象数组，当前 ID 必须存在，ID 不重复 |
| mastery | 以概念 ID 为键；值只有 `{status,evidence_ids}`。从评估日志按顺序派生，不凭主观判断填高等级 |
| weak_points | 当前主要缺口的字符串数组，描述可观察困难，不贴人格标签 |
| review_queue | `{concept_id,due_at,basis_id}` 数组；basis_id 引用同概念有效独立评估 |
| task | 无实际任务时 null；有任务时用下述完整结构 |
| checkpoint | 每次活动都更新；暂停时保留原活动、原题与已答部分 |
| insight_capture | `{enabled,authorized_at}`；默认 false/null，单独授权后才启用 |

实际问题或行动的 task 结构：

```json
{"description":"具体任务","success_criteria":["事先明确的成功信号"],"status":"planned","plan":["本次动作"],"actual_result":"","source":"none","verification":""}
```

status 可为 open/planned/in_progress/reported_done/verified/blocked；source 可为 none/user_report/observed/artifact_verified。reported_done 与 verified 都需要实际结果和来源；verified 额外需要成功标准、观察或核验产出来源及 verification 依据。文字写得完整不等于已经核验，必须实际检查。

checkpoint 字段不可省略：resume_activity、task_prompt、response_so_far、response_status、pending_question、hint_level、scaffold_level、next_action。response_status 为 none/partial/complete；hint_level 是 0—4 的整数；scaffold_level 为 L0—L3。非暂停时 resume_activity 等于 activity；暂停时 activity=paused，resume_activity 保留原活动。原活动为 check 时 task_prompt 必须有完整必要题面；已有部分／完整回答时 response_so_far 非空；暂停时 next_action 必须具体。

## assessments.jsonl

按 assessment 模板逐条保存。`scores` 的 accuracy、reasoning、transfer、independence 各为 0—2 的整数；布尔字段必须是 true/false，不能用 0/1 替代。

只在作答已经结束或用户明确提交当前答案供评估时追加正式评估。部分作答与暂停直接进入 checkpoint 和 session，不能仅因未答完生成 not_passed 日志。occurred_at 不能是尚未发生的未来时间。

kind：immediate/retention/transfer。evidence_source：observed_response/user_report/artifact_verified。source_ref 写真实可追溯来源，核验产出不可缺失；answer_excerpt 保留可评估的关键作答或产出摘要，不改造成标准答案。

result：reported/revealed/not_passed/assisted/provisional/retained/transferred，按评估规则计算。assessments.jsonl 的 result 字段不包含 mastered；mastered 只存在于 state.mastery 中，由同概念累计保持与迁移证据派生产生。模块工具可以在输入省略 result 时自动计算；最终日志必须包含该字段。

非自述记录须有实际 answer_excerpt。有提示或支架时 independence 不能为 2；看过答案时为 0。保持和迁移引用同概念此前有效独立评估，不能跨越最近一次未通过继续沿用旧证据升级。

日志按真实发生时间追加；记录 ID 唯一。完全相同的 ID 和内容视为重试，不再追加；相同 ID 的不同内容报冲突，不能覆盖。需要更正时保留原日志，核对范围后制作带恢复点的修订，不能随意篡改历史。

mastery 的派生方法：按日志顺序，reported/revealed 不升级；not_passed 把该概念回退 introduced 并开启新的证据段；assisted 在尚无更强状态时升级 assisted；当前证据段的独立结果支持 provisional、retained、transferred；同时有 retained 和 transferred 则 mastered。evidence_ids 保留当前证据段的相关记录 ID，未通过记录作为该段起点；不能删除旧日志来隐藏回退。

## sources.jsonl

只在课程实际使用外部资料且已有 `progress` 或 `full` 保存授权时创建。每行使用 source 模板，记录来源本身及其在当前课程中的用途；它追溯教学内容依据，不替代 `assessments.jsonl` 对用户作答和能力证据的追溯。

`source_type` 可为：

- `law_or_regulation`
- `official_standard`
- `official_filing`
- `official_guidance`
- `original_work`
- `original_data`
- `academic_research`
- `textbook`
- `professional_analysis`
- `news`
- `open_web`
- `user_material`

`use_status` 可为 `supporting`、`contextual`、`discovery_only` 或 `conflicting`。分类只描述资料性质和本次用途，不保证结论正确；`authority_basis` 写明为什么适合支持当前内容，`limitations` 保留立场、口径、时效或证据限制。

`retrieved_at` 使用真实含时区时间且不得在未来；日志按获取时间追加。`used_for` 只放稳定的小写英文 ID。`location` 使用直接 URL、本地路径或稳定标识，不能只写搜索结果标题。`supports` 说明该资料实际支持什么，不把来源自身陈述扩大为客观事实。

相同 ID 和内容视为安全重试；相同 ID 的不同内容报冲突。资料更新或纠正时追加新 ID，并用 `supersedes` 引用当前日志中更早的来源记录；不覆盖旧记录。旧记录可以继续用于追溯，但教学时应说明已经被哪个版本替代。

## insights.jsonl

只按 insight 模板保存授权的提炼记录。kind 是 fact/self_report/hypothesis/preference/learning_evidence。source 包含 kind、reference、time；kind 为 user/assistant/document/observation。没有核验来源的 user/assistant 陈述不能直接标 fact。

保留 conditions、uncertainty、evidence_refs；learning_evidence 必须引用实际存在的评估 ID。禁止增加 messages、transcript、full_conversation 等字段塞入逐字对话。完整档案进入授权的 Markdown session，不进入洞见日志。

## 写入、并发与恢复

1. 先检查用户当前存储选择，再读取指定 V5 课程。当前要求 off 时不得调用写入工具，即使文件里仍有旧授权。off 不创建文件，包括临时记录与日志。
2. 检查版号、字段、已有 JSONL 和证据引用；遇到损坏内容停止追加，保留原文件。不能在无换行的末尾直接拼接 JSON。
3. 状态更新比较读到的 updated_at；变了就重新读取合并，不覆盖另一会话。保存期间串行写入，拒绝课程目录本身及课程内部文件使用软链接，避免日志被链接到别处。
4. 单个文件使用同目录临时文件后原子替换，写后回读。保留中文进度自动区之外的个人补充；旧文件没有自动区边界时停止覆盖。
5. 多文件更新先保存证据日志，再保存派生状态和中文摘要。它不是跨文件数据库事务；若中途失败，明确已写入范围，不报告全部成功。核对完整日志后重新派生 mastery 并恢复摘要，不重复追加同一记录。
6. 无可靠原子写入或并发控制能力时，不直接改共享课程；输出可复制的新记录或恢复卡，说明尚未安全落盘。

## 数据根目录命令

默认设置文件是 `~/.config/ai-tutor-v5/settings.json`，只接受一个 `data_root` 字段。设置文件属于本机路径配置，不是课程内容，也不代表用户已经授权保存学习进度。

```sh
python3 -B scripts/tutor.py root
python3 -B scripts/tutor.py configure-root --data-root "/绝对路径/AI-Tutor-V5-学习记录"
python3 -B scripts/tutor.py courses
```

`root` 只解析并显示当前数据根目录，不创建目录。`configure-root` 保存并回读本机设置，但不创建课程或数据根目录。`courses` 只读取根目录直接子目录中的 `state.json`，列出兼容 V5 课程并报告被忽略的旧版或损坏状态；选中课程后再使用 `validate` 读取其日志。

命令行也可临时传 `root --data-root "/绝对路径"` 或 `courses --data-root "/绝对路径"`，本次明确路径优先于本机设置。相对路径和技能安装目录会被拒绝。

## 命令行工具

在技能目录执行；把示例目录和输入文件替换成实际路径。所有授权标志只表示用户已经授权，不能靠工具参数自行创造授权。

```sh
python3 -B scripts/tutor.py root
python3 -B scripts/tutor.py courses
python3 -B scripts/tutor.py init "课程目录" --title "概率基础" --slug probability --storage progress --authorize-progress
python3 -B scripts/tutor.py validate "课程目录"
python3 -B scripts/tutor.py save "课程目录" --input "候选状态.json" --expected-update "上次读到的 updated_at"
python3 -B scripts/tutor.py assessment "课程目录" --input "本次评估.json"
python3 -B scripts/tutor.py source "课程目录" --input "本次来源.json"
python3 -B scripts/tutor.py insight "课程目录" --input "本次洞见.json"
python3 -B scripts/tutor.py session "课程目录" --kind progress --input "本次记录.md" --name "2026-09-06_193500_概率基础_练习与反馈.md"
python3 -B scripts/tutor.py sync "课程目录"
```

full 建档同时使用 `--storage full --authorize-progress --authorize-full`；单独获准启用洞见库时加 `--authorize-insights`。已有课程通过 save 切换 full 或启用洞见库时也需要相应授权标志和真实授权时间。session 的 full/unit 类型仅允许 full 档；同名记录不覆盖。

init 只接受新的独立目录；off 返回会话内状态，不建目录。save 需要完整候选状态，mastery 必须与已有日志一致，不能手动写高状态。assessment 追加后自动更新掌握与中文进度。source 只登记实际采用的资料，不代表工具已经判断事实真伪。sync 用于核对后恢复中断写入造成的派生不一致，保留原日志，不把损坏日志强行当作有效记录。

文件锁只使用 `.tutor-write.lock` 拒绝并发写入；无论成功或失败，都在 `finally` 清除本次创建的锁。异常遗留锁须确认没有写入进程后再移走，不能自动抢锁。不得另造 `.save.lock` 等第二种锁名，不得把已完成操作的锁留在课程目录。脚本只检查结构和明确不变量；事实真伪、用户真实授权、题目等价性与场景差异仍需导师判断。
## 模板目录

- `assets/templates/state.json`：完整状态结构。
- `assets/templates/assessment.json`：单条评估结构。
- `assets/templates/source.json`：单条教学资料来源结构。
- `assets/templates/insight.json`：单条洞见结构。
- `assets/templates/学习记录_session.md`：最小学习记录。
- `assets/templates/完整档案_session-full.md`：完整档案与原文分区。
- `assets/templates/学习地图_curriculum.md`、`assets/templates/学习总结_summary.md`：按需要生成。
