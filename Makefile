# 《盒子与钻石》构建（依赖并排的 ../OpenLogic-Zh）
# 中文版使用 XeLaTeX；screen/print 是上游英文对照构建。

LATEXMK ?= latexmk
LATEXMKFLAGS ?= -interaction=nonstopmode -halt-on-error -g

.PHONY: all zh zh-print screen print cover portraits check clean FORCE

# Preserve the upstream default: English screen/print outputs and cover.
# The localized edition remains an explicit `make zh` target.
all: screen print cover

zh: zh-bd-screen.pdf
	@sh scripts/check-build.sh zh-bd-screen

zh-print: zh-bd-print.pdf
	@sh scripts/check-build.sh zh-bd-print

screen: bd-screen.pdf
	@sh scripts/check-build.sh bd-screen

%.pdf: %.tex FORCE
	$(LATEXMK) $(LATEXMKFLAGS) -xelatex $<

bd-screen.pdf: bd-screen.tex FORCE
	$(LATEXMK) $(LATEXMKFLAGS) -pdf $<

zh-bd-screen.pdf bd-screen.pdf bd-print-cover.pdf: | portraits

print: bd-print.pdf

bd-print.pdf: bd-print.tex FORCE
	$(LATEXMK) $(LATEXMKFLAGS) -pdf $<

cover: bd-print-cover.pdf

portraits:
	@sh scripts/fetch-portraits.sh

bd-print-cover.pdf: bd-print-cover.tex FORCE
	$(LATEXMK) $(LATEXMKFLAGS) -pdf $<

# Build both variants and perform deterministic text/log checks.  The checks
# intentionally ignore known font/layout warnings; TeX errors and missing
# localized output remain failures.
check: zh zh-print screen

clean:
	$(LATEXMK) -C
	rm -f *.prb *.thm *.xdv *.xmpi

FORCE:
