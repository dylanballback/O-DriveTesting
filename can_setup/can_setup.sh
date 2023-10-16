sudo ip link set can0 up type can bitrate 250000
candump can0 -xct z -n 10

cowsay -f elephant "Succesful Conection"