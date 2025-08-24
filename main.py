import random
import asyncio
import aiohttp
import aiofiles
import os
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# === Configuración Twitch ===
TOKEN_TWITCH = os.getenv("TOKEN_TWITCH")
CLIENT_ID_TWITCH = os.getenv("CLIENT_ID_TWITCH")
BEARER_TWITCH = os.getenv("BEARER_TWITCH")
BROADCASTER_ID = os.getenv("BROADCASTER_ID")
SENDER_ID = os.getenv("SENDER_ID")
JUEGO = os.getenv("JUEGO")
personajes = os.getenv("PERSONAJES")

# === Configuración OpenAI ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SYSTEM_CONTEXT_TEMPLATE = os.getenv("SYSTEM_CONTEXT")
USER_CONTEXT_TEMPLATE = os.getenv("USER_CONTEXT")
client = OpenAI(api_key=OPENAI_API_KEY)

url = "https://api.twitch.tv/helix/chat/messages"

headers = {
    "Authorization": f"Bearer {BEARER_TWITCH}",
    "Client-Id": CLIENT_ID_TWITCH,
    "Content-Type": "application/json",
}

data = {"broadcaster_id": BROADCASTER_ID, "sender_id": SENDER_ID, "message": ""}


async def generar_tema():
    """Genera un tema usando ChatGPT"""
    print("Generando tema con GPT-4o-mini...")

    try:
        async with aiofiles.open(
            "transcripcion.txt", mode="r", encoding="utf-8"
        ) as file:
            file_content = await file.read()
    except FileNotFoundError:
        print("El archivo transcripcion.txt no se encontró. Usando contenido vacío.")
        file_content = ""

    # Reemplazar placeholders en los contextos
    system_context = SYSTEM_CONTEXT_TEMPLATE.replace("{JUEGO}", JUEGO).replace(
        "{PERSONAJES}", personajes
    )
    user_context = USER_CONTEXT_TEMPLATE.replace("{TRANSCRIPCION}", file_content)

    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_context},
            {"role": "user", "content": user_context},
        ],
        max_tokens=100,
    )
    res = respuesta.choices[0].message.content.strip()
    return res


async def sendMessage(twitch_message, testing=False):
    """Envía un mensaje al chat de Twitch"""
    print(f"Enviando mensaje a Twitch: {twitch_message}")
    data["message"] = twitch_message
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            if resp.status == 200:
                print(f"Mensaje enviado con éxito: {data}")
            else:
                print(f"Error al enviar mensaje: {resp.status}")
                print("Respuesta:", await resp.text())


async def main():
    while True:
        await sendMessage(await generar_tema(), testing=False)
        waitTime = random.randint(1, 6) * 30
        print(f"Esperando {waitTime} segundos para el próximo mensaje...")
        for i in range(waitTime, 0, -1):
            print(f"Esperando {i} segundos...", end="\r")
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
