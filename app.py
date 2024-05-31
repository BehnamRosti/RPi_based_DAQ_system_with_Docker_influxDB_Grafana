from influxdb import InfluxDBClient
import time
import smbus
import os
import board
import busio
from datetime import datetime
import adafruit_mcp9808
import adafruit_tmp117
import adafruit_bme280
import adafruit_sht31d
import adafruit_scd30
import adafruit_tsl2591
import adafruit_veml7700
import adafruit_bh1750
import adafruit_si1145
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

#---------------------------------------------
# Configure InfluxDB connection variables
host = "influxdb"
port = 8086
user = "admin"
password = "admin"
dbname = "sensordata"

# Create the InfluxDB client object
client = InfluxDBClient(host, port, user, password, dbname)

#---------------------------------------------
# Initialize I2C buses
i2c1 = busio.I2C(board.SCL, board.SDA)
i2c2 = busio.I2C(board.D1, board.D0)

#---------------------------------------------
# Define sensor configurations
sensors_config = [
    {"name": "mcp1", "class": adafruit_mcp9808.MCP9808, "bus": i2c1, "address": None, "location": "cavity"},            # Tco_low
    {"name": "mcp2", "class": adafruit_mcp9808.MCP9808, "bus": i2c1, "address": 0x19, "location": "cavity"},            # Tco_mid
    {"name": "mcp3", "class": adafruit_mcp9808.MCP9808, "bus": i2c1, "address": 0x1a, "location": "cavity"},            # Tco_up
    {"name": "mcp4", "class": adafruit_mcp9808.MCP9808, "bus": i2c1, "address": 0x1b, "location": "cavity"},            # Tci_low
    {"name": "mcp5", "class": adafruit_mcp9808.MCP9808, "bus": i2c1, "address": 0x1c, "location": "cavity"},            # Tci_mid
    {"name": "mcp6", "class": adafruit_mcp9808.MCP9808, "bus": i2c1, "address": 0x1d, "location": "cavity"},            # Tci_up
    {"name": "mcp7", "class": adafruit_mcp9808.MCP9808, "bus": i2c1, "address": 0x1e, "location": "glazing"},           # Ts_oo
    {"name": "mcp8", "class": adafruit_mcp9808.MCP9808, "bus": i2c1, "address": 0x1f, "location": "glazing"},           # Ts_oi
    {"name": "tmp1", "class": adafruit_tmp117.TMP117, "bus": i2c1, "address": None, "location": "glazing"},             # Ts_oo
    {"name": "bme1", "class": adafruit_bme280.Adafruit_BME280_I2C, "bus": i2c1, "address": None, "location": "outdoor"},# T_out
    {"name": "sht1", "class": adafruit_sht31d.SHT31D, "bus": i2c1, "address": None, "location": "outdoor"},             # T_out
    {"name": "scd1", "class": adafruit_scd30.SCD30, "bus": i2c1, "address": None, "location": "outdoor"},               # C_out
    {"name": "tsl1", "class": adafruit_tsl2591.TSL2591, "bus": i2c1, "address": None, "location": "outdoor"},           # I_out
    {"name": "bh1", "class": adafruit_bh1750.BH1750, "bus": i2c1, "address": None, "location": "outdoor"},              # I_out
    {"name": "veml1", "class": adafruit_veml7700.VEML7700, "bus": i2c1, "address": None, "location": "outdoor"},        # I_out
    {"name": "si1", "class": adafruit_si1145.SI1145, "bus": i2c1, "address": None, "location": "outdoor"},              # I_out
    {"name": "mcp9", "class": adafruit_mcp9808.MCP9808, "bus": i2c2, "address": None, "location": "glazing"},           # Ts_io
    {"name": "mcp10", "class": adafruit_mcp9808.MCP9808, "bus": i2c2, "address": 0x19, "location": "glazing"},          # Ts_ii
    {"name": "tmp2", "class": adafruit_tmp117.TMP117, "bus": i2c2, "address": None, "location": "glazing"},             # Ts_ii
    {"name": "bme2", "class": adafruit_bme280.Adafruit_BME280_I2C, "bus": i2c2, "address": None, "location": "indoor"}, # T_in
    {"name": "sht2", "class": adafruit_sht31d.SHT31D, "bus": i2c2, "address": None, "location": "indoor"},              # T_in
    {"name": "scd2", "class": adafruit_scd30.SCD30, "bus": i2c2, "address": None, "location": "indoor"},                # C_in
    {"name": "tsl2", "class": adafruit_tsl2591.TSL2591, "bus": i2c2, "address": None, "location": "indoor"},            # I_in
    {"name": "bh2", "class": adafruit_bh1750.BH1750, "bus": i2c2, "address": None, "location": "indoor"},               # I_in
    {"name": "veml2", "class": adafruit_veml7700.VEML7700, "bus": i2c2, "address": None, "location": "indoor"},         # I_in
    {"name": "si2", "class": adafruit_si1145.SI1145, "bus": i2c2, "address": None, "location": "indoor"},               # I_in
]

