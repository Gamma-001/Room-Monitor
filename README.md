# Room-Monitor

#### A really basic room monitor using Bolt IOT and Arduino UNO

## Instructions to recreate

- Set up all the connections as provided in the schematics
- Create a new ardiuino project and paste in "monitor.ino"
- Install the required libraries
- Upload it to the Arduino board ( Note that this might fail the first time if serial pins are also connected, to avoid upload failure upload the code without serial pins connected )
- Turn off the arduino
- Connect the bolt wifi module to a power source, start the server by running "python main.py / python3 main.py"
- Reconnect the arduino and wait for the data to be collected ( you can modify the data collection rate if its too slow )


## Format of app_config.py

```python
bolt_api_key    = "------"
bolt_device_id  = "------"
twilio_sid      = "------"
twilio_key      = "------"
twilio_phone    = "------"
twilio_contacts = [
  "------",
  "------"
]
```
