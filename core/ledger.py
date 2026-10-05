import re

def normalize_location(loc):
    if not loc:
        return ""
    loc = loc.lower().strip()
    # Remove punctuation for slugging
    slug = re.sub(r'[^\w\s]', '', loc).replace(" ", "_")
    
    synonyms = {
        "ice_cave": ["ice cave", "icy cavern"],
        "cottage": ["cabin", "cottage", "wooden cabin interior"]
    }
    
    for target, matches in synonyms.items():
        if loc in matches:
            return target
    
    # Check if the slugified version of a synonym is actually what we want 
    # (e.g. if input was 'icy cavern', slug is 'icy_cavern', but it should be 'ice_cave')
    # The plan says "maps a small synonym table". Let's stick to exact matches for simplicity first.
    
    return slug

def normalize_person(traits):
    tokens = []
    for key, val in traits.items():
        if not val:
            continue
        val = val.lower().replace(",", "").replace(" ", "_")
        tokens.append(f"{key}:{val}")
    return frozenset(sorted(tokens))

def is_unreliable(count_men, count_women, people):
    if count_men + count_women >= 2:
        # Check if all normalized persons are identical
        normalized = [normalize_person(p) for p in people]
        if len(set(normalized)) <= 1 and len(people) > 0:
            return True
    
    # If count is positive (meaning we found someone) but no people data provided?
    # The plan says "when the count is positive and `people` is empty".
    if (count_men + count_women) > 0 and not people:
        return True
        
    return False