#------------------------------------------------------------------------------------------------
# Initialize ADS1115 sensor
ads = ADS.ADS1115(i2c1, address=0x4b) # we chose this address to avoid conflict with other sensors address
ads.gain = 1
chan1 = AnalogIn(ads, ADS.P0, ADS.P1) # Create differential input between channel A0 & A1 for q_out
chan2 = AnalogIn(ads, ADS.P2, ADS.P3) # Create differential input between channel A2 & A3 for q_in

#---------------------------------------------
# Initialize SDP sensors
def readDP_sdp610(busnum):
    bus = smbus.SMBus(busnum)
    addr = 0x40
    MAXPRESSURE = 25
    scalefactor = 1200.0 if MAXPRESSURE == 25 else 240.0 if MAXPRESSURE == 125 else 60.0 if MAXPRESSURE == 500 else exit(1)
    
    bus.write_byte(addr, 0xF1)
    time.sleep(1)
    MSB = bus.read_byte(addr)
    LSB = bus.read_byte(addr)
    result = (MSB << 8) + LSB
  
    if result > 0x7FFF:
        result -= 0x10000
    differential_pressure = float(result / scalefactor)
    bus.close()
    return differential_pressure

def readDP_sdp810(busnum):
    bus = smbus.SMBus(busnum)
    address = 0x25
    bus.write_i2c_block_data(address, 0x3F, [0xF9]) # Stop any cont measurement of the sensor
    time.sleep(1)
    bus.write_i2c_block_data(address, 0x36, [0x03]) # Start single shot measurement
    time.sleep(1)
    reading = bus.read_i2c_block_data(address, 0, 9)
    pressure_value = reading[0] + float(reading[1]) / 255
    differential_pressure = (pressure_value * 240 / 256) if pressure_value < 128 else (-(256 - pressure_value) * 240 / 256)
    bus.close()
    return differential_pressure

#---------------------------------------------
# Initialize sensors
sensors = {}
for sensor in sensors_config:
    if sensor["address"]:
        sensors[sensor["name"]] = sensor["class"](sensor["bus"], address=sensor["address"])
    else:
        sensors[sensor["name"]] = sensor["class"](sensor["bus"])

# Set sensor configurations
sensors["bme1"].sea_level_pressure = 1013.25
sensors["bme2"].sea_level_pressure = 1013.25

#------------------------------------------------------------------------------------------------
# Ensure the data directory exists
data_directory = "/app/data"
os.makedirs(data_directory, exist_ok=True)

# Paths to data files
sensor_files = {sensor["name"]: os.path.join(data_directory, f"{sensor['name']}.csv") for sensor in sensors_config}
sensor_files["hfm1"] = os.path.join(data_directory, "hfm1.csv")
sensor_files["hfm2"] = os.path.join(data_directory, "hfm2.csv")
sensor_files["sdp1_810"] = os.path.join(data_directory, "sdp1_810.csv")
sensor_files["sdp1_610"] = os.path.join(data_directory, "sdp1_610.csv")
sensor_files["sdp2_810"] = os.path.join(data_directory, "sdp2_810.csv")
sensor_files["sdp2_610"] = os.path.join(data_directory, "sdp2_610.csv")

#---------------------------------------------
# Initialize data files with headers
headers = {
    "mcp": "timestamp,temperature\n",
    "tmp": "timestamp,temperature\n",
    "bme": "timestamp,temperature,humidity,pressure\n",
    "sht": "timestamp,temperature,humidity\n",
    "scd": "timestamp,temperature,humidity,co2\n",
    "tsl": "timestamp,lux\n",
    "bh": "timestamp,lux\n",
    "veml": "timestamp,lux\n",
    "si": "timestamp,uv,visible,ir\n",
    "hfm": "timestamp,voltage,value\n",
    "sdp": "timestamp,differential_pressure\n",
}

#---------------------------------------------
for sensor, file_path in sensor_files.items():
    prefix = sensor[:3]
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write(headers[prefix])

#---------------------------------------------
def write_sensor_data(sensor_data):
    client.write_points(sensor_data)
    
#---------------------------------------------
def write_to_file(file_path, data):
    with open(file_path, "a") as f:
        f.write(",".join(map(str, data)) + "\n")

