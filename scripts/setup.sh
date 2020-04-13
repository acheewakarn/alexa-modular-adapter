echo 'Setting up SmartHome for AVS...'

echo 'Copying files to destination...'
cp -f ../src/*.cpp ~/sdk-folder/sdk-source/avs-device-sdk/SampleApp/src

echo 'Building...'
cd ~/sdk-folder/sdk-build
cmake ~/sdk-folder/sdk-source/avs-device-sdk \
-DSENSORY_KEY_WORD_DETECTOR=ON \
-DSENSORY_KEY_WORD_DETECTOR_LIB_PATH=/home/pi/sdk-folder/third-party/alexa-rpi/lib/libsnsr.a \
-DSENSORY_KEY_WORD_DETECTOR_INCLUDE_DIR=/home/pi/sdk-folder/third-party/alexa-rpi/include \
-DGSTREAMER_MEDIA_PLAYER=ON \
-DPORTAUDIO=ON \
-DPORTAUDIO_LIB_PATH=/home/pi/sdk-folder/third-party/portaudio/lib/.libs/libportaudio.a \
-DPORTAUDIO_INCLUDE_DIR=/home/pi/sdk-folder/third-party/portaudio/include \
-DENABLE_ALL_ENDPOINT_CONTROLLERS=ON

make SampleApp

echo 'Generate config.json...'
cd ~/sdk-folder/sdk-source/avs-device-sdk/tools/Install 

bash genConfig.sh config.json 12345 \
~/sdk-folder/db \
~/sdk-folder/sdk-source/avs-device-sdk \
~/sdk-folder/sdk-build/Integration/AlexaClientSDKConfig.json \
-DSDK_CONFIG_MANUFACTURER_NAME="raspberrypi" \
-DSDK_CONFIG_DEVICE_DESCRIPTION="raspberrypi" \

echo 'Running AVS SDK: Sample App...'
cd /home/pi/sdk-folder/sdk-build
./SampleApp/src/SampleApp ./Integration/AlexaClientSDKConfig.json ../third-party/alexa-rpi/models