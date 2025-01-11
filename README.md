
# 🐕 Ayudante de Santa Claus 🐾

![image](https://github.com/user-attachments/assets/3c6901f2-f46e-4837-86bf-441a53133245)


## 📜 Descripción
El **Ayudante de Santa Claus** es un bot de Telegram diseñado para gestionar el script de transcodificación **CodecCrusher.sh**. 
Este bot permite interactuar con el servidor mediante comandos y menús , proporcionando información en tiempo real sobre el estado de los servicios y recursos del sistema.

## 🚀 Funcionalidades
- ✅ Iniciar y detener el servicio **CodecCrusher**.
- 📊 Obtener informes diarios y totales de transcodificaciones completadas.
- ⏳ Consultar el progreso de la transcodificación en curso.
- 💻 Mostrar información del sistema (CPU, RAM, Swap, temperatura).
- 📂 Ver el estado de los discos conectados.
- 📜 Leer las últimas líneas del archivo de log de transcodificación.
- 📬 Enviar notificaciones a través de Telegram.

---

## 🧰 Requisitos
- Ubuntu Server
- Python 3
- Biblioteca de Telegram (`python-telegram-bot`)
- Psutil (`psutil`)
- Archivo de entorno con las variables `BOT_TOKEN` y `CHAT_ID`:

```env
# ~/.codeccrusher_env
export BOT_TOKEN="<tu_token_de_telegram>"
export CHAT_ID="<tu_chat_id_de_telegram>"
```

---

## 📦 Instalación
### 1️⃣ Clonar el script en la ruta `/usr/local/bin`
```bash
sudo cp Ayudante_de_Santa_Claus.py /usr/local/bin
```

### 2️⃣ Hacer ejecutable el script
```bash
sudo chmod +x /usr/local/bin/Ayudante_de_Santa_Claus.py
```

### 3️⃣ Crear el archivo de entorno con las variables de configuración
```bash
nano ~/.codeccrusher_env
```
Agrega:
```env
export BOT_TOKEN="<tu_token_de_telegram>"
export CHAT_ID="<tu_chat_id_de_telegram>"
```
Guarda y cierra el archivo.

### 4️⃣ Crear el servicio systemd
```bash
sudo nano /etc/systemd/system/ayudante_de_santa.service
```

Pega el siguiente contenido:
```ini
[Unit]
Description=Ayudante de Santa Claus
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/bin/Ayudante_de_Santa_Claus.py
WorkingDirectory=/usr/local/bin
Environment="PATH=/usr/bin:/usr/local/bin"
Restart=always
RestartSec=5
User=TU_USUARIO

[Install]
WantedBy=multi-user.target
```

Guarda y cierra el archivo.

### 5️⃣ Recargar systemd y habilitar el servicio
```bash
sudo systemctl daemon-reload
sudo systemctl enable ayudante_de_santa.service
```

### 6️⃣ Iniciar el servicio
```bash
sudo systemctl start ayudante_de_santa.service
```

---

## 📋 Comandos disponibles en el bot
- **/start**: Inicia el bot y muestra el menú principal.
- **Botones del menú principal**:
  - ▶️ **Iniciar**: Inicia el servicio CodecCrusher.
  - 🛑 **Detener**: Detiene el servicio CodecCrusher.
  - 📊 **Informe**: Muestra los informes diarios y totales de transcodificaciones.
  - ⏳ **Progreso**: Muestra el progreso y el tiempo restante de la transcodificación en curso.
  - ℹ️ **Info Sistema**: Muestra información del sistema (CPU, RAM, Swap, temperatura).
  - ❌ **Cerrar menú**: Cierra el menú interactivo.

---

## 📂 Estructura de la base de datos SQLite
El bot utiliza una base de datos SQLite para registrar los archivos transcodificados.

- **Nombre de la base de datos**: `codeccrusher.db`
- **Tabla**: `transcodificados`
  - `archivo` (TEXT, clave primaria)
  - `fecha_transcodificacion` (TEXT)
  - `estado` (TEXT, valor por defecto 'en proceso')

---

## 📜 Logs
El bot lee el archivo de log generado por el proceso de transcodificación.
- **Ruta del log**: `~/codeccrusher_logs/transcode.log`

---

## 🔧 Comprobación del servicio
Verifica que el servicio esté activo:
```bash
sudo systemctl status ayudante_de_santa.service
```

Ver los logs del servicio en tiempo real:
```bash
sudo journalctl -u ayudante_de_santa.service -f
```

---

## 🤖 Créditos
- **Versión**: 1.0
- **Autor**: rogergdev

---

## ℹ️ Configuración del menú de comandos en Telegram
Para tener el menú de comandos disponible de forma accesible en el bot, utiliza /setcommands en el BotFather de Telegram y añade el siguiente comando (pégalo en el Botfather exactamente):
```bash
start - Inicia el bot y muestra el menú principal
```
![image](https://github.com/user-attachments/assets/1c8b1986-4f7e-46cb-baff-ecbd96c4f77a)