#---------------------------------------------
def read_sensor(sensor, sensor_type):
    if sensor_type == "mcp" or sensor_type == "tmp":
        return {"temperature": sensor.temperature}
    elif sensor_type == "bme":
        return {
            "temperature": sensor.temperature,
            "humidity": sensor.humidity,
            "pressure": sensor.pressure,
        }
    elif sensor_type == "sht":
        return {
            "temperature": sensor.temperature,
            "humidity": sensor.relative_humidity,
        }
    elif sensor_type == "scd":
        return {
            "temperature": sensor.temperature,
            "humidity": sensor.relative_humidity,
            "co2": sensor.CO2,
        }
    elif sensor_type == "tsl":
        return {"lux": sensor.lux}
    elif sensor_type == "bh" or sensor_type == "veml":
        return {"lux": sensor.lux}
    elif sensor_type == "si":
        return {
            "uv": sensor.read_uv,
            "visible": sensor.read_visible,
            "ir": sensor.read_ir,
        }

#---------------------------------------------
def format_data(sensor, location, fields):
    return [
        {
            "measurement": "sensor_data",
            "tags": {
                "sensor": sensor,
                "location": location,
            },
            "fields": fields,
        }
    ]

#------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    while True:
        try:
            timestamp = datetime.utcnow().isoformat()

            for sensor in sensors_config:
                sensor_name = sensor["name"]
                sensor_type = sensor_name[:3]
                data = read_sensor(sensors[sensor_name], sensor_type)
                json_data = format_data(sensor_name, sensor["location"], data)
                
                # Write data to InfluxDB
                write_sensor_data(json_data)
                
                # Write data to CSV files
                file_data = [timestamp] + list(data.values())
                write_to_file(sensor_files[sensor_name], file_data)
                
                # Print data to console (optional)
                print(f"{sensor_name.upper()}: {data}")
            
            #---------------------------------------------
            # Read and process ADS1115 data
            hfm1_voltage = chan1.voltage
            hfm1_value = hfm1_voltage * 1e6 / 63.55 # q_out
            hfm2_voltage = chan2.voltage
            hfm2_value = hfm2_voltage * 1e6 / 62.98 # q_in
            
            hfm1_json = format_data("hfm1", "glazing", {"voltage": hfm1_voltage, "value": hfm1_value})
            hfm2_json = format_data("hfm2", "glazing", {"voltage": hfm2_voltage, "value": hfm2_value})

            write_sensor_data(hfm1_json)
            write_sensor_data(hfm2_json)

            write_to_file(sensor_files["hfm1"], [timestamp, hfm1_voltage, hfm1_value])
            write_to_file(sensor_files["hfm2"], [timestamp, hfm2_voltage, hfm2_value])

            print(f"HFM1: voltage={hfm1_voltage}, value={hfm1_value}")
            print(f"HFM2: voltage={hfm2_voltage}, value={hfm2_value}")
            
            #---------------------------------------------
            # Read and process SDP data
            sdp1_810 = readDP_sdp810(0)
            sdp1_610 = readDP_sdp610(0)
            sdp2_810 = readDP_sdp810(1)
            sdp2_610 = readDP_sdp610(1)
            
            sdp1_810_json = format_data("sdp1_810", "outdoor", {"differential_pressure": sdp1_810})
            sdp1_610_json = format_data("sdp1_610", "outdoor", {"differential_pressure": sdp1_610})
            sdp2_810_json = format_data("sdp2_810", "indoor", {"differential_pressure": sdp2_810})
            sdp2_610_json = format_data("sdp2_610", "indoor", {"differential_pressure": sdp2_610})

            write_sensor_data(sdp1_810_json)
            write_sensor_data(sdp1_610_json)
            write_sensor_data(sdp2_810_json)
            write_sensor_data(sdp2_610_json)

            write_to_file(sensor_files["sdp1_810"], [timestamp, sdp1_810])
            write_to_file(sensor_files["sdp1_610"], [timestamp, sdp1_610])
            write_to_file(sensor_files["sdp2_810"], [timestamp, sdp2_810])
            write_to_file(sensor_files["sdp2_610"], [timestamp, sdp2_610])

            print(f"SDP1_810: differential_pressure={sdp1_810}")
            print(f"SDP1_610: differential_pressure={sdp1_610}")
            print(f"SDP2_810: differential_pressure={sdp2_810}")
            print(f"SDP2_610: differential_pressure={sdp2_610}")
            
            #---------------------------------------------
            # Wait for 10 seconds before reading again
            time.sleep(10)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)
