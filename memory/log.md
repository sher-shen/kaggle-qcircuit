# kaggle-qcircuit 时间线

## 2026-10-29
- 立项：Kaggle Google Quantum AI 量子电路编译赛（$150k，2027-01-20 截止）；建目录 + memory，整理赛题事实（部分来自第三方 repo，待核对）
- 还没报名、没下数据；下一步见 plan.md
- 用户粘贴 Overview 页 → competition_facts.md 改为官方版：给奖牌；1,544 队；总分 = 三题改进倍数的几何平均；奖金：总榜前 6 + 11/20 里程碑 $10k + Longest Leader $10k + **单题最好各 $10k**；用户还没点 Join
- 独立 agent 审核 + 抽查：dfthcsos 不是蓝海（公开 notebook 已 ≈9.6×），抄公开 notebook 即 ≈22.37，前三 ≈26 → 结论写入 landscape_1029.md；建议降为第二优先，Smart Buildings 升为主力（待用户确认）
- 用户定：量子题为主力（求职导向，目标奖牌），Smart Buildings 为备选；写新对话提示词 docs/NEXT_PROMPT.md
- 独立 agent 审核记忆：plan.md 重写（过时方案并入"已排除"）、NEXT_PROMPT 补约束、trunk 注来源
- 第二个对话：建 .venv（py3.12，kaggle CLI + numpy/scipy）；sparse clone Qualtran/kickmix 到 ext/，编出 Python 模块 kickmix 和 CLI bin/kickmix（Apple clang 21，C++20）；比赛参考电路/验证器不在 Qualtran 里，要从 Kaggle 数据拿
- 读 arXiv:2610.23832 §III：三题 cost 官方公式写进 competition_facts.md，替换 [三方] 段；等用户放 ~/.kaggle/kaggle.json
- token 存 ~/.kaggle/access_token（用户把 KGAT_ token 原文贴在了对话里，已建议比赛中途可在 Kaggle 重新生成替换）；数据共 1.04GB，下了 <50MB 的 28MB 到 data/；没下 dqi.kmb（886MB，用 dqi_reference_circuit.py 本地生成，字节数完全一致）和 FeMoCo fcidump（128MB，dfthcsos 验证必需，待用户批）
- data/kickmix/kickmix.so 是 Linux x86 版，Mac 用自编的
- invsqrt 参考：本地验证 PASS，cost 2,076,774.23 = 官方参考值（倍数 1.000），10 核 4 分钟
- 公开最高：ahmedberatozer v12 本地 GM 22.810（20.29 / 59.27 / 9.87），拆解写进 top_public_1029.md；正在本地复跑它的 invsqrt + dqi（runs/top_v12/）
- 用户看完复现结果后觉得太难、倾向不做；fcidump 不下载；主攻方向未拍板（建议 dfthcsos 主攻 + invsqrt 副线，见 plan.md）。dqi 参考验证仍在后台（runs/chain1.sh）
- dqi 参考本地验证 PASS：cost 2.443947e13，与官方参考一致（1.000×），142 秒；invsqrt+dqi 参考都 ≈1.0，dfthcsos 因没下 fcidump 未验
- 用户问：公开 notebook 算不算不公平（答：Kaggle 常态，规则允许公开分享；后果是地板高）、为什么要化学背景（答：dfthcsos 是量子化学的 DF/THC 张量分解，化学背景是捷径不是门槛）；用户自称"看不懂这个项目"，给了小学生版解释
- 用户想找跟论文相关的：Kaggle 现无生物/蛋白类进行中比赛；方法上最近的是 Squares in Squares（硬体堆积 + MC）
- 用户想找冷门赛（类似华为 AF）：扫了 AtCoder/DrivenData/华为/ROADEF，结论合并进个人记忆 项目/简历比赛机会.md；HTTF2027（AHC074）奖金只给日本居民
- 状态：本题暂停、可能放弃，等用户决定；环境和复现都保留
- 10/29–30：3 个独立 agent 全球搜"人少+现金+住法国能领"的赛：无一全核实；能领奖的只剩蛋白设计赛（长江杯/Poreva/PDC2026）→ 个人记忆 项目/蛋白设计赛.md；本题仍暂停待定
## 2026-10-31

- 10/31：用户重新有兴趣，要求"小学生也能听懂、不要公式"地讲清项目；讲了量子计算机原理、三题、invsqrt 任务与工具箱（核实 kickmix op_type.h）；读了 busyaprime 笔记本，纠正了我 Newton 的猜测（见 invsqrt_notes_1031.md）；用户觉得多题混讲太乱，决定新对话**只聊题1**；仍未决定是否参赛
- 10/31 晚：新对话只聊题1。ch.4 是纯文字叙述无表代码；改为自编小工具把 invsqrt.kmb 转文本，数出静态门数（CCX 1154/CSWAP 194/CCZ 49/Z_POW 48 等，详见 invsqrt_notes_1031.md），看出查表形状 CX–CCX–CX + HMR/CZ 擦除；与官方 1629.6 stamps 未对账。下一步：在序列里定位 172 个 AND 的主表
- 10/31 夜：用户转去补量子基础：经典/量子比特、Shor 数论半边（N=21 例）已懂；量子傅立叶变换半边未讲，用户将开新对话继续。题1 主表定位仍未做（见 invsqrt_notes_1031.md「学习进度」）

