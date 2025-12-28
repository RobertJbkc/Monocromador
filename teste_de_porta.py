import serial.tools.list_ports

ports = serial.tools.list_ports.comports()

print("Buscando portas seriais...")
for port, desc, hwid in sorted(ports):
    print(f"Porta: {port} | Descrição: {desc}")