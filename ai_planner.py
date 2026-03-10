import random

def generate_itinerary(df, days):

    places = df["name"].tolist()

    random.shuffle(places)

    itinerary = {}

    per_day = max(1, len(places)//days)

    index = 0

    for d in range(1, days+1):

        itinerary[f"Day {d}"] = places[index:index+per_day]

        index += per_day

    return itinerary