## 2026-11-01

- 11/01：用户一对一学 Shor 量子半边，读完「学习进度」后全程只聊找周期；讲通账簿全流程（号码本/草稿/配对/读草稿留梳子/QFT 亮点/连分数/验算），详见 invsqrt_notes_1031.md「学习进度」；顺带查官方 verifier：x 寄存器 22 位、max_x=3,133,452，更正「榜首 63 qubit 是总数、22 只是输入」；解释题1 输入输出与 S=Q×C。未参赛、未提交、无下载

## 2026-11-04

- 11/04 晚：为用掉云端试用额度（11-05 08:59 过期），本目录 git init（.gitignore 排除 .venv/bin/ext/Qualtran/大 .kmb/dqi.kmb.xz/fcidump，约 33MB，无 token），用户手动推到 **私有仓库 sher-shen/kaggle-qcircuit**（main；本地另有 worktree 分支 claude/modest-clarke-ghok88）。auto 模式拦了 `gh repo create --push`，需用户自己跑
- 建一次性云端 routine（Opus，主攻 invsqrt、dfthcsos 只用公开 fcidump、不提交 Kaggle、开 PR）两次返回 403 repo_access_denied：Claude GitHub App 未覆盖新私有仓库；用户称已授权仍 403，未再重试 → 留给新对话（任务说明见 docs/NEXT_PROMPT_cloud.md）
- 11/04 夜（诊断，未向 Kaggle 提交任何东西）：gh 确认 kaggle-qcircuit 私有、owner=sher-shen、我有 admin/push。RemoteTrigger list：无任何"私有仓库源"的成功 routine（block-blast / bio-soft 都是公开仓库）。create 测试（只 ls，Opus，clear_mcp_connections）：kaggle-qcircuit → 403 repo_access_denied；另一私有仓库 techarena2026 → 同样 403；公开仓库 xiaomei-tools → 200 建成（trig_01CDAGaQRPLha6oU7R7SNf9r，已 enabled=false 未真跑）。结论：**所有私有仓库都不行、公开可以** → 不是这个仓库的问题，是 Claude GitHub App 对私有仓库的授权没在云端侧生效/没装到 sher-shen 账号。下一步：https://github.com/settings/installations 检查 Claude App 是否装在 sher-shen 且 Repository access=All；并到 https://claude.ai/settings/connectors 重连 GitHub。仍不通 → 11-05 08:59 前用 App New session → Cloud 手动开，贴 docs/NEXT_PROMPT_cloud.md 的 B 段（第 14 行起）。
- 11/04 夜（续）：用户把 kaggle-qcircuit 改为**公开**后，同样的测试 routine 建成（200，trig_01Cbgx59Vok7eY2rXwVTwhym，已 enabled=false）→ 确认问题仅是云端读不到私有仓库。注意：仓库公开后 Kaggle 相关内容（含 memory/、docs）对外可见，正式任务前确认无不该公开的内容；任务期间别提交比赛敏感方案。正式任务待用户确认后用 docs/NEXT_PROMPT_cloud.md B 段建。
- 11/04 夜（正式 routine）：先 grep 仓库（含 memory/、docs/）和 git 历史，无 token/邮箱/密钥（KGAT 仅出现在文字描述里，无原值；只有 build 日志含本机路径 /Users/shenhuaiyu，无敏感）。建一次性 routine **trig_011DZvEqeihjMMGmPYst4hmE**（kaggle-qcircuit-invsqrt-overnight）：公开仓库 sher-shen/kaggle-qcircuit，claude-opus-5-5，env_011CUXq5rHvMuL2eiQM8H4W4，clear_mcp_connections，tools=Bash/Read/Write/Edit/Glob/Grep，run_once_at **2026-11-04T20:36:00Z**（巴黎 21:36），enabled=true，我没有手动 run。prompt = NEXT_PROMPT_cloud.md B 段，改"私有仓库"→"公开仓库"，加"不要把比赛非公开信息写进 PR/提交"，另按用户要求补一句"尽量多试、用满额度；做完开独立子 agent 当监工挑刺再收尾"。管理页 https://claude.ai/code/routines/trig_011DZvEqeihjMMGmPYst4hmE 。注意：本地 memory/log.md、trunk.md 有未推送改动，docs/NEXT_PROMPT_cloud.md 未入库，云端读到的是上次推送的版本。未向 Kaggle 提交任何东西。
- 11/04 夜（监工）：worker routine trig_011DZvEqeihjMMGmPYst4hmE 已在 20:36:22Z 触发（会话 cse_01Q175btyNNbdmDXkkALJJVc，https://claude.ai/code/session_01Q175btyNNbdmDXkkALJJVc ），**用的是旧 prompt**（我 20:37 才把含监工协议的新 prompt 更新进去，晚了 1 分钟，routine 已 disabled/run_once_fired）。新建每小时监工 routine **trig_01J5WjhhzXQyGxvKgokkj1Rb**（cron `5 21-23,0-7 * * *` UTC，首次 21:05Z，Opus，云端额度）：复核 worker 分支（自动识别 claude/* 分支）、亲自重跑 verifier、写 SUPERVISOR.md 推 claude/supervisor，默认 NOT_APPROVED；worker 看不到它，所以 worker 停/收尾时监工接手继续做（分支 claude/invsqrt-supervisor-work）。07:05Z 是最后一次触发（试用额度巴黎 08:59=07:59Z 过期）。
- 11/04 夜（重登 GitHub）：用户重新登录了 GitHub，云端授权状态可能变了，要在新对话里重新开始。已知：worker 会话 cse_01Q175btyNNbdmDXkkALJJVc（旧 prompt，无监工协议）可能仍在跑或已失败，需 list_runs/get_run_log 核实；监工 routine trig_01J5WjhhzXQyGxvKgokkj1Rb 仍 enabled（cron 5 21-23,0-7 * * * UTC，07:05Z 末次）；两个 routine 的 prompt 都可用 RemoteTrigger get 读出复用（worker 的新 prompt 在 trig_011DZ... 的 job_config 里，已含监工协议和 claude/invsqrt-worker 分支约定）。新对话提示词 → docs/NEXT_PROMPT_cloud2.md。未向 Kaggle 提交任何东西。

