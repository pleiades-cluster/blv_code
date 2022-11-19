import board
import busio
import digitalio
import time
import adafruit_rfm9x
from adafruit_motor import servo
import pwmio
import adafruit_gps

pwm = pwmio.PWMOut(board.A0, frequency=50)
servo = servo.Servo(pwm, min_pulse=750, max_pulse=2250)

uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)
gps = adafruit_gps.GPS(uart, debug=False)

gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220,1000")

gps_alt = 0 
gps_speed = 0
gps_track_angle = 0 

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D10)
reset = digitalio.DigitalInOut(board.D11)
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 437.4)

rfm9x.spreading_factor=8
rfm9x.tx_power=14
rfm9x.node=0xfa
rfm9x.destination=0xfb
rfm9x.receive_timeout=10
rfm9x.enable_crc=True

servo.angle=180

cmd_keys = {
    65:   'cut_away',
    66:   'query',
    67:   'exec_cmd',
    68:   'ping'
}

def cmd_handler(msg):
    try:
        header = msg[0:10]
        print(f"Re: {header}")
        if msg[0:10] == b'KN6NAQ!CMD':
            print(f"CMD Received: {msg}")

            rfm9x.send("CMD ACK!")
            rfm9x.send("CMD ACK!")
            rfm9x.send("CMD ACK!")

            time.sleep(1)

            cmd_key = msg[10]
            print(cmd_key)
            
            eval(cmd_keys[cmd_key])

            cmd_args = None

            if len(msg) > 11: 
                cmd_args = msg[11:]
                print(f"CMD with ARGS: {cmd_args}")

            if cmd_key in cmd_keys:
                try:
                    if cmd_args is None:
                        print('running {} (no args)'.format(cmd_keys[cmd_key]))
                        # eval a string turns it into a func name
                        eval(cmd_keys[cmd_key])()
                    else:
                        print('running {} (with args: {})'.format(cmd_keys[cmd_key],cmd_args))
                        eval(cmd_keys[cmd_key])(cmd_args)

                except Exception as e:
                    print('something went wrong: {}'.format(e))
                    rfm9x.send(str(e).encode())

            else:
                print('invalid command!')
                rfm9x.send(b'invalid cmd_key'+msg[11:])

        else:
            print(rfm9x.send(f"Not a CMD. Check Syntax? RSSI:{rfm9x.last_rssi}"))

    except Exception as e:
        print(e)

def gps_handler(gps_alt, gps_speed, gps_track_angle):
    # Make sure to call gps.update() every loop iteration and at least twice
    # as fast as data comes from the GPS unit (usually every second).
    # This returns a bool that's true if it parsed new data (you can ignore it
    # though if you don't care and instead look at the has_fix property).
    gps.update()
    # Every second print out current location details if there's a fix.

    if not gps.has_fix:
        # Try again if we don't have a fix yet.
        print("Waiting for fix...")

        return "No GPS Fix"
    # We have a fix! (gps.has_fix is true)
    # Print out details about the fix like location, date, etc.
    print("=" * 40)  # Print a separator line.
    print(
        "Fix timestamp UTC: {}/{}/{} {:02}:{:02}:{:02}".format(
            gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
            gps.timestamp_utc.tm_mday,  # struct_time object that holds
            gps.timestamp_utc.tm_year,  # the fix time.  Note you might
            gps.timestamp_utc.tm_hour,  # not get all data like year, day,
            gps.timestamp_utc.tm_min,  # month!
            gps.timestamp_utc.tm_sec,
        )
    )
    print("Latitude: {0:.6f} degrees".format(gps.latitude))
    print("Longitude: {0:.6f} degrees".format(gps.longitude))

    print("Fix quality: {}".format(gps.fix_quality))
    # Some attributes beyond latitude, longitude and timestamp are optional
    # and might not be present.  Check if they're None before trying to use!
    if gps.altitude_m is not None:
        print("Altitude: {} meters".format(gps.altitude_m))
        gps_alt = gps.altitude_m
    if gps.speed_knots is not None:
        print("Speed: {} knots".format(gps.speed_knots))
        gps_speed = gps.speed_knots
    if gps.track_angle_deg is not None:
        print("Track angle: {} degrees".format(gps.track_angle_deg))
        gps_track_angle = gps.track_angle_deg

    gps_data_string = "UTC Time {}/{}/{} {:02}:{:02}:{:02} | Lat: {} Long: {} | Alt: {} | Knts: {} | TRKA: {}".format(
        gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
        gps.timestamp_utc.tm_mday,  # struct_time object that holds
        gps.timestamp_utc.tm_year,  # the fix time.  Note you might
        gps.timestamp_utc.tm_hour,  # not get all data like year, day,
        gps.timestamp_utc.tm_min,  # month!
        gps.timestamp_utc.tm_sec,
        gps.latitude,
        gps.longitude,
        gps_alt,
        gps_speed,
        gps_track_angle
    )

    return gps_data_string


def cut_away():
    print("Cutting!")
    servo.angle = 0
    rfm9x.send("Cut Away Initiated")

def ping():
    rfm9x.destination=0xff
    rfm9x.send(f"This is the Bronco Space BLV Callsign KN6NAQ! Time: {time.monotonic()}. Last RSSI: {rfm9x.last_rssi}")
    rfm9x.destination=0xfb

def query(args):
    print(f'query: {args}')
    print(rfm9x.send(data=str(eval(args))))

def exec_cmd(args):
    print(f'exec: {args}')
    exec(args)


while True:

    rfm9x.send(gps_handler(gps_alt, gps_speed, gps_track_angle))

    msg = rfm9x.receive()
    
    print(f"{msg} RSSI: {rfm9x.last_rssi}")

    if gps_alt == 32000:
        cut_away()

    if msg is not None:
        cmd_handler(msg)

    time.sleep(1)
