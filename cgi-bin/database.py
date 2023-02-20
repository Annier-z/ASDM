#!/usr/bin/env python3
import cgi
import cgitb
import sys
import os
import folium
import cx_Oracle
from folium import plugins


def load_oracle(result, flag):
    name = []
    coord = []
    for row in result:
        points = []
        name = row[0]
        coord = row[1].read().split()
        if (coord[0] == "POINT"):
            for i in range(1, len(coord)-1, 2):
                point_x = (float(coord[i].strip('(),')))
                point_y = (float(coord[i+1].strip('(),')))
                points.append((point_y, point_x))
            if (flag == 'service'):
                folium.Marker(location=points.pop(), popup=str(name), icon=folium.Icon(
                    icon='eye-open', color='red')).add_to(layer_point_services)
            if (flag == 'servicenearby'):
                folium.Marker(location=points.pop(), popup=str(name), icon=folium.Icon(
                    icon='info-sign')).add_to(layer_point_services)
            if (flag == 'busstop'):
                folium.Marker(location=points.pop(), popup=str(name), icon=folium.Icon(
                    icon='bullhorn', color='orange')).add_to(layer_point_busstops)
        elif (coord[0] == "POLYGON"):
            for i in range(1, len(coord)-1, 2):
                point_x = (float(coord[i].strip('(),')))
                point_y = (float(coord[i+1].strip('(),')))
                points.append([point_y, point_x])
            if (flag == 'nei'):
                folium.Polygon(locations=points, popup=str(
                    name), fill=True).add_to(layer_poly_nei)
            if (flag == 'sarea'):
                folium.Polygon(locations=points, popup=str(
                    name), fill=True, fill_color='red', fillOpacity=0.5, weight=1).add_to(layer_poly_serarea)
            if (flag == 'harea'):
                folium.Polygon(locations=points, popup=str(
                    name), fill=True, fill_color='green', fillOpacity=0.5, weight=1).add_to(layer_poly_serarea)
        elif (coord[0] == "LINESTRING"):
            for i in range(1, len(coord)-1, 2):
                point_x = (float(coord[i].strip('(),')))
                point_y = (float(coord[i+1].strip('(),')))
                points.append([point_y, point_x])
            if (flag == 'busroute'):
                folium.PolyLine(locations=points, weight=5, color='lightgreen', popup=str(
                    name)).add_to(layer_poly_busroutes)


# Local Debug Parameters:
# os.environ['QUERY_STRING']="postcode='EH3 9NG'&nei='Old Town'&lat=55.111&lon=-3.11&service_type=1"
flags = []
cgitb.enable()
# Dict of Service_Type_ID
services = {"0": "All Service",
            "1": "Shelter",
            "2": "Police Station",
            "3": "Hospital",
            "4": "Information Hub"
            }
