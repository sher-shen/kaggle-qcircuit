# 10/29 最高公开 notebook 拆解（ahmedberatozer v12，本地 GM 22.810）

来源：kaggle.com/code/ahmedberatozer/quantum-ai-df-thc-group-compression；数据集 ahmedberatozer/vqcc-v12-889q-verified-portfolio（约 25MB，已下到 ext/top_v12/，dqi.kmb.xz 解压后 544MB，sha256 已核对）
它是"拼盘"：invsqrt 用 busyaprime/mrmeows 的 63-qubit 电路，dqi 用 somejoint 的 889-qubit，化学用 heliosli 的角度电路 + Gluzdov gauge + somejoint 团队的 C60 分解。几乎所有高分 notebook 都是互相拼的同一批组件（alexchilton v54 = 22.795，busyaprime LB 22.724）

参考 cost（官方 metric 常数）：invsqrt 2,076,774.23 / dqi 2.44395e13 / dfthcsos 3,355,599,588.3

| 题 | 倍数 | 现状 | 瓶颈 |
|---|---|---|---|
| invsqrt | 20.29× | Q=63，C=1624.6 = Toffoli 1329.5 + (1 T + 41 旋转×≈28.9T)/4 | worst_err/tol=0.9993 → 误差余量几乎用光，旋转按 ε=2.4e-13 计价，旋转占 C 的 ≈18%；Q 里 41 个 scratch |
| dqi | 59.27× | Q=889（840 是输入 syndrome，只剩 49 工作 qubit），T=437,947，R=1.191（0 失败地板） | Q 已逼近 840 下限（再压最多 ≈(889/850)²=1.09×）；剩下只能砍 Toffoli；R 地板动不了 |
| dfthcsos | 9.87× | λ_eff=48.59，T=16,276，Q=430 | E_gap=3.914899 和 error_2=0.019999 都**贴在约束线上**；Λ=303.5；T：角度电路 8346 + inner prep 5311 + Givens 2250 + outer 369；Q：常驻 126 + **inner prep 临时 304**（启发式成本，随 R,B,C 变） |

GM = 22.810（三倍数之积开立方）

## 本地复现（10/29，salt=notebook-verification）
- invsqrt：cost 102,349.22，与作者完全一致（10 核 4 分钟）
- dqi：cost 4.12318e11，与作者完全一致（93 秒，峰值内存 8.7GB）
- dfthcsos：缺 fcidump（128MB）未跑；分解维度 R,B,C = 8,143,60（R·B=1144 个向量），baseline 是 65,60,60（3900 个向量），brot=8
