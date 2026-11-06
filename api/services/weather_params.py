BASIC_ELEMENTS = (
    "datetime,solarradiation,solarenergy,temp,cloudcover"
)

FULL_ELEMENTS = (
    "datetime,tempmax,tempmin,temp,cloudcover,"
    "solarradiation,solarenergy,sunrise,sunset,"
    "description,icon,feelslike,humidity,windspeed"
)

def get_weather_params(token: str, elements: str):

    return {
        "key": token,
        "contentType": "json",
        "unitGroup": "metric",
        "include": "hours",
        "elements": elements,
        "lang": "tr"
    }