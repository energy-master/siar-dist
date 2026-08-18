# siar-dist

The download for **siar-build** — build SIaR detection models from your own labelled audio, and
run them in siar-app.

This repository holds built wheels and nothing else. The source lives elsewhere and is not
public; what is published here is compiled.

## Install

Python **3.13 exactly** — the wheels are native extensions built against that ABI, and pip will
refuse them on anything else rather than fail later.

```bash
pip install https://raw.githubusercontent.com/energy-master/siar-dist/main/dist/siar_build-0.2.0-cp313-cp313-linux_x86_64.whl
```

`brahma-intelligence` resolves automatically — it is named by URL in the wheel's metadata, with a
marker so the right platform's build is chosen.

To also run the finished model (`siar-build verify` and `siar-build scan` need it):

```bash
pip install "siar-build[run] @ https://raw.githubusercontent.com/energy-master/siar-dist/main/dist/siar_build-0.2.0-cp313-cp313-linux_x86_64.whl"
```

Then:

```bash
siar-build --help
```

## Platforms

| platform | wheel |
|---|---|
| Linux x86_64 (glibc) | ✅ |
| macOS arm64 / x86_64 | on request |
| Windows x86_64 | on request |

Unlike an obfuscator, the compiler does not cross-build: each platform needs a machine of that
kind, so a row is added when there is somewhere to build it. Alpine and other musl distributions
are **not** covered by the Linux wheel and will fail at import.

## What is in a release

`dist/RELEASE.json` records the source commits each wheel was built from, their sha256, and what
the build verified before publishing — the wheels are installed into a clean environment and the
full test suite is run against them, not against the source they came from.

## Licence

Proprietary — Vixen Intelligence. See the licence carried in each wheel.
