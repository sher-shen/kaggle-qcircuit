# kaggle-qcircuit 主干（当前结论）

- 定位 → **暂停待定，但用户对题1(invsqrt)重新有兴趣，先在专门对话里学懂它**，未决定参赛 → 见 plan.md、invsqrt_notes_1031.md
- 目标（若继续）→ 至少前 10% 铜牌，争取银牌或单题 $10k → 见 plan.md
- 截止 → 报名 2027-01-13，最终 2027-01-20 23:59 UTC → 见 competition_facts.md
- 计分 → 各题 = 参考 cost / 提交 cost，总分取几何平均；三题官方公式已从论文核实 → 见 competition_facts.md
- 竞争 → 公开最高本地 GM 22.81 = 20.29 / 59.27 / 9.87（大家互相拼同一批组件），公榜前三 ≈26 → 见 top_public_1029.md
- 环境 → Mac 上 venv + 自编 kickmix + 数据已就绪；invsqrt / dqi 参考验证 = 1.000；dfthcsos 缺 fcidump（128MB，用户暂不批）→ 见 env_setup.md
- 复现 → 公开最高的 invsqrt、dqi 本地复现与作者逐位一致；dfthcsos 未复现 → 见 top_public_1029.md
- 深挖建议（未拍板）→ dfthcsos 主攻（λ_eff·T·Q 全随分解维度变，是数值优化问题）+ invsqrt 副线（4 分钟一轮、适合 MC 搜索）；dqi 不碰 → 见 plan.md
- 状态 → huawei-CSI 11/13 截止前它优先；未决定参赛；仓库已**公开**；11/04–05 云端额度已用完（07:59Z 过期）：worker 零推送，监工接手做出自研 invsqrt **10.132×**（109q，官方 verifier PASS，PR #1 已合并 main 并拉到本地，低于公开最高 20.3×）→ 见 cloud_run_1104.md、log.md 末段
- 规则 → AI 不替用户提交，交之前给文件 + 预期分；≥50MB 下载先问
- invsqrt 榜上做法 → 不是 Newton，是「加法+查表」，成本大头在 8 位进 35 位出的主查表（186→172 个 AND）；省 qubit 靠借已知值的比特；工具箱里只有 Toffoli 类和旋转算钱 → 见 invsqrt_notes_1031.md
- invsqrt 输入输出 → 输入 22 位 x∈[1,3133452]，输出=给每个 x 盖∝1/√x 相位、x 还原、草稿清零；S=Q×C（榜首 63×≈1630）→ 见 invsqrt_notes_1031.md
- Shor 量子半边学习 → 已讲通全流程（账簿比喻），QFT 内部电路仅到直觉 → 见 invsqrt_learning_shor.md
