import requests
import asyncio
import os
import nest_asyncio  # 🔹 SOLUCIÓN para MacOS
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from dotenv import load_dotenv
from flask import Flask
import threading

# 🔹 Cargar variables de entorno desde .env
nest_asyncio.apply()
load_dotenv()

CHAT_ID = os.getenv("CHAT_ID")
PORT = int(os.getenv("PORT", 5000))  # Si PORT no está definido, usa 8080 por defecto
TOKEN = os.getenv("TOKEN")
API_URL = os.getenv("API_URL")

ALERTA_PRECIO = 4200  # Valor de la alerta por defecto

# 🔹 Iniciar servidor Flask para evitar suspensión en Render
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot del Dólar está activo"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)  # Usamos el puerto 8080

# Iniciar Flask en un hilo separado
flask_thread = threading.Thread(target=run_flask, daemon=True)  # 🔹 Hilo como daemon
flask_thread.start()

# 🔹 FUNCIÓN PARA OBTENER EL PRECIO
async def obtener_precio():
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "conversion_rates" in data and "COP" in data["conversion_rates"]:
            precio_dolar = data["conversion_rates"]["COP"]
            return precio_dolar
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error en la API: {e}")
        return None

# 🔹 COMANDO /PRECIO
async def precio(update: Update, context: CallbackContext) -> None:
    precio_actual = await obtener_precio()
    if precio_actual:
        mensaje = f"📈 Cotización actual del dólar:\n 1 USD = {precio_actual} COP"
    else:
        mensaje = "⚠️ No se pudo obtener la cotización."
    
    await update.message.reply_text(mensaje)

# 🔹 COMANDO /ALERTA
async def alerta(update: Update, context: CallbackContext) -> None:
    try:
        alerta_precio = int(context.args[0])
        global ALERTA_PRECIO
        ALERTA_PRECIO = alerta_precio
        mensaje = f"🔔 Alerta configurada. Te avisaré cuando el dólar llegue a {alerta_precio} COP."
    except (IndexError, ValueError):
        mensaje = "⚠️ Debes indicar un valor numérico para configurar la alerta."
    
    await update.message.reply_text(mensaje)
    
# 🔹 COMANDO /CONVERTIR
async def convertir(update: Update, context: CallbackContext) -> None:
    try:
        cantidad = float(context.args[0])
        precio_actual = await obtener_precio()
        if precio_actual:
            conversion = cantidad * precio_actual
            mensaje = f"💵 {cantidad} USD = {conversion} COP"
        else:
            mensaje = "⚠️ No se pudo obtener la cotización."
    except (IndexError, ValueError):
        mensaje = "⚠️ Debes indicar un valor numérico para convertir."
    
    await update.message.reply_text(mensaje)

# 🔹 COMANDO /AYUDA
async def ayuda(update: Update, context: CallbackContext) -> None:
    mensaje = (
        "👋 ¡Hola! Bienvenido al *Bot del Dólar* 💰.\n\n"
        "Aquí tienes mayor información de los comandos:\n"
        "📌 /precio - Ver la cotización actual del dólar\n"
        "🚨 /alerta - Allí debes digitar el valor que deseas configurar como alerta después del comando (Ej: /alerta 4200)\n"
        "🔄 /convertir USD a COP - Allí debes digitar el valor a convertir después del comando (Ej: /convertir 100)\n"
        "Escribe un comando para comenzar 👇"
    )
    
    await update.message.reply_text(mensaje, parse_mode="Markdown")

# 🔹 FUNCIÓN PARA MONITOREAR Y ENVIAR ALERTA CUANDO LLEGUE A 4200
async def monitorear_precio(app: Application):
    while True:
        precio_actual = await obtener_precio()

        if precio_actual and precio_actual >= ALERTA_PRECIO:
            mensaje_alerta = f"🚨 ¡ALERTA! El dólar ha llegado a {precio_actual} COP. 📊"
            await app.bot.send_message(chat_id=CHAT_ID, text=mensaje_alerta)

        await asyncio.sleep(3600)  # 🔄 Verifica cada 1 hora

# 🔹 COMANDO /START
async def start(update: Update, context: CallbackContext) -> None:
    """Responde con un saludo y muestra las opciones disponibles."""
    mensaje = (
        "👋 ¡Hola! Bienvenido al *Bot del Dólar* 💰.\n\n"
        "Aquí tienes las opciones disponibles:\n"
        "📌 /precio - Ver la cotización actual del dólar\n"
        "🚨 /alerta - Configurar alerta cuando el dólar supere un valor\n"
        "🔄 /convertir USD a COP - Digite el número después del comando\n"
        "ℹ️ /ayuda - Mostrar esta información nuevamente\n\n"
        "Escribe un comando para comenzar 👇"
    )
    
    await update.message.reply_text(mensaje, parse_mode="Markdown")

# 🔹 FUNCIÓN PRINCIPAL
async def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("precio", precio))
    app.add_handler(CommandHandler("alerta", alerta))
    app.add_handler(CommandHandler("convertir", convertir))
    app.add_handler(CommandHandler("ayuda", ayuda))

    print("🤖 Bot iniciado... Monitoreando el dólar 💰")

    # 🔹 Iniciar monitoreo en segundo plano después de `run_polling()`
    async with app:
        asyncio.create_task(monitorear_precio(app))  # 🔹 Tarea en segundo plano
        await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())  # 🔹 Usa asyncio.run() para evitar problemas de event loop
