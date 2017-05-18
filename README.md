# DroneMagneticMapGeneratorPy

A software to generate routes for Magnetic Coverage with rotary wing drones.

  - Generate waypoints at a fixed interval
  - Several drones
  - Hexagon segmentation

### Tech

DroneMagneticMapGeneratorPy uses a number of open source projects to work properly:

* [Python] - one of the greatest script languages ever
* [Shapely] - a awesome library for geometric calculations
* [PyQT4] - for generating desktop UI
* [numpy] - a library for math computations
* [Leaflet] - a opensource javascript library for maps

### Installation

1) Clone the repo `git clone https://github.com/h3ct0r/DroneMagneticMapGeneratorPy`
2) Install `pip install shapely numpy pygame PyQt4 networkx scipy matplotlib PIL`

### How to run

1) Go to the folder of the program `cd DroneMagneticMapGeneratorPy/`
2) Run `python main.py`

### Todos

 - Write MOAR Tests
 - Support load and save polygon
 - Add set default location based on current location
 - Save previous config and load it on start up
 - Configure start and end nodes for the hexagons and magnetic route

License
----

MIT


**Free Software, Hell Yeah!**