import board
import busio
import digitalio
import time
import adafruit_rfm9x

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D10)
reset = digitalio.DigitalInOut(board.D11)
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 437.4)

rfm9x.spreading_factor=8
rfm9x.tx_power=14
rfm9x.node=0xfb
rfm9x.destination=0xfa
rfm9x.receive_timeout=10
rfm9x.enable_crc=True

cmd_keys = ['A','B','C','D']

def cmd_dispatcher():

    print("Please select a command key from the following list:")
    print("====================================================")
    print("A: cut_away")
    print("B: query")
    print("C: exec_cmd")
    print("D: ping")
    print("====================================================")

    cmd_key = input()

    if cmd_key in cmd_keys:
        print(f"CMD: {cmd_key} accepted!")

        cmd_args = None

        if cmd_key == 'B' or cmd_key == 'C':
            print("Please input cmd_args:")
            cmd_args = input()

        for attempts in range(5):
            print(f"Attempting CMD: {attempts}/5")
            if cmd_args is not None:
                rfm9x.send(f"KN6NAQ!CMD{cmd_key}{cmd_args}")
            else:
                rfm9x.send(f"KN6NAQ!CMD{cmd_key}")

            msg = rfm9x.receive()

            if msg is not None:
                print(msg)

                if 'CMD ACK!' in msg:
                    return True
                else:
                    pass

    else: 
        print(f"Invalid cmd_key! Breaking back to main loop.")
        return False

def listen():
    print("Listening for pings. Use CTRL + C to Break to CMD Selection")
    msg = rfm9x.receive()
    print(f"Recieved:{msg} RSSI: {rfm9x.last_rssi} Time: {time.monotonic()}")
    time.sleep(1)


while True:
    try:
        listen()
    except KeyboardInterrupt: 
        cmd_dispatcher()



    
