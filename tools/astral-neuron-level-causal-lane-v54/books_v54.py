"""V54 frozen candidate book list (fresh text, disjoint from every V50 book). State slices:
astral-neuron-level-causal-lane-v54-execution, instrument-validity-gate-v3.
(gutenberg id, expected title substring, operator-declared year). IDs/titles are AI-recalled; a title
mismatch on the Gutenberg header drops the book with no replacement."""
BOOKS = [
    (55, "Oz", 1900), (54, "Marvelous Land of Oz", 1904), (78, "Tarzan of the Apes", 1912), (81, "Return of Tarzan", 1913),
    (113, "Secret Garden", 1911), (146, "Little Princess", 1905), (108, "Return of Sherlock Holmes", 1905),
    (3289, "Valley of Fear", 1915), (863, "Styles", 1920), (1155, "Secret Adversary", 1922), (1245, "Night and Day", 1919),
    (3825, "Pygmalion", 1913), (5200, "Metamorphosis", 1915), (1250, "Anthem", 1938), (2500, "Siddhartha", 1922),
    (64, "Gods of Mars", 1913), (68, "Warlord of Mars", 1914), (47, "Anne of Avonlea", 1909), (8164, "Jeeves", 1919),
    (2480, "Western Eyes", 1911), (525, "Youth", 1902), (2948, "Angels Fear", 1905), (1164, "Iron Heel", 1908),
    (1013, "First Men in the Moon", 1901), (2781, "Just So", 1902), (1450, "Pollyanna", 1913), (157, "Daddy-Long-Legs", 1912),
    (498, "Sunnybrook", 1903), (559, "Greenmantle", 1916), (139, "Lost World", 1912), (10002, "Borderland", 1908),
    (64317, "Gatsby", 1925), (28333, "Rainbow", 1915), (5670, "Jacob", 1922), (166, "Summer", 1917), (1142, "Typhoon", 1902),
    (2554, "Crime and Punishment", 1866), (1342, "Pride and Prejudice", 1813),  # last two: deliberate year rejects
]
MIN_YEAR = 1900
PER_DOC_CAP = 400
