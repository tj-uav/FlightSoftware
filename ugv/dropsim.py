#TODO: Maybe don't assume it hits terminal velocity immediately?
# Time differential
dt = 0.01

#Plane velocities (initial and final)
Vp0 = 20.0
Vpf = 10.0

Mp = 3
altitude = 60

# Drag and area constants
Dp = 0.1
Ap = 0.8
#Dux = 0.0
#Duy = 1.75
#Au = 5.0
p = 1.225

# UGV terminals
Vux = 0.2
Vuy = 0.2


def drag(m, v, C, A):
    return ((1/2) * p * v * v * C * A) / m

t = 0.0
Xp = 0.0
Vp = Vp0
# Cut throttle
while Vp > Vpf:
    a = drag(Mp, Vp, Dp, Ap)
    Vp -= a * dt
    Xp += Vp * dt
    t += dt

print(t, Xp)

Xu, Yu = 0.0, altitude
while Yu > 0.0:
    Xu += Vux * dt
    Yu -= Vuy * dt
    t += dt

print(t, Xu)
print("Total distance traveled: {}".format(Xu + Xp))