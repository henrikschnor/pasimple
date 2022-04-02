#!/usr/bin/env python3

import wave
import pasimple

# Audio attributes for the recording
FORMAT = pasimple.PA_SAMPLE_S32LE
SAMPLE_WIDTH = pasimple.format2width(FORMAT)
CHANNELS = 1
SAMPLE_RATE = 41000

# Record 10 seconds of audio
with pasimple.PaSimple(pasimple.PA_STREAM_RECORD, FORMAT, CHANNELS, SAMPLE_RATE) as pa:
    audio_data = pa.read(CHANNELS * SAMPLE_RATE * SAMPLE_WIDTH * 10)

# Save audio to a file
with wave.open('recording.wav', 'wb') as wave_file:
    wave_file.setsampwidth(SAMPLE_WIDTH)
    wave_file.setnchannels(CHANNELS)
    wave_file.setframerate(SAMPLE_RATE)
    wave_file.writeframes(audio_data)
