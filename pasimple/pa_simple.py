import ctypes
from pasimple import PaSimpleError, PA_STREAM_PLAYBACK, PA_STREAM_RECORD


# The C library interface is stored in a global variable
# and is only initialized when needed.
_libpulse_simple = None
def get_libpulse_simple():
    global _libpulse_simple
    if _libpulse_simple is None:
        try:
            _libpulse_simple = ctypes.CDLL('libpulse-simple.so.0')
            _libpulse_simple.pa_simple_new.restype = ctypes.c_void_p
            _libpulse_simple.pa_simple_get_latency = ctypes.c_ulonglong
        except OSError as err:
            raise PaSimpleError(f'{type(err)}: {err}')
    return _libpulse_simple


class pa_sample_spec(ctypes.Structure):
    """Struct describing the audio encoding for the pulse server"""

    _fields_ = [
        ('format', ctypes.c_int),
        ('rate', ctypes.c_uint32),
        ('channels', ctypes.c_uint8)
    ]


class pa_buffer_attr(ctypes.Structure):
    """Struct describing playback and record buffer metrics"""

    _fields_ = [
        ('maxlength', ctypes.c_uint32),
        ('tlength', ctypes.c_uint32),
        ('prebuf', ctypes.c_uint32),
        ('minreq', ctypes.c_uint32),
        ('fragsize', ctypes.c_uint32),
    ]


class PaSimple:
    def __init__(self, direction, format, channels, rate, app_name='python',
                 stream_name=None, server_name=None, device_name=None,
                 maxlength=-1, tlength=-1, prebuf=-1, minreq=-1, fragsize=-1):
        """Initialize a pulseaudio simple API stream.

        direction: either PA_STREAM_PLAYBACK or PA_STREAM_RECORD
        format: one of the PA_SAMPLE_* formats
        channels: integer specifying the number of channels
        rate: integer specifying the sample rate
        app_name: string specifying the name of the application
        stream_name: None (use app_name) or string specifying a name for this stream
        server_name: None (use default) or string specifying a pulseaudio server name
        device_name: None (use default) or string specifying a pulseaudio device

        Buffer-related options are in units of bytes:
        maxlength: integer buffer size limit, or -1 (default: max supported)
        tlength: keep this many bytes in playback buffer, or -1 (default: about 2s)
        prebuf: buffer this many bytes before starting playback, or -1 (default: ==tlength)
        minreq: refill playback buffer in chunks at least this big, or -1 (default: about 2s)
        fragsize: receive recorded audio in chunks of this size, or -1 (default: about 2s)
        """

        # Save audio encoding properties
        self._direction = direction
        self._format = format
        self._channels = channels
        self._rate = rate

        # If no stream_name is specified, use the app_name
        if stream_name is None:
            stream_name = app_name

        # Prepare arguments for initializing a pulseaudio stream
        sample_spec = pa_sample_spec(format, rate, channels)
        buffer_attr = pa_buffer_attr(maxlength, tlength, prebuf, minreq, fragsize)
        arg_server_name = ctypes.c_char_p(server_name.encode()) if server_name is not None else None
        arg_app_name = ctypes.c_char_p(app_name.encode())
        arg_device_name = ctypes.c_char_p(device_name.encode()) if device_name is not None else None
        arg_stream_name = ctypes.c_char_p(stream_name.encode())
        error = ctypes.c_int(0)

        # Initialize the stream.
        # Keep track of the underlying stream's state to avoid double frees
        self._stream_alive = False
        self._stream = get_libpulse_simple().pa_simple_new(arg_server_name, arg_app_name, direction, arg_device_name, arg_stream_name, ctypes.byref(sample_spec), None, ctypes.byref(buffer_attr), ctypes.byref(error))
        if self._stream is None:
            raise PaSimpleError(f'Error while creating stream: {error.value}')
        self._stream_alive = True


    def close(self):
        """Close the underlying stream and free resources"""

        if self._stream_alive:
            self._stream_alive = False
            get_libpulse_simple().pa_simple_free(ctypes.c_void_p(self._stream))
    

    def __enter__(self):
        """Context manager - enter"""

        return self
    

    def __exit__(self, type, value, traceback):
        """Context manager - exit"""

        self.close()


    def direction(self):
        """Get the direction specified in the constructor"""

        return self._direction


    def format(self):
        """Get the audio format specified in the constructor"""

        return self._format
    

    def channels(self):
        """Get the audio channels specified in the constructor"""

        return self._channels
    

    def rate(self):
        """Get the audio rate specified in the constructor"""

        return self._rate


    def read(self, num_bytes):
        """Record data from the PulseAudio server.

        PA_STREAM_RECORD must be used during initialization.
        This function blocks and returns `num_bytes` number of bytes.
        """

        if not self._stream_alive:
            raise PaSimpleError('Cannot perform operation on closed stream')
        if self._direction != PA_STREAM_RECORD:
            raise PaSimpleError('Stream was not initialized for recording')
        
        rec_buffer = bytearray(num_bytes)
        rec_buffer_ptr = ctypes.c_char * num_bytes
        error = ctypes.c_int(0)
        ok = get_libpulse_simple().pa_simple_read(ctypes.c_void_p(self._stream), rec_buffer_ptr.from_buffer(rec_buffer), num_bytes, ctypes.byref(error))
        if ok != 0:
            raise PaSimpleError(f'Could not record audio, error code: {error.value}')
        return rec_buffer


    def write(self, data):
        """Play audio via the PulseAudio server.

        PA_STREAM_PLAYBACK must be used during initialization.
        Encoding of `data` must match the one specified in the constructor.
        """

        if not self._stream_alive:
            raise PaSimpleError('Cannot perform operation on closed stream')
        if self._direction != PA_STREAM_PLAYBACK:
            raise PaSimpleError('Stream was not initialized for playback')
        
        error = ctypes.c_int(0)
        ok = get_libpulse_simple().pa_simple_write(ctypes.c_void_p(self._stream), data, len(data), ctypes.byref(error))
        if ok != 0:
            raise PaSimpleError(f'Could not play audio, error code: {error.value}')


    def drain(self):
        """Blocks until all remaining data in the buffer has been played"""

        if not self._stream_alive:
            raise PaSimpleError('Cannot perform operation on closed stream')
        if self._direction != PA_STREAM_PLAYBACK:
            raise PaSimpleError('Stream was not initialized for playback')
        
        error = ctypes.c_int(0)
        ok = get_libpulse_simple().pa_simple_drain(ctypes.c_void_p(self._stream), ctypes.byref(error))
        if ok != 0:
            raise PaSimpleError(f'Could not drain, error code: {error.value}')


    def flush(self):
        """Discards any data in the record/playback buffers"""

        if not self._stream_alive:
            raise PaSimpleError('Cannot perform operation on closed stream')
        
        error = ctypes.c_int(0)
        ok = get_libpulse_simple().pa_simple_flush(ctypes.c_void_p(self._stream), ctypes.byref(error))
        if ok != 0:
            raise PaSimpleError(f'Could not flush, error code: {error.value}')


    def get_latency(self):
        """Get the record/playback latency reported by PulseAudio in microseconds"""

        if not self._stream_alive:
            raise PaSimpleError('Cannot perform operation on closed stream')
        
        error = ctypes.c_int(0)
        latency = get_libpulse_simple().pa_simple_get_latency(ctypes.c_void_p(self._stream), ctypes.byref(error))
        if error != 0:
            raise PaSimpleError(f'Could not get latency, error code: {error.value}')
        return latency.value
