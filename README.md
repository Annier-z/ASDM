# ASDM Group 1
## Introduction
This is a group project of the course (Advanced Spatial Database Methods), School of GeoScience, The University of Edinburgh.  
[Link](https://www.geos.ed.ac.uk/~s2298227/ASDM/index.html)
## index.html
Contains the form and JavaScripts related.
```javascript
 function show_list(flag) {
        let checkBox = document.getElementById(flag);
        // Get the corresponding list object
        let select_list = document.getElementById(flag + "_list");
        // If the checkbox is checked, display the list
        if (checkBox.checked === true) {
            select_list.style.display = "inline";
        }
        else {
            select_list.style.display = "none";
        }
    }

    function hideShowOptions(x) {
        let hideTrigger = [0, 1, 2, 3, 4];
        let list = $('#nearby_list')
        switch (x) {
            case hideTrigger[0].toString():
                list.children('option[value="0"]').css('display', 'block');;
                list.children('option[value="1"]').css('display', 'block');
                list.children('option[value="2"]').css('display', 'block');
                list.children('option[value="3"]').css('display', 'block');
                list.children('option[value="4"]').css('display', 'block');
                break;
            case hideTrigger[1].toString():
                list.children('option[value="1"]').css('display', 'none');
                list.children('option[value="0"]').css('display', 'block');
                list.children('option[value="2"]').css('display', 'block');
                list.children('option[value="3"]').css('display', 'block');
                list.children('option[value="4"]').css('display', 'block');
                break;
            case hideTrigger[2].toString():
                list.children('option[value="2"]').css('display', 'none');
                list.children('option[value="1"]').css('display', 'block');
                list.children('option[value="0"]').css('display', 'block');
                list.children('option[value="3"]').css('display', 'block');
                list.children('option[value="4"]').css('display', 'block');
                break;
            case hideTrigger[3].toString():
                list.children('option[value="3"]').css('display', 'none');
                list.children('option[value="1"]').css('display', 'block');
                list.children('option[value="2"]').css('display', 'block');
                list.children('option[value="0"]').css('display', 'block');
                list.children('option[value="4"]').css('display', 'block');
                break;
            case hideTrigger[4].toString():
                list.children('option[value="4"]').css('display', 'none');
                list.children('option[value="1"]').css('display', 'block');
                list.children('option[value="2"]').css('display', 'block');
                list.children('option[value="3"]').css('display', 'block');
                list.children('option[value="0"]').css('display', 'block');
                break;
            default:
                list.children('option[value="0"]').css('display', 'block');
                list.children('option[value="1"]').css('display', 'block');
                list.children('option[value="2"]').css('display', 'block');
                list.children('option[value="3"]').css('display', 'block');
                list.children('option[value="4"]').css('display', 'block');
        }
    }

    function validateForm() {
        display();
        return true;
    }

    function enable_submit() {
        if (document.getElementById("lat").value !== '') {
            $('#submit').removeAttr("disabled");
        }
    }

    function check() {
        let posts = document.getElementById("postcode").value
        jQuery.getJSON("https://nominatim.openstreetmap.org/search?postalcode=" + posts + "&format=json&limit=1", function (data) {
            let tmp_lat = 0
            let tmp_lon = 0
            let tmp_addr = ''
            try {
                tmp_lat = data[0].lat;
                tmp_lon = data[0].lon;
                tmp_addr = data[0].display_name
            }
            catch (err) {
                alert("Incorrect PostCode! Please Check")
                return
            }
            let lat = document.getElementById("lat")
            let lon = document.getElementById("lon")
            let addr = document.getElementById("addr")
            lat.removeAttribute('readonly');
            lon.removeAttribute('readonly');
            addr.removeAttribute('readonly');
            lat.value = tmp_lat;
            lon.value = tmp_lon;
            addr.value = tmp_addr;
            lon.setAttribute('readonly', 'readonly');
            lat.setAttribute('readonly', 'readonly');
            addr.setAttribute('readonly', 'readonly');
        })
    }

    function display() {
        let ifrm = document.getElementById('pymap');
        ifrm.style.display = 'block';
    }
```
## /cgi-bin/database.py
Contains Python scripts using Folium and cx_Oracle.
```python
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
```