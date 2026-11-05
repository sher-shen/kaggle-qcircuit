---
name: cloud_run_1104
description: 11/04-05 云端 routine 试跑结果与教训（worker/监工/限额/私有仓库403/成果位置）
metadata:
  type: project
---
- 结果：监工 11 次接手，自研 LUT+二次方案 lut_U2 = 109q / Toffoli 1618 / cost 204,973 = 10.132×，官方 verifier 全量 PASS；NOT_APPROVED。成果在 GitHub：分支 claude/invsqrt-supervisor-work、claude/supervisor、PR #1（11/05 已合并进 main 81c976d，已拉本地，代码在 supervisor_work/invsqrt/，报告 docs/SUPERVISOR_1105.md）
- 公开 62q 电路（67482db6，~1327 Toffoli，~20.3×）可从 manwithacat/kickmix-macos 的 circuit-viewer ops.json 经 tools/ops2kmx.py 字节级重建（worker 做过，但没推）；监工没用它，走自己架构 → 想超公开最高应从它出发
- 教训：1) 云端读不到私有仓库(403)，须公开；2) 单个长会话约 48 分钟/106 轮就撞 5 小时限额，worker 零推送→**必须要求早推、频推分支**；3) 每小时监工+接手比单 worker 稳；4) 试用额度用量查不到，只能看 claude.ai 用量页；5) 自带 kickmix.so 是 py3.13，py3.12 须手编
- 精度方向已到头（fy=28 余量 0.9%），再提升只能降 Q 或降 Toffoli（SUPERVISOR.md 列了 y 步不留 b2、自写加法器、pad 借用等方向）
