kaggle-qcircuit：我想一对一学懂 Kaggle「Google Quantum AI - Verifiable Quantum Circuit Compilation」里的**题1 invsqrt（核聚变）**，目前只是学习，还没决定要不要参赛。

先读 ~/Desktop/CLAUDE-HUB/kaggle-qcircuit/memory/invsqrt_notes_1031.md（上一轮学到的全部结论），需要时再看 trunk.md。

我的背景：计算生物物理 PhD（会 MC / 模拟退火、C++/Python），没有量子计算基础。

讲解规则（很重要）：
- 用小学生也能听懂的话，多用生活比喻；不要数学公式、不要数学定理，除非我明确要
- **只聊题1**，不要顺带讲题2、题3，也不要提别的项目
- 一次只讲一个小点；我说"没懂"就换比喻重讲，不要堆术语
- 如果我说"念出来"，用 `say -v Meijia` 读（长文本别用 Flo，会中途断）

我们讲到哪了：
- 已懂：任务是"给每个输入 x 把硬币拧一个角度"、量子计算机的工具箱（只有 Toffoli 类和旋转算钱）、榜上做法是"加法 + 查表"而不是先猜再修正、借比特的两种情形
- 下一步：把榜首那张"8 位进、35 位出"的主查表具体拆开给我看（读 ext/top_v12/invsqrt.kmb 和 ext/nb/busyaprime_* 笔记本第 4 章），再数各类门占成本的比例

规则：
- 不要替我向 Kaggle 提交；≥50MB 下载先报大小再问我
- 进展写进 memory/log.md，结论写进 memory/invsqrt_notes_1031.md
