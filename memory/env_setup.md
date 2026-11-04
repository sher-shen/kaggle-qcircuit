# 本地环境与验证跑法（Mac，10/29 搭好）

- Python：`kaggle-qcircuit/.venv`（uv 建，py3.12；系统 py3.15 太新）。装了 kaggle CLI 2.2.5、numpy、scipy、pybind11 2.12、kickmix
- kaggle 认证：新版 KGAT_ token 存 `~/.kaggle/access_token`（600），不是 kaggle.json；CLI 2.2.5 自动读
- kickmix 源码：`ext/Qualtran/kickmix`（sparse clone，只 kickmix 目录）
  - Python 模块：在 kaggle-qcircuit/ 目录下 `uv pip install --python .venv/bin/python --no-build-isolation ./ext/Qualtran/kickmix`（约 30 秒）。**坑**：在 Qualtran 目录里跑 uv 会报 "Required uv version >=0.13.4"（仓库配置要求），从外层目录跑即可
  - CLI：`bin/kickmix`，`clang++ -std=c++20 -O3 -fno-strict-aliasing -Isrc` + 所有非 test/perf/pybind 的 .cc（约 40 秒；zsh 不按空格拆 $SRC，要用 bash -c）
  - **坑**：比赛数据自带的 `data/kickmix/kickmix.so` 是 Linux x86，Mac 不能用
- 比赛数据：`data/`（只下 <50MB 的 28MB，按原目录结构摊平；kaggle -f 单文件下载的 zip 会多套一层路径）
  - **没下**：`sample_submission/dqi.kmb`（886MB）→ 用 `data/verifiers/dqi/dqi_reference_circuit.py runs/ref/dqi_ref.kmb` 本地生成，5 秒，字节数一致；`verifiers/dfthcsos/FeMoCo76o113e.fcidump`（128MB）→ dfthcsos 验证必需，用户 10/29 暂不批
- 验证命令（在 kaggle-qcircuit/ 下，`.venv/bin/python`）：
  - `data/verifiers/invsqrt/verify_submission_invsqrt.py X.kmb [--salt S]` → 10 核 4 分钟，内存 0.5GB
  - `data/verifiers/dqi/verify_submission_dqi.py X.kmb [--salt S]` → 公开 889q 版 93 秒（峰值 8.7GB）；参考版 142 秒
  - dfthcsos：在 data/ 下 `verifiers/dfthcsos/verify.py RUN_DIR/`，需要 fcidump
- 参考验证结果（runs/ref/）：invsqrt cost 2,076,774.23（=官方参考，1.000×）；dqi cost 2.443947e13（官方 2.443947e13，1.000×；Toffoli 均值 5,725,109、Q=1893、R=1.191）；dfthcsos 未跑
- 公开 notebook 源码在 `ext/nb/`，公开最高的组合数据集在 `ext/top_v12/`
