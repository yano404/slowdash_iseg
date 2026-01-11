import os
import pathlib
import requests
import json
from dotenv import load_dotenv
from slowpy.control import ControlSystem, RandomWalkDevice
from slowpy.store import DataStore_SQLite, LongTableFormat

DOTENV_FILE = pathlib.Path(__file__).resolve().parent.parent.joinpath(".env").resolve()

load_dotenv(DOTENV_FILE)
    
hostname = os.environ.get("MPOD_HOST")
port = os.environ.get("MPOD_PORT")
user = os.environ.get("MPOD_USER")
password = os.environ.get("MPOD_PASS")
baseurl = f"http://{hostname}:{port}"
dbpath = os.environ.get("DBPATH")
interval = int(os.environ.get("LOG_INTERVAL"))
conf_det_list = os.environ.get("DET_LIST")

# Define functions to communicate with iCS
def get_apikey():
    try:
        r = requests.get(f"{baseurl}/api/login/{user}/{password}")
        if r.ok:
            return r.content.decode().replace('\n', '')
        else:
            print("Error: {r.status_code}")
            return None
    except requests.exceptions.ConnectionError as err:
        print(err)
        return None

def measure_voltage(apikey, line="*", address="*", channel="*"):
    try:
        r = requests.get(f"{baseurl}/api/getItem/{apikey}/{line}/{address}/{channel}/Status.voltageMeasure")
        if r.ok:
            return r.content
        else:
            print("Error: {r.status_code}")
            return None
    except requests.exceptions.ConnectionError as err:
        print(err)
        return None

def measure_current(apikey, line="*", address="*", channel="*"):
    try:
        r = requests.get(f"{baseurl}/api/getItem/{apikey}/{line}/{address}/{channel}/Status.currentMeasure")
        if r.ok:
            return r.content
        else:
            print("Error: {r.status_code}")
            return None
    except requests.exceptions.ConnectionError as err:
        print(err)
        return None


class MpodDataFormat(LongTableFormat):
    schema_numeric = '(datetime DATETIME, timestamp REAL, channel STRING, value REAL, PRIMARY KEY(timestamp, channel))'
    def insert_numeric_data(self, cur, timestamp, channel, value):
        cur.execute(f'INSERT INTO {self.table} VALUES(CURRENT_TIMESTAMP,%d,?,%f)' % (timestamp, value), (channel,))


ctrl = ControlSystem()
device = RandomWalkDevice(n=4)
datastore = DataStore_SQLite(
        dbpath,
        table="data",
        table_format=MpodDataFormat())


with open(conf_det_list) as f:
    det_list = json.load(f)


def _loop():
    for i, det in enumerate(det_list):

        line = det["id"][0]
        addr = det["id"][1]
        ch   = det["id"][2]
        det_id = line<<16 | addr<<8 | ch
        name = det["name"]

        # Get API key
        apikey = get_apikey()

        # Read voltage
        json_volt = measure_voltage(apikey, line, addr, ch)

        # Read current
        json_current = measure_current(apikey, line, addr, ch)

        if not json_volt:
            continue
        volt = json.loads(json_volt)
        volt = volt[0]["c"][0]
        data = volt["d"]
        val  = float(data["v"])
        unit = data["u"]
        t    = float(data["t"])
        if unit == "kV":
            val *= 1e3
        datastore.append(val, tag=f"{name}_V", timestamp=t)


        if not json_current:
            continue
        current = json.loads(json_current)
        current = current[0]["c"][0]
        data = current["d"]
        line = int(data["p"]["l"])
        addr = int(data["p"]["a"])
        ch   = int(data["p"]["c"])
        val  = float(data["v"])
        unit = data["u"]
        t    = float(data["t"])
        if unit == "kA":
            val *= 1e6
        elif unit == "A":
            val *= 1e3
        elif unit == "µA":
            val *= 1e-3
        elif unit == "nA":
            val *= 1e-6

        datastore.append(val, tag=f"{name}_I", timestamp=t)

    ctrl.sleep(interval)


def _finalize():
    datastore.close()


if __name__ == '__main__':
    ctrl.stop_by_signal()
    while not ctrl.is_stop_requested():
        _loop()
    _finalize()