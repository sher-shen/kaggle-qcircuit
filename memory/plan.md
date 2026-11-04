# kaggle-qcircuit 计划

## 当前定位
- **暂停待定**：用户 10/29 下午觉得看不懂、太难，倾向不做；10/31 重新有兴趣，先只学题1 invsqrt（新对话 docs/NEXT_PROMPT_invsqrt.md），继续与否仍等用户决定
- 若继续：求职导向（Kaggle 奖牌 + Google 背书 + "AI 搜索 + 验证闭环"故事）；底线是明显超过公开最高 GM 22.81，进前 10% 拿铜牌，争取银牌或单题 $10k
- huawei-CSI 11/13 截止前 CSI 优先；Smart Buildings 降为备选（见 ../../kaggle-smartbuildings/）

## 进度
1. ✅ Join（API 能下数据即已 Join）；kaggle CLI + token（~/.kaggle/access_token）
2. ✅ 下载前问大小：只下了 28MB；dqi.kmb 本地生成；fcidump 128MB 未批
3. ✅ 三题 cost 公式（论文 §III）写进 competition_facts.md；verifier 源码与之一致
4. ✅ kickmix 编译；invsqrt / dqi 参考 = 1.000；❌ dfthcsos 缺 fcidump
5. ✅ 复现公开最高（GM 22.81）的 invsqrt、dqi；❌ dfthcsos 待 fcidump
6. ⏸ 深挖哪题：已给建议（下方），用户未拍板，且倾向放弃本题

## 方法方向
- 经典算术电路优化（加法器 / 乘法器 / 查表）+ 局部重写搜索（模拟退火 / MC，用户熟）+ Claude 写生成器
- **不烧钱跑大规模 agent 进化**（三方 repo 估算约 $1.5k 一轮）
- 候选：dfthcsos 是数值优化问题（不是化学，用户背景是计算生物物理）但对手强（公开已 ≈9.6×，要靠更低 1-范数的分解）；dqi 公开已 59.27×；invsqrt 上手最快
- 11/20 里程碑奖要公开 notebook，跟 CSI 撞期，不追
- 规则同 huawei 两题：AI 不擅自提交，提交前给文件 + 预期分

## 已排除 / 被推翻
- 10/29 上午"本题为主力、底线超过 ≈22.37"→ 下午用户暂停待定；22.37 被公开最高 22.81 取代
- 10/29 早先"先攻 invsqrt""dfthcsos 冷门、主攻冲单题奖""量子降为次要、Smart Buildings 主力"→ 被审核数据（landscape_1029.md）和用户最终决定推翻

## 10/29 深挖建议（待用户拍板）
- 建议主攻 dfthcsos，invsqrt 当副线（理由和预期数字见 top_public_1029.md 及当日对话）
- 用户当天反应：觉得太难，可能不做；fcidump 暂不下载
