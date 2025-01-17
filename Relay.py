import serial
from serial.tools import list_ports
import time

def list_com_ports():
    """List all available COM ports."""
    ports = list_ports.comports()
    return [port.device for port in ports]

def main():
    # List available COM ports
    available_ports = list_com_ports()
    if not available_ports:
        print("No COM ports found. Please check your connection.")
        return

    # Display the COM ports and ask user to select one
    print("Available COM ports:")
    for idx, port in enumerate(available_ports):
        print(f"{idx + 1}: {port}")

    try:
        selection = int(input("Select a COM port by number: ")) - 1
        if selection < 0 or selection >= len(available_ports):
            raise ValueError("Invalid selection.")
        selected_port = available_ports[selection]
        print(f"Selected COM port: {selected_port}")
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Open the selected COM port
    try:
        ser = serial.Serial(selected_port, 9600, timeout=1)
        print(f"Connected to {selected_port}")

        # Initialize shot counter
        shot_counter = 0
        max_shots = 36

        while True:
            print("\nReady to fire 16 shots sequence:")
            print("Press [Enter] to start firing 16 shots.")
            print("Type 'status' to see the shot count.")
            print("Type 'exit' to quit.")

            user_input = input("Enter your command: ").strip().lower()

            if user_input == "":
                if shot_counter + 16 <= max_shots:
                    # Fire 16 shots with a 1-second interval
                    for i in range(16):
                        # Fire the camera (Relay 2 ON and OFF)
                        ser.write(bytearray([0xA0, 0x02, 0x01, 0xA3]))  # Turn Relay 2 ON
                        time.sleep(0.2)  # Relay ON duration (adjust as needed)
                        ser.write(bytearray([0xA0, 0x02, 0x00, 0xA2]))  # Turn Relay 2 OFF
                        shot_counter += 1
                        print(f"Shot {shot_counter} fired! ({i + 1}/16 in this sequence)")
                        
                        # Wait for 1 second between shots
                        if i < 15:  # Avoid waiting after the last shot in the sequence
                            time.sleep(1)
                else:
                    print("Not enough shots remaining. Please reload the camera!")

            elif user_input == "status":
                print(f"Total shots taken: {shot_counter}/{max_shots}")

            elif user_input == "exit":
                print("Exiting program.")
                break

            else:
                print("Invalid command. Please try again.")

    except serial.SerialException as e:
        print(f"Error connecting to {selected_port}: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print(f"Closed connection to {selected_port}")

if __name__ == "__main__":
    main()
