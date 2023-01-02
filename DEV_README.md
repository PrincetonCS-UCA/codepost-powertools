# codePost Powertools Development

## Dependencies

This project uses [Poetry](https://python-poetry.org/) to manage dependencies,
virtual environments, builds, and packaging. Install it by following the
instructions [here](https://python-poetry.org/docs/#installation).

## Development

Setup:

1. Clone the repo:
   ```bash
   $ git clone https://github.com/PrincetonCS-UCA/codepost-powertools.git
   $ cd codepost-powertools
   ```
   or pull if you already have a local copy.
2. Create/update the virtual environment with Poetry:
   ```bash
   $ poetry install
   ```
   If editing the docs, be sure to include the optional `docs` group:
   ```bash
   $ poetry install --with docs
   ```

To run the powertools CLI, use the following command:

```bash
$ poetry run cptools ...
```

Remember to prefix `poetry run` for any commands that require the virtual
environment.
