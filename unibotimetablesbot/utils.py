import math


def my_round(x, base=5):
    return base * round(x/base)


def distance(lat_A, lon_A, lat_B, lon_B):
    r = 6372.795477598

    radLatA = math.pi * lat_A / 180
    radLonA = math.pi * lon_A / 180
    radLatB = math.pi * lat_B / 180
    radLonB = math.pi * lon_B / 180

    phi = abs(radLonA - radLonB)

    p = math.acos((math.sin(radLatA) * math.sin(radLatB)) +
                  (math.cos(radLatA) * math.cos(radLatB) * math.cos(phi)))

    distance = p * r * 1000
    return distance  # meters
