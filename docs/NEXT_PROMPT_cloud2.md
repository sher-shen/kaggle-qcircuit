# 新对话提示词（11-04 夜，重登 GitHub 后）

kaggle-qcircuit：我刚重新登录了 GitHub，请重新把云端 invsqrt 任务跑起来。**必须全部在云端用云端试用额度跑**（额度巴黎 2026-11-05 08:59 = 07:59 UTC 过期），本地不跑任何实验。不要向 Kaggle 提交任何东西。

背景（详见 memory/log.md 最后三条）：
- 仓库 https://github.com/sher-shen/kaggle-qcircuit 已是公开（私有仓库云端读不了，403）。
- 已有两个 routine：worker `trig_011DZvEqeihjMMGmPYst4hmE`（一次性，20:36Z 已触发过一次，会话 cse_01Q175btyNNbdmDXkkALJJVc，用的是**旧 prompt**，没有监工协议；它现存的 prompt 是新版，含监工协议）；监工 `trig_01J5WjhhzXQyGxvKgokkj1Rb`（每小时 cron `5 21-23,0-7 * * *` UTC，复核 worker 分支、亲自重跑 verifier、写 SUPERVISOR.md 推 claude/supervisor，worker 停了就接手）。

要做的：
1. RemoteTrigger list_runs + get_run_log 查 worker 会话和监工的状态：还在跑吗、有没有因为重登 GitHub 失败（403 / 克隆失败）、`git ls-remote https://github.com/sher-shen/kaggle-qcircuit` 看有没有 claude/* 分支被推上来。一张表告诉我。
2. 若 worker 已死或失败：用 RemoteTrigger get 读出 trig_011DZ... 的 prompt（新版，含监工协议），建一个新的一次性 routine（run_once_at 取现在 UTC 往后 5 分钟，claude-opus-5-5，environment env_011CUXq5rHvMuL2eiQM8H4W4，clear_mcp_connections: true，allowed_tools Bash/Read/Write/Edit/Glob/Grep，源仓库同上），建完告诉我 id 和时间，不要自己 run。若 worker 还在正常跑，就别重复启动，只确认监工 routine 仍 enabled、next_run_at 正常。403 就停下告诉我怎么处理，不要反复试。
3. 额度要尽量用满：如果 07:05Z 后还有额度，提醒我；到期前最后一次监工触发之后，帮我 list_runs 看一遍总结果（候选 cost / 倍数、PR 链接、SUPERVISOR.md 结论）。
4. 结果写进 memory/log.md，然后用 5 个字以内告诉我是否还有别的要做。
