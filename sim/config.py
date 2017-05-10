from math import pi, sqrt
import os

IMAGE_WIDTH = 800
IMAGE_HEIGHT = 600

THETA = pi / 3.0 					# Angle from one point to the next
RADIUS = 40 						# Size of a hex

HEXES_WIDE = int(IMAGE_WIDTH / RADIUS)  # How many hexes in a row
HEXES_HIGH = int(IMAGE_HEIGHT / RADIUS) + 1  # How many rows of hexes

HALF_RADIUS = RADIUS / 2.0
HALF_HEX_HEIGHT = sqrt(RADIUS ** 2 - HALF_RADIUS ** 2)

user_home = os.path.expanduser('~')
USER_PREFERENCE_FILE = user_home + "/" + ".sim_preferences.json"

BACKGROUND_BASE = "background_base.png"
BACKGROUND_IMAGE = "background.png"

NP_GROUND_TRUTH = "/tmp/magnetic_ground_truth.np"

NUMBER_OF_ROBOTS = 3
BATTERY_AUTONOMY = 1000

LINE_WIDTH = 20

ROBOT_BASE_HEIGHT = 40

DEBUG = True
