# siar-dist

The download for **siar-build** — build SIaR detection models from your own labelled audio, and
run them in siar-app.

This repository holds built wheels and nothing else. The source lives elsewhere and is not
public; what is published here is compiled.

## Install

The wheels are native extensions built against the CPython **3.13** ABI, and carry a
`requires-python` that refuses anything else rather than failing later at import. You do not need
a 3.13 on the machine already: [uv](https://docs.astral.sh/uv/) will fetch one for the
environment it creates, which is why the instructions below use it rather than pip.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### To build models

`uv tool install` puts `siar-build` on the PATH as a standalone command, in its own environment
with its own 3.13:

```bash
uv tool install --python 3.13 \
  https://raw.githubusercontent.com/energy-master/siar-dist/main/dist/siar_build-0.2.0-cp313-cp313-linux_x86_64.whl

siar-build --help
```

`brahma-intelligence` resolves automatically — it is named by URL in the wheel's metadata, with a
marker so the right platform's build is chosen.

### To also run the finished model

`siar-build verify` and `siar-build scan` shell out to `siar-app`, so they need it **on the
PATH** — not merely installed alongside. `uv tool install` exposes only the requested package's
own command, so the `[run]` extra wants a virtual environment you activate instead:

```bash
uv venv --python 3.13
source .venv/bin/activate

uv pip install "siar-build[run] @ https://raw.githubusercontent.com/energy-master/siar-dist/main/dist/siar_build-0.2.0-cp313-cp313-linux_x86_64.whl"
```

That puts `siar-build` and `siar-app` both on the PATH for as long as the environment is active.
Installing the extra as a tool instead leaves `siar-app` inside the tool's environment, where
`verify` and `scan` cannot see it and report it as missing even though it is there.

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
