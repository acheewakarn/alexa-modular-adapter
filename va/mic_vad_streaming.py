#############
###CREDITS###
#############
# https://github.com/mozilla/DeepSpeech-examples

import time, logging
from datetime import datetime
import threading, collections, queue, os, os.path
import deepspeech
import numpy as np
import pyaudio
import wave
import webrtcvad
from halo import Halo
from scipy import signal
from wifi import Cell, Scheme
import subprocess

logging.basicConfig(level=20)

#############################
#############################
######GLOBAL VARIABLES#######
#############################
#############################
cut_mic = False



class Audio(object):
    """Streams raw audio from microphone. Data is received in a separate thread, and stored in a buffer, to be read from."""

    FORMAT = pyaudio.paInt16
    # Network/VAD rate-space
    RATE_PROCESS = 16000
    CHANNELS = 1
    BLOCKS_PER_SECOND = 50

    def __init__(self, callback=None, device=None, input_rate=RATE_PROCESS, file=None):
        def proxy_callback(in_data, frame_count, time_info, status):
            #pylint: disable=unused-argument
            if self.chunk is not None:
                in_data = self.wf.readframes(self.chunk)
            callback(in_data)
            return (None, pyaudio.paContinue)
        if callback is None: callback = lambda in_data: self.buffer_queue.put(in_data)
        self.buffer_queue = queue.Queue()
        self.device = device
        self.input_rate = input_rate
        self.sample_rate = self.RATE_PROCESS
        self.block_size = int(self.RATE_PROCESS / float(self.BLOCKS_PER_SECOND))
        self.block_size_input = int(self.input_rate / float(self.BLOCKS_PER_SECOND))
        self.pa = pyaudio.PyAudio()

        kwargs = {
            'format': self.FORMAT,
            'channels': self.CHANNELS,
            'rate': self.input_rate,
            'input': True,
            'frames_per_buffer': self.block_size_input,
            'stream_callback': proxy_callback,
        }

        self.chunk = None
        # if not default device
        if self.device:
            kwargs['input_device_index'] = self.device
        elif file is not None:
            self.chunk = 320
            self.wf = wave.open(file, 'rb')

        self.stream = self.pa.open(**kwargs)
        self.stream.start_stream()

    def resample(self, data, input_rate):
        """
        Microphone may not support our native processing sampling rate, so
        resample from input_rate to RATE_PROCESS here for webrtcvad and
        deepspeech

        Args:
            data (binary): Input audio stream
            input_rate (int): Input audio rate to resample from
        """
        data16 = np.fromstring(string=data, dtype=np.int16)
        resample_size = int(len(data16) / self.input_rate * self.RATE_PROCESS)
        resample = signal.resample(data16, resample_size)
        resample16 = np.array(resample, dtype=np.int16)
        return resample16.tostring()

    def read_resampled(self):
        """Return a block of audio data resampled to 16000hz, blocking if necessary."""
        return self.resample(data=self.buffer_queue.get(),
                             input_rate=self.input_rate)

    def read(self):
        """Return a block of audio data, blocking if necessary."""
        return self.buffer_queue.get()

    def destroy(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    frame_duration_ms = property(lambda self: 1000 * self.block_size // self.sample_rate)

    def write_wav(self, filename, data):
        logging.info("write wav %s", filename)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        # wf.setsampwidth(self.pa.get_sample_size(FORMAT))
        assert self.FORMAT == pyaudio.paInt16
        wf.setsampwidth(2)
        wf.setframerate(self.sample_rate)
        wf.writeframes(data)
        wf.close()


class VADAudio(Audio):
    """Filter & segment audio with voice activity detection."""

    def __init__(self, aggressiveness=3, device=None, input_rate=None, file=None):
        super().__init__(device=device, input_rate=input_rate, file=file)
        self.vad = webrtcvad.Vad(aggressiveness)

    def frame_generator(self):
        """Generator that yields all audio frames from microphone."""
        if self.input_rate == self.RATE_PROCESS:
            while True:
                yield self.read()
        else:
            while True:
                yield self.read_resampled()

    def vad_collector(self, padding_ms=300, ratio=0.75, frames=None):
        """Generator that yields series of consecutive audio frames comprising each utterence, separated by yielding a single None.
            Determines voice activity by ratio of frames in padding_ms. Uses a buffer to include padding_ms prior to being triggered.
            Example: (frame, ..., frame, None, frame, ..., frame, None, ...)
                      |---utterence---|        |---utterence---|
        """
        if frames is None: frames = self.frame_generator()
        num_padding_frames = padding_ms // self.frame_duration_ms
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False

        for frame in frames:
            if len(frame) < 640:
                return

            is_speech = self.vad.is_speech(frame, self.sample_rate)


            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > ratio * ring_buffer.maxlen:
                    triggered = True
                    for f, s in ring_buffer:
                        yield f
                    ring_buffer.clear()

            else:
                yield frame
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > ratio * ring_buffer.maxlen:
                    triggered = False
                    yield None
                    ring_buffer.clear()

def decipher(password):
    """This function takes a password full of words and
    deciphers it into single letters (i.e. first letter of word)
    or a number.
    """
    deciphered_pass = ""

    password = password.split(" ")

    for char in password:
        if char == "":
            continue
        elif char == "one":
            deciphered_pass += "1"
        elif char == "to" or char == "two":
            deciphered_pass += "2"
        elif char == "three" or char == "tree":
             deciphered_pass += "3"
        elif char == "four" or char == "for":
            deciphered_pass += "4"
        elif char == "five" or char == "fiv":
            deciphered_pass += "5"
        elif char == "six":
             deciphered_pass += "6"
        elif char == "seven":
            deciphered_pass += "7"
        elif char == "eight":
            deciphered_pass += "8"
        elif char == "nine":
             deciphered_pass += "9"
        else:
            deciphered_pass += char[0]
    return deciphered_pass

def connect_to_wifi(password, current_network):
    """Connects the Modular Adapter to the Wifi
    It does this by taking the "password" and
    current_network (SSID) then deciphers the
    password to get the correct letters and #'s
    for the password. When that finishes it opens
    the wpa_supplicant.conf file and writes the
    SSID and password into it. Then it calls
    the wpa_cli to reconnect to the wifi.
    """

    # This part takes the full password said by the client
    # Then deciphers those words and numbers into actual
    # individual letters and numbers.
    # Example: red car one --> rc1
    deciphered_password = decipher(password)

    # This variable holds the message of the network's
    # ssid and psk that is written to the wpa_supplicant.conf.
    # One thing that I would recommend is to make the psk a hash
    # than plain_text. This would make this part of the program
    # much safer without having to trust root.
    config_message = """network={{
                        ssid="{}"
                        psk="{}"
                        key_mgmt=WPA-PSK
                     }}""".format(current_network, deciphered_password)
    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "a") as f:
        f.write(config_message)

    # This process tells the RPI to reconnect to wlan0 again. This makes
    # it possible to connect to the WiFI without having to reboot the
    # entire RPI.
    subprocess.run(["wpa_cli", "-i", "wlan0", "reconfigure"])

def find_wifi_networks(wifi_networks):
    """Looks for at most three local
    WiFi networks that the RPI could
    connect with. Then lists those
    WiFi networks so the client
    can see the available choices.
    """
    while(len(wifi_networks) == 0):
        wifi_networks = list(Cell.all('wlan0'))
        print("Found these networks")
        for i in range(0, (len(wifi_networks) if len(wifi_networks) < 3 else 3)):
            print(str(i) + ".) " + wifi_networks[i].ssid)
        return wifi_networks


def main(ARGS):

    # Load DeepSpeech model
    if os.path.isdir(ARGS.model):
        model_dir = ARGS.model
        ARGS.model = os.path.join(model_dir, 'output_graph.pb')
        ARGS.scorer = os.path.join(model_dir, ARGS.scorer)

    print('Initializing model...')
    logging.info("ARGS.model: %s", ARGS.model)
    model = deepspeech.Model(ARGS.model)
    if ARGS.scorer:
        logging.info("ARGS.scorer: %s", ARGS.scorer)
        model.enableExternalScorer(ARGS.scorer)

    # Start audio with VAD
    vad_audio = VADAudio(aggressiveness=ARGS.vad_aggressiveness,
                         device=ARGS.device,
                         input_rate=ARGS.rate,
                         file=ARGS.file)
    print("Listening (ctrl-C to exit)...")
    frames = vad_audio.vad_collector()

    # Stream from microphone to DeepSpeech using VAD
    spinner = None
    if not ARGS.nospinner:
        spinner = Halo(spinner='line')
    stream_context = model.createStream()
    wifi_networks = []
    current_network = ""
    password = ""
    inference_word = ""
    wav_data = bytearray()

    # This for-loop is basically a while loop given 
    # that frames is actually a generator that is constantly
    # generating audio frames from the microphone.
    for frame in frames:
        # If an audio frame is recorded as speech and not silence.
        # The program adds the frame to the deepspeech streamer which
        # is constantly collecting Audio frames to be recognized.
        if frame is not None:
            if spinner: spinner.start()
            logging.debug("streaming frame")
            stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
            if ARGS.savewav: wav_data.extend(frame)
        else:
            # Once the frame is no longer recognized as audio anymore,
            # the deepspeech stream is finished where it takes all the audio
            # that it has collected and returns the finished text version.
            if spinner: spinner.stop()
            logging.debug("end utterence")
            if ARGS.savewav:
                vad_audio.write_wav(os.path.join(ARGS.savewav, datetime.now().strftime("savewav_%Y-%m-%d_%H-%M-%S_%f.wav")), wav_data)
                wav_data = bytearray()
            text = stream_context.finishStream()
            print("Recognized: %s" % text)

            # This makes gets the modular adapter to connect to a WiFi network given that the current_networ and password are atleast
            # something.
            if((text == "connect" or text == "cnnect" or text == "net" or text == "that") and current_network != "" and password != ""):
                connect_to_wifi(password, current_network)
            if(len(current_network) != 0):
                if(text == "destroy"):
                    password = ""
                elif(text == "yes"):
                    password += " "
                    password += inference_word
                else:
                    inference_word = text
            # This is where the user can actually select one of the three WiFi networks.
            if(len(wifi_networks) != 0):
                if(text == "the first one" or text == "first one" or text == "first" or text == "one"):
                    current_network = wifi_networks[0].ssid
                    print("Selected Network: " + current_network)
                elif((text == "the second one" or text == "second one" or text == "second" or text == "to") and len(wifi_networks) >= 2):
                    current_network = wifi_networks[1].ssid
                    print("Selected Network: " + current_network)
                elif((text == "the third one" or text == "third one" or text == "third") and len(wifi_networks) >= 3):
                    current_network = wifi_networks[2].ssid
                    print("Selected Network: " + current_network)
                else:
                    pass


            # This part of the program initiates the program. This is where the user prompts the device to find available networks.
            if(text == "find internet networks" or text == "find internet" or text == "ind internet" or text == "internet"):
                 wifi_networks = find_wifi_networks(wifi_networks)

            stream_context = model.createStream()

if __name__ == '__main__':
    DEFAULT_SAMPLE_RATE = 48000

    import argparse
    parser = argparse.ArgumentParser(description="Stream from microphone to DeepSpeech using VAD")

    parser.add_argument('-v', '--vad_aggressiveness', type=int, default=3,
                        help="Set aggressiveness of VAD: an integer between 0 and 3, 0 being the least aggressive about filtering out non-speech, 3 the most aggressive. Default: 3")
    parser.add_argument('--nospinner', action='store_true',
                        help="Disable spinner")
    parser.add_argument('-w', '--savewav',
                        help="Save .wav files of utterences to given directory")
    parser.add_argument('-f', '--file',
                        help="Read from .wav file instead of microphone")

    parser.add_argument('-m', '--model', required=True,
                        help="Path to the model (protocol buffer binary file, or entire directory containing all standard-named files for model)")
    parser.add_argument('-s', '--scorer',
                        help="Path to the external scorer file.")
    parser.add_argument('-d', '--device', type=int, default=None,
                        help="Device input index (Int) as listed by pyaudio.PyAudio.get_device_info_by_index(). If not provided, falls back to PyAudio.get_default_device().")
    parser.add_argument('-r', '--rate', type=int, default=DEFAULT_SAMPLE_RATE,
                        help=f"Input device sample rate. Default: {DEFAULT_SAMPLE_RATE}. Your device may require 44100.")

    ARGS = parser.parse_args()
    if ARGS.savewav: os.makedirs(ARGS.savewav, exist_ok=True)
    main(ARGS)
