import serial
import threading
import csv
import os
from datetime import datetime

ser = serial.Serial()   # open serial port

print(ser.name)  

#set frequency and seconds wanted
frequency = 20 #hz  1- 20
seconds_wanted = 20 #In seconds

#set on file name and location
output_filename = 'dmm_out_oldPrototypev2.csv'
output_directory = "/home/tomasinha/Desktop"

# Serial port setup and open
ser.port = "/dev/ttyUSB0"  

no_of_records = seconds_wanted*frequency
logging_period = 1/frequency
print(logging_period)
os.chdir(output_directory)

ser.baudrate = 115200
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.xonxoff = True
ser.rtscts = False  
ser.dsrdtr = False
ser.timeout = 0.1  # seconds
try:
    ser.open()
except:
    print("Cannot open serial port...")
    exit()

dmm_response_ok = 1
measurements = list()
measurements.append(['TIMESTAMP', 'CMD_ACK', 'VALUE', 'UNIT', 'STATE', 'ATTRIBUTE'])


# This starts a thread every N seconds
def logger():
    global no_of_records
    global dmm_response_ok
    global measurements

    no_of_records -= 1
    # Check if the last response was valid
    if dmm_response_ok == 0:
        print("DMM not responding. Check connections and make sure that the dmm is turned on")
    if no_of_records >= 0 and dmm_response_ok:
        #Start a new instance of logger after logging_period seconds
        threading.Timer(logging_period, logger).start()
        #Make a measurement, decode it and append to measurements list
        measurements.append(decode_response(read_with_qm()))
    else:
        #Write the measurements list to a CSV file
        write_csv(output_filename, measurements)
        ser.close()
        print("done")


# Send 'QM' command and read the response
def read_with_qm():
    # Flush buffers and send command in ASCII
    ser.flushInput()
    ser.flushOutput()
    ser.write(('QM' + '\r').encode('utf-8'))
    # Define End Of Line character
    response = b''
    second_eol = False
    # Read the response
    while True:
        # Fetch a character from the receive buffer
        c = ser.read(1)
        if c:
            # Append characters to response
            response += c
            if c == b'\r':
                # Break when the second EOL comes
                if second_eol:
                    break
                else:
                    # When the first EOL comes set the second_eol flag True
                    second_eol = True
        else:
            break
    return response


# Decode the dmm's response and return a list
def decode_response(response):
    global dmm_response_ok
    measurement_list = list()
    # Timestamp
    measurement_list.append(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
    if len(response) > 0:
        response_string = response.decode("utf-8")
        response_split = response_string.split('\r')
        # Check if there are two '/r'
        if len(response_split) == 3:
            # CMD_ACK
            measurement_list.append(response_split[0])
            measurement_split = response_split[1].split(',')
            if len(measurement_split) == 4:
                # Value
                measurement_list.append(float(measurement_split[0]))
                # Unit
                measurement_list.append(measurement_split[1])
                # State
                measurement_list.append(measurement_split[2])
                # Attribute
                measurement_list.append(measurement_split[3])
                return measurement_list
            else:
                print("Exiting. Incorrect no of items...")
                dmm_response_ok = 0
        else:
            print("Exiting. Incorrect no of '\\r's...")
            dmm_response_ok = 0
    else:
        print("Exiting. No response from dmm...")
        dmm_response_ok = 0


# Write the csv file
def write_csv(filename, csv_list):
    print("writing_csv function")
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(csv_list)
        print("Measurements written to \"" + os.getcwd() + "\\" + filename + "\"")


# Start logging
logger()
print("started")