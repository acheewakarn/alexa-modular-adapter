/*
 * Add these two lines to the bottom of CMakeLists.txt in SampleApp/src 
 * to link the libraries
 *
 * target_link_libraries(SampleApp "-lwiringPi")
 * target_link_libraries(SampleApp "-ljsoncpp")
 *
 * If you have troubles, this guide helps:
 * https://developer.amazon.com/en-US/docs/alexa/alexa-voice-service/indicate-device-state-with-leds.html
*/

#include <memory>
#include <unordered_map>
#include <utility>
#include <vector>

#include "ConsolePrinter.h"
#include "ConsoleReader.h"
#include "DefaultClient/EqualizerRuntimeSetup.h"
#include "SampleApp/GuiRenderer.h"
#include "SampleApplicationReturnCodes.h"
#include "UserInputManager.h"

#include <iostream>
#include <fstream>
#include <csignal>
#include <wiringPi.h>
#include <strings.h>
#include <jsoncpp/json/json.h>

void GPIO_Control(std::string Called_Device, std::string Controller_Type) {
    // Open configuration file containing each device's capabilities
    std::ifstream config_file("/home/pi/connectedDevices.json");
    
    if (config_file.is_open()) {
        Json::Value root;
        config_file >> root;
        bool valid_device = false;
        
        // See if device being called is in config file
        for(const Json::Value& Device : root["Devices"]) {
            
            std::cout << Device["name"] << std::endl;
            std::cout << Device["connected"] << std::endl;
            
            // Case-insensitive to reduce format errors between Alexa commmands and configuration file
            if(strcasecmp(Called_Device.c_str(), Device["name"].asString().c_str()) == 0) {
                valid_device = true;
            
                // Proceed with GPIO control if valid device and command
                wiringPiSetupGpio();
                
                if(strcasecmp(Controller_Type.c_str(), "PowerController") == 0) {
   
                } else if(strcasecmp(Controller_Type.c_str(), "ToggleController") == 0) {
                 
                } else if(strcasecmp(Controller_Type.c_str(), "RangeController") == 0) {
              
                } else if(strcasecmp(Controller_Type.c_str(), "ModeController") == 0) {

                } else {
                    std::cout << "Command was not recognized." << std::endl;
                }
            }
            break;
        }
        if(valid_device == false) {
            std::cout << "Device does not exist within configuration file." << std::endl;
        }
    } else {
        std::cout << "Configuration file was not found." << std::endl;
    }
}
