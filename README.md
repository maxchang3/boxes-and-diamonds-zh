# Boxes and Diamonds — 中文版

> [!WARNING]  
>  
> **当前译文由 AI 初步生成，仍在持续润色中。**
> - 初始翻译：使用 DeepSeek V4 Flash 0731 Max (DeepSeek Harness)
> - 翻译润色：使用 GPT 5.6 Sol High (Codex)、GPT 5.6 Sol Pro (ChatGPT)，并辅以人工校对
>
> 正文译文维护在 [OpenLogic-Zh](https://github.com/maxchang3/OpenLogic-Zh) 的 `locale/zh/` 中；本书专属的前言、导论与外壳文字维护在本仓库。

本仓库是 [rzach/boxes-and-diamonds](https://github.com/rzach/boxes-and-diamonds) 的中文本地化，基于 [OpenLogic-Zh](https://github.com/maxchang3/OpenLogic-Zh) 组装。


## 编译

两个仓库必须位于同一父目录，目录名固定如下：

```text
workspace/
├── OpenLogic-Zh/
└── boxes-and-diamonds-zh/
```

从本项目仓库克隆：

```sh
mkdir boxes-and-diamonds-workspace
cd boxes-and-diamonds-workspace
git clone https://github.com/maxchang3/OpenLogic-Zh.git OpenLogic-Zh
git clone https://github.com/maxchang3/boxes-and-diamonds-zh.git boxes-and-diamonds-zh
cd boxes-and-diamonds-zh
```

如果只做英文回归测试，可把第一个仓库换成 `git clone https://github.com/OpenLogicProject/OpenLogic.git OpenLogic-Zh`；它不包含中文 locale，因此不能构建中文版。

## 本地构建

需要安装主流 TeX 套件（TeX Live、MacTeX 或 MiKTeX，含 ctex），并确保 `latexmk`、`xelatex`、`pdflatex`、`curl` 和 `pdftotext` 等命令在 PATH 中。封面肖像由构建脚本按需下载并在本地缓存，不纳入 Git。

```sh
make zh         # 中文屏幕版：zh-bd-screen.pdf
make zh-print   # 中文印刷内页：zh-bd-print.pdf
make check      # 中文两版 + 英文回归测试
make screen     # 仅本地测试用的英文屏幕版：bd-screen.pdf
make print      # 仅本地测试用的英文印刷内页：bd-print.pdf
make cover      # 上游英文印刷封面
make clean
```

`make zh` 和 `make zh-print` 使用 XeLaTeX，`make screen` 和 `make print` 使用 pdfLaTeX。日志中可能出现继承自上游的字体替代、overfull、PDF 资产和 hyperref 警告；TeX 错误、未定义 token、缺少输出或正文语言错误会使检查失败。

## 同步上游

```sh
git remote add upstream https://github.com/rzach/boxes-and-diamonds.git
git fetch upstream
git log --oneline HEAD..upstream/master
```

## 上游项目说明

_Boxes and Diamonds_ is a textbook for modal and other intensional logics based on the Open Logic Project. It covers normal modal logics, relational semantics, axiomatic and tableaux proof systems, intuitionistic logic, and counterfactual conditionals. The original project is maintained by [Richard Zach](https://richardzach.org/), and the latest English PDF is available from the [Open Logic builds site](https://bd.openlogicproject.org/).

The original edition and this translation are licensed under a [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
