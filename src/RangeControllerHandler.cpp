/*
 * Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *     http://aws.amazon.com/apache2.0/
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

#include "SampleApp/ConsolePrinter.h"
#include "SampleApp/RangeControllerHandler.h"
#include "SampleApp/SampleApplication.h"

#include <AVSCommon/Utils/Configuration/ConfigurationNode.h>
#include <AVSCommon/Utils/JSON/JSONUtils.h>
#include <AVSCommon/Utils/Logger/Logger.h>

#include <algorithm>
#include <iostream>
#include <list>
#include <wiringPi.h>
#include <time.h>
#include "jsoncpp/json/json.h"

/// The range controller maximum range.
static const double MAXIMUM_RANGE = 10;

/// The range controller minimum range.
static const double MINIMUM_RANGE = 0;

/// The range controller precision.
static const double RANGE_PRECISION = 0.1;

/// String to identify log entries originating from this file.
static const std::string TAG("RangeControllerHandler");

/**
 * Create a LogEntry using this file's TAG and the specified event string.
 *
 * @param The event string for this @c LogEntry.
 */
#define LX(event) avsCommon::utils::logger::LogEntry(TAG, event)

namespace alexaClientSDK {
namespace sampleApp {

using namespace avsCommon::avs;
using namespace avsCommon::sdkInterfaces;
using namespace avsCommon::sdkInterfaces::rangeController;

std::shared_ptr<RangeControllerHandler> RangeControllerHandler::create(std::string endpointId) {
    auto rangeControllerHandler = std::shared_ptr<RangeControllerHandler>(new RangeControllerHandler(endpointId));
    return rangeControllerHandler;
}

RangeControllerHandler::RangeControllerHandler(std::string endpointId) :
        m_endpointId(endpointId),
        m_currentRangeValue{MINIMUM_RANGE},
        m_maximumRangeValue{MAXIMUM_RANGE},
        m_minmumRangeValue{MINIMUM_RANGE},
        m_precision{RANGE_PRECISION} {
}

RangeControllerInterface::RangeControllerConfiguration RangeControllerHandler::getConfiguration() {
    std::lock_guard<std::mutex> lock{m_mutex};
    return {m_minmumRangeValue, m_maximumRangeValue, m_precision};
}

std::pair<AlexaResponseType, std::string> RangeControllerHandler::setRangeValue(
    double value,
    AlexaStateChangeCauseType cause) {
    std::list<std::shared_ptr<RangeControllerObserverInterface>> copyOfObservers;
    bool notifyObserver = false;

    {
        std::lock_guard<std::mutex> lock{m_mutex};
        if (value < m_minmumRangeValue || value > m_maximumRangeValue) {
            ACSDK_ERROR(LX("setRangeValueFailed").d("reason", "valueOutOfSupportedRange").d("value", value));
            return std::make_pair(AlexaResponseType::VALUE_OUT_OF_RANGE, "valueOutOfSupportedRange");
        }

        if (m_currentRangeValue != value && strcmp(m_endpointId.c_str(), "Table") == 0) {
            if(DetectDevice(m_endpointId)) {
                ConsolePrinter::prettyPrint("DEVICE NAME: " + m_endpointId);
                ConsolePrinter::prettyPrint("SET RANGE TO : " + std::to_string(value));  
                    
                //Read/update height value in json file
                Json::Value root;
                Json::Reader reader;
                Json::StyledStreamWriter writer;
                std::ofstream outFile;
                std::ifstream config_file("/home/pi/connectedDevices.json");
                
                if(!reader.parse(config_file, root)) {
                    std::cout << reader.getFormattedErrorMessages();
                } else {
                    // Calculate requested height since scaling is from 1-10
                    if(root.isMember(m_endpointId.c_str())) {  
                        double currentHeight = root[m_endpointId]["CurrentRangeValue"].asDouble();
                        double minRange = root[m_endpointId]["Range"][0].asDouble();
                        double maxRange = root[m_endpointId]["Range"][1].asDouble();
                        double scalingFactor = (maxRange-minRange)/MAXIMUM_RANGE;
                        double requestedHeight = (value * scalingFactor) + minRange;
                        double timeToCompleteRange = 11.57;
                        double heightAdjust = timeToCompleteRange * ((abs(currentHeight-requestedHeight) / (maxRange-minRange)));
                        int raisePin = 23;
                        int lowerPin = 24;
                        
                        wiringPiSetupGpio();
                        pinMode(raisePin, OUTPUT);  
                        pinMode(lowerPin, OUTPUT); 
                         
                        // Raise desk    
                        if(requestedHeight > currentHeight) {
                            digitalWrite(raisePin, LOW);
                            delay(heightAdjust*1000);
                            digitalWrite(raisePin, HIGH);
                        // Lower desk    
                        } else {
                            digitalWrite(lowerPin, LOW);
                            delay(heightAdjust*1000);
                            digitalWrite(lowerPin, HIGH);
                        }
                        root[m_endpointId]["CurrentRangeValue"] = requestedHeight;
                        outFile.open("/home/pi/connectedDevices.json");
                        writer.write(outFile, root);
                        outFile.close(); 
                    }
                    
                    m_currentRangeValue = value;
                    copyOfObservers = m_observers;
                    notifyObserver = true;
                
                }
            }
        }
    }

    if (notifyObserver) {
        notifyObservers(
            RangeControllerInterface::RangeState{
                m_currentRangeValue, avsCommon::utils::timing::TimePoint::now(), std::chrono::milliseconds(0)},
            cause,
            copyOfObservers);
    }

    return std::make_pair(AlexaResponseType::SUCCESS, "");
}

std::pair<AlexaResponseType, std::string> RangeControllerHandler::adjustRangeValue(
    double deltaValue,
    AlexaStateChangeCauseType cause) {
    std::list<std::shared_ptr<RangeControllerObserverInterface>> copyOfObservers;
    bool notifyObserver = false;

    {
        std::lock_guard<std::mutex> lock{m_mutex};
        auto newvalue = m_currentRangeValue + deltaValue;
        if (newvalue < m_minmumRangeValue || newvalue > m_maximumRangeValue) {
            ACSDK_ERROR(
                LX("adjustRangeValueFailed").d("reason", "requestedRangeValueInvalid").d("deltaValue", deltaValue));
            return std::make_pair(AlexaResponseType::VALUE_OUT_OF_RANGE, "ValueOutOfRange");
        }

        m_currentRangeValue += deltaValue;
        ConsolePrinter::prettyPrint("ADJUSTED RANGE TO : " + std::to_string(m_currentRangeValue));
        copyOfObservers = m_observers;
        notifyObserver = true;
    }

    if (notifyObserver) {
        notifyObservers(
            RangeControllerInterface::RangeState{
                m_currentRangeValue, avsCommon::utils::timing::TimePoint::now(), std::chrono::milliseconds(0)},
            cause,
            copyOfObservers);
    }

    return std::make_pair(AlexaResponseType::SUCCESS, "");
}

std::pair<AlexaResponseType, avsCommon::utils::Optional<RangeControllerInterface::RangeState>> RangeControllerHandler::
    getRangeState() {
    std::lock_guard<std::mutex> lock{m_mutex};
    return std::make_pair(
        AlexaResponseType::SUCCESS,
        avsCommon::utils::Optional<RangeControllerInterface::RangeState>(RangeControllerInterface::RangeState{
            m_currentRangeValue, avsCommon::utils::timing::TimePoint::now(), std::chrono::milliseconds(0)}));
}

bool RangeControllerHandler::addObserver(std::shared_ptr<RangeControllerObserverInterface> observer) {
    std::lock_guard<std::mutex> lock{m_mutex};
    m_observers.push_back(observer);
    return true;
}

void RangeControllerHandler::removeObserver(const std::shared_ptr<RangeControllerObserverInterface>& observer) {
    std::lock_guard<std::mutex> lock{m_mutex};
    m_observers.remove(observer);
}

void RangeControllerHandler::notifyObservers(
    const RangeControllerInterface::RangeState& rangeState,
    AlexaStateChangeCauseType cause,
    std::list<std::shared_ptr<RangeControllerObserverInterface>> observers) {
    ACSDK_DEBUG5(LX(__func__));
    for (auto& observer : observers) {
        observer->onRangeChanged(rangeState, cause);
    }
}

void RangeControllerHandler::setRangeValue(double value) {
    auto result = setRangeValue(value, AlexaStateChangeCauseType::APP_INTERACTION);
    if (AlexaResponseType::SUCCESS != result.first) {
        ACSDK_ERROR(LX("setRangeValueFailed").d("AlexaResponseType", result.first).d("Description", result.second));
    } else {
        ACSDK_DEBUG5(LX(__func__).m("Success"));
    }
}

}  // namespace sampleApp
}  // namespace alexaClientSDK
