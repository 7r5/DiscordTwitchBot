import sounddevice as sd
import numpy as np
import queue
import threading
import speech_recognition as sr
from collections import deque
import time

# ---------- CONFIG ----------
MAX_WORDS = 50
SAMPLE_RATE = 48000
DEVICE_INDEX = 77
CHUNK_DURATION = 3  # segundos de audio a juntar antes de reconocer

# ---------- VARIABLES ----------
last_words = deque(maxlen=MAX_WORDS)
r = sr.Recognizer()
q = queue.Queue()


def actualizar_archivo():
    with open("transcripcion.txt", "w", encoding="utf-8") as f:
        f.write(" ".join(last_words))


def audio_callback(indata, frames, time, status):
    if status:
        print("Status:", status)
    # Mezclar estéreo → mono
    if indata.shape[1] > 1:
        mono = np.mean(indata, axis=1)
    else:
        mono = indata[:, 0]
    q.put(mono.copy())


def reconocer_audio():
    buffer = []
    last_time = time.time()

    while True:
        audio_chunk = q.get()
        buffer.append(audio_chunk)

        # Si ya acumulamos CHUNK_DURATION segundos, procesamos
        if time.time() - last_time >= CHUNK_DURATION:
            combined = np.concatenate(buffer)
            buffer = []
            last_time = time.time()

            # Convertir float32 [-1,1] → int16
            audio_int16 = np.int16(combined * 32767)
            audio_data = sr.AudioData(
                audio_int16.tobytes(),
                sample_rate=SAMPLE_RATE,
                sample_width=2,
            )
            try:
                texto = r.recognize_amazon(audio_data, language="es-MX")
                for palabra in texto.split():
                    last_words.append(palabra)
                actualizar_archivo()
                print("Últimas palabras:", " ".join(last_words))
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"Error de servicio: {e}")
                break


# ---------- INICIAR STREAM ----------
stream = sd.InputStream(
    channels=2,
    samplerate=SAMPLE_RATE,
    device=DEVICE_INDEX,
    callback=audio_callback,
)

# ---------- HILO DE RECONOCIMIENTO ----------
threading.Thread(target=reconocer_audio, daemon=True).start()

# ---------- EJECUTAR ----------
with stream:
    print("🎤 Escuchando y transcribiendo...")
    while True:
        sd.sleep(1000)
