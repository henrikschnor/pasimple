#!/usr/bin/env python3

import wave
import pasimple

# Read a .wav file with its attributes
with wave.open('recording.wav', 'rb') as wave_file:
    format = pasimple.width2format(wave_file.getsampwidth())
    channels = wave_file.getnchannels()
    sample_rate = wave_file.getframerate()
    audio_data = wave_file.readframes(wave_file.getnframes())

# Play the file via PulseAudio
with pasimple.PaSimple(pasimple.PA_STREAM_PLAYBACK, format, channels, sample_rate) as pa:
    pa.write(audio_data)
    pa.drain()
