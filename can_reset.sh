sudo /sbin/ip link set can0 down
sudo ip link set can0 type can restart-ms 100
ip link set can0 type can restart

#echo("Reset was Succesful")

sudo ip link set can0 up type can bitrate 250000
candump can0 -xct z -n 10

#cowsay -f elephant "Succesful Conection"