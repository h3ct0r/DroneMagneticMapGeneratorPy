#!/usr/bin/python

import os
import sys
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebKitWidgets
from layout import Ui_MainWindow
from PyQt5.QtCore import *
import json
import datetime
import sim.simulation
import sim.config
import sim.math_helper
import math
import time
import sim.cover_polygon
import sim.cover_hexagon

class WebPage(QtWebKitWidgets.QWebPage):
    def javaScriptConsoleMessage(self, msg, line, source):
        print '%s line %d: %s' % (source, line, msg)


class MainUi(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainUi, self).__init__(parent)

        self.ui = Ui_MainWindow()

        self.ui.setupUi(self)

        page = WebPage()
        self.ui.webView.setPage(page)

        self.loadHTMLTemplate()

        self.timer = QtCore.QTimer()

        self.ui.btnGenRoute.clicked.connect(self.callGetShape)
        self.ui.btnClearPaths.clicked.connect(self.clearPaths)
        self.ui.btnHexToggleMaps.clicked.connect(self.toggleMapsJS)

        self.ui.spinAngle.valueChanged.connect(self.paramsChanged)
        self.ui.doubleSpinWidthSize.valueChanged.connect(self.paramsChanged)
        self.ui.doubleSpinPointSpacement.valueChanged.connect(self.paramsChanged)

        self.ui.actionSave_polygon_shape.triggered.connect(self.savePolyShapeToFile)
        self.ui.actionLoad_polygon_shape.triggered.connect(self.loadPolyShapeFromFile)
        self.ui.actionAdd_GPS_markers_from_file.triggered.connect(self.loadGPSMarkersFromFile)
        self.ui.actionClear_GPS_markers.triggered.connect(self.clearGPSMarkers)
        self.ui.actionExit_program.triggered.connect(self.close)
        self.ui.actionReload_Map.triggered.connect(self.loadHTMLTemplate)
        self.ui.actionExport_Route.triggered.connect(self.exportGPSroute)

        self.path_gps_json = None
        self.path_simplified_gps_json = None
        self.path_hex_gps_json = None
        self.roi_gps_json = None


    def loadFinishedHtml(self):
        msg = "Map reloaded"
        print msg
        self.ui.labelStatus.setText(msg + " " + str(datetime.datetime.now()))
        pass

    def loadGPSMarkersFromFile(self):
        self.ui.labelStatus.setText("Loading GPS markers from file... " + str(datetime.datetime.now()))

        fileName = QtWidgets.QFileDialog.getOpenFileName(self, "Select a GPS file to load into markers", "", "")
        if fileName:
            print(fileName)

            gps_list = []
            with open(fileName) as f:
                for line in f:
                    e = line.split(',')
                    gps_list.append((e[0].strip(), e[1].strip()))

            if len(gps_list) > 0:
                json_data = json.dumps(gps_list)
                print 'json_data', json_data
                print "gps_list[0][0], gps_list[0][1]", gps_list[0][0], gps_list[0][1]
                self.ui.webView.page().mainFrame().evaluateJavaScript("addDrawedMarkers(\'{0}\');".format(json_data))
                self.ui.webView.page().mainFrame().evaluateJavaScript("panToGPS(\'{0}\', \'{1}\');".format(
                    gps_list[0][0], gps_list[0][1])
                )
            else:
                self.ui.labelStatus.setText(
                    "Error loading GPS file: no GPS locations at the selected file... " + str(datetime.datetime.now()))
        else:
            self.ui.labelStatus.setText("Error loading GPS file: no file selected... " + str(datetime.datetime.now()))

    def clearGPSMarkers(self):
        self.ui.labelStatus.setText("GPS markers cleared... " + str(datetime.datetime.now()))
        self.ui.webView.page().mainFrame().evaluateJavaScript("clearDrawedMarkers();")
        pass

    def savePolyShapeToFile(self):
        self.ui.labelStatus.setText("Polygon shape saved... " + str(datetime.datetime.now()))
        if self.roi_gps_json is not None:
            with open(os.path.expanduser('~') + '/.dronemapgenerator.map', 'w') as file:
                file.write(json.dumps(self.roi_gps_json, ensure_ascii=True))
        pass

    def loadPolyShapeFromFile(self):
        with open(os.path.expanduser('~') + '/.dronemapgenerator.map') as map_file:
            data = json.load(map_file)

        json_data = json.dumps(data)
        print 'json_data', json_data
        self.ui.webView.page().mainFrame().evaluateJavaScript("setROIGPS(\'{0}\');".format(json_data))
        self.ui.labelStatus.setText("Polygon shape loaded... " + str(datetime.datetime.now()))
        pass

    def loadHTMLTemplate(self, filename='html/map_template.html'):
        msg = "Loading map..."
        self.ui.labelStatus.setText(msg + " " + str(datetime.datetime.now()))

        html_template = ""
        try:
            with open(filename, 'r') as template_file:
                html_template = template_file.read()
        except Exception as e:
            print "Error {0}".format(str(e))
            msg = "Error loading map: {0} : ".format(str(e), str(datetime.datetime.now()))
            self.ui.labelStatus.setText(msg)

        #self.ui.webView.setHtml(html_template, QtCore.QUrl('qrc:/'))
        self.ui.webView.load(QtCore.QUrl.fromLocalFile(os.path.abspath(filename)))
        self.ui.webView.page().mainFrame().addToJavaScriptWindowObject('self', self)
        self.ui.webView.loadFinished.connect(self.loadFinishedHtml)
        pass

    def clearPaths(self):
        self.path_gps_json = None
        self.path_simplified_gps_json = None
        self.addLoadingModal()
        self.ui.webView.page().mainFrame().evaluateJavaScript("clearGeneratedPaths();")
        self.removeLoadingModal()
        pass

    def addLoadingModal(self):
        self.ui.webView.page().mainFrame().evaluateJavaScript("addLoadingModal();")

    def removeLoadingModal(self):
        self.ui.webView.page().mainFrame().evaluateJavaScript("removeLoadingModal();")

    def callGetShape(self):
        self.ui.webView.page().mainFrame().evaluateJavaScript("centerOnShape();")
        self.addLoadingModal()
        self.ui.webView.page().mainFrame().evaluateJavaScript("setTimeout(function(){sendShapeToQT();}, 350);")

    def paramsChanged(self, val):
        print 'paramsChanged...', val
        self.callGetShape()
        pass

    def exportGPSroute(self):
        routes = {}
        if self.path_gps_json:
            routes['magnetic'] = self.path_gps_json

        if self.path_simplified_gps_json:
            routes['magnetic_simplified'] = self.path_simplified_gps_json

        if self.path_hex_gps_json:
            for k, v in self.path_hex_gps_json.items():
                routes['aerial_'+str(k)] = v

        print 'Routes:', routes

        if len(routes.keys()) > 0:
            directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select directory to export routes ...')
            directory = str(directory)
            print 'selected dir', directory
        else:
            self.ui.labelStatus.setText("Error: No route available to export, generate one route first... "
                                        + str(datetime.datetime.now()))

        hex_altitude_multiplicator = 0 # at every hex drone add some meters of altitude
        for k, v in routes.items():
            header = "QGC WPL 110"

            # 0 : counter
            # 1 : mission start (all 0 only one set as 1)
            # 2 : type of command, 0 to set home, 3 to go to waypoint, 10 follow terrain
            # 3 : command, 16 go to waypoint, 22 takeoff, 20 RTL, 115 CONDITION-YAW, 203 trigger cam
            # 4 : time to wait at waypoint/min pitch when command=22/desired yaw when command=115
            # 5 : reach radius
            # 6 : ??
            # 7 : desired angle at waypoint. INFO: not used, use CONDITION-YAW instead
            # 8 : lat
            # 9 : lon
            # 10 : altitude

            base_srt = "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\t{10:.2f}\t1"

            p_counter = 0
            gps_export_str = []
            reach_radius = 1
            desired_angle = 0
            wp_alt_type = 3

            if k in ['magnetic', 'magnetic_simplified']:
                altitude_mts = self.ui.doubleSpinAltitude.value()
                time_to_wait = self.ui.spinSeconds.value()
                desired_angle = self.ui.spinDroneAngle.value()
                line_width = self.ui.doubleSpinWidthSize.value()
                point_spacement = self.ui.doubleSpinPointSpacement.value()
                filename = "{}_alt{}_linewidth{}_pointspace{}_droneang{}.txt".format(k, altitude_mts, line_width,
                                                                                     point_spacement, desired_angle)

            else:
                altitude_mts = self.ui.spinHexAltitude.value() + hex_altitude_multiplicator
                time_to_wait = 0
                if not (0 <= desired_angle <= 360):
                    desired_angle = self.ui.spinHexAngle.value()

                filename = "{}_alt{}_width{}_droneang{}.txt".format(k, altitude_mts, desired_angle)

            wp_alt_combo_text = self.ui.comboWPALT.currentText()
            if wp_alt_combo_text == "Follow Terrain":
                wp_alt_type = 10

            print "WP alt type:", wp_alt_type, wp_alt_combo_text

            for coord in v:
                print 'coord', coord
                if p_counter == 0:
                    # Set home
                    gps_export_str.append(
                        base_srt.format(p_counter, 1, 0, 16, 0, reach_radius, 0, 0,
                                        coord['lat'], coord['lng'], 0, 1))
                    p_counter += 1

                    # 22 Takeoff
                    gps_export_str.append(
                        base_srt.format(p_counter, 0, wp_alt_type, 22, 0, reach_radius, 0, desired_angle,
                                        coord['lat'], coord['lng'], altitude_mts, 1))
                    p_counter += 1

                    # add desired yaw
                    # http://ardupilot.org/copter/docs/mission-command-list.html#mission-command-list-condition-yaw
                    gps_export_str.append(
                        base_srt.format(p_counter, 0, wp_alt_type, 115, desired_angle, reach_radius, 0, 0,
                                        coord['lat'], coord['lng'], altitude_mts, 1))

                    p_counter += 1

                    # go to first WP
                    gps_export_str.append(
                        base_srt.format(p_counter, 0, wp_alt_type, 16, 0, reach_radius, 0, desired_angle,
                                        coord['lat'], coord['lng'], altitude_mts, 1))
                else:
                    # normal waypoint
                    gps_export_str.append(
                        base_srt.format(p_counter, 0, wp_alt_type, 16, 0, reach_radius, 0, desired_angle,
                                        coord['lat'], coord['lng'], altitude_mts, 1))

                p_counter += 1

                if time_to_wait > 0:
                    # trigger cam
                    # http://ardupilot.org/copter/docs/mission-command-list.html#do-digicam-control
                    gps_export_str.append(
                        base_srt.format(p_counter, 0, wp_alt_type, 203, 0, reach_radius, 0, 0,
                                        coord['lat'], coord['lng'], altitude_mts, 1))

                    p_counter += 1

                    # send WP with time
                    gps_export_str.append(
                        base_srt.format(p_counter, 0, wp_alt_type, 16, time_to_wait, reach_radius, 0, desired_angle,
                                        coord['lat'], coord['lng'], altitude_mts, 1))

                    p_counter += 1

            # RTL
            last_coord = v[-1]
            gps_export_str.append(
                base_srt.format(p_counter, 0, wp_alt_type, 20, 0, reach_radius, 0, desired_angle,
                                last_coord['lat'], last_coord['lng'], altitude_mts, 1))

            filepath = os.path.join(directory, filename)
            print "Writting to file...", filepath, v

            f = open(filepath, 'w')
            f.write(header)
            f.write('\n')
            for elem in gps_export_str:
                f.write(elem)
                f.write('\n')

            f.close()

            print "Route exported to ", filepath
            msg = "Route exported to " + filepath
            self.ui.labelStatus.setText(msg + " " + str(datetime.datetime.now()))

            if k is not 'magnetic':
                hex_altitude_multiplicator += self.ui.spinHexAltMult.value()

        pass

    @pyqtSlot(str)
    def QTgetPixelShape(self, vertex_list):
        print "QTgetPixelShape called"
        self.clearPaths()
        data = json.loads(str(vertex_list))
        #print type(data), data

        angle = self.ui.spinAngle.value()
        line_width = self.ui.doubleSpinWidthSize.value()
        point_spacement = self.ui.doubleSpinPointSpacement.value()
        shape = data['shape']
        wp_spacement_mode = self.ui.comboWPSequence.currentText()

        shape.append(shape[0])

        c_polygon = sim.cover_polygon.CoverPolygon(shape, line_width, angle,
                                                   meter_pixel_ratio=data['meter_pixel_ratio'],
                                                   spacement_mode=wp_spacement_mode,
                                                   point_spacement=point_spacement)
        lawnmower_path = c_polygon.get_lawnmower()

        c_simp_polygon = sim.cover_polygon.CoverPolygon(shape, line_width, angle,
                                                        meter_pixel_ratio=data['meter_pixel_ratio'],
                                                        spacement_mode=wp_spacement_mode,
                                                        point_spacement=point_spacement,
                                                        path_with_minimized_points=True)
        simplified_lawnmower_path = c_simp_polygon.get_lawnmower()

        hex_r = self.ui.spinHexRadius.value()
        robot_size = self.ui.spinHexRobotNumber.value()
        hex_line_w = self.ui.spinHexWidthSize.value()
        angle = self.ui.spinHexAngle.value()

        hex_tours = None
        if robot_size > 0:
            hex_p_cover = sim.cover_hexagon.CoverHexagon(shape, hex_r, hex_line_w, angle, robot_size=robot_size, meter_pixel_ratio=data['meter_pixel_ratio'])
            hex_p_cover.get_intersecting_hexagons()
            hex_p_cover.calculate_clusters()
            hex_p_cover.optimize_tours()
            hex_tours = hex_p_cover.get_tours()

        #print "Pixel lawnmower path:", lawnmower_path

        self.generateRouteFromPixel(lawnmower_path, hex_tours, simplified_lawnmower_path)

    def generateRouteFromPixel(self, flight_plan, hex_tours, simplified_flight_plan):
        msg = "Generating route from a pixel flight plan coordinates ..."
        self.ui.labelStatus.setText(msg + " " + str(datetime.datetime.now()))

        json_flight_plan = json.dumps(flight_plan)
        self.ui.webView.page().mainFrame().evaluateJavaScript("createFlightPlans(\'{0}\');".format(json_flight_plan))

        json_simplified_flight_plan = json.dumps(simplified_flight_plan)
        self.ui.webView.page().mainFrame().evaluateJavaScript("createSimplifiedFlightPlans(\'{0}\');".format(json_simplified_flight_plan))

        msg = "Route generated..."
        self.ui.labelStatus.setText(msg + " " + str(datetime.datetime.now()))

        if hex_tours is not None:
            time.sleep(1)
            msg = "Generating hex routes from a pixel flight plan coordinates ..."
            self.ui.labelStatus.setText(msg + " " + str(datetime.datetime.now()))
            lawnmower_tours = {}
            for k, v in hex_tours.items():
                print k, 'len:', len(v)
                lawn_tour = []
                for h in v:
                    lawn_tour += h.getLawnmower()

                lawnmower_tours[k] = lawn_tour

            json_flight_plan = json.dumps(lawnmower_tours)
            print "Json hexagon flight plan:", json_flight_plan

            self.ui.webView.page().mainFrame().evaluateJavaScript(
                "createHexagonFlightPlans(\'{0}\');".format(json_flight_plan))

            msg = "Hexagon route generated..."
            self.ui.labelStatus.setText(msg + " " + str(datetime.datetime.now()))

        self.removeLoadingModal()
        pass

    @pyqtSlot(str)
    def QTgetGPSPath(self, gps_list):
        print "QTgetGPSPath called"
        self.path_gps_json = None

        data = json.loads(str(gps_list))
        #print type(data), data

        self.path_gps_json = data
        pass

    @pyqtSlot(str)
    def QTgetSimplifiedGPSPath(self, gps_list):
        print "QTgetGPSPath called"
        self.path_simplified_gps_json = None

        data = json.loads(str(gps_list))
        self.path_simplified_gps_json = data
        pass

    @pyqtSlot(str)
    def QTgetHexGPSPath(self, gps_list):
        print "QTgetHexGPSPath called"
        self.path_hex_gps_json = None

        data = json.loads(str(gps_list))
        print type(data), data

        self.path_hex_gps_json = data
        pass

    @pyqtSlot(str)
    def QTsetRegionOfInterestGPSShape(self, gps_list):
        print "QTsetRegionOfInterestGPSShape called"

        data = json.loads(str(gps_list))
        print type(data), data

        self.roi_gps_json = data
        pass

    def toggleMapsJS(self):
        self.ui.webView.page().mainFrame().evaluateJavaScript("toggleHexagonMaps();")
        pass


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    qt_app = MainUi()
    qt_app.show()
    sys.exit(app.exec_())
