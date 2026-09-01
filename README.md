# SIaR Framework


Signal Intelligence and Reconnaissance (SIaR) Framework from Vixen Intelligence. c. 2026

SIaR is our machine learning library, bot repository, benchmarking, and model production framework. This 
download intsalls:


| application | what it does |
|---|---|
| `siar-app` | run models from vixen intelligence and/or your proprietary models built using siar-build |
| `siar-build` | breed a society of bots that searches for your target, and package it as a model |
| `siar-db` | scan a corpus into a queryable structure database, then group and review what is in it |
| `siar-lib` | our proprietart machine learning framework for non linear signals |


>This repository holds built wheels and nothing else. The sources are private; what is published
>here is compiled.

All output can be viewed by simply dropping the output folder into Ident dynamcis at www.goident.ai as well as being incorporated into
exisitng data pipelines. `siar-app run` writes such a folder directly, and `siar-db scan --idout`
writes one beside its own output. siar-app, siar-build and siar-db each have a comprehensive
README documenting their full functionality.

> The full manual ships inside each install. `siar-app readme` opens siar-app's in a browser and
> `siar-build readme` opens siar-build's. This README is how to get started, and a reference for
> every command at the end.

---

## Install

The wheels are native extensions built against the CPython **3.13** ABI, and carry a
`requires-python` that refuses anything else rather than failing later at import. You do not need a
3.13 for download as [uv](https://docs.astral.sh/uv/) fetches one for the environment it
creates, which is why these instructions use it rather than pip.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # or: brew install uv
```

```powershell
winget install --id astral-sh.uv -e               # Windows
```

Close and reopen PowerShell after that, or `uv` is not on the `PATH` yet: the installer writes it
to the registry, and a shell already open keeps the environment it started with.

### Pick the wheels for your machine

```bash
BASE=https://raw.githubusercontent.com/energy-master/siar-dist/main/dist

SIAR=$BASE/siar-0.1.0-py3-none-any.whl
APP=$BASE/siar_app-0.7.0-cp313-cp313-linux_x86_64.whl
BUILD=$BASE/siar_build-0.2.0-cp313-cp313-linux_x86_64.whl
DB=$BASE/siar_db-0.1.0-cp313-cp313-linux_x86_64.whl
```

See [Platforms](#platforms) to see which platforms have builds. `$SIAR` is the same file whatever
you are on — it holds no compiled code, and names the right wheels for the machine it lands on.

### The whole download, one command

```bash
uv tool install --python 3.13 "$SIAR"
```

That puts `siar-app`, `siar-build`, `siar-db` and `siar` on the PATH, in one environment with its
own 3.13. It is the install to want: `siar-build verify`, `siar-build scan` and `siar-build soc
scan` each need `siar-app` **on the PATH**, and this is what satisfies them.

```bash
siar readme          # this page, in a browser, offline
```

The manual travels inside the install, so it is there on a survey box with no network and nothing
checked out. `siar-app readme` and `siar-build readme` open each program's own.

### Or one half of it

**Just running models.**

```bash
uv tool install --python 3.13 "$APP"
```

**Building only, never running** — this box breeds models and something else scans with them:

```bash
uv tool install --python 3.13 "$BUILD"
```

**Surveying a corpus, with no model yet.** `siar-db` needs neither of the others: it finds
structure with a bank of cellular automata rather than with a bred model, so it is what to reach
for when the question is "what is in this folder" rather than "where is my target in it".

```bash
uv tool install --python 3.13 "$DB"
```

**A virtual environment**, when you want them importable as libraries rather than only as
commands:

```bash
uv venv --python 3.13
source .venv/bin/activate

uv pip install "$SIAR"
```

### Check it

```bash
siar version         # every part of the download, and whether it is installed
siar readme          # this manual, rendered in a browser, offline
siar-app --help
siar-build --help
siar-db --help
```

---

## Update

```bash
uv tool install --force --refresh --python 3.13 "$SIAR"     # the whole download
```

One program on its own, if that is how it was installed:

```bash
uv tool install --force --refresh --python 3.13 "$APP"
uv tool install --force --refresh --python 3.13 "$DB"
```

Inside a virtual environment:

```bash
uv pip install --reinstall --refresh "$SIAR"
```

**`uv tool upgrade siar` does nothing here, and neither does pip's `-U`.** Upgrading means asking
an index for a higher version, and these are direct URLs at a pinned filename — there is no index
to ask. A release republishes the *same* filename with different bytes, so `--force` is what
reinstalls it.

**`--refresh` is the flag people miss.** uv caches downloads keyed on the URL, and the URL does not
change between releases. Without it you can get a forced reinstall of the copy already in the
cache, which looks exactly like an update that did nothing. If a version still looks wrong after
this, `uv cache clean` and install again.

Check what you ended up with:

```bash
siar version
```

Nothing you have built or scanned is touched by an update. Models, societies, output folders,
siar-db's workspace under `$SIARDB_HOME` and the local indexes all live outside the install.

## Remove

If you installed the whole download, the tool is called **`siar`** — one install, four
executables. Uninstalling `siar-app` or `siar-db` by name does nothing, because neither is a tool
you installed:

```bash
uv tool uninstall siar
```

If you installed one program on its own, uninstall that one by name instead:

```bash
uv tool uninstall siar-app       # or siar-build, or siar-db
rm -rf .venv                     # venv install (deactivate first)
```

Check it is gone with `uv tool list`. To be certain the next install downloads afresh rather than
reusing what uv already has for these URLs, follow it with `uv cache clean` — see
[Update](#update) for why that matters here.

That removes the programs and leaves your work alone. What stays behind, to delete by hand only if
you mean it:

| path | what it is |
|---|---|
| `~/.siar-app/` | the cached IDent Dynamics token, downloaded algorithm bundles, imported models |
| `~/.siar-build/` | this machine's build index and its societies' configuration |
| `~/.siar-db/` | the structure database, per-run output folders and the grid cache |
| your `--out` folders | the scans, societies and models themselves — the actual work |

---

## Quick start - Run a model with siar-app

### With a terminal user interface (TUI)

View everything this machine can run, the bots and features behind each. Add an input and run:

```bash
siar-app lib        # also what bare `siar-app` opens
```

It lists the algorithm bundles downloaded here and the models built on the box with siar-build, side by
side. Keys: `↑↓` select, `tab` switch pane, `i` input folder, `o` output folder, `p` worker count,
`enter` edit or run, `R` reload, `q` quit. It needs a terminal.

### The command line

Scan the input folder first to get some metadata. This reads headers only, so a multi-GB corpus is summarised in a second
and a mixed sample rate is caught before a long run rather than during one:

```bash
siar-app scan ~/audio/survey
```

Then run a model over it. Either one your account can download:

```bash
siar-app login                      # once; writes ~/.siar-app/credentials.json
siar-app algorithms                 # the catalogue your super user has published
siar-app run ~/audio/survey -a sonar-recall --out ~/scans/survey_sonar
```

…or one straight off disk, which needs no login and is the fastest way to try something just bred:

```bash
siar-app run ~/audio/survey \
  --algorithm-path ~/siar-soc/sonar_big/socs/NAME \
  --out ~/scans/survey_sonar
```

Useful flags on a real corpus: `--parallel` to set high performance computing flag to `TRUE`;
`--tui` to draw the whole run in one live panel, `--limit N` for a trial pass over a big folder;
`--resume` to pick up where an interrupted run stopped; `--link` to hardlink the audio instead of
copying it. The analysis grid and the algorithm's own parameters can be overridden — `--fft`,
`--hop`, `--fmin`, `--fmax`, `--param NAME=VALUE` — but the defaults come from the algorithm and
are usually what it was trained with.

### Read the results

`siar-app run` writes an output folder holding all relevant output metrics and decisions. **Open that folder in IDent Dynamics** (goident.ai) to work through the detections.

If the scan ran on a remote box, serve the folder read-only and look at it through an ssh tunnel
— the command prints the exact tunnel line:

```bash
siar-app serve ~/scans/survey_sonar
```

`siar-app runs` lists the scans run from this machine, `siar-app installed` what is cached locally,
and `siar-app feedback NAME -s 7` tells whoever published an algorithm how it did on your audio.

### Move a model to another machine


```bash
siar-app export NAME --out sonar.siarmodel # download the model (can also publish to transfer models)
siar-app import sonar.siarmodel      # on the other machine
```

It lands in that machine's workspace, appears in `siar-app lib`, and is runnable with
`siar-app run -a NAME`. Downloaded algorithms cannot be exported — they are licensed per machine.

---

## Quick start - Evolve a society fof bots searching for your target with siar-build

A **society** is a population of bots continuously evolving to better detect a target or feature in an input stream (e.g. acoustic stream). 
It runs autonmomously against and input stream always adapting and inproving its ability to infer and detect features within the stream. It is designed to evolve expressions rather than weights. It allows not only for a reactive model for a feature in a complex input stream, it also allows for insight by providing the expressions that have evovled to better represent the complex dataset fed to it.

Your input is a folder of recordings, each with a `<stem>_labels.json` file that provides data on the label/target being searched for.


```json
{
  "labels": [
    {"tmin": 75.0,  "tmax": 81.1,  "fmin": 6000, "fmax": 7500, "tag": "sonar",  "desc": "", "id": 848},
    {"tmin": 143.2, "tmax": 144.6, "fmin": 5800, "fmax": 7200, "tag": "sonar",  "desc": "second sweep", "id": 849},
    {"tmin": 212.4, "tmax": 218.0, "fmin": 300,  "fmax": 1200, "tag": "vessel", "desc": "", "id": 850}
  ],
  "file_desc": "deployment 04, north mooring"
}
```

Each label is a rectangle in time (seconds from the start of that recording) and frequency (Hz).
Only `tag`, `tmin` and `tmax` are needed — a row without a `tag` is skipped, `fmin`/`fmax` may be
omitted or left at `0` when the annotation carries no frequency bounds, and `desc` and `id` are
carried through for display only (ids do not have to be unique).

The `tag` is matched against `--target` **case-sensitively**: `--target sonar` above evolves the
society against the two `sonar` boxes and treats everything else in the stream — the `vessel` box
included — as not-target.

`<stem>.json` and `<stem>.labels.json` are accepted as well, as is Audacity's tab-separated
`<stem>.txt`. TRhe `.txt` form carries no frequency bounds, so prefer the JSON where you have both.


```bash
siar-build soc start ~/audio/sonar_big \
  --target sonar \
  --out ~/siar-soc/sonar_big
```

It returns as soon as the society is up, and keeps running when you close the terminal. Useful
options: `--name` to name it, `--top N` for how many bots vote in the published model (default 20),
`--min-recall X` when a miss costs more than a false alarm, and `--parallel N` for how many
searches run at once.

`--parallel` and `--workers` are both node counts, but for different processes. `--parallel N`
sets the society's search **node** count. N searches running side by side, each its own lineage with its own
seed, all competing for places in the same population. That is *more* search rather than *faster*
search. The default is `off` (one node) and `auto` or a non defined `--parallel` takes every core. The
resolved number is written into the society's `soc.json`, so a replay breeds the same society on a
machine with a different core count instead of silently becoming a different one.

`--workers N` set the number of cores that a single search spreads its own generations
across.  Several nodes already have the cores spoken for, so leave `--workers` at `off` whenever `--parallel` is used.

### Watch it

```bash
siar-build soc              # the info screen
siar-build soc list         # every society, and whether it is alive
siar-build soc status NAME  # one in detail, with its leaderboard
siar-build soc genes NAME   # what the expressions are made of, and what selection is doing
```

Control it with `siar-build soc pause NAME`, `resume`, and `stop NAME` (which waits for the running
searches to land; `--now` throws their work away).

---

## See the results

Two different streams get published:

### The run — what the society *did*

```bash
siar-build soc share NAME
```

Publishes the society's evo history, live status, gene counts and heartbeat to IDent Dynamics and prints a link that
shows it **live to anyone**. It is the same link every time, so one
already sent out keeps working across a stop and a restart. Note that what goes up includes every
bot's evolved expression. Turn it off with `--revoke` and publishing again revives the same link.

To watch from a browser without publishing anything, serve it read-only over an ssh tunnel instead. The command prints out instructions.

```bash
siar-build serve
```

### The model — what the society *builds*

```bash
siar-build soc publish NAME \
  --title "Sonar recall — society of 20" \
  --description "Bred on the sonar_big corpus, 96 kHz. Fires where 6 of 20 metrics agree."
```

This needs an IDent Dynamics login on the box — the same token `siar-app` uses, so nothing new has
to be created:

```bash
siar-app login                       # writes ~/.siar-app/credentials.json
export SIAR_APP_URL=https://goident.ai   # which installation, if not the one you logged in to
```

What goes up is the same `siar_<society>/` package that `siar-app run --algorithm-path` loads, so
what runs on the server is what runs here. Read `report.txt` and `publish.results` in the model folder before you publish.

**Uploading is not releasing.** The model lands *unpublished* so you  can run it
immediately in IDent dynamics.


---

## Quick start - Survey a corpus with siar-db

siar-app and siar-build both answer "where is my target". siar-db answers the question that comes
before it: **what is in this folder at all.** It runs a bank of fuzzy cellular automata over every
recording, draws an edge around everything that is structured rather than noise, and writes every
one of those edges to a SQLite database. Nothing is classified and nothing is named — the
interesting question is then asked of the database rather than of a detector.

```bash
# 1. scan a folder of recordings, using every core but two
siar-db scan /data/rsa_stream --dataset rsa_stream -j -2

# 2. see what it found
siar-db query --run 1

# 3. narrow it to the structures worth looking at
siar-db select --run 1 --min-dur 0.5 --f-low 2000 --f-high 8000

# 4. cluster that set into recurring families
siar-db embed && siar-db group

# 5. write a folder per family, with a picture of every member
siar-db print --out ./groups
```

`select`, `group` and `print` are one chain and each step stores its result, so you can re-print at
a wider margin without re-clustering, and re-cluster at a lower threshold without re-reading a byte
of audio. `siar-db view` says what is currently selected and how it grouped.

### Into IDent Dynamics

```bash
siar-db scan /data/rsa_stream --out ./run1 --idout
```

`--idout` writes `./run1/ident` — the recordings, a sidecar of boxes per rule per recording, and a
lane thumbnail each. Drop that folder into IDent Dynamics and every structure is drawn over a live
spectrogram, with a toggle per rule so you can see which of the automata found what. The audio is
copied into it, so the folder is self-contained and roughly doubles the disk the corpus takes.

Everything else lives under `$SIARDB_HOME` (default `~/.siar-db`): the database, the per-run output
folders and the cache. `siar-db info` prints the paths.

> Unlike the other two, siar-db has no `readme` command — its manual is the README in its own
> repository rather than a copy carried in the wheel.

---

## Platforms

| platform | siar-app | siar-build | siar-db |
|---|---|---|---|
| Linux x86_64 (glibc) | ✅ published | ✅ published | ✅ published |
| macOS 11+ arm64 (Apple Silicon) | ✅ published | ✅ published | not yet built |
| macOS x86_64 (Intel) | on request | on request | on request |
| Windows x86_64 | ✅ published — command line only | ✅ published — command line only | not yet built |

### Linux needs a recent C library

The Linux wheels are compiled against the build machine's glibc, and a wheel tag carries no way to
say so — `linux_x86_64` matches every x86_64 Linux, so pip will install these on a machine that
cannot load them and the failure arrives at first import rather than at install.

| what | glibc needed |
|---|---|
| `siar-app`, `siar-build`, `brahma-intelligence` | **2.34** or newer |
| `siar-db` | **2.38** or newer |

That is Ubuntu 22.04+ / Debian 12+ / RHEL 9+ for the first row, and Ubuntu 23.10+ / Debian 13+ /
Fedora 38+ for siar-db. `ldd --version` says what a box has. Alpine and other musl distributions
match the same wheel tag and are **not** supported.

If a box is too old, the command says so in as many words rather than raising a loader traceback:

```
error: siar-db cannot start — the C library on this machine is too old for it.

  this machine has  glibc 2.28
  this build needs  glibc 2.38 or newer
```

It reads the requirement out of the compiled module rather than repeating what the loader said,
which matters: the loader stops at the *first* version it cannot satisfy, so it reports 2.29 for a
module that actually needs 2.38, and upgrading to what it asked for does not fix anything.
`siar version` reports the same thing, and marks which parts are installed but cannot be loaded.
Every wheel carries this check itself, so it works whether you installed the whole download or one
program on its own.

Ask us for a build against an older glibc if you need one. Nothing in the programs requires a
recent C library; the wheels are simply compiled on a current machine, and a build made on an
older one runs on both.

**A platform is only in the one-command install once every column is filled.** Nuitka does not
cross-build, so each row is a machine somebody has to run the build on, and the columns are filled
on different days. `siar` — the wheel that installs all of it — names only the platforms that have
the complete set, so a machine with two of the three fails as "no wheel for this platform" rather
than installing part of the download and breaking on the missing URL. The individual wheels above
still install on their own wherever they are published.

**What "command line only" excludes, and why it is said here rather than discovered.** On Windows
`siar-app run`, `siar-app scan` and siar-build's pipeline all work. **`siar-build soc` — the
society daemon — and the `run-tui` screens do not.** They rest on process groups, `waitpid` and
terminal handling that Windows has no equivalent of, and one of the gaps is worse than an absent
feature: the daemon's liveness check is `os.kill(pid, 0)`, which on Windows is not a check at all
but a Ctrl-C sent to every process sharing the console. Breed societies on macOS or Linux, and
scan with what they breed anywhere.

Windows is also the one row in `dist/RELEASE.json` with an empty `verified`. Its wheels compile,
pass the leak check, install and run; 714 of 741 of siar-build's tests pass against them. The
suite has not been run green end to end on that platform, and the manifest records that rather
than rounding it up.


---

# Command reference

Every command and every option, as the programs themselves report them. `--help` on any command
prints the same thing with more detail.

## siar-app

```
siar-app [--version] [--server URL] <command> [options]
```

`--server URL` picks which IDent Dynamics install to talk to, and can be given globally or on any
command that reaches the network; the default is the one you logged in to. With no command at all,
`siar-app` opens the library screen.

| command | what it does |
|---|---|
| `version` | print the package version and this machine's build tag |
| `license` | show the licence, or accept it without a prompt |
| `quick-start` | open the illustrated quickstart in your browser (`quickstart` also works) |
| `readme` | open the full manual in your browser |
| `lib` | browse what this machine can run, and start a scan from it (`library` also works) |
| `signup` | create an IDent Dynamics account |
| `login` | sign in and cache a token |
| `logout` | forget the cached token on this machine |
| `whoami` | show who the cached token belongs to |
| `algorithms` | list the algorithms your account can download |
| `installed` | list the bundles downloaded to this machine |
| `feedback` | rate how well an algorithm performed, 0–9 |
| `scan` | summarise a folder of recordings from headers alone |
| `run` | scan a folder and build an output folder for the web app |
| `serve` | browse an output folder in a browser, without copying it |
| `export` | write a model built here to one file another machine can import |
| `import` | unpack a model bundle exported from another machine |
| `runs` | list the scans run from this machine |

### `siar-app run FOLDER --out DIR`

The one that does the work. `FOLDER` is a root of WAV/FLAC recordings.

| option | meaning |
|---|---|
| `-a, --algorithm NAME` | which model (see `siar-app algorithms`) |
| `-o, --out DIR` | output folder to create — **required** |
| `--algorithm-path DIR` | run an unobfuscated algorithm package straight off disk; needs no login |
| `--platform TAG` | download the build for this platform tag instead of this machine's |
| `--refresh` | re-download the algorithm even if it is cached |
| `--server URL` | IDent Dynamics install to talk to |

Analysis grid — defaults come from the algorithm:

| option | meaning |
|---|---|
| `--fft N` | FFT size, a power of two |
| `--hop N` | hop in samples (default: fft/4) |
| `--window {hann,hamming,blackman,rectangular}` | window function |
| `--channel SEL` | `mix` (default), `left`, `right`, or a channel index |

Algorithm parameters:

| option | meaning |
|---|---|
| `--param NAME=VALUE` | set one algorithm parameter; repeatable |
| `--fmin HZ` | low edge of the band to scan |
| `--fmax HZ` | high edge of the band to scan |

Output:

| option | meaning |
|---|---|
| `--link` | hardlink the audio instead of copying it (same filesystem only) |
| `--resume` | skip recordings already written to the output folder |
| `--no-thumbnails` | skip the per-recording lane thumbnails |
| `--limit N` | stop after N recordings — a trial run over a big corpus |
| `--max-size SIZE` | skip recordings larger than this, so one enormous file cannot take the run's memory with it (default 550MB; `0` for no ceiling). Accepts KB, MB, GB or a plain byte count |
| `--parallel [N]` | scan N recordings at once, one process each; bare `--parallel` uses every core this machine's memory will hold |
| `--no-recursive` | only the top level of the folder |
| `--tui` | draw the whole run in one live panel: progress, where the time is going, what is being found, and a row per worker |
| `-q, --quiet` | no per-file progress |

### `siar-app scan FOLDER`

| option | meaning |
|---|---|
| `--no-recursive` | only the top level of the folder |

### `siar-app serve [DIR]`

Serves one output folder read-only over HTTP — `DIR` defaults to the most recent `siar-app run`.
Binds loopback and requires a token; no route can change anything in the folder.

| option | meaning |
|---|---|
| `--port N` | port to listen on (default 8420; `0` picks a free one) |
| `--bind ADDR` | address to listen on (default 127.0.0.1 — the `ssh -L` end) |
| `--allow-remote` | permit a `--bind` other than loopback, over plain HTTP |
| `--token VALUE` | use this token instead of a fresh random one |
| `--open` | also open the page in a browser on **this** machine |
| `--no-audio` | refuse to serve the recordings themselves |
| `--allow-origin ORIGIN` | let this web origin read the daemon; repeatable, none by default |
| `-v, --verbose` | log one line per request |

### `siar-app lib`

No options. Keys: `↑↓` select, `tab` pane, `i` input, `o` output, `p` parallel, `enter` edit or
run, `R` reload, `q` quit.

### `siar-app signup`

| option | meaning |
|---|---|
| `--email ADDRESS` | where the verification link is sent (prompted for if omitted) |
| `--username NAME` | 3–64 characters: letters, digits, and `.` `_` `-` |
| `--display-name NAME` | how your name appears in the app (default: your username). Pass an empty string to accept the default without a prompt |
| `--server URL` | IDent Dynamics install to talk to |

### `siar-app login [USERNAME]`

`USERNAME` is a username or email, prompted for if omitted. Set `$SIAR_APP_PASSWORD` to avoid the
password prompt in a script.

| option | meaning |
|---|---|
| `--device LABEL` | how this machine is labelled in your account's token list |
| `--server URL` | IDent Dynamics install to talk to |

### `siar-app algorithms`

| option | meaning |
|---|---|
| `--family NAME` | only models in this family (name or title) |
| `--params` | also print each algorithm's tunable parameters |
| `--json` | print the raw catalogue as JSON |
| `--server URL` | IDent Dynamics install to talk to |

### `siar-app installed`

| option | meaning |
|---|---|
| `--check` | also ask the server whether a newer version is published |
| `--json` | print the raw list as JSON |
| `--server URL` | IDent Dynamics install to talk to |

### `siar-app feedback [NAME]`

`NAME` is a model from `siar-app installed`. One rating per person per build is kept; rating again
replaces your last answer.

| option | meaning |
|---|---|
| `-s, --score 0-9` | 0 found nothing useful, 9 found what was there and little else (prompted for if omitted) |
| `-m, --comment TEXT` | a sentence on what it did well or badly |
| `--mine` | list the ratings you have given instead of adding one |
| `--server URL` | IDent Dynamics install to talk to |

### `siar-app export [NAME]`

With no name, lists what could be exported.

| option | meaning |
|---|---|
| `--out PATH` | file to write, or a folder to write it into (default: `<name>-<version>.siarmodel` here) |

### `siar-app import [FILE]`

With no file, lists the models already imported here. Nothing in the bundle is executed.

| option | meaning |
|---|---|
| `--into DIR` | unpack somewhere other than the workspace (not listed in `lib`) |
| `--inspect` | print what the bundle says about itself and import nothing |

### `siar-app runs`

| option | meaning |
|---|---|
| `--limit N` | how many to list |
| `--json` | print as JSON |

### `siar-app license` / `readme`

| option | meaning |
|---|---|
| `--accept` | (`license`) record acceptance and exit — for a script or a container |
| `--text` | (`readme`) print it as Markdown instead of opening a browser |

`version`, `logout`, `whoami` and `quick-start` take no options beyond `--server` where it applies.

---

## siar-build

```
siar-build [--version] <command> [options]
```

| command | what it does |
|---|---|
| `all` | prepare, evolve, package, verify and scan |
| `prepare` | cut the labelled stream into a class-folder corpus |
| `evolve` | search for a metric and measure it on unseen recordings |
| `package` | turn the model into a package siar-app can run |
| `verify` | prove the package computes what the search measured |
| `scan` | run the model over the audio with siar-app |
| `run-tui` | set up and watch a build on one screen |
| `models` | list what this machine has built |
| `name` | rename a model, on disk and in the index |
| `forget` | remove a build from the index, leaving the model on disk |
| `delete` | delete a model from disk, and its row with it |
| `soc` | societies — keep breeding bots for one target and publish their vote |
| `serve` | watch this machine's societies from a browser, over an ssh tunnel |
| `readme` | open the manual in your browser |

### The pipeline: `all`, `prepare`, `evolve`, `package`, `verify`, `scan`

All six take the same `INPUT` — a folder of recordings, each with a `<stem>_labels.json` sidecar —
and the same options, so a stage can be re-run on its own with the flags the whole run used.
`all` and `scan` additionally take `--no-scan`.

| option | meaning |
|---|---|
| `-t, --target TAG` | the label tag to detect — **required** |
| `-o, --out DIR` | where the corpus, model and scans go — **required** |
| `--name NAME` | what to call this run (default: a minted `<target>_<tag>_vxrun`). Bots are always named `<target>_<tag>_vxbot`. Pass a full bot name to continue a build that exists |
| `--no-scan` | (`all`, `scan`) stop after verify; the model is still built and packaged |

**Corpus:**

| option | meaning |
|---|---|
| `--alias TAG` | another tag meaning the same thing; repeatable. `--alias none` for strictly the target tag |
| `--max-label-seconds S` | cap how much audio one label contributes. Long context spans otherwise dominate the positive class by window count |
| `--background-ratio X` | seconds of background per second of target (default 2) |
| `--test-recordings N` | whole recordings kept unseen by the search entirely (default 2) |

**Search:**

| option | meaning |
|---|---|
| `--seed N` | random seed |
| `--objective NAME` | what fitness measures |
| `--selection NAME` | the selection strategy |
| `--pop N` | population size |
| `--generations N` | how many generations |
| `--elite N` | how many of the best survive a generation unchanged (default 4). 0 lets a bad crossover lose the champion; large turns the search into a hill climb |
| `--tournament K` | how many individuals a fitness tournament draws (default 5) — the selection pressure. 2 is nearly a random walk; 20 hands each generation to one lineage |
| `--size-tournament K` | the size tournament `double_tournament` holds beside the fitness one (default 2) |
| `--crossover W` | weight of subtree crossover (default 0.55). Weights are relative and normalised; 0 switches an operator off |
| `--subtree-mutation W` | replace a subtree with a fresh random one (default 0.15) |
| `--point-mutation W` | swap one node for another of the same arity (default 0.10) |
| `--hoist-mutation W` | promote a subtree to the root (default 0.07) |
| `--shrink-mutation W` | replace a subtree with a terminal (default 0.05) |
| `--constant-tweak W` | nudge a constant (default 0.08) |
| `--mutation-scale X` | how far a constant is nudged, in units of its own magnitude (default 0.15) |
| `--max-nodes N` | hard cap on an individual's size (default 64) |
| `--max-depth N` | hard cap on an individual's depth (default 8) |
| `--parsimony HOW` | how size enters the comparison: `none`, `lexicographic` (default, scale-free) or `linear` |
| `--parsimony-coeff X` | the coefficient for `--parsimony linear`, and only for it |
| `--sharing SIGMA` | fitness-sharing radius (default 0, off). Above zero, individuals that score the same windows the same way split their fitness |
| `--parallel [N]` | score each generation across N worker processes; bare `--parallel` uses every core. Wall clock only — same seed, same champion |
| `--no-null-control` | skip the label-shuffle control. Not advised: it is the only check that the pipeline is not leaking |

**Frontend** — derived from the corpus; override with care:

| option | meaning |
|---|---|
| `--fft N` | FFT size |
| `--hop N` | hop in samples |
| `--delta-t MS` | how far apart the spectrogram's columns are, in milliseconds — the readable way to say `--hop`. Given without `--fft`, the FFT follows it at the same 75% overlap |
| `--point-buffer MS` | how much audio either side of a **point** label is the event. Without it, a click corpus reports its labels and zero seconds of labelled audio |
| `--n-bins N` | how many bands the analysed range is divided into — the width of the vector every bot reads (default 128). Above what the band's resolution can fill, the surplus are constant-zero columns |
| `--time-op` | cut the corpus from the **neighbourhoods of labels** only, discarding audio far from anything anybody marked |
| `--buffer-time S` | seconds either side of a label that `--time-op` keeps (default 5) |
| `--window S` | analysis window; rounded to a whole even number of STFT hops |
| `--fmin HZ` | bottom of the analysed band. Raising it to just below the target stops the search reaching for out-of-band session artefacts |
| `--fmax HZ` | top of the analysed band. Everything above it is invisible |
| `--raw-level` | do **not** normalise each window to unit RMS. Exposes the search to energy dominance |

### `siar-build run-tui [INPUT]`

| option | meaning |
|---|---|
| `-t, --target TAG` | pre-select the target tag |
| `-o, --out DIR` | pre-fill the output root |

### `siar-build models`

| option | meaning |
|---|---|
| `-t, --target TAG` | only this target |
| `--targets` | list the targets instead of the runs — what this machine has been taught to detect |
| `-n, --limit N` | how many to list |
| `--programs ID` | show one build's champion and runners-up instead of the listing |

### `siar-build name ID NAME` · `forget [ID]` · `delete ID`

| option | meaning |
|---|---|
| `--missing` | (`forget`) forget every build whose packaged model is no longer on this disk, instead of one by id |
| `--scans` | (`delete`) delete the scan output folder as well |
| `-y, --yes` | (`delete`) do not ask. Without this the folders are named and confirmed |

### `siar-build serve [SOC]`

Serves what the societies on this machine are writing, read-only, so IDent Dynamics' pedigree panel
can play them live. `SOC` defaults to every society on this machine.

| option | meaning |
|---|---|
| `--port N` | port to listen on (default 8421; `0` takes a free one) |
| `--bind ADDR` | address to listen on (default 127.0.0.1 — the tunnel's end) |
| `--allow-remote` | permit a non-loopback `--bind`. Plain HTTP, so anything on the path can read the token |
| `--token VALUE` | use this token instead of minting one, for a link that survives a restart |
| `--allow-origin ORIGIN` | a web origin allowed to read this daemon; repeatable. Defaults to `https://goident.ai` |
| `-v, --verbose` | one line per request, with the token removed |

### `siar-build readme`

| option | meaning |
|---|---|
| `--text` | print it as Markdown instead of opening a browser |

---

## siar-build soc

Bare `siar-build soc` opens the screen.

| subcommand | what it does |
|---|---|
| `start` | start a society, detached |
| `list` | every society, and whether it is alive |
| `status` | one society in detail |
| `genes` | what the society's expressions are made of, and what is surviving |
| `share` | publish a society's run, or turn its public link off |
| `publish` | send a society's **model** to IDent Dynamics, so it can be run there |
| `stop` | ask a society to stop, and wait for it |
| `pause` | stop a society starting new searches |
| `resume` | let a paused society carry on |
| `rattle` | shake a society that has stopped moving |
| `scan` | run a society's published model over audio |
| `forget` | remove a society from the index, leaving its searches alone |

### `siar-build soc start INPUT`

Takes the **search** and **frontend** groups above — pinned once, for every search this society
ever runs — plus its own:

| option | meaning |
|---|---|
| `-t, --target TAG` | the label tag to detect — **required** |
| `-o, --out DIR` | where the society's work goes — **required** |
| `--name NAME` | what to call the society (default: a minted `<target>_<tag>_vxsoc`) |
| `--arena N` | whole recordings kept for ranking only, which no search ever trains on (default 2) |
| `--unseen N` | whole recordings kept for reporting only — never trained on, never selected on (default 2) |
| `--top N` | how many bots the published model votes with (default 20) |
| `--min-recall X` | the share of the target's windows the published vote must find on the arena, 0 to 1 (default 0 — no floor). Set it when a miss costs more than a check |
| `--allow-small-corpus` | run even when the corpus cannot supply all three splits. The arena is kept first; the reporting split is what goes |
| `--seed-bots N` | how many of the society's best a new search starts from (default 8). 0 starts every search from noise, which is the honest control |
| `--rounds N` | stop after this many selections (default: keep going) |
| `--eval-dir DIR` | a folder of labelled recordings the **published model** is scored against, over and over. This is the curve that says whether the thing you ship is getting better |
| `--eval-every MIN` | minutes between evaluations (default 10) |
| `--no-eval-figures` | do not draw each evaluation as a picture of the corpus |
| `--note TEXT` | why this society was started; recorded against it |
| `--public` | publish this society as it runs, and print a link that shows it live to **anyone** — including every bot's evolved expression |
| `--foreground` | run in this terminal instead of detaching |
| `--parallel [off\|auto\|N]` | how many **searches** run at once — the society's nodes. Each is a separate lineage arriving in the same population |
| `--workers [off\|auto\|N]` | cores **one** search spreads its generations across. Wall clock only. Leave `off` when running several nodes |
| `--max-pop N` | how many bots the society holds (default 200). Intake beyond it culls the worst |
| `--intake N` | how many of each evolution's best enter the society (default 5) |
| `--assess-every N` | how many selections apart the whole-society overview is measured (default 5, 0 never). Output only |
| `--explorers N` | how many nodes start from noise instead of from the society's members (default: a third) |
| `--rattle-after N` | selections the published model may stand still before the society shakes itself (default 40, 0 never) |
| `--rattle-for N` | how many selections one rattle lasts (default 5) |

### `siar-build soc list` · `status SOC` · `genes SOC`

| option | meaning |
|---|---|
| `-t, --target TAG` | (`list`) only societies for this target |
| `--top N` | (`status`) how much of the leaderboard to print |
| `--kind {feature,op,motif,all}` | (`genes`) which grain to print (default `all`) |
| `--sort {frequency,differential}` | (`genes`) what the society holds, commonest first (default), or what its selection is pushing hardest |
| `-n, --limit N` | (`genes`) how many genes to print. 0 prints all |
| `--json` | (`genes`) print the whole count as JSON |

### `siar-build soc share SOC`

| option | meaning |
|---|---|
| `--revoke` | turn the link off. What was published is kept and stops being readable; publishing again revives the same link |
| `--title TEXT` | what to call it on the shared page (default: the society's name) |

### `siar-build soc publish SOC`

`SOC` is a society name **or** a path to a model folder. Asks for the publishing account's own
password rather than using this box's token — publishing is a person's act, not a daemon's.

| option | meaning |
|---|---|
| `--title TEXT` | what to call it in the catalogue. Used only when the model is **new** — editing done on the site is never overwritten |
| `--description TEXT` | what it is for, in a sentence. New models only, as `--title` |
| `--login USER` | the account to publish as (username or email). Defaults to whoever `siar-app login` signed this box in as. Set `$SIAR_PUBLISH_PASSWORD` on a box that must publish unattended |
| `--no-share-link` | do not record which published society this model came out of |

### `siar-build soc stop SOC` · `scan SOC [INPUT]`

| option | meaning |
|---|---|
| `--now` | (`stop`) do not wait for the running searches; their work is lost |
| `-o, --out DIR` | (`scan`) where the scan goes |
| `-k N` | (`scan`) how many members must agree; overrides the calibrated bar |

`pause`, `resume`, `rattle` and `forget` take a society name and no options.

---

## siar-db

```
siar-db [--db PATH] <command> [options]
```

`--db PATH` works on every command and overrides the default database.

| command | what it does |
|---|---|
| `siar-db scan FOLDER` | run the automaton bank over every recording under `FOLDER` and fill the database |
| `siar-db query` | figures for one scan, one recording or one corpus |
| `siar-db select` | narrow the database to a working set and store it under a name |
| `siar-db group` | cluster a stored selection into named similarity families |
| `siar-db print --out DIR` | write a folder per family of a stored grouping |
| `siar-db view` | what is currently selected, and how it grouped |
| `siar-db clear` | forget a stored selection or grouping |
| `siar-db embed` | compute the similarity vectors `group` needs |
| `siar-db runs` | list scans, newest first |
| `siar-db info` | version, workspace paths, machine, and what is in the database |

### `siar-db scan FOLDER`

| option | meaning |
|---|---|
| `--dataset NAME` | name to register the corpus under (default: the folder's name) |
| `--limit N` | stop after N files, for a trial run |
| `--out DIR` | where PNGs and the report go (default `$SIARDB_HOME/runs/run_NNNN`) |
| `--idout` | also write `<out>/ident`, a folder to drop into IDent Dynamics. Copies the audio |
| `--no-png` | skip rendering |
| `--show-mask` | tint surviving cells as well as boxing them |
| `-j, --nodes N` | worker processes. Negative leaves that many cores free; `1` runs inline |
| `--bank NAMES` | which rules to run: `freq`, `time`, `sweep` (default `freq,time`) |
| `--rule SPEC` | add a tuned rule, `[base:]gene=value,...`. Repeatable |
| `--min-cells N` · `--min-frames N` · `--min-bins N` | a flood valve, not a size filter — raise only to stop a rule producing hundreds of thousands of objects per tile |
| `--delta-t SECONDS` | time between frames; sets `--n-fft` and `--hop` to attain it. The grid flag to reach for |
| `--sample-rate HZ` · `--fmin HZ` · `--fmax HZ` · `--bins N` | the band layout audio is resampled and analysed on |
| `--n-fft N` · `--hop N` | override the window and hop derived from `--delta-t` |

**The rule bank is additive.** Every detection is attributed to the rule that made it, so two
rules agreeing on one object leaves two rows — that is corroboration, and collapsing it would
destroy the one signal saying several independent local rules agreed. `scan` prints the bank
before it starts and `query` reports the split by rule afterwards.

**A rule has a minimum duration and it is the thing to check first** when a structure you can see
is not being found. A cell survives by having company at plus and minus one and two probe widths
along time, so the default `time` probe cannot confirm anything shorter than about 1.6 s. Add
`sweep` to the bank for briefer ones; `scan` prints every rule's minimum before it starts.

### `siar-db select` · `group` · `print`

One chain, and each step stores its result, so the next one argues with a set that is not moving
underneath it. `select` takes the descriptor filters (`--min-dur`, `--f-low`, `--f-high`,
`--min-cells` and the rest) and stores the rows that matched; `group` clusters that stored set at a
cosine threshold; `print` renders a stored grouping to a folder per family with a picture of every
member. Re-print at a wider margin without re-clustering, and re-cluster at a lower threshold
without re-reading any audio.

`select` and `list` also take `--shape` and `--rule`, and those are two different questions.
`--rule` is which detector drew the box — `freq`, `time`, `sweep`, whatever the bank held. `--shape`
is what the box turned out to look like, measured from the structure itself: `click`, `tonal`,
`sweep`, `patch` or `blob`. A rule is tuned toward a kind of structure but is not a classifier, so
every rule publishes every shape — a `time` scan of a sonar corpus returns tonals, patches, sweeps
and blobs in one run — and "the tonals the sweep rule found" needs both flags. Repeat either for a
set.

One thing worth knowing about `click`: it means "shorter than 50 ms, and taller than it is wide".
A scan's `--delta-t` sets the shortest structure that can exist — a one-frame box is one frame
long — so a grid coarser than 50 ms can never produce one, whatever is in the audio. The default
0.01 s is well inside it; `--delta-t 0.1`, five times the ceiling, is not. A corpus of clicks that
reports no clicks is usually this and not the recordings.

---

## Licence

`siar-build`, `siar-db` and `brahma-intelligence` are proprietary — Vixen Intelligence. The
`siar-app` command line is MIT; the scanning algorithms it downloads are proprietary and licensed
separately. Each wheel carries its own licence file, and `siar-app license` prints siar-app's.
