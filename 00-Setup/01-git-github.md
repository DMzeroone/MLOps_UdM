## Git y GitHub: Instalar, Configurar y Colaborar

### 1) Instalar Git

- macOS:
  - Preferido: `brew install git`
  - O: `xcode-select --install` para obtener el Git de Apple
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

### 3) Configurar claves SSH para GitHub

Generar una nueva clave (ed25519):

```bash
ssh-keygen -t ed25519 -C "you@example.com"
# Press Enter to accept default path, set a passphrase if you want
```

Añadir tu clave al agente SSH:

- macOS:

```bash
eval "$(ssh-agent -s)"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

- Windows (PowerShell):

```powershell
# Set the sshd service to be started automatically.
Get-Service -Name sshd | Set-Service -StartupType Automatic

# Start the sshd service.
Start-Service sshd
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

Copia la clave pública y añádela en GitHub → Settings → SSH and GPG keys:

- macOS:

```bash
pbcopy < ~/.ssh/id_ed25519.pub
```

- Windows (PowerShell):

```powershell
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
# Copy the output manually
```

Probar el acceso por SSH:

```bash
ssh -T git@github.com
```

### 4) Clonar el repositorio y configurar remotos

```bash
# Clona tu fork
git clone git@github.com:<your-username>/<repo-name>.git
cd <repo-name>


### 5) Flujo de trabajo diario

```bash
# Crea una rama para tu trabajo
git checkout -b feature/my-topic

# Realiza tus cambios, añade y commitea
git add -A
git commit -m "Add: tutorial for X"

# Actualiza tu rama con los últimos cambios de main
git fetch upstream
git rebase upstream/main

# Haz push a tu fork
git push -u origin feature/my-topic
```

Abre un Pull Request en GitHub desde tu rama hacia `main`.

### 6) Resolución de problemas comunes

- Permiso SSH denegado: verifica que tu clave esté añadida al agente y a GitHub; ejecuta `ssh -T git@github.com`.
- Errores por saltos de línea en Windows: asegúrate de `core.autocrlf true` y usa PowerShell para scripts `.ps1`.
- Tu rama está desactualizada: ejecuta `git fetch upstream && git rebase upstream/main`.
