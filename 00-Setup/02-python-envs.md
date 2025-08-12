## Python y Entornos Virtuales (uv, venv, Poetry)

### 1) Instalar Python 3.11+ (recomendado 3.11)

- macOS (recomendado: pyenv):

```bash
brew update
brew install pyenv
brew install pyenv-virtualenv  # opcional, para gestionar entornos

# Configura tu shell (zsh)
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.zshrc  # si instalaste pyenv-virtualenv
exec "$SHELL"

# Instala y selecciona una versión de Python
pyenv install 3.11.9
pyenv global 3.11.9           # versión por defecto a nivel de usuario

# Dentro del repositorio del curso (local a la carpeta)
pyenv local 3.11.9
python -V
```

- Windows (PowerShell):

```powershell
#(pyenv-win): administrar múltiples versiones
winget install pyenv-win.pyenv-win 

# Cierra y abre la terminal, luego:
pyenv install 3.11.9
pyenv global 3.11.9
# Dentro del repositorio del curso
pyenv local 3.11.9
python -V
```

Verificar:

```bash
python -V
```

### 2) uv: empaquetado de Python rápido y moderno

Instalar uv:

- macOS/Linux:

```bash
brew install uv
```

- Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Crear y activar un entorno virtual:

```bash
uv venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

Instalar dependencias si existe `pyproject.toml`:

```bash
uv sync
```

Añadir una dependencia:

```bash
uv add numpy
```

### 3) venv integrado (opción alternativa)

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Inside the venv, use pip
pip install -U pip
pip install -r requirements.txt  # if provided
```

### 4) Poetry (alternativa a uv)

Instalar Poetry:

- macOS/Linux:

```bash
brew install poetry
exec "$SHELL"
```

- Windows (PowerShell):

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Crear/activar entorno e instalar:

```bash
poetry --version
poetry env use python
poetry install --no-root

# Run commands inside the Poetry env
poetry run python -V
poetry add numpy
```

### 5) Guía rápida de activación

- macOS/Linux (bash/zsh): `source .venv/bin/activate`
- Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
- Windows (Cmd): `\.venv\Scripts\activate.bat`
- Poetry: antepone los comandos con `poetry run ...` o usa `poetry shell`
