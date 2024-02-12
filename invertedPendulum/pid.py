import time

class PID:
    def __init__(self, kp, ki, kd, setpoint, lower_limit, upper_limit):
        self.kp = kp  # Proportional gain
        self.ki = ki  # Integral gain
        self.kd = kd  # Derivative gain
        self.setpoint = setpoint  # Desired value or range (tuple for range, single value otherwise)
        self.lower_limit = lower_limit  # Minimum output limit
        self.upper_limit = upper_limit  # Maximum output limit
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = time.time()

    def calculate_error(self, current_value):
        """
        Calculate error based on whether the setpoint is a single value or a range.
        """
        if isinstance(self.setpoint, tuple) or isinstance(self.setpoint, list):
            # Setpoint is a range
            lower_sp, upper_sp = self.setpoint
            if current_value < lower_sp:
                return lower_sp - current_value
            elif current_value > upper_sp:
                return upper_sp - current_value
            else:
                return 0  # Current value is within the setpoint range
        else:
            # Setpoint is a single value
            return self.setpoint - current_value

    def update(self, current_value):
        current_time = time.time()
        dt = current_time - self.last_time
        if dt <= 0.0:
            dt = 1e-16

        error = self.calculate_error(current_value)
        self.integral += error * dt
        derivative = (error - self.last_error) / dt
        
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        output = max(self.lower_limit, min(output, self.upper_limit))
        
        self.last_error = error
        self.last_time = current_time
        
        return output

"""
Example

# Single value setpoint
pid_single = PID(kp=1.0, ki=0.1, kd=0.01, setpoint=100, lower_limit=-50, upper_limit=50)

# OR

# Range setpoint
pid_range = PID(kp=1.0, ki=0.1, kd=0.01, setpoint=(-4, 4), lower_limit=-50, upper_limit=50)


current_value = 0
for _ in range(100):  # Simulate 100 time steps
    control = pid.update(current_value=current_value)
    current_value += control  # Update system with control output (simple simulation)
    print(f"Control: {control}, Current Value: {current_value}")
    time.sleep(1)  # Simulate some delay, e.g., waiting for sensor reading or actuator response

"""