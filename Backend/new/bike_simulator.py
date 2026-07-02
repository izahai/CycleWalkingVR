import socket
import time
import json  # Added json module

# --- NETWORK CONFIGURATION ---
UDP_IP = "127.0.0.1"  
UDP_PORT = 9000        # Match this exactly with Unity's listenPort (e.g., 9000 or 5050)

# --- SIMULATION CONFIGURATION ---
FREQUENCY_HZ = 60      
INTERVAL = 1.0 / FREQUENCY_HZ

def simulate_bike():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print(f"--- Bike Hardware Simulator Started ---")
    print(f"Sending UDP JSON packets to {UDP_IP}:{UDP_PORT} at {FREQUENCY_HZ}Hz")
    print("Press Ctrl+C to stop simulation.\n")
    
    start_time = time.time()
    
    try:
        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            
            simulated_angle = (elapsed * 120.0) % 360.0  
            simulated_timestamp = elapsed                
            
            # --- CREATE JSON TARGETING UNITY'S FIELDS ---
            # Make sure these keys match the exact variable names in your C# AnglePacket struct
            packet_dict = {
                "angle_deg": simulated_angle,
                "ts": simulated_timestamp
            }
            
            # Convert dictionary to JSON string and encode to bytes
            json_string = json.dumps(packet_dict)
            packet_data = json_string.encode('utf-8')
            
            # Send over UDP
            sock.sendto(packet_data, (UDP_IP, UDP_PORT))
            
            print(f"[SENT] {json_string}", end="\r")
            
            time.sleep(INTERVAL)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    finally:
        sock.close()

if __name__ == "__main__":
    simulate_bike()