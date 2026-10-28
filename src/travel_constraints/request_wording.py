"""Authored held-out wording, fixed before any v2 model evaluation.

These are controlled paraphrases, not independent real-user observations.
"""

VALIDATION = {
    "place_include_hard": [
        "The visit to {gallery} is non-negotiable.", "{gallery} has to remain in the schedule.",
        "Ensure that I still visit {gallery}.", "Treat {gallery} as a compulsory stop."],
    "place_include_soft": [
        "Seeing {gallery} would be a bonus if it fits.", "Keep {gallery} only if convenient.",
        "My preference is to retain {gallery}, but it is optional.", "Could {gallery} stay if the schedule allows?"],
    "place_exclude": [
        "Leave {museum} off the revised schedule.", "Delete the planned visit to {museum}.",
        "Exclude {museum} from my trip today.", "The new plan must not contain {museum}."],
    "hotel_time_by": [
        "I have to arrive at the hotel at or before {value}.", "Hotel arrival cannot be later than {spoken}.",
        "Ensure I am back at my hotel by {spoken} at the latest.", "{value} is the latest acceptable hotel arrival."],
    "hotel_time_exact": [
        "Hotel arrival is fixed at exactly {value}.", "I require a hotel arrival of precisely {spoken}.",
        "Match my hotel arrival to {value} exactly.", "Return me to the hotel at {spoken} on the dot."],
    "walking_limit_daily": [
        "Across the entire day, walking must not exceed {value} minutes.", "The sum of all walking time must be no greater than {value} minutes.",
        "Keep the day's combined walks within {value} minutes.", "I have an upper bound of {value} walking minutes for the whole day."],
    "walking_limit_segment": [
        "No single continuous walk may be longer than {value} minutes.", "Cap each individual walking stretch at {value} minutes.",
        "I can walk uninterrupted for at most {value} minutes per stretch.", "Every walking leg must be {value} minutes or shorter."],
    "walking_minimize": [
        "Choose an itinerary with as little walking as possible.", "I would rather spend less of the day on foot.",
        "Please prioritize reducing the overall amount of walking.", "Make the plan gentler on my feet by minimizing walking."],
    "ambiguous_time": [
        "An early return to my hotel is compulsory, though I haven't specified a clock time.", "I must reach my hotel early tonight, but have not decided the deadline.",
        "I require an early hotel arrival this evening.", "Getting back early to my hotel is essential."],
    "ambiguous_walking_scope": [
        "Walking may last no longer than {value} minutes.", "I have a {value}-minute walking cap.",
        "Keep walking within a limit of {value} minutes.", "There is a {value}-minute maximum on walking."],
    "near_lunch": [
        "Put the lunch venue near {gallery}.", "I need somewhere close to {gallery} for lunch.",
        "Locate lunch in the area around {gallery}.", "For lunch, pick a spot near the gallery, {gallery}."],
    "weather_alternative": [
        "In dry weather retain the South Bank walk; in rain switch that walk to a book cafe visit.",
        "Rain calls for a bookshop cafe in place of the walk. Without rain, the walk stays.",
        "Keep the outdoor walk unless it rains, in which case substitute a book cafe.",
        "If rain occurs, exchange the walk for a book cafe; if not, leave the walk in place."],
    "combined": [
        "Put lunch near {gallery}. Retain the walk without rain, or replace it with a book cafe if rain arrives. Keep {museum} in any weather. Hotel arrival must stay exactly {hotel}. Prefer the least walking overall.",
        "Lunch needs to be close to the gallery. In rain, a bookshop cafe replaces the walk; otherwise retain the walk. {museum} is compulsory regardless of rain. Match the original hotel arrival exactly. Minimize the day's walking.",
        "Retain {museum} rain or shine. Choose lunch near {gallery}. Keep the walk in dry weather and substitute a book cafe in wet weather. I require hotel arrival precisely at {hotel}. I would prefer minimal walking.",
        "Preserve the hotel return exactly as scheduled and keep {museum} regardless of rain. Lunch must be close to the gallery. No rain means retain the walk, rain means replace it with a book cafe. Reduce walking wherever possible."],
}

