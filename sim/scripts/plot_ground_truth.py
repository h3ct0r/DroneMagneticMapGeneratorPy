import os
import sys
sys.path.insert(0, '/Library/Python/2.7/site-packages/')

from mayavi import mlab
from scipy.ndimage.filters import gaussian_filter
from skimage.measure import structural_similarity as ssim
import numpy as np
from scipy.linalg import norm
import inspect
import matplotlib.pyplot as plt
from cv2 import *

WIDTH = 800
HEIGHT = 600

x = np.linspace(0, WIDTH, 1)
y = np.linspace(0, HEIGHT, 1)
xx, yy = np.meshgrid(x, y)

z = np.loadtxt('/tmp/magnetic_ground_truth.np')
original = z
original_255 = z
original_255 *= 255.0/original_255.max()

mlab.figure(bgcolor=(1,1,1), fgcolor=(0,0,0))
mlab.surf(x, y, original_255, warp_scale='auto')
mlab.colorbar(title=' ', orientation='vertical')

plt.show()
mlab.show()


