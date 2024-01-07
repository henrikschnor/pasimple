# Specifies the direction for a pulseaudio stream
PA_STREAM_PLAYBACK=1
PA_STREAM_RECORD=2

# Audio formats supported by pulseaudio are documented here:
# https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/SupportedAudioFormats/
PA_SAMPLE_U8 = 0            # Unsigned 8 Bit PCM
PA_SAMPLE_ALAW = 1          # 8 Bit a-Law
PA_SAMPLE_ULAW = 2          # 8 Bit mu-Law
PA_SAMPLE_S16LE = 3         # Signed 16 Bit PCM, little endian (PC)
PA_SAMPLE_S16BE = 4         # Signed 16 Bit PCM, big endian
PA_SAMPLE_FLOAT32LE = 5     # 32 Bit IEEE floating point, little endian (PC), range -1.0 to 1.0
PA_SAMPLE_FLOAT32BE = 6     # 32 Bit IEEE floating point, big endian, range -1.0 to 1.0
PA_SAMPLE_S32LE = 7         # Signed 32 Bit PCM, little endian (PC)
PA_SAMPLE_S32BE = 8         # Signed 32 Bit PCM, big endian
PA_SAMPLE_S24LE = 9         # Signed 24 Bit PCM packed, little endian (PC)
PA_SAMPLE_S24BE = 10        # Signed 24 Bit PCM packed, big endian
PA_SAMPLE_S24_32LE = 11     # Signed 24 Bit PCM in LSB of 32 Bit words, little endian (PC)
PA_SAMPLE_S24_32BE = 12     # Signed 24 Bit PCM in LSB of 32 Bit words, big endian


from .exceptions import PaSimpleError
from .pa_simple import PaSimple


# Maps sample widths to their most common audio formats
LOOKUP_FORMAT_BY_WIDTH = {
    1: PA_SAMPLE_U8,
    2: PA_SAMPLE_S16LE,
    3: PA_SAMPLE_S24LE,
    4: PA_SAMPLE_S32LE
}

# Maps audio formats to their sample widths
LOOKUP_WIDTH_BY_FORMAT = {
    PA_SAMPLE_U8: 1,
    PA_SAMPLE_ALAW: 1,
    PA_SAMPLE_ULAW: 1,
    PA_SAMPLE_S16LE: 2,
    PA_SAMPLE_S16BE: 2,
    PA_SAMPLE_FLOAT32LE: 4,
    PA_SAMPLE_FLOAT32BE: 4,
    PA_SAMPLE_S32LE: 4,
    PA_SAMPLE_S32BE: 4,
    PA_SAMPLE_S24LE: 3,
    PA_SAMPLE_S24BE: 3,
    PA_SAMPLE_S24_32LE: 4,
    PA_SAMPLE_S24_32BE: 4
}


def width2format(sample_width):
    """Returns the most common audio format for a sample width"""

    return LOOKUP_FORMAT_BY_WIDTH[sample_width]

def format2width(audio_format):
    """Returns the sample width for an audio format"""

    return LOOKUP_WIDTH_BY_FORMAT[audio_format]


import wave

def play_wav(file_path):
    """Plays a wav file via PulseAudio.

    This blocks until all of the file has been played.
    The following formats are supported:
    PA_SAMPLE_U8, PA_SAMPLE_S16LE, PA_SAMPLE_S24LE, PA_SAMPLE_S32LE
    """

    with wave.open(file_path, 'rb') as wf:
        with PaSimple(PA_STREAM_PLAYBACK,
                      width2format(wf.getsampwidth()),
                      wf.getnchannels(),
                      wf.getframerate()) as pa:
            pa.write(wf.readframes(wf.getnframes()))
            pa.drain()

def record_wav(file_path, length, format=PA_SAMPLE_S24LE, channels=1, sample_rate=41000):
    """Records a wav file via PulseAudio.

    The length of the recording is given in seconds.
    Blocks until all data has been recorded.
    The following formats are supported:
    PA_SAMPLE_U8, PA_SAMPLE_S16LE, PA_SAMPLE_S24LE, PA_SAMPLE_S32LE
    """

    with PaSimple(PA_STREAM_RECORD, format, channels, sample_rate) as pa:
        audio_data = pa.read(channels * sample_rate * format2width(format) * length)
    with wave.open(file_path, 'wb') as wf:
        wf.setsampwidth(format2width(format))
        wf.setnchannels(channels)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)
