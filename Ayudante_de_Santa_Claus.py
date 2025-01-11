#!/usr/bin/env python3
# ============================================================
#     🐕 AYUDANTE DE SANTA CLAUS 🐾
# ============================================================
# 📜 Descripción: 
# Bot de Telegram para gestionar el script CocecCrusher.sh
# 
# 🧰 Desarrollado para: Ubuntu Server
# 🚀 Servicios gestionados: CodecCrusher, HandBrakeCLI
# 📬 Notificaciones: Telegram Bot
# 
# Archivo: Ayudante_de_Santa_Claus.py
# Versión: 1.0
# Autor: rogergdev
# ============================================================

import os
import re
import sqlite3
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import asyncio
import psutil
from datetime import datetime, date

closed_message_ids = []

def load_env_from_file():
    env_path = os.path.expanduser("~/.codeccrusher_env")
    if not os.path.isfile(env_path):
        raise FileNotFoundError(f"No se encontró el archivo de entorno: {env_path}")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r'^(?:export\s+)?(\w+)=(["\'])?(.+?)\2$', line)
            if m:
                key, _, val = m.groups()
                os.environ[key] = val

load_env_from_file()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN y/o CHAT_ID no están configurados correctamente.")

DB_FILE = os.path.expanduser("~/codeccrusher.db")
LOG_FILE = os.path.expanduser("~/codeccrusher_logs/transcode.log")

bot = telegram.Bot(token=BOT_TOKEN)

# ============================================================
#                    FUNCIONES DE BBDD
# ============================================================
async def obtener_informe_actual():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM transcodificados WHERE estado='completado'")
    total = cursor.fetchone()[0]
    conn.close()
    return total

async def obtener_informe_diario():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) 
        FROM transcodificados 
        WHERE estado='completado' 
          AND DATE(fecha_transcodificacion) = DATE('now', 'localtime')
    """)
    total_diario = cursor.fetchone()[0]
    conn.close()
    return total_diario

async def obtener_informe_diario_detallado():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
          COUNT(*) as total_archivos,
          SUM(size_original) as suma_original,
          SUM(size_final) as suma_final
        FROM transcodificados 
        WHERE estado='completado' 
          AND DATE(fecha_transcodificacion) = DATE('now', 'localtime')
    """)
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        total_archivos, suma_original, suma_final = resultado
        orig_gb = (suma_original or 0) / (1024**3)
        final_gb = (suma_final or 0) / (1024**3)
        ahorrado_gb = orig_gb - final_gb
        ahorro_total = (ahorrado_gb / orig_gb * 100) if orig_gb != 0 else 0
        return total_archivos, orig_gb, final_gb, ahorrado_gb, ahorro_total
    return 0, 0, 0, 0, 0

