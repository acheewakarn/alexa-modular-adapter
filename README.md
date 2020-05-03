# Alexa-Enabled Accessibility
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

## Resources
1. [AVS Device SDK Endpoints](https://developer.amazon.com/en-US/docs/alexa/avs-device-sdk/endpoints.html): This article goes through the four endpoints that are on the AVS Home Kit: ModeController, PowerController, RangeController, and ToggleController. Also discusses the device discoball that has the ModeController, PowerController, RangeController, and ToggleController already enabled to it.
