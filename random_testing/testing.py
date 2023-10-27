import numpy as np
import time

def generate_sine_wave(amplitude, frequency, duration, sampling_rate):
    """
    Generate a sine wave and return its values at specified time steps.

    Parameters:
    - amplitude: The amplitude of the sine wave.
    - frequency: The frequency of the sine wave (in Hz).
    - duration: The duration of the sine wave (in seconds).
    - sampling_rate: The number of samples per second.

    Returns:
    - A list of sine wave values at specified time steps.
    """
    t = np.linspace(0, duration, int(duration * sampling_rate), endpoint=False)
    sine_wave = amplitude * np.sin(2 * np.pi * frequency * t)
    return sine_wave

# Example usage:
amplitude = 10.0
frequency = .1  # 2 Hz
duration = 1.0  # 1 second
sampling_rate = 10 # 1000 samples per second

sine_wave_values = generate_sine_wave(amplitude, frequency, duration, sampling_rate)

# Print the first 10 values of the sine wave
#print(sine_wave_values[:1000])

while True: 
    for num in sine_wave_values:
        print(num)
        time.sleep(.1)
        

#from time import time
#end_time = time() + 3
#print("delay starts")
#while True:
#  now = time()
#  if now > end_time:
#    for num in sine_wave_values:
#       print(num)
#    end_time = now + 3