# Guia resumen para tener seteado el ambiente para el curso

## Git y GitHub: Instalar, Configurar y Colaborar

### 1) Instalar Git

- Windows:
  - Seguir la guia de: <https://git-scm.com/downloads/win>
  
Verificar:

```bash
git --version
```

### 2) Configurar Git (identidad y valores por defecto)

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 3) Crear repositorio en github, o clonarlo si ya existe

### 4) Clonar el repositorio y configurar remotos

```bash
# Clona tu repo
git clone git@github.com:<your-username>/<repo-name>.git
cd <repo-name>
```

### 5) Flujo de trabajo diario

```bash
# Crea una rama para tu trabajo
git checkout -b feature/my-topic

# Realiza tus cambios, añade y commitea
git add -A
git commit -m "Add: tutorial for X"


# Haz push a tu repo
git push -u origin feature/my-topic

# trae los últimos cambios del repositorio
git pull
```

## Pyenv y uv

### 1) Instalar Python 3.11+ (recomendado 3.11)

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

- Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Crear y activar un entorno virtual (siempre dentro de la carpeta del repositorio):

```bash
uv venv
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

Si el proyecto es nuevo para usar uv por primera vez debemos correr:

```bash
uv sync
```

Añadir dependencias corremos:

```bash
uv add numpy
```

Podemos añadir varias a la vez:

```bash
uv add numpy pandas scikit-learn matplotlib seaborn
```

Instalar dependencias en nuestro equipo si existe `pyproject.toml`, también sirve para actualizar:

```bash
uv sync
```

### 3) venv integrado (opción alternativa) --> no recomendada

```bash
python -m venv .venv
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Inside the venv, use pip
pip install -U pip
pip install -r requirements.txt  # if provided
```

### 4) Guía rápida de activación

- Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
