#!/usr/bin/env python3
"""Example to echo audio with 1s of delay.

This demonstrates how audio can be streamed,
(i.e. continuously read from a source and/or
written to a sink).

To avoid feedback, this should be used with headphones.
"""

import pasimple
import signal
import wave

# Audio attributes for recording/playback
FORMAT = pasimple.PA_SAMPLE_S32LE
SAMPLE_WIDTH = pasimple.format2width(FORMAT)
CHANNELS = 1
SAMPLE_RATE = 44100
BYTES_PER_SEC = CHANNELS * SAMPLE_RATE * SAMPLE_WIDTH

def print_stream_attrs(stream):
    print(f'  Direction: {stream.direction()}')
    print(f'  Format: {stream.format()}')
    print(f'  Channels: {stream.channels()}')
    print(f'  Rate: {stream.rate()} Hz')
    print(f'  Latency: {stream.get_latency() / 1000} ms')

# Open audio streams for recording/playback
# and print their attributes. We choose:
# maxlength=2s (buffer size), should be
# sufficient if we plan for 1s of delay.
# fragsize=200ms (recording fragment size)
# minreq=200ms (how much playback data the
# server should at least ask for)
# prebuf=1s (how far the buffer must be
# filled before playback starts)
# tlength=2s (target length of playback buffer)
print('Opening stream for recording...')
stream_rec = pasimple.PaSimple(pasimple.PA_STREAM_RECORD,
                               FORMAT,
                               CHANNELS,
                               SAMPLE_RATE,
                               app_name='pasimple-echo-test',
                               stream_name='record-mono',
                               maxlength=BYTES_PER_SEC * 2,
                               fragsize=BYTES_PER_SEC // 5)
print_stream_attrs(stream_rec)
print('Opening stream for playback...')
stream_play = pasimple.PaSimple(pasimple.PA_STREAM_PLAYBACK,
                                FORMAT,
                                CHANNELS,
                                SAMPLE_RATE,
                                app_name='pasimple-echo-test',
                                stream_name='play-mono',
                                maxlength=BYTES_PER_SEC * 2,
                                minreq=BYTES_PER_SEC // 5,
                                prebuf=BYTES_PER_SEC,
                                tlength=BYTES_PER_SEC * 2)
print_stream_attrs(stream_play)

# We want to echo the recorded audio with 1s delay,
# so let's start by recording a second of audio.
# This blocks until all audio (1s) has been read.
print('Recording...')
audio = stream_rec.read(BYTES_PER_SEC)
# Then, we just add it to the playback buffer,
# which returns immediately because tlength is
# larger than 1s of audio. It will also start playing
# immediately becuase we set prebuf to 1s.
stream_play.write(audio)

# Set up a signal handler, so we can gracefully
# stop the following loop.
running = True
def sigint_handler(sig, frame):
    global running
    print('\rStopping...')
    running = False
signal.signal(signal.SIGINT, sigint_handler)

# Keep reading and writing 200ms chunks of audio.
# Since there is already 1s of audio in the playback
# buffer, it will continue to be played delayed.
print('Echoing (press Ctrl+C to interrupt)...')
while running:
    audio = stream_rec.read(BYTES_PER_SEC // 5)
    stream_play.write(audio)

# We were interrupted, so all that's
# left to do is cleaning things up.
# By calling flush(), the remaining data in the
# playback buffer will be discarded.
stream_play.flush()
stream_play.close()
stream_rec.close()
