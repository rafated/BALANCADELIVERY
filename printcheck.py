
import usb.core
import usb.util
from datetime import datetime


#README
#Para correr este programa é necessário garantir que:
# - Existe o ficheiro libusb.dll na pasta System32 e SYSWOW64 na pasta principal do Windows. --> Instalar o libusb usando o ZADIG é a mlehor solução.
# - pacote pysub está instalado
# - necessário reinstalar os drivers da impressora Epson, com o software ZADIG. Fazer replace driver pelo da libusb.  
# - verificar se os endereços da impressora sºao os mesmos que os definidos abaixo


# Find the device (replace with your device's vendor and product ID)
printer = usb.core.find(idVendor=0x04b8, idProduct=0x0202)

normal_size = b'\x1b\x21\x00'    # Normal size
double_height = b'\x1b\x21\x10'  # Double height
double_width = b'\x1b\x21\x20'   # Double width
double_height_width = b'\x1b\x21\x30'  # Double height and width
bold_on = b'\x1b\x45\x01'        # Bold on
bold_off = b'\x1b\x45\x00'       # Bold off
underline_on = b'\x1b\x2d\x01'   # Underline on
underline_off = b'\x1b\x2d\x00'  # Underline off
align_center = b'\x1b\x61\x01'   # Center align
align_left = b'\x1b\x61\x00'     # Left align
align_right = b'\x1b\x61\x02'    # Right align

# Define paper cut commands
full_cut = b'\x1d\x56\x00'   # Full cut
partial_cut = b'\x1d\x56\x01'  # Partial cut



def print_confirmation(order_number):
    if printer is None:
        raise ValueError("Printer not found.")
    
    message = str(order_number)
    
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)
    
    # Assuming the printer is already configured by Windows, try writing directly
    try:
        # Typically endpoint 0x01 is used for output to the printer
        endpoint = 1
    
        # Initialize the printer

        printer.write(endpoint, b'\x1b\x32\x20')
    
        printer.write(endpoint, align_center)

        printer.write(endpoint, b' Pedido pesado e confirmado\n\n\n\n')
        printer.write(endpoint, b'electronicamente por um sistema\n\n\n\n')
        printer.write(endpoint, b'de pesagem com balanca e imagem.\n\n\n\n')
        
        # Numero do pedido
    
        printer.write(endpoint, double_height_width)  # Large size
        printer.write(endpoint, bold_on)
        printer.write(endpoint, b'\n\n\n\n\n\n Pedido numero:')
        printer.write(endpoint, message.encode('utf-8'))
        printer.write(endpoint, normal_size)  # Normal size
        printer.write(endpoint, bold_off)

        printer.write(endpoint, align_left)
        printer.write(endpoint, b'\n\n\n\n\n\n\n Validado a: ')
        printer.write(endpoint, dt_string.encode('utf-8'))
        printer.write(endpoint, b'\n\n\n\n \n\n\n\n')
        printer.write(endpoint, b'\n\n\n\n \n\n\n\n')
        printer.write(endpoint, b'\n\n\n\n \n\n\n\n')

    
        # Cut the paper
        printer.write(endpoint, b'\x1d\x56\x01')
        
    except usb.core.USBError as e:
        print(f"Could not write to the printer: {e}")

def main():

    numero='A5B6T'
    print_confirmation(numero)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Logging error: {e}")
        with open("Erro_Log.log", "a") as logf:
            t = datetime.now()
            s = t.strftime('%Y%m%d_%Hh%Mm%Ss')
            logf.write(f"{s};Erro no GUI ;{str(e)}\n")
    
