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
  --help  Show this message and exit.

Commands:
  render instance INSTANCE_ID [OUTPUT_PATH]

```

For example, Basic authorization with user `demo` and password `demo`
could be set with:

```
export CAMUNDA_AUTHORIZATION="Basic ZGVtbzpkZW1v"
```
