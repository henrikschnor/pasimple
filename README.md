# pulseaudio-simple

A python wrapper for the [pulseaudio simple API](https://www.freedesktop.org/software/pulseaudio/doxygen/simple.html). Supports playing and recording audio via PulseAudio and PipeWire.

This library is feature-complete, so there won't be much ongoing activity in this repository. Reported bugs will be fixed. PRs for improvements are always welcome.


## Dependencies

- `libpulse-simple.so.0` (part of `libpulse0` on Debian or `libpulse` on Arch)
- A running PulseAudio/PipeWire server

There's a good chance your Linux distribution comes with PulseAudio or PipeWire preinstalled.


## Installation

```sh
pip3 install pasimple
```


## Quick start

There are two simple convenience functions for recording/playing audio to/from a `.wav` file:

```python
from pasimple import record_wav, play_wav

# Record 5 seconds of audio from the default recording device
record_wav('/tmp/test_recording.wav', 5)

# Play the recording via the default output device
play_wav('/tmp/test_recording.wav')
```

Both functions block until all audio has been recorded/played. The default encoding used by `record_wav` is `PA_SAMPLE_S24LE`, mono, 41kHz. The function `play_wav` can only recognize files encoded in one of the following formats: `PA_SAMPLE_U8`, `PA_SAMPLE_S16LE`, `PA_SAMPLE_S24LE`, `PA_SAMPLE_S32LE`. For more complex use cases, scroll down to the "Documentation" section.


### Recording

A more extensive example for recording audio can be found in [examples/record.py](https://github.com/henrikschnor/pasimple/blob/master/examples/record.py):

```python
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
```

In this example we're explicity specifying the audio format to be used for recording. When the `PaSimple` object is created, it opens a PulseAudio stream with the specified format. Further parameters that can be used in the `PaSimple` constructor are described in more detail under "Documentation" below.

The recording starts as soon as the `PaSimple` object is created and audio data is buffered internally. Calls to `read` can retrieve the raw audio data, specifying the number of bytes to read as an argument. The function will block until the requested number of bytes is available. When done recording, the `PaSimple` object's audio stream should be closed with a call to `close()`. Alternatively, it can be used with python's context manager (the `with` statement in the example above).

Finally, the data is written to a `.wav` file. We specify the audio format again, so that a correct `.wav` file header can be written.


### Playing

An example for playing audio can be found in [examples/play.py](https://github.com/henrikschnor/pasimple/blob/master/examples/play.py):

```python
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
```

To play a `.wav` file, we basically do the recording steps in reverse. First, we read the audio encoding together with the raw audio data from the file. When creating the `PaSimple` object, this time, we're opening a playback stream and specify the format of the audio we're going to play. It's then as simple as passing the raw audio data to the `write` function. Finally, we call `drain` to make sure all audio has played before closing the stream by leaving the `with` context.


### Streaming

An annotated example of how to stream audio from/to a source/sink can be found in [examples/echo.py](https://github.com/henrikschnor/pasimple/blob/master/examples/echo.py)


## Documentation

This sections describes all constants/functions/classes available in the `pasimple` module.

### Constants

**Stream directions**

The stream direction is used when creating a `PaSimple` object to specify whether the stream should be used for playing or recording audio.

| Constant | Description |
| --- | --- |
| PA_STREAM_PLAYBACK | Open a stream for playback |
| PA_STREAM_RECORD | Open a stream for recording |


**Audio formats**

Formats that can be used with PulseAudio to play or record audio. PulseAudio's documentation for these formats can be found [here](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/SupportedAudioFormats/).

| Constant | Description |
| --- | --- |
| PA_SAMPLE_U8 | Unsigned 8 Bit PCM |
| PA_SAMPLE_ALAW | 8 Bit a-Law |
| PA_SAMPLE_ULAW | 8 Bit mu-Law |
| PA_SAMPLE_S16LE | Signed 16 Bit PCM, little endian (PC) |
| PA_SAMPLE_S16BE | Signed 16 Bit PCM, big endian |
| PA_SAMPLE_FLOAT32LE | 32 Bit IEEE floating point, little endian (PC), range -1.0 to 1.0 |
| PA_SAMPLE_FLOAT32BE | 32 Bit IEEE floating point, big endian, range -1.0 to 1.0 |
| PA_SAMPLE_S32LE | Signed 32 Bit PCM, little endian (PC) |
| PA_SAMPLE_S32BE | Signed 32 Bit PCM, big endian |
| PA_SAMPLE_S24LE | Signed 24 Bit PCM packed, little endian (PC) |
| PA_SAMPLE_S24BE | Signed 24 Bit PCM packed, big endian |
| PA_SAMPLE_S24_32LE | Signed 24 Bit PCM in LSB of 32 Bit words, little endian (PC) |
| PA_SAMPLE_S24_32BE | Signed 24 Bit PCM in LSB of 32 Bit words, big endian |


### Convenience functions

**width2format**(`sample_width`)
- `sample_width`: Audio sample width to return a matching format for.

Returns one of `PA_SAMPLE_U8`, `PA_SAMPLE_S16LE`, `PA_SAMPLE_S24LE` or `PA_SAMPLE_S32LE` (common PCM audio formats), corresponding to the provided sample width or an error if none match.


**format2width**(`audio_format`)
- `audio_format`: One of the `PA_SAMPLE_*` audio formats to return the width for.

Returns the sample width for an audio format.


**play_wav**(`file_path`)
- `file_path`: Path to a `.wav` file to be played.

Plays a `.wav` file via PulseAudio and blocks until all audio data has been played. The following formats are supported: `PA_SAMPLE_U8`, `PA_SAMPLE_S16LE`, `PA_SAMPLE_S24LE`, `PA_SAMPLE_S32LE`. Throws a `wave.Error` if the `.wav` file cannot be read or a `PaSimpleError` if the audio data cannot be played.


**record_wav**(`file_path`, `length`, `format=PA_SAMPLE_S24LE`, `channels=1`, `sample_rate=41000`)
- `file_path`: Path to a `.wav` file the recorded audio will be written to.
- `length`: The length of the recording in seconds.
- `format`: Audio format to be used for the recording (one of `PA_SAMPLE_U8`, `PA_SAMPLE_S16LE`, `PA_SAMPLE_S24LE`, `PA_SAMPLE_S32LE`).
- `channels`: Number of channels to record (1=mono, 2=stereo).
- `sample_rate`: Sample rate for the recording in Hz.

Records a `.wav` file via PulseAudio and blocks until all audio data has been recorded. The following formats are supported: `PA_SAMPLE_U8`, `PA_SAMPLE_S16LE`, `PA_SAMPLE_S24LE`, `PA_SAMPLE_S32LE`. Throws a `wave.Error` if the `.wav` file cannot be written or a `PaSimpleError` if the audio data cannot be recorded.


### PaSimple

An instance of `PaSimple` represents an audio stream for playing or recording audio via PulseAudio. On error, all functions throw a `PaSimpleError`.

**PaSimple**(`direction`, `format`, `channels`, `rate`, `app_name='python'`, `stream_name=None`, `server_name=None`, `device_name=None`, `maxlength=-1`, `tlength=-1`, `prebuf=-1`, `minreq=-1`, `fragsize=-1`):
- `direction`: Either `PA_STREAM_PLAYBACK` or `PA_STREAM_RECORD`.
- `format`: The audio encoding (one of `PA_SAMPLE_*`) for this stream.
- `channels`: Integer specifying the number of channels (1=mono, 2=stereo).
- `rate`: Integer specifying the sample rate in Hz.
- `app_name`: String specifying the name of the application that will be registered in PulseAudio.
- `stream_name`: `None` (use `app_name`) or a string specifying the name of this stream that will be registered in PulseAudio.
- `server_name`: `None` (default) or a string specifying a PulseAudio server name.
- `device_name`: `None` (default) or a string specifying a specific PulseAudio device for recording or playback.
- `maxlength`: `-1` (default: max supported) or an integer specifying the buffer size limit in bytes.
- `tlength`: `-1` (default: about 2s) or an integer specifying how many bytes to keep in the playback buffer.
- `prebuf`: `-1` (use `tlength`) or an integer specifying how many bytes to buffer before starting playback.
- `minreq`: `-1` (default: about 2s) or an integer specifying the minimum size of chunks for refilling the playback buffer in bytes.
- `fragsize`: `-1` (default: about 2s) or an integer specifying the size of recording chunks in bytes.

Initialize a PulseAudio simple API stream for playing or recording audio data.


**close()**

Close the underlying stream and free resources.


**direction()**

Returns the direction specified in the constructor.


**format()**

Returns the audio format specified in the constructor.


**channels()**

Returns the number of audio channels specified in the constructor.


**rate()**

Returns the audio rate specified in the constructor.


**read(`num_bytes`)**
- `num_bytes`: The number of bytes to read.

Record data from the PulseAudio server. `PA_STREAM_RECORD` must have been used during initialization. This function blocks and returns `num_bytes` bytes of audio data.


**write(`data`)**
- `data`: Raw audio data to be played.

Play audio via the PulseAudio server. `PA_STREAM_PLAYBACK` must have been used during initialization. Encoding of `data` must match the one specified in the constructor.


**drain()**

Blocks until all remaining data in the buffer has been played.


**flush()**

Discards any data in the record/playback buffers.


**get_latency()**

Returns the record/playback latency reported by PulseAudio in microseconds.


### PulseAudio error codes

This list of PulseAudio internal error codes has been [taken from here](https://gitlab.freedesktop.org/pulseaudio/pulseaudio/-/blob/master/src/pulse/def.h#L471).

| Error code | Description |
| --- | --- |
| 0 | No error |
| 1 | Access failure |
| 2 | Unknown command |
| 3 | Invalid argument |
| 4 | Entity exists |
| 5 | No such entity |
| 6 | Connection refused |
| 7 | Protocol error |
| 8 | Timeout |
| 9 | No authentication key |
| 10 | Internal error |
| 11 | Connection terminated |
| 12 | Entity killed |
| 13 | Invalid server |
| 14 | Module initialization failed |
| 15 | Bad state |
| 16 | No data |
| 17 | Incompatible protocol version |
| 18 | Data too large |
| 19 | Operation not supported |
| 20 | The error code was unknown to the client |
| 21 | Extension does not exist |
| 22 | Obsolete functionality |
| 23 | Missing implementation |
| 24 | The caller forked without calling execve() and tried to reuse the context |
| 25 | An IO error happened |
| 26 | Device or resource busy |
| 27 | Not really an error but the first invalid error code |