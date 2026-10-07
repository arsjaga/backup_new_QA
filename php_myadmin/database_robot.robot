*** Settings ***
Library          database.Database
Library          Process
Library          OperatingSystem
Library          Dialogs
Library          DateTime
Resource         common.resource


Suite Setup     Connect Database and Setup QA Meta Data
Suite Teardown   QA Suite Teardown

*** Keywords ***

Connect Database and Setup QA Meta Data
    Connect Database    product_db
    Setup QA Meta Data
    Get Device Port
    Open Serial Connection    ${DEVICE_PORT}    115200

Setup QA Meta Data
    ${serial_number}=  Get Value From User  Update Product Serial Number
    Set Suite Variable  ${PRODUCT_SERIAL_NUMBER}  ${serial_number}
    Insert the Values in Table    ${PRODUCT_SERIAL_NUMBER}

    ${Hardware Version}=  Get Value From User  Update Hardware Version
    Update Test Data  ${PRODUCT_SERIAL_NUMBER}  Hardware_Version  ${Hardware Version}
    ${QA Performed By}=  Get Value From User  Update QA Performed By
    Update Test Data  ${PRODUCT_SERIAL_NUMBER}  QA_Performed_By  ${QA Performed By}
    ${QA_Performed_On}  Get Current Date  result_format=%d/%m/%Y
    Update Test Data  ${PRODUCT_SERIAL_NUMBER}  QA_Performed_On  ${QA_Performed_On}

QA Suite Teardown
    ${status}=    Set Variable    ${TEST_STATUS}
    Update Test Data    ${PRODUCT_SERIAL_NUMBER}    QA_Passed    ${status}
    Close Database
    Close Serial Connection

Test Connection    
    Create Table In Database
    Check Table Exists    USB_RELAY
    Setup QA Meta Data

Send serial command for Version
    Write  V\r

Verify the Device version matches the 1.4.0 Version
    Read Response  V\r\n1.4.0\r\nOK\r\n>
    Update Test Data  ${PRODUCT_SERIAL_NUMBER} Firmware_Version  1.4.0

Send serial command for CRC
    Write  h\r

Verify the Device CRC Value matches CRC:0xFB89EB37 Value
    Read Response  h\r\nCRC:0xFB89EB37\r\nOK\r\n>

*** Test Cases ***
Test to check 1.4.0 Version
    Send serial command for Version
    Verify the Device version matches the 1.4.0 Version

Test to check 0xFB89EB37 Checksum
    Send serial command for CRC
    Verify the Device CRC Value matches CRC:0xFB89EB37 Value