async def obtener_informe_total_detallado():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
          COUNT(*) as total_archivos,
          SUM(size_original) as suma_original,
          SUM(size_final) as suma_final
        FROM transcodificados 
        WHERE estado='completado'
    """)
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        total_archivos, suma_original, suma_final = resultado
        orig_gb = (suma_original or 0) / (1024**3)
        final_gb = (suma_final or 0) / (1024**3)
        ahorrado_gb = orig_gb - final_gb
        ahorro_total = (ahorrado_gb / orig_gb * 100) if orig_gb != 0 else 0
        return total_archivos, orig_gb, final_gb, ahorrado_gb, ahorro_total
    return 0, 0, 0, 0, 0

# ============================================================
#               FUNCIONES DE PROGRESO Y SISTEMA
# ============================================================
async def obtener_progreso_y_tiempo():
    """
    Lee el archivo de log para extraer el porcentaje completado y el tiempo restante.
    """
    try:
        with open(LOG_FILE, "r") as log:
            lines = log.readlines()
            # Buscar la última línea que contenga "Encoding:" y "ETA"
            for line in reversed(lines):
                if "Encoding:" in line and "ETA" in line:
                    # Intentar extraer porcentaje y ETA usando una expresión regular flexible
                    match = re.search(r'Encoding: task \d+ of \d+,\s*([\d\.]+) %.*ETA\s*([^\s\]]+)', line)
                    if match:
                        porcentaje = match.group(1)
                        eta = match.group(2)
                        # Eliminar cualquier paréntesis de cierre al final de 'eta'
                        eta = eta.rstrip(")")
                        return porcentaje, eta, ""
            return "N/A", "N/A", ""
    except Exception as e:
        print(f"Error al obtener progreso: {e}")
        return "N/A", "N/A", ""

async def obtener_temperatura():
    temps = psutil.sensors_temperatures()
    if "coretemp" in temps:
        for entry in temps["coretemp"]:
            if entry.label == "Package id 0":
                return f"{entry.current}°C"
    return "N/A"

async def estado_discos():
    rutas = [
        "/media/roger/Disco1", 
        "/media/roger/Disco3", 
        "/media/roger/Disco4", 
        "/mnt/D10TB"
    ]
    resultado = []
    for disco in rutas:
        try:
            uso = psutil.disk_usage(disco)
            resultado.append(f"📂 {os.path.basename(disco)}: {uso.percent}% usado")
        except FileNotFoundError:
            resultado.append(f"📂 {os.path.basename(disco)}: No encontrado")
    return "\n".join(resultado)

async def obtener_info_sistema():
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    ram_percent = mem.percent
    swap = psutil.swap_memory()
    swap_percent = swap.percent
    temperatura = await obtener_temperatura()
    info_str = (
        f"🌡️ *Temperatura CPU:* {temperatura}\n"
        f"🖥 *CPU:* {cpu_percent}%\n"
        f"💾 *RAM:* {ram_percent}%\n"
        f"🔃 *Swap:* {swap_percent}%\n"
    )
    return info_str

async def leer_ultimas_lineas_log(n=5):
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            return "".join(lines[-n:])
    except FileNotFoundError:
        return "No se ha encontrado el archivo de log."

# ============================================================
#                    MENÚS E INTERACCIÓN
# ============================================================
def construir_keyboard_principal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Iniciar", callback_data='iniciar'),
         InlineKeyboardButton("🛑 Detener", callback_data='detener')],
        [InlineKeyboardButton("📊 Informe", callback_data='informe'),
         InlineKeyboardButton("⏳ Progreso", callback_data='progreso')],
        [InlineKeyboardButton("ℹ️ Info Sistema", callback_data='info_sistema')],
        [InlineKeyboardButton("❌ Cerrar menú", callback_data='cerrar')]
    ])

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE, mensaje_extra=""):
    keyboard = construir_keyboard_principal()
    mensaje_base = "🐕* Ayudante de Santa Claus *🐾" if not mensaje_extra else ""
    mensaje = f"{mensaje_extra}\n\n{mensaje_base}" if mensaje_extra else mensaje_base
    try:
        if update.message:
            try:
                await update.message.delete()
            except telegram.error.BadRequest:
                pass
            await update.message.reply_text(mensaje, parse_mode="Markdown", reply_markup=keyboard)
        else:
            query = update.callback_query
            await query.edit_message_text(text=mensaje, parse_mode="Markdown", reply_markup=keyboard)
    except telegram.error.BadRequest:
        pass

async def configuracion_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Reiniciar servicio", callback_data='reiniciar'),
         InlineKeyboardButton("🛑 Detener servicio", callback_data='detener_servicio')],
        [InlineKeyboardButton("⬅️ Volver", callback_data='volver_menu_principal')]
    ])
    mensaje = "⚙️ *Configuración de CodecCrusher*\nSelecciona una opción:"
    query = update.callback_query
    try:
        await query.edit_message_text(text=mensaje, parse_mode="Markdown", reply_markup=keyboard)
    except telegram.error.BadRequest:
        pass

async def informe_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Informe diario", callback_data='informe_diario'),
         InlineKeyboardButton("📂 Informe total", callback_data='informe_total')],
        [InlineKeyboardButton("👀 Ver últimos logs", callback_data='ver_logs')],
        [InlineKeyboardButton("⬅️ Volver", callback_data='volver_menu_principal')]
    ])
    mensaje = "📊 *Informe de CodecCrusher:*"
    query = update.callback_query
    try:
        await query.edit_message_text(text=mensaje, parse_mode="Markdown", reply_markup=keyboard)
    except telegram.error.BadRequest:
        pass

async def actualizar_informe_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, mensaje_extra=""):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Informe diario", callback_data='informe_diario'),
         InlineKeyboardButton("📂 Informe total", callback_data='informe_total')],
        [InlineKeyboardButton("👀 Ver últimos logs", callback_data='ver_logs')],
        [InlineKeyboardButton("⬅️ Volver", callback_data='volver_menu_principal')]
    ])
    mensaje = mensaje_extra if mensaje_extra else ""
    query = update.callback_query
    try:
        await query.edit_message_text(text=mensaje, parse_mode="Markdown", reply_markup=keyboard)
    except telegram.error.BadRequest:
        pass

# ============================================================
#                    MANEJO DE BOTONES
# ============================================================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "iniciar":
        os.system("sudo /usr/bin/systemctl start codeccrusher.service")
        await menu_principal(update, context, mensaje_extra="▶️ *CodecCrusher iniciado.*")

    elif data == "detener":
        os.system("sudo /usr/bin/systemctl stop codeccrusher.service")
        await menu_principal(update, context, mensaje_extra="🛑 *CodecCrusher detenido.*")

    elif data == "informe":
        await informe_menu(update, context)

    elif data == "progreso":
        # Obtención de datos de progreso
        porcentaje, eta, _ = await obtener_progreso_y_tiempo()
        
        # Preparar valores en negrita
        porcentaje_formateado = f"**{porcentaje}%**"
        tiempo_formateado = f"**{eta}**"
        
        info = (
            f"🎞️ Completado: {porcentaje_formateado}\n"
            f"⏳ Tiempo restante: {tiempo_formateado}"
        )
        await menu_principal(update, context, mensaje_extra=info)

    elif data == "configuracion":
        await configuracion_menu(update, context)

    elif data == "info_sistema":
        try:
            await query.edit_message_text(text="⏳ Obteniendo información del sistema...", parse_mode="Markdown")
        except telegram.error.BadRequest:
            pass
        info = await obtener_info_sistema()
        await menu_principal(update, context, mensaje_extra=info)

    elif data == "cerrar":
        try:
            # En lugar de enviar un mensaje, simplemente cerramos el menú sin notificación
            await query.delete_message()
        except telegram.error.BadRequest:
            pass

    elif data == "reiniciar":
        os.system("sudo systemctl.restart codeccrusher.service")
        await configuracion_menu(update, context)

    elif data == "detener_servicio":
        os.system("sudo systemctl.stop codeccrusher.service")
        await configuracion_menu(update, context)

    elif data == "volver_menu_principal":
        await menu_principal(update, context)

    elif data == "informe_diario":
        try:
            total_archivos, orig_gb, final_gb, ahorrado_gb, ahorro_total = await obtener_informe_diario_detallado()
            informe = f"📅 *Archivos transcodificados hoy:* {total_archivos}\n"
            informe += f"📏 *Tamaño original total:* {orig_gb:.2f} GB\n"
            informe += f"📏 *Tamaño final total:* {final_gb:.2f} GB\n"
            informe += f"💾 *Espacio ahorrado:* {ahorrado_gb:.2f} GB\n"
            informe += f"🔻 *Ahorro total:* {ahorro_total:.2f}%\n"
        except sqlite3.OperationalError:
            informe = "Error al obtener los datos detallados."
        await actualizar_informe_menu(update, context, mensaje_extra=informe)

    elif data == "informe_total":
        try:
            total_archivos, orig_gb, final_gb, ahorrado_gb, ahorro_total = await obtener_informe_total_detallado()
            informe = f"📂 *Archivos transcodificados (total):* {total_archivos}\n"
            informe += f"📏 *Tamaño original total:* {orig_gb:.2f} GB\n"
            informe += f"📏 *Tamaño final total:* {final_gb:.2f} GB\n"
            informe += f"💾 *Espacio ahorrado:* {ahorrado_gb:.2f} GB\n"
            informe += f"🔻 *Ahorro total:* {ahorro_total:.2f}%\n"
        except sqlite3.OperationalError:
            informe = "Error al obtener los datos detallados."
        await actualizar_informe_menu(update, context, mensaje_extra=informe)

    elif data == "ver_logs":
        ult_lines = await leer_ultimas_lineas_log(n=5)
        ult_lines_escaped = ult_lines.replace(".", "\.").replace("-", "\-")
        info = f"📜 *Últimas líneas del log:*\n\n```\n{ult_lines_escaped}\n```"
        await actualizar_informe_menu(update, context, mensaje_extra=info)

    else:
        try:
            await query.edit_message_text(text="Opción no reconocida.", parse_mode="Markdown")
        except telegram.error.BadRequest:
            pass

# ============================================================
#                    INICIALIZACIÓN DEL BOT
# ============================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for msg_id in closed_message_ids:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
        except telegram.error.BadRequest:
            pass
    closed_message_ids.clear()
    await menu_principal(update, context)

application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler('start', start_command))
application.add_handler(CallbackQueryHandler(button))

if __name__ == "__main__":
    asyncio.run(application.run_polling())
