# 🚕 NYC Taxi Duration Prediction - Guía de Despliegue

Esta guía te ayudará a desplegar el servicio de predicción de duración de viajes de taxi de NYC paso a paso.

## 📋 Tabla de Contenidos

- [Prerequisitos](#prerequisitos)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
- [Configuración del Entorno](#configuración-del-entorno)
- [Despliegue Local](#despliegue-local)
- [Pruebas del Servicio](#pruebas-del-servicio)
- [Monitoreo](#monitoreo)
- [Troubleshooting](#troubleshooting)
- [Despliegue en Producción](#despliegue-en-producción)

## 🔧 Prerequisitos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.8+**
- **uv** (gestor de paquetes y entornos virtuales moderno)
- **Git** (para clonar el repositorio)
- **curl** (para probar los endpoints)

### Verificar Instalaciones

```bash
# Verificar Python
python --version
# o
python3 --version

# Verificar uv
uv --version

# Verificar Git
git --version

# Verificar curl
curl --version
```

### Instalar uv (si no lo tienes)

```bash
# En macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# En Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Con pip (alternativa)
pip install uv
```

## 📁 Estructura del Proyecto

```
04-Deployment/deploy/web-service/
├── README.md              # Esta guía
├── pyproject.toml         # Configuración uv y dependencias
├── .python-version        # Versión de Python del proyecto
├── predict.py             # Servicio Flask principal
├── predict_test.py        # Módulo de testing sin servidor
├── test.py               # Cliente de pruebas HTTP
├── lin_reg.bin           # Modelo entrenado (pickle)
├── main.py               # Punto de entrada alternativo
└── .venv/                # Entorno virtual (creado automáticamente)
```

## 🚀 Instalación

### Paso 1: Navegar al Directorio del Proyecto

```bash
# Navegar al directorio web-service
cd /Users/mdurango/University/MLOps/04-Deployment/deploy/web-service/
```

### Paso 2: El Entorno ya está Configurado

El proyecto ya tiene configurado un entorno uv independiente con:
- **pyproject.toml** - Configuración del proyecto y dependencias
- **Entorno virtual** - Se crea automáticamente al ejecutar comandos
- **Dependencias instaladas** - Flask, scikit-learn, pandas, numpy, requests, gunicorn

### Paso 3: Verificar la Configuración

```bash
# Verificar que uv detecta el proyecto
uv info

# Ver dependencias instaladas
uv tree
```

### Instalar Dependencias Adicionales (si es necesario)

```bash
# Agregar nuevas dependencias
uv add <package-name>

# Instalar dependencias de desarrollo
uv add --dev pytest black flake8

# Instalar para producción
uv add gunicorn
```

### Ejecutar Comandos en el Entorno

```bash
# Ejecutar cualquier comando Python con uv
uv run python predict.py

# Ejecutar scripts directamente
uv run python test.py

# Ver información del proyecto
uv info
```

## ⚙️ Configuración del Entorno

### Verificar el Proyecto uv

```bash
# Ver información del proyecto
uv info

# Ver dependencias instaladas
uv tree

# Ver archivos del proyecto
ls -la
```

### Verificar el Modelo

Asegúrate de que el archivo `lin_reg.bin` esté presente:

```bash
# Verificar que el modelo existe
ls -la lin_reg.bin

# Si el archivo existe, deberías ver algo como:
# -rw-r--r-- 1 user user 411363 fecha lin_reg.bin
```

### Probar la Carga del Modelo

```bash
# Ejecutar prueba directa del modelo
uv run python predict_test.py
```

**Salida esperada:**

```
INFO:__main__:🔄 Loading model and DictVectorizer for testing...
INFO:__main__:✅ Model and DV loaded successfully
INFO:__main__:🧪 Running prediction test...
INFO:__main__:✅ Features prepared for testing: PU_DO=161_236, distance=2.5
INFO:__main__:🎯 Testing prediction made: 12.34 minutes
INFO:__main__:📊 Test result:
INFO:__main__:   Origin: 161
INFO:__main__:   Destination: 236
INFO:__main__:   Distance: 2.5 miles
INFO:__main__:   Predicted duration: 12.34 minutes
```

## 🌐 Despliegue Local

### Método 1: Ejecutar el Servidor Flask

```bash
# Ejecutar el servidor principal
uv run python predict.py
```

**Salida esperada:**

```
INFO:__main__:🔄 Loading model and DictVectorizer...
INFO:__main__:✅ Model and DV loaded successfully
INFO:__main__:🚀 Starting Flask server on port 9696...
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:9696
 * Running on http://[tu-ip]:9696
```

### Método 2: Usando Flask CLI

```bash
# Configurar variables de entorno
export FLASK_APP=predict.py
export FLASK_ENV=development

# Ejecutar servidor
flask run --host=0.0.0.0 --port=9696
```

### Método 3: Usando Gunicorn (Producción)

```bash
# Instalar Gunicorn
uv add gunicorn

# Ejecutar con Gunicorn
uv run gunicorn --bind 0.0.0.0:9696 --workers 4 predict:app
```

## 🧪 Pruebas del Servicio

### Prueba 1: Health Check

```bash
# Verificar que el servicio está funcionando
curl http://localhost:9696/health
```

**Respuesta esperada:**

```json
{
  "dv_loaded": true,
  "model_loaded": true,
  "service": "NYC Taxi Duration Prediction",
  "status": "healthy"
}
```

### Prueba 2: Predicción Simple

```bash
# Hacer una predicción
curl -X POST http://localhost:9696/predict \
  -H "Content-Type: application/json" \
  -d '{
    "PULocationID": 161,
    "DOLocationID": 236,
    "trip_distance": 2.5
  }'
```

**Respuesta esperada:**

```json
{
  "duration": 12.34,
  "pickup_location": 161,
  "dropoff_location": 236,
  "trip_distance": 2.5
}
```

### Prueba 3: Suite Completa de Pruebas

```bash
# Ejecutar cliente de pruebas automatizado
uv run python test.py
```

**Salida esperada:**

```
INFO:__main__:🚀 Starting test client for NYC Taxi API...
INFO:__main__:🧪 Starting comprehensive test suite...

INFO:__main__:1️⃣ Testing Health Check...
INFO:__main__:🏥 Checking health endpoint at http://localhost:9696/health
INFO:__main__:✅ Service healthy!

INFO:__main__:2️⃣ Testing basic prediction...
INFO:__main__:🚕 Sending test request to http://localhost:9696/predict
INFO:__main__:✅ Request successful!
INFO:__main__:📈 Predicted duration: 12.34 minutes

INFO:__main__:3️⃣ Testing edge cases...
INFO:__main__:   🔍 Case: Short trip
INFO:__main__:   ✅ Short trip: 8.45 minutes
INFO:__main__:   🔍 Case: Long trip
INFO:__main__:   ✅ Long trip: 45.67 minutes

INFO:__main__:🎉 Test suite completed!
```

## 📊 Monitoreo

### Logs del Servidor

Los logs aparecerán en la consola donde ejecutaste el servidor:

```
INFO:__main__:🚕 New prediction: 161 -> 236
INFO:__main__:✅ Features prepared: PU_DO=161_236, distance=2.5
INFO:__main__:🎯 Prediction made: 12.34 minutes
INFO:__main__:✅ Response sent: 12.34 minutes
```

### Endpoints Disponibles


| Endpoint   | Método | Descripción                  |
| ---------- | ------- | ----------------------------- |
| `/health`  | GET     | Verificar estado del servicio |
| `/predict` | POST    | Realizar predicción          |

### Formato de Request para `/predict`

```json
{
  "PULocationID": 161,      // ID de zona de recogida (1-263)
  "DOLocationID": 236,      // ID de zona de destino (1-263)
  "trip_distance": 2.5      // Distancia en millas
}
```

### Formato de Response

```json
{
  "duration": 12.34,        // Duración predicha en minutos
  "pickup_location": 161,   // Zona de recogida
  "dropoff_location": 236,  // Zona de destino
  "trip_distance": 2.5      // Distancia del viaje
}
```

## 🔧 Troubleshooting

### Problema 1: "lin_reg.bin file not found"

**Síntomas:**

```
ERROR:__main__:❌ Error: lin_reg.bin file not found
```

**Solución:**

```bash
# Verificar que el archivo existe en el directorio correcto
ls -la lin_reg.bin

# Si no existe, necesitas entrenar el modelo primero
# o copiar el archivo desde otro directorio
```

### Problema 2: "Port already in use"

**Síntomas:**

```
OSError: [Errno 48] Address already in use
```

**Solución:**

```bash
# Encontrar el proceso usando el puerto 9696
lsof -i :9696

# Terminar el proceso
kill -9 <PID>

# O usar un puerto diferente
python predict.py --port 9697
```

### Problema 3: Errores de Dependencias

**Síntomas:**

```
ModuleNotFoundError: No module named 'flask'
```

**Solución:**

```bash
# Verificar que el entorno virtual está activado
which python

# Reinstalar dependencias
pip install -r requirements.txt
```

### Problema 4: Errores de Predicción

**Síntomas:**

```json
{
  "error": "Missing required field: PULocationID"
}
```

**Solución:**

- Verificar que el JSON incluye todos los campos requeridos
- Verificar el Content-Type header: `application/json`
- Verificar que los valores son del tipo correcto (int/float)

## 🚀 Despliegue en Producción

### Opción 1: Docker

```bash
# Crear Dockerfile
cat > Dockerfile << EOF
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 9696

CMD ["gunicorn", "--bind", "0.0.0.0:9696", "--workers", "4", "predict:app"]
EOF

# Construir imagen
docker build -t taxi-prediction .

# Ejecutar contenedor
docker run -p 9696:9696 taxi-prediction
```

### Opción 2: Heroku

```bash
# Crear Procfile
echo "web: gunicorn predict:app" > Procfile

# Crear runtime.txt
echo "python-3.9.16" > runtime.txt

# Deploy a Heroku
heroku create tu-app-name
git add .
git commit -m "Deploy taxi prediction service"
git push heroku main
```

### Opción 3: AWS EC2

```bash
# En tu instancia EC2
sudo apt update
sudo apt install python3-pip
pip3 install -r requirements.txt

# Usar systemd para mantener el servicio corriendo
sudo nano /etc/systemd/system/taxi-prediction.service
```

### Variables de Entorno para Producción

```bash
# Configurar variables de entorno
export FLASK_ENV=production
export MODEL_PATH=/path/to/lin_reg.bin
export PORT=9696
export WORKERS=4
```

## 📚 Recursos Adicionales

### Comandos Útiles

```bash
# Ver procesos de Python
ps aux | grep python

# Monitorear logs en tiempo real
tail -f /var/log/taxi-prediction.log

# Verificar uso de memoria
htop

# Hacer múltiples requests de prueba
for i in {1..10}; do curl -X POST http://localhost:9696/predict -H "Content-Type: application/json" -d '{"PULocationID": 161, "DOLocationID": 236, "trip_distance": 2.5}'; done
```

### Mejores Prácticas

1. **Siempre usar entornos virtuales**
2. **Validar datos de entrada**
3. **Implementar logging adecuado**
4. **Usar HTTPS en producción**
5. **Implementar rate limiting**
6. **Monitorear métricas de performance**

### Próximos Pasos

* Implementar autenticación (capas de seguridad)
* Generar board con métricas del sistema (cantidad de instancias, responses, memoria, tiempos de respuesta) - [DataDog](https://docs.datadoghq.com/es/getting_started/application/)

* Agregar tests unitarios

* Configurar CI/CD pipeline

## 🆘 Soporte

Si tienes problemas:

1. **Revisa los logs** del servidor
2. **Verifica las dependencias** están instaladas
3. **Confirma que el modelo** se carga correctamente
4. **Prueba con curl** antes de usar clientes complejos
5. **Consulta la documentación** de Flask si es necesario

**¡Felicidades! 🎉 Tu servicio de predicción de taxi está listo para usar.**

Para más información sobre MLOps y despliegue de modelos, consulta la documentación de teo y yo hemos preparado para ti.
