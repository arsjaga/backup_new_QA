*** Settings ***
Library          USB
Library          Serial
Library          Dialogs
Library          SeleniumLibrary
Library          DateTime
Library          Process
Library          OperatingSystem

*** Variables ***

${PRODUCT_SERIAL_FILE} =  ${CURDIR}/../test_cases/product-serial.txt

*** Keywords ***
Get Device Port
    Pause Execution  Disconnect the serial interface from host pc
    Wait for USB Device  2s
    ${Disconnected} =  Get Ports
    Pause Execution  Connect the serial interface to host pc
    Wait for USB Device  2s
    ${Connected} =  Get Ports
    ${Detected_Device} =  Evaluate  list(set(${Connected}) - set(${Disconnected}))
    Set Suite Variable  ${DEVICE_PORT}  ${Detected_Device[0]}

Open Serial Connection
    [Arguments]  ${device_port}  ${baudrate}
    Open Serial Port  ${device_port}  ${baudrate}
    Flush Received Data

Close Serial Connection
    Close Serial Port

Read Response
    [Arguments]  ${read_response}
    ${Response}=  Read Until  >
    Should Be Equal  ${Response}  ${read_response}

Input Product Meta Data from User
    [Arguments]  ${db_file}  ${db_path}
    Read CSV File  ${db_file}
    Setup QA Meta Data
    Export Product Serial Number  ${db_path}

Setup port and CSV File
    [Arguments]  ${db_file}  ${db_path}
    Input Product Meta Data from User  ${db_file}  ${db_path}
    Get Device Port

Wait for USB Device
    [Arguments]  ${time}
    sleep  ${time}
