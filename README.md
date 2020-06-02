# Alexa Modular Adapter
UCSC Computer Science and Engineering Senior Capstone Project. Sponsored by Amazon; Amazon Alexa.

Working in collaboeration with the "Alexa for Everyone" Team @ Santa Cruz, CA

## Set Up AVS SDK
### Requirements
1. Raspberry Pi 3B or 4
2. Internet connection
3. USB microphone 
4. Keyboard
5. Mouse
6. A microSD card with Raspbian
7. Monitor (optional, can SSH from another device)

### Steps To Setup AVS Smart Home on RPI
1. Go this link [AVS Device SDK Repository](https://github.com/alexa/avs-device-sdk).
2. From that link, scroll down and select your platform (Raspberry Pi).
3. That link will give you a series of instructions. Follow those instructions until you get to the step "Build the SDK".
4. When you get to that step, you will run these commands instead of the ones given in the link:

```
 cd /home/pi/sdk-folder/sdk-build
 cmake /home/pi/sdk-folder/sdk-source/avs-device-sdk \
 -DSENSORY_KEY_WORD_DETECTOR=ON \
 -DSENSORY_KEY_WORD_DETECTOR_LIB_PATH=/home/pi/sdk-folder/third-party/alexa-rpi/lib/libsnsr.a \
 -DSENSORY_KEY_WORD_DETECTOR_INCLUDE_DIR=/home/pi/sdk-folder/third-party/alexa-rpi/include \
 -DGSTREAMER_MEDIA_PLAYER=ON \
 -DPORTAUDIO=ON \
 -DPORTAUDIO_LIB_PATH=/home/pi/sdk-folder/third-party/portaudio/lib/.libs/libportaudio.a \
 -DPORTAUDIO_INCLUDE_DIR=/home/pi/sdk-folder/third-party/portaudio/include
 -DENABLE_ALL_ENDPOINT_CONTROLLERS=ON
 ```
 
 5. After that command is done, type into the command line `make SampleApp`.
 6. Then keep following the rest of the instructions.
 7. Then run the Sample App.
 8. To make sure the AVS Smart Home endpoints are working, say the command "Hey Alexa, turn on discoball". From there should be somekind of message printed. If there is a message printed like "POWERSTATE: ON", that means AVS Home Kit Endpoints have been enabled on your AVS SDK.
9. Good Job! Now you have the AVS SDK on your RPI with AVS Home Kit Skills.


### Steps to Setup Our Application
1. Once you have the AVS SDK working on your Raspberry Pi, clone this repository.
2. Run the setup script, `bash scripts/setup.sh`.
3. Follow the above section from Step 5 to Step 7.
4. You should now have the Alexa Modular Adapter App installed.

### Steps to Setup and Run the Offline WiFi Voice Assistant
1. Go to directory va.
2. Run: ```pip3 install requirements```
3. You may run into an issue with not having a library called libf77blas.so. If so run this command: ```sudo apt-get install libatlas-base-dev```.
4. Then run this command: ```sudo -E python3 mic_vad_streaming.py -m ./deepspeech-0.7.0-models.tflite ```

### Trouble Shooting for Offline WiFi Voice Assitant
1. I have a problem where my program is always listening (i.e. the line on the command line is forever spinning).
   1. The solution that I found to this problem was the quality of my microphone. If you get this problem, it might be a sign for you to use a more upgraded microphone (i.e. ~$40). Sorry, given the sensitivity of the ```webrtcvad``` a small USB microphone will not cut it..
2. I have an error where it is not saying that I have bad SAMPLE_RATE.
   1. The solution that I found is to tweak the variable in the program called ```DEFAULT_SAMPLE_RATE``` to around 48000. You may need to play around to find a good Sample_Rate for your microphone.
3. I have an error where it says deepspeech is not a module.
   1. This problem has to do with sudo and it not being able to find the deepspeech python package.
   2. You would want to set the environment variable called PYTHONPATH and set up your sudo to recognize those python libraries.
   3. These resources should be helpful:
      1.[Set Up PYTHONPATH](https://bic-berkeley.github.io/psych-214-fall-2016/using_pythonpath.html)
      2. [Connect PYTHONPATH to sudo](https://stackoverflow.com/questions/25346171/cant-import-module-when-using-root-user)

## Resources
1. [AVS Device SDK Endpoints](https://developer.amazon.com/en-US/docs/alexa/avs-device-sdk/endpoints.html): This article goes through the four endpoints that are on the AVS Home Kit: ModeController, PowerController, RangeController, and ToggleController. Also discusses the device discoball that has the ModeController, PowerController, RangeController, and ToggleController already enabled to it.
