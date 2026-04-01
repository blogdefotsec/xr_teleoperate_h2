import asyncio
import websockets
import msgpack
import time
import math
import ssl
import argparse

async def mock_pico4_client(server_ip, server_port=8012):
    uri = f"wss://{server_ip}:{server_port}"
    print(f"Attempting to connect to Vuer server at {uri}...")

    # Ignore SSL certificate verification since the server uses self-signed certs
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            print("✅ Successfully connected! Simulating Pico 4 data stream...")
            print("The server should now show 'websocket is connected'.")
            print("Press 'r' on the server terminal to start tracking.")
            
            start_time = time.time()
            
            while True:
                t = time.time() - start_time
                
                # Generate a simple sine wave motion for the hands
                # Amplitude = 0.1m, Frequency = 0.5Hz
                z_offset = 0.15 * math.sin(2 * math.pi * 0.5 * t)
                
                # Vuer expects 16-element arrays representing 4x4 column-major transformation matrices
                
                # Head: static at origin
                head_matrix = [
                    1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    0, 0, 0, 1
                ]
                
                # In XR coordinates: 
                # X is right, Y is up, -Z is forward.
                # Let's put hands 30cm in front (-0.3 Z), 20cm down (-0.2 Y), and 20cm apart (X = +/- 0.2)
                
                # Left Hand: moving up and down (Y axis)
                left_hand_matrix = [
                    1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    -0.2, -0.2 + z_offset, -0.3, 1
                ]
                
                # Right Hand: moving up and down opposite to left hand
                right_hand_matrix = [
                    1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    0.2, -0.2 - z_offset, -0.3, 1
                ]

                # The Vuer WEBRTC_TRACKING event actually expects the raw rig data directly inside 'data'
                # Not nested inside another 'rig' key, despite what the wrapper implies internally.
                payload = {
                    "type": "CLIENT_EVENT",
                    "event": "WEBRTC_TRACKING",
                    "data": {
                        "head": {
                            "matrix": head_matrix
                        },
                        "leftHand": {
                            "matrix": left_hand_matrix
                        },
                        "rightHand": {
                            "matrix": right_hand_matrix
                        }
                    }
                }

                # vuer expects msgpack bytes, not json strings
                await websocket.send(msgpack.packb(payload))
                
                # Send data at roughly 60Hz to mimic a VR headset
                await asyncio.sleep(1/60.0)
                
    except ConnectionRefusedError:
        print(f"❌ Connection refused. Is the server running on {server_ip}:{server_port}?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock Pico 4 Client for Vuer")
    parser.add_argument("--ip", type=str, required=True, help="IP address of the remote server running xr_teleoperate")
    parser.add_argument("--port", type=int, default=8012, help="WebSocket port (default: 8012)")
    args = parser.parse_args()

    asyncio.run(mock_pico4_client(args.ip, args.port))