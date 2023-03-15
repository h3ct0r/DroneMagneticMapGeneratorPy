# DroneMagneticMapGeneratorPy

A software to generate routes for Magnetic Coverage with rotary wing drones.

  - Generate waypoints at a fixed interval
  - Several drones
  - Hexagon segmentation
  
![image](https://user-images.githubusercontent.com/14208261/225181310-d1f46064-8bdf-4bfb-991d-56e078808a9b.png)

### Tech

DroneMagneticMapGeneratorPy uses a number of open source projects to work properly:

* [Python] - one of the greatest script languages ever
* [Shapely] - a awesome library for geometric calculations
* [PyQT5] - for generating desktop UI
* [numpy] - a library for math computations
* [Leaflet] - a opensource javascript library for maps

### Installation
> Option #1: Docker - It work on all machines!
1) Clone the repo 
```sh
git clone https://github.com/h3ct0r/DroneMagneticMapGeneratorPy
```
2) Set server access control program for X
```sh
xhost +
```
3) Running the application
```sh
docker compose up # or docker-compose up depending on your docker version
```

> Option #2: System Install - It work on my machine!
1) Clone the repo 
```sh
git clone https://github.com/h3ct0r/DroneMagneticMapGeneratorPy
```
2) Install dependencies
```sh
pip install shapely numpy pygame PyQt5 networkx scipy matplotlib PIL
```
3) Go to the folder of the program 
```sh
cd DroneMagneticMapGeneratorPy/
```
4) Run 
```sh
python main.py
```

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
