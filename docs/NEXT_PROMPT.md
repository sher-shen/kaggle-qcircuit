kaggle-qcircuit：继续 Kaggle「Google Quantum AI - Verifiable Quantum Circuit Compilation」（10/29 下午我暂停了，现在决定继续）。

先读 ~/Desktop/CLAUDE-HUB/kaggle-qcircuit/memory/MEMORY.md → trunk.md，再按需读 env_setup.md、top_public_1029.md、plan.md。

已完成（10/29）：venv + 自编 kickmix + 数据（28MB）就绪；invsqrt/dqi 参考验证 = 1.000；公开最高（GM 22.81 = 20.29/59.27/9.87）的 invsqrt、dqi 本地复现一致。
背景：计算生物物理 PhD（MC 搜索、C++/Python、HPC），没有量子计算经验；huawei-CSI 11/13 截止前它优先，别占用 Windows 机器。

这次要做的：
1. 我同意下载 FeMoCo fcidump（128MB）后：跑 dfthcsos 参考 + 复现公开最高的 dfthcsos（ext/top_v12/）
2. 按我拍板的方向开工（建议 dfthcsos 主攻 + invsqrt 副线，见 plan.md）：先用白话讲清这题要改什么、改哪几个旋钮，再给第一个可验证的小改进

规则：
- 不要替我向 Kaggle 提交，提交前把文件和预期分给我
- ≥50MB 下载先报大小再问我；不跑烧钱的大规模 agent 进化
- 进展写进 memory/log.md，结论写进对应 memory 文件