TEST = {
    "place_include_hard": [
        "Under no circumstances drop {gallery}.", "{gallery} is a stop I insist on keeping.",
        "Retain {gallery}; I require that visit.", "A visit to {gallery} must be included."],
    "place_include_soft": [
        "Retaining {gallery} is desirable rather than compulsory.", "If there is enough time, I'd enjoy {gallery}.",
        "I hope {gallery} can remain, but I can do without it.", "Consider keeping {gallery} as an optional stop."],
    "place_exclude": [
        "Drop the stop at {museum}.", "Cancel my planned {museum} visit.",
        "{museum} is somewhere I want removed.", "Take {museum} off my list of stops."],
    "hotel_time_by": [
        "My hotel arrival has a strict cutoff of {spoken}.", "Arrange things so I reach the hotel no later than {spoken}.",
        "I require arrival at my hotel before or at {value}.", "The deadline for reaching my hotel is {value}."],
    "hotel_time_exact": [
        "Neither before nor after {value}: that is when I must arrive at the hotel.", "My hotel arrival must be exactly {spoken}.",
        "Lock the hotel return to {value}, with no earlier or later arrival.", "I need hotel arrival at {spoken} exactly."],
    "walking_limit_daily": [
        "Budget at most {value} minutes for every walk added together.", "In total, I can spend no more than {value} minutes on foot today.",
        "The whole day's walking has a ceiling of {value} minutes.", "Add up all the walks and keep the result at or below {value} minutes."],
    "walking_limit_segment": [
        "Between breaks, I can walk for a maximum of {value} minutes.", "Do not schedule any uninterrupted walk exceeding {value} minutes.",
        "Each separate walking leg has an upper limit of {value} minutes.", "{value} minutes is the longest continuous walk I can do."],
    "walking_minimize": [
        "Where choices exist, favour the option involving less walking.", "My preference is for the least walking you can arrange.",
        "I'd appreciate a reduction in walking over the day.", "Aim for minimal walking without assuming a numerical limit."],
    "ambiguous_time": [
        "The hotel return needs to be early, but I cannot give you a precise time yet.", "I insist on arriving at my hotel early this evening.",
        "An early-evening arrival at the hotel is a must for me.", "Please make sure I get to my hotel early tonight."],
    "ambiguous_walking_scope": [
        "My maximum walking time is {value} minutes.", "I must not spend longer than {value} minutes walking.",
        "Walking needs a ceiling of {value} minutes.", "At most {value} minutes of walking is acceptable to me."],
    "near_lunch": [
        "Lunch must be in the neighbourhood of {gallery}.", "Arrange a midday meal close to {gallery}.",
        "Choose somewhere near {gallery} for my lunch break.", "Keep the lunch location close by the gallery, {gallery}."],
    "weather_alternative": [
        "When there is no rain the planned walk must remain; when there is rain a book cafe must take its place.",
        "Use a bookshop cafe instead of the walk in rainy weather, and retain the walk in rain-free weather.",
        "A dry forecast means keep the South Bank walk. A rainy forecast means replace it with a book cafe.",
        "The outdoor walk stays if it does not rain; otherwise I require a book cafe visit instead."],
    "combined": [
        "Eat lunch close to {gallery}. The walk is required if it stays dry; a book cafe replaces it if it rains. {museum} must remain whatever the forecast. Keep hotel arrival fixed at {hotel}. Favour less walking.",
        "{museum} is mandatory in all weather. Have lunch near the gallery. If it rains swap the walk for a bookshop cafe, and if it does not rain retain the walk. Arrive at the hotel at the original time exactly. Minimize walking.",
        "Hotel arrival is locked to {hotel}. Lunch must be near {gallery}. Keep {museum} rain or shine. Retain the walk without rain, but use a book cafe in its place with rain. Walking should be minimized overall.",
        "Lunch belongs near the gallery and {museum} stays regardless of weather. Preserve the scheduled hotel return exactly. Dry weather keeps the walk; rain replaces it with a book cafe. Choose the least walking possible."],
}


def held_out_texts(family, split, itinerary, target):
    item = target["constraints"][0]
    key = family
    if family == "place_include":
        key += "_" + item["priority"]
    elif family == "hotel_time":
        key += "_by" if item["operator"] == "<=" else "_exact"
    elif family == "walking_limit":
        key += "_daily" if item["scope"] == "daily_total" else "_segment"
    value = item["value"]
    spoken = value
    if family == "hotel_time":
        hour, minute = map(int, value.split(":"))
        spoken = f"{hour % 12 or 12}:{minute:02d} {'pm' if hour >= 12 else 'am'}"
    context = {"gallery": itinerary[0]["place"], "museum": itinerary[3]["place"],
               "hotel": itinerary[-1]["time"], "value": value, "spoken": spoken}
    pool = {"validation": VALIDATION, "test": TEST}[split]
    return [text.format(**context) for text in pool[key]]
