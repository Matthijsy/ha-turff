# Turff for Home Assistant
The Turff Integration allows you to track the balance or all products of your [turff.nl](https://www.turff.nl/) household. 

## Installation
Copy the content of the `custom_components` directory of this repository into the `custom_components` directory of your Home Assistant installation. After you have done this restart your Home Assistant.

## Configuration via the frontend

Menu: **Configuration** -> **Integrations**.

Click on the `+` sign to add an integration and click on **Turff**.
Follow the configuration flow, after finishing, the Turff
integration will be available.

## Sensors

This integration provides sensors for every product in your Turff account. The state of the sensor will be the total balance. The balance of every user will be available within the sensor attributes.


## Remark
Currently the integration with the Turff "API" is also placed within this repository. This is not in line with the HA recommendations, and might be changed in the future to improve the integration.