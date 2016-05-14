from flask import Flask, request, render_template, send_from_directory
from googleplaces import GooglePlaces
from geopy.distance import vincenty
import random
import os

application = Flask(__name__)

@application.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(application.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
@application.route('/')
@application.route('/index')
def my_form():
    locations = [[31.6532001,-7.99124],[13.3674002,103.8610001],[41.06073,28.9877701],
                 [21.0288906,105.8546371],[50.1269188,14.4567204],[51.5064201,-0.12721],
                 [41.9030495,12.4958],[-34.6145554,-58.4458771],[48.8569298,2.3412001],
                 [-33.9205017,18.4211998],[40.7820015,-73.8317032],[46.0116005,7.7483602],
                 [41.375,2.1575899],[38.643573,34.830751],[-8.5059204,115.26017],
                 [-13.5165796,-71.9783707],[59.928875,30.2215462],[13.7533503,100.5048294],
                 [27.6933002,85.3225021],[37.9928017,23.7695007],[47.513031,19.1229801],
                 [-45.0317993,168.6640015],[22.3361568,114.1869659],[25.2873306,55.3206406],
                 [-33.8740005,151.2030029]]
                 
    return render_template("index.html",latlong = random.choice(locations))

@application.route('/', methods=['POST'])
def my_form_post():

    dest = request.form['destination']
    sugthings = request.form.getlist('formActivity')
    knowthings = [request.form['active1'],
                  request.form['active2'],
                  request.form['active3'],
                  request.form['active4'],
                  request.form['active5'],]
              
    (output, error) = backend(dest,sugthings,knowthings)
    if error:
        return error
        
    results = []        
    for i in range(5):
        results.append({'num':i+1, 
                        'hotel':output[i][0],
                        'latlong': '['+str(output[i][1])+','+str(output[i][2])+']', 
                        'attractions':[]})
        for attraction in output[i][4]:
            results[-1]['attractions'].append({'name': attraction[0],
                                               'latlong': '['+str(attraction[2])+','+str(attraction[3])+']', 
                                               'dist': int(attraction[1])})
        
    return render_template("result.html", results = results)
                    
def backend(destination,activities,knownactivities):
    
    YOUR_API_KEY = '...'
    
    google_places = GooglePlaces(YOUR_API_KEY)
    
    spot = google_places.autocomplete(destination)
    destination = spot.predictions[0].description
                    
    hotelresults = {}
    query_result = google_places.nearby_search(location=destination, 
                                               types=[u'lodging'])
            
    if len(query_result.places) == 0:
        return ([],'Error: No lodgings found in this location. Please check input')
        
    for place in query_result.places:
        hotelresults[place.name] = (place.geo_location[u'lat'],
                                    place.geo_location[u'lng'])
                                    
    if activities:
        activeresults = []
        for activity in activities:
            query_result = google_places.nearby_search(location=destination, types=[activity])
            if len(query_result.places) > 0:
                activeresults.append((activity,{}))
                for place in query_result.places:
                   activeresults[-1][1][place.name] = (place.geo_location[u'lat'],
                                                       place.geo_location[u'lng'])
                                                  
    else:
        activeresults = [('known',{})]        
        
        for location in knownactivities:
            if location:
                
                spot = google_places.autocomplete(location,location=destination)
                spot.predictions[0].get_details()
                                
                activeresults[0][1] = (spot.predictions[0].place.geo_location[u'lat'],
                                       spot.predictions[0].place.geo_location[u'lng'])

    hotelLocsDists = []
    for hotel in hotelresults.keys():
        hotelLocsDists.append([hotel,hotelresults[hotel][0],hotelresults[hotel][1],0,{}])
        
        for activity in activeresults:
            hotelLocsDists[-1][-1][activity[0]]=[]
            for actloc in activity[1].keys():
                dist = vincenty((hotelLocsDists[-1][1],hotelLocsDists[-1][2]),
                                (activity[1][actloc][0],activity[1][actloc][1])).meters
                hotelLocsDists[-1][-1][activity[0]].append((actloc, dist,
                                                            activity[1][actloc][0],
                                                            activity[1][actloc][1]))
                    
            hotelLocsDists[-1][-1][activity[0]].sort(key=lambda tup: tup[1])  
            
    finalresult = []
    
    for hotel in hotelLocsDists:
        finalresult.append(hotel[:4])
        finalresult[-1].append([])
        resnum = 0
        eachnum = 0
        while (resnum < 10):
            for activity in hotel[-1].keys():
                finalresult[-1][-1].append((hotel[-1][activity][eachnum][0],
                                            hotel[-1][activity][eachnum][1],
                                            hotel[-1][activity][eachnum][2],
                                            hotel[-1][activity][eachnum][3]))
                finalresult[-1][-2] = finalresult[-1][-2] + finalresult[-1][-1][-1][1]
            
            eachnum= eachnum + 1
            resnum = resnum + len(hotel[-1].keys())

    finalresult.sort(key=lambda tup: tup[-2]) 
    
    return (finalresult, '')
    
if __name__ == "__main__":
    application.run()