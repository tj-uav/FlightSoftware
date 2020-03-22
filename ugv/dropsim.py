#TODO: Maybe don't assume it hits terminal velocity immediately?
# Time differential
dt = 0.01

#Plane velocities (initial, final, and terminal)
Vp0 = 20.0
Vpf = 10.0

Mp = 3
altitude = 60

# Drag and area constants
Dp = 0.05
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

data = []
t = 0.0
Xp = 0.0
Vp = Vp0
# Cut throttle
while Vp > Vpf:
    a = drag(Mp, Vp, Dp, Ap)
    Vp -= a * dt
    Xp += Vp * dt
    t += dt
    data.append((t, Xp))

print(t, Xp)

Xu, Yu = 0.0, altitude
while Yu > 0.0:
    Xu += Vux * dt
    Yu -= Vuy * dt
    t += dt

print(t, Xu)
print("Total distance traveled: {}".format(Xu + Xp))

"""
from matplotlib import pyplot as plt
x = [i[0] for i in data]
y = [i[1] for i in data]
plt.scatter(x, y)
plt.show()
""'