## 2026-11-04 20:45Z 重登 GitHub 后复查云端 invsqrt
- worker 会话 cse_01Q175btyNNbdmDXkkALJJVc 在跑（worker_status=running，20:43Z 仍有事件），无 403/克隆失败；已在云端从源码编 kickmix(py3.12)，用公开 Apache-2.0 op 列表重建 63q/62q 电路（sha256 吻合），在跑参考 verify。
- worker 还没推任何 claude/* 分支（ls-remote 仅 main 71957a1）。
- 监工 trig_01J5WjhhzXQyGxvKgokkj1Rb enabled，next_run_at 21:05Z，尚无 run（首次未到）。
- 未新建 routine（worker 正常，不重复启动）。额度 07:59Z 到期；待办：07:05Z 后看剩余额度，最后一次监工后 list_runs 汇总。

## 2026-11-05 08:30Z 云端试用额度到期后的总结果
- worker 21:24Z 撞 5 小时限额（12:40 UTC 才重置）后一直 idle，**零推送**，其环境搭建/复现/log 都留在沙箱里丢了；它读到的事实：公开 62q 电路（67482db6，~1327 Toffoli）已从 kickmix-macos 的 ops.json 字节级重建，参考 verify=1.000×，dfthcsos FCIDUMP 来自 zhendongli2008/Active-space-model-for-FeMoco（sha 吻合）。
- 监工 11 次（22:06Z–07:06Z 起）接手：分支 claude/invsqrt-supervisor-work，draft PR #1，最佳 lut_U2 = 109q / Toffoli 1618 / cost 204,973 = **10.132×**，官方 verifier 全量 PASS（换 salt 复核一致）。结论 NOT_APPROVED；低于公开最高 ~20.3×（62–63q），自研架构降 Q 做不动。
- 未向 Kaggle 提交，未推 main，无大文件。
- 11/05 08:30Z 复盘：云端试用额度具体用量 RemoteTrigger/本地都读不到，只能看 claude.ai 用量页（本地 Pro 套餐 5h 15%、周 22%，是另一回事）。监工成果在 GitHub：分支 claude/invsqrt-supervisor-work（59c0844，supervisor_work/ 目录）、claude/supervisor（SUPERVISOR.md）、draft PR #1，**尚未合并/未拉到本地**。
- 11/05 收尾：draft PR #1 已转 ready 并合并进 main（81c976d），本地 main 已拉到最新，supervisor_work/invsqrt/ 在本地；SUPERVISOR.md 存为 docs/SUPERVISOR_1105.md；记忆/docs 提交 d3a8496 已推 origin/main。云端 routine 均已结束（worker 一次性已触发，监工 07:05Z 末次后额度到期）。下一步（若继续）：从公开 62q 电路出发（tools/ops2kmx.py 可重建）再改，而不是自研 109q 架构；见 cloud_run_1104.md
