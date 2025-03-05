import requests
import asyncio
import time
import os
import nest_asyncio  # 🔹 SOLUCIÓN para MacOS
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

nest_asyncio.apply()
CHAT_ID = "1117095261"  # ID del chat donde enviará las alertas

PORT = int(os.environ.get("PORT", 8080))  # Usa el puerto de Render o 8080 por defecto

# 🔹 TOKEN de tu bot de Telegram
TOKEN = "7846162619:AAH6NWIhnJ95uGjAABT1Y3z-0iK_t-ZoDaY"

# 🔹 URL de la API del exchange (ajústala según tu proveedor)
API_URL = "https://v6.exchangerate-api.com/v6/be19caf6019774a23fc2850b/latest/USD" 

ALERTA_PRECIO = 4200  # Valor de la alerta por defecto

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
        "🚨 /alerta - Allí debes digitar el valor que deseas configurar como alerta después del comando(Ejm: /alerta 4200 *Enviar \n"
        "🔄 /convertir USD a COP - Allí debes digitar el valora convertir después del comando(Ejm: /convertir 100 *Enviar \n"
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

async def start(update: Update, context: CallbackContext) -> None:
    """Responde con un saludo y muestra las opciones disponibles."""
    mensaje = (
        "👋 ¡Hola! Bienvenido al *Bot del Dólar* 💰.\n\n"
        "Aquí tienes las opciones disponibles:\n"
        "📌 /precio - Ver la cotización actual del dólar\n"
        "🚨 /alerta - Configurar alerta cuando el dólar supere un valor\n"
        "🔄 /convertir USD a COP - Digite el número despues del comando\n"
        "ℹ️ /ayuda - Mostrar esta información nuevamente\n\n"
        "Escribe un comando para comenzar 👇"
    )
    
    await update.message.reply_text(mensaje, parse_mode="Markdown")

def keep_alive():
    while True:
        requests.get("https://botpythonexchangepython3-bot-py.onrender.com")
        time.sleep(600)  # Pingea cada 10 minutos

from threading import Thread
Thread(target=keep_alive).start()


# 🔹 FUNCIÓN PRINCIPAL
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))  # 🔹 Mensaje de bienvenida
    app.add_handler(CommandHandler("precio", precio))
    app.add_handler(CommandHandler("alerta", alerta))
    app.add_handler(CommandHandler("convertir", convertir))
    app.add_handler(CommandHandler("ayuda", ayuda))

    print("🤖 Bot iniciado... Monitoreando el dólar 💰")
    asyncio.create_task(monitorear_precio(app))  # 🔄 Activar monitoreo automático
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())  # ✅ Usa `asyncio.run()` sin `loop.close()`
    except RuntimeError:
        pass  # 🔹 Evita el error de "Cannot close a running event loop"