try:
    # Create instance of FieldStorage
    form = cgi.FieldStorage()
    # Get data from fields
    addr = form.getvalue('addr')
    lat = form.getvalue('lat')
    lon = form.getvalue('lon')
    nei = form.getvalue('nei')
    service_type = form.getvalue('service_type')
    f_nearby_service = form.getvalue('nearby')
    service_nearby = form.getvalue('nearby_service')
    f_bus = form.getvalue('bus')
    bus_type = form.getvalue('bus_list')
    f_cover = form.getvalue('cover')
    cover_type = form.getvalue('cover_list')
    f_nearcover = form.getvalue('nearcover')
    nearcover = form.getvalue("nearcover_list")
    flags.append([f_nearcover, nearcover])
    # Check key values
    if lat is None:
        flags.append('form.lat is None')
    else:
        lat = float(lat)
    if lon is None:
        flags.append('form.lon is None')
    else:
        lon = float(lon)

    queries = {
        'nei': "SELECT NATURALCOM,SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(ORA_GEOMETRY,4326)) FROM NNH WHERE NATURALCOM='%s'" % (nei),
        'nei_all': "SELECT NATURALCOM,SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(ORA_GEOMETRY,4326)) FROM NNH WHERE NATURALCOM IN (SELECT NATURALCOM FROM NNH A, S1885898.SUPPORT_SERVICES B WHERE SDO_CONTAINS(A.ORA_GEOMETRY,B.COORDINATES)='TRUE')",
        'spec_service': "SELECT SERVICE_NAME, SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(COORDINATES,4326)) FROM S1885898.SUPPORT_SERVICES WHERE TYPE='%s'" % (service_type),
        'spec_service_inone': "SELECT A.SERVICE_NAME, SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(A.COORDINATES,4326)) FROM S1885898.SUPPORT_SERVICES A, S2298227.NNH B WHERE SDO_NN(B.ORA_GEOMETRY, A.COORDINATES, 'SDO_NUM_RES=1')='TRUE' AND B.NATURALCOM='%s' AND A.TYPE='%s'" % (nei, service_type),
        'service_all_inone': "SELECT A.SERVICE_NAME, SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(A.COORDINATES,4326)) FROM S1885898.SUPPORT_SERVICES A, S2298227.NNH B WHERE SDO_CONTAINS(B.ORA_GEOMETRY, A.COORDINATES)='TRUE' AND B.NATURALCOM='%s'" % (nei),
        'service_all': "SELECT SERVICE_NAME, SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(COORDINATES,4326)) FROM S1885898.SUPPORT_SERVICES",
        'busr': "SELECT ROUTE_ID,SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(ROUTE,4326)) FROM S1885898.BUS_ROUTES",
        'busr_nearby': "SELECT A.ROUTE_ID,SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(A.ROUTE,4326)) FROM S1885898.BUS_ROUTES A,S2298227.NNH B WHERE SDO_NN(A.ROUTE, B.ORA_GEOMETRY, 'SDO_NUM_RES=1', 1) = 'TRUE' AND B.NATURALCOM='%s'" % (nei),
        'info': "SELECT B.SERVICE_NAME as Near_IC, SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(B.COORDINATES,4326)) FROM S1885898.SUPPORT_SERVICES A, S1885898.SUPPORT_SERVICES B WHERE SDO_WITHIN_DISTANCE(A.COORDINATES, B.COORDINATES, 'DISTANCE = 1000') = 'TRUE' AND A.TYPE = 1 AND B.TYPE = 4",
        'nearby': "SELECT A.SERVICE_NAME, SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(A.COORDINATES,4326)) FROM S1885898.SUPPORT_SERVICES A, S2298227.NNH B WHERE SDO_NN(B.ORA_GEOMETRY, A.COORDINATES, 'SDO_NUM_RES=2')='TRUE' AND B.NATURALCOM='%s' AND A.TYPE='%s'" % (nei, service_nearby),
        'nearbyall': "SELECT A.SERVICE_NAME, SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(A.COORDINATES,4326)) FROM S1885898.SUPPORT_SERVICES A, S2298227.NNH B WHERE SDO_NN(B.ORA_GEOMETRY, A.COORDINATES, 'SDO_NUM_RES=2')='TRUE' AND B.NATURALCOM='%s' AND A.TYPE != '%s'" % (nei, service_type),
        'busstop': "SELECT BUS_STOP_NAME,SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(COORDINATES,4326)) FROM S1885898.BUS_STOPS",
        'busstop_nearby': "SELECT A.BUS_STOP_NAME,SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(A.COORDINATES,4326)) FROM S1885898.BUS_STOPS A, S2298227.NNH B WHERE SDO_NN(A.COORDINATES, B.ORA_GEOMETRY, 'SDO_NUM_RES=1', 1) = 'TRUE' AND B.NATURALCOM='%s'" % (nei),
        'cover_safe': "SELECT SERVICE_NA,SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(ORA_GEOMETRY,4326)) FROM POLAREA",
        'cover_health': "SELECT SERVICE_NA,SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(ORA_GEOMETRY,4326)) FROM HOSAREA",
        'cover_safe_inone': "SELECT A.SERVICE_NA,SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(A.ORA_GEOMETRY,4326)) FROM POLAREA A, NNH B WHERE SDO_RELATE( B.ORA_GEOMETRY,A.ORA_GEOMETRY, 'MASK=OVERLAPBDYINTERSECT')='TRUE' AND B.NATURALCOM='%s'" % (nei),
        'cover_health_inone': "SELECT A.SERVICE_NA,SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(A.ORA_GEOMETRY,4326)) FROM HOSAREA A, NNH B WHERE SDO_RELATE( B.ORA_GEOMETRY,A.ORA_GEOMETRY, 'MASK=OVERLAPBDYINTERSECT')='TRUE' AND B.NATURALCOM='%s'" % (nei),
        'cover_safe_near': "SELECT A.SERVICE_NA,SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(A.ORA_GEOMETRY,4326)) FROM POLAREA A, NNH B WHERE SDO_NN(A.ORA_GEOMETRY, B.ORA_GEOMETRY, 'SDO_NUM_RES=1', 1) = 'TRUE' AND B.NATURALCOM='%s'" % (nei),
        'cover_health_near': "SELECT A.SERVICE_NA,SDO_UTIL.TO_WKTGEOMETRY(SDO_CS.TRANSFORM(A.ORA_GEOMETRY,4326)) FROM HOSAREA A, NNH B WHERE SDO_NN(A.ORA_GEOMETRY, B.ORA_GEOMETRY, 'SDO_NUM_RES=1', 1) = 'TRUE' AND B.NATURALCOM='%s'" % (nei),
        'part': "SELECT LOCATED_AREA  FROM (SELECT A.LOCATED_AREA, B.NATURALCOM FROM S2437514.PART A, NNH B WHERE SDO_RELATE(A.CENTRE_LOCATION, B.ORA_GEOMETRY, 'MASK=CONTAINS QUERYTYPE=WINDOW') = 'TRUE') WHERE NATURALCOM = '%s' " % (nei)
    }

    # Using folium to create map
    map = folium.Map(location=[lat, lon], control_scale=True, zoom_start=12, height=550,
                     attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>')
    # Add satellite image tile layer to map
    folium.TileLayer(name="Google Maps", tiles="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", subdomains=[
        'mt0', 'mt1', 'mt2', 'mt3'], attr='Imagery &copy; <a href="https://maps.google.com/">Google</a>').add_to(map)
    # Create feature layers
    layer_poly_nei = folium.FeatureGroup(name="NeighbourHoods")
    layer_point_services = folium.FeatureGroup(name="Services")
    layer_poly_serarea = folium.FeatureGroup(name="Service Area")
    layer_poly_busroutes = folium.FeatureGroup(name="Bus Routes")
    layer_point_busstops = folium.FeatureGroup(name="Bus Stops")
    # Excute queries
    with open("oracle", 'r') as pwf:
        db = pwf.readline().strip()
        usr = pwf.readline().strip()
        pw = pwf.readline().strip()
        conn = cx_Oracle.connect(dsn=db, user=usr, password=pw)
        c = conn.cursor()

        if (nei == 'all'):
            result = c.execute(queries.get('nei_all'))
            load_oracle(result, 'nei')
            if (service_type == '0'):
                result = c.execute(queries.get('service_all'))
                load_oracle(result, 'service')
            else:
                result = c.execute(queries.get('spec_service'))
                load_oracle(result, 'service')
            if (f_cover == 'yes'):
                if (cover_type == '0'):
                    result = c.execute(queries.get('cover_safe'))
                    load_oracle(result, 'sarea')
                    result = c.execute(queries.get('cover_health'))
                    load_oracle(result, 'harea')
                if (cover_type == '1'):
                    result = c.execute(queries.get('cover_safe'))
                    load_oracle(result, 'sarea')
                if (cover_type == '2'):
                    result = c.execute(queries.get('cover_health'))
                    load_oracle(result, 'harea')
            else:
                if(f_nearcover == 'yes'):
                    if (nearcover == '0'):
                        result = c.execute(queries.get('cover_safe'))
                        load_oracle(result, 'sarea')
                        result = c.execute(queries.get('cover_health'))
                        load_oracle(result, 'harea')
                    if (nearcover == '1'):
                        result = c.execute(queries.get('cover_safe'))
                        load_oracle(result, 'sarea')
                    if (nearcover== '2'):
                        result = c.execute(queries.get('cover_health'))
                        load_oracle(result, 'harea')
        else:
            part = None
            result = c.execute(queries.get('part'))
            for row in result:
                part = row[0]
            result = c.execute(queries.get('nei'))
            load_oracle(result, 'nei')
            if (f_nearby_service == 'yes'):
                if (service_nearby == '0'):
                    result = c.execute(queries.get('nearbyall'))
                    load_oracle(result, 'servicenearby')
                else:
                    result = c.execute(queries.get('nearby'))
                    load_oracle(result, 'servicenearby')
            if (service_type == '0'):
                result = c.execute(queries.get('service_all_inone'))
                load_oracle(result, 'service')
            else:
                result = c.execute(queries.get('spec_service_inone'))
                load_oracle(result, 'service')
            if (f_cover == 'yes'):
                if (cover_type == '0'):
                    result = c.execute(queries.get('cover_safe_inone'))
                    load_oracle(result, 'sarea')
                    result = c.execute(queries.get('cover_health_inone'))
                    load_oracle(result, 'harea')
                if (cover_type == '1'):
                    result = c.execute(queries.get('cover_safe_inone'))
                    load_oracle(result, 'sarea')
                if (cover_type == '2'):
                    result = c.execute(queries.get('cover_health_inone'))
                    load_oracle(result, 'harea')
            if (f_nearcover == 'yes'):
                if (nearcover == '0'):
                    result = c.execute(queries.get('cover_safe_near'))
                    load_oracle(result, 'sarea')
                    result = c.execute(queries.get('cover_health_near'))
                    load_oracle(result, 'harea')
                if (nearcover == '1'):
                    result = c.execute(queries.get('cover_safe_near'))
                    load_oracle(result, 'sarea')
                if (nearcover == '2'):
                    result = c.execute(queries.get('cover_health_near'))
                    load_oracle(result, 'harea')

        # Nearby Services Queries

        if (f_bus == 'yes'):
            if (bus_type == '0'):
                result = c.execute(queries.get('busr'))
                load_oracle(result, 'busroute')
                result = c.execute(queries.get('busstop'))
                load_oracle(result, 'busstop')
            else:
                result = c.execute(queries.get('busr_nearby'))
                load_oracle(result, 'busroute')
                result = c.execute(queries.get('busstop_nearby'))
                load_oracle(result, 'busstop')

    # Add Toolbox to map
    map.add_child(plugins.MeasureControl(position='topleft'))
    # Add overlayers and layercontrol to map
    layer_poly_nei.add_to(map)
    layer_point_services.add_to(map)
    layer_poly_busroutes.add_to(map)
    layer_poly_serarea.add_to(map)
    layer_point_busstops.add_to(map)
    folium.LayerControl().add_to(map)

    print("Content-type:text/html\n")
    print("Hello - Welcome you from")
    print("<b>%s</b>" % (addr.split(',')[0]))
    print("<br>")
    if (nei == 'all'):
        print("You are looking for <b>%ss</b> in <b>%s</b>." %
              (services.get(service_type), nei))
    else:
        if (part is not None):
            print("You are looking for <b>%ss</b> in <b>%s</b>,<b>" %
                  (services.get(service_type), nei))
            print(part)
            print("</b>of City Edinburgh.")
        else:
            print("You are looking for <b>%ss</b> in <b>%s</b>." %
                  (services.get(service_type), nei))
    # print("<br>")
    # print("Custom Debug Info:")
    # print(flags)
    # print("<br>")
    print(map.get_root().render())

except:
    print("Content-type:text/html\n")
    print("Custom Debug Info:")
    print("<br>")
    print(flags)
    print(cgitb.html(sys.exc_info()))
