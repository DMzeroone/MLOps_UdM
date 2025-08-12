## Herramientas: Editor, Linters, Formateadores, Pre-commit

### Editor (VS Code recomendado)

- Instala VS Code: `https://code.visualstudio.com/`
- Extensiones recomendadas:
  - Python (ms-python.python)
  - Pylance (ms-python.vscode-pylance)
  - Ruff (charliermarsh.ruff)
  - Black Formatter (ms-python.black-formatter)

### Ruff y Black

Con uv:

```bash
uv add --dev ruff black
uv run ruff --version
uv run black --version

# Comprobar formato y lint
uv run ruff check .
uv run black --check .
```

Con Poetry:

```bash
poetry add -G dev ruff black
poetry run ruff check .
poetry run black --check .
```

### Hooks de pre-commit

1) Copia la plantilla a la raíz del proyecto:

```bash
cp 00-Setup/templates/pre-commit-config.yaml .pre-commit-config.yaml
```

2) Instala pre-commit en tu entorno y habilita los hooks:

- uv:

```bash
uv add --dev pre-commit
uv run pre-commit install
```

- Poetry:

```bash
poetry add -G dev pre-commit
poetry run pre-commit install
```

3) Ejecuta los hooks manualmente (opcional):

```bash
pre-commit run --all-files
```

Los hooks se ejecutarán automáticamente en cada commit y mantendrán tu código limpio y consistente.
