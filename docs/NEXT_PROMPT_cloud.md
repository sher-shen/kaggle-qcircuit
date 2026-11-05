# 新对话提示词（11-04 晚写）

## A. 本地对话用（在 kaggle-qcircuit 目录开）

kaggle-qcircuit：把云端 invsqrt 任务开起来。云端会话试用额度 11-05 08:59（巴黎时间）过期，要在那之前跑起来。

背景（11-04 晚）：本目录已推到私有仓库 sher-shen/kaggle-qcircuit（main）。用 RemoteTrigger 建一次性 routine 两次都返回 403 repo_access_denied，我已经在 GitHub 的 Claude App 里加了这个仓库的权限。详情见 memory/log.md 的 11-04 段和 ~/.claude/projects/-Users-shenhuaiyu/memory/tools_claude_cloud_sessions_routines.md。

要做的：
1. 用 RemoteTrigger 建一次性 routine：仓库 https://github.com/sher-shen/kaggle-qcircuit，模型 claude-opus-5-5，environment env_011CUXq5rHvMuL2eiQM8H4W4，加 `clear_mcp_connections: true`，prompt 用本文件 B 段原文。再报 403 就停下，告诉我去 claude.ai 重新连 GitHub，或者改用 App 的 New session → Cloud 手动开（贴 B 段）
2. 顺便用 RemoteTrigger list_runs 看一下另外两个 routine 的状态：block-blast（trig_018AmeZ1tMFc3dpk3sjhPk6Y）和 bio-soft（trig_01JANJNGS17apUEjFqS3nSDF），再用 gh 看 sher-shen/xiaomei-tools、block-blast-luck-vs-skill、bio-soft-mc-locomotion 有没有新 PR，一张表汇报
3. 不要向 Kaggle 提交；进展写 memory/log.md

## B. 云端任务说明（routine prompt / 手动开云端会话时贴这段）

背景：这是用户参加 Kaggle「Google Quantum AI - Verifiable Quantum Circuit Compilation」比赛（截止 2027-01-20）的工作区，私有仓库。用户是计算生物物理 PhD（MC 搜索、C++/Python、HPC），量子计算新手，现在正在学题1 invsqrt。用户在睡觉，你要全自动推进、不能提问；有分歧时选更稳妥的方案并写进 PR 描述。

硬规则：
- 绝对不要向 Kaggle 提交（你也没有 token）。产出是候选文件 + 本地 verifier 跑出来的 cost 和预期分数。
- 产出是一个向 main 的 PR，不要直接推 main。超过 50MB 的文件不要提交（.kmb 电路要提交的话先 xz 压缩，或者只提交生成脚本）。
- 不要跑大规模 LLM agent 进化。

任务：
1. 先读 memory/MEMORY.md → trunk.md，再读 competition_facts.md、cost_formulas.md、env_setup.md、top_public_1029.md、invsqrt_notes_1031.md、plan.md。
2. 在 Linux 上把环境搭起来：python3.12 venv（numpy、scipy、pybind11）；按 commit 638777fac4379bc62e2a1e4a52cf1a1753895d48 稀疏 clone https://github.com/quantumlib/Qualtran 的 kickmix 目录到 ext/Qualtran，编译 Python 模块和 CLI（data/kickmix/kickmix.so 本身就是 Linux x86 版，可能直接能用）。把 Linux 上的步骤补进 env_setup.md。
3. 复现基线：invsqrt 参考电路验证 = 1.000×，公开最高的 invsqrt（用 ext/top_v12/reproduction_v12.zip.xz 或 ext/nb/ 里的 notebook 重建）验证约 20.29×。
4. 主攻 invsqrt：在公开最高的基础上做可验证的改进。方向参考 invsqrt_notes_1031.md：主查表（8 位进 35 位出）的 AND 数、借比特减 qubit、S=Q×C 的权衡、查表或加法分段的局部搜索（MC 或模拟退火，用户熟悉这一套）。每个候选都要用官方 verifier 验证通过，记录 cost 和倍数；保留最好的那个，给出可复现的生成脚本。
5. 时间充裕的话做副线 dfthcsos：只能从公开渠道（论文附带的仓库、Zenodo 等，不能走 Kaggle）拿 FeMoCo76o113e.fcidump，拿到了就复现参考 cost 和公开最高的约 9.87×；拿不到就记下来，然后跳过。dqi 不碰。
6. 进展写进 memory/log.md，结论写进对应 memory 文件，并更新 trunk.md 的状态行。PR 描述要用白话（用户是新手）讲清楚：改了什么旋钮、为什么省、invsqrt 的新 cost/倍数和对总分几何平均的影响、候选提交文件在哪、下一步建议。
