# ccli

A placeholder project for to be opinionated Camunda Platform 7 CLI.


## Requirements

Use of `ccli` to render BPMN diagrams require NodeJS (`node`) and Chrome
(`chrome`) or Chromium (`chromium`) browser on the current system path.


## Usage

```

Usage: ccli [OPTIONS] COMMAND [ARGS]...

  Opinionated Camunda Platform 7 CLI

Options:
  --url TEXT            Set Camunda REST API base URL (env: CAMUNDA_URL).
  --authorization TEXT  Set Authorization header (env: CAMUNDA_AUTHORIZATION).
  --help                Show this message and exit.

Commands:
  render instance INSTANCE_ID [OUTPUT_PATH]

```

For example, Basic authorization with user `demo` and password `demo`
could be set with:

```
export CAMUNDA_AUTHORIZATION="Basic ZGVtbzpkZW1v"
```


## Usage with RCC

If you already have Chrome or Chromium, there is a good chance to get `ccli` running
also with [Robocorp RCC](https://downloads.robocorp.com/rcc/releases/index.html), with
the following `conda.yaml`:

```yaml
channels:
  - conda-forge

dependencies:
  - nodejs
  - python
  - pip
  - pip:
    - cmndseven-cli==0.2.1
```

`robot.yaml`:

```yaml
tasks:
  ccli:
    shell: ccli
condaConfigFile: conda.yaml
artifactsDir: .
```

And then:

```
rcc --silent run -- --help
```

## Usage with Nix

Also works with Nix:

```
nix run github:datakurre/cmndseven-cli -- --help
```
