import random

_RAW = [
    # Zwierzęta
    "pies", "kot", "ryba", "ptak", "kura", "koza", "owca", "krowa", "kon", "lew",
    "tygrys", "lis", "wilk", "zajac", "bober", "wydra", "jelen", "sarna", "dzik",
    "zubr", "kret", "mysz", "szczur", "zolw", "zaba", "waz", "sroka", "wrona",
    "bocian", "czapla", "jastrzab", "sokol", "sowa", "kaczka", "ges", "labedz",
    "pingwin", "papuga", "kanarek", "chomik", "krolik", "delfin", "wieloryb",
    "rekin", "krab", "homar", "malpa", "goryl", "slon", "hipopotam", "nosorozec",
    "zebra", "wielbladz", "kangur", "koala", "panda", "niedzwiedz", "byk", "swinia",
    "prosie", "ciele", "jagniak", "pelikan", "flamingo", "tukan", "lemur", "gepard",
    "jaguar", "pantera", "hiena", "szakal", "mors", "foka", "albatros",
    # Przyroda
    "rzeka", "jezioro", "morze", "ocean", "las", "pole", "laka", "gora", "dolina",
    "wzgorze", "pustynia", "plaza", "wyspa", "woda", "ogien", "ziemia", "powietrze",
    "wiatr", "deszcz", "snieg", "mraz", "grad", "burza", "chmura", "niebo", "slonce",
    "ksiezyc", "gwiazda", "kometa", "planeta", "galaktyka", "kosmos", "meteor",
    "zorza", "tecza", "mgla", "wulkan", "powodz", "huragan", "tornado", "lawina",
    "trzesienie", "tsunami", "lodowiec", "rownina", "wawoz", "kanion", "jaskinia",
    "grota", "skala", "klif", "mierzeja", "delta",
    # Dom i meble
    "stol", "krzeslo", "lozko", "szafa", "okno", "drzwi", "podloga", "sufit",
    "sciana", "dach", "komin", "piec", "zlew", "wanna", "lustro", "obraz", "lampa",
    "dywan", "sofa", "fotel", "polka", "szuflada", "lodowka", "kuchenka", "zmywarka",
    "pralka", "wentylator", "grzejnik", "kominek", "balkon", "taras",
    "piwnica", "strych", "garaz", "weranda", "altana", "plot", "brama", "furtka",
    # Jedzenie
    "chleb", "maslo", "ser", "jajko", "mleko", "herbata", "kawa", "sok", "zupa",
    "kasza", "makaron", "ziemniak", "kapusta", "marchew", "cebula", "czosnek",
    "pomidor", "ogorek", "papryka", "groch", "fasola", "orzech", "jablko", "gruszka",
    "sliwka", "wisnia", "truskawka", "malina", "borowka", "cytryna", "pomarancz",
    "banan", "mango", "ananas", "winogrono", "miod", "konfitura", "oliwa", "ocet",
    "sol", "pieprz", "cukier", "ryz", "maka", "ciasto", "ciastko", "tort", "lody",
    "czekolada", "cukierek", "wafelek", "herbatnik", "precel", "bajgiel", "rogalik",
    "bulka", "bigos", "pierogi", "barszcz", "kotlet", "schab", "kielbasa", "szynka",
    # Liczby
    "jeden", "dwa", "trzy", "cztery", "piec", "szesc", "siedem", "osiem",
    "dziewiec", "dziesiec", "jedenscie", "dwanascie", "trzynascie", "czternascie",
    "pietnascie", "szesnascie", "siedemnascie", "osiemnascie", "dwadziescia",
    "trzydziesci", "czterdziesci", "piecdziesiat", "sto", "tysiac", "milion", "zero",
    # Kolory
    "czerwony", "niebieski", "zielony", "zolty", "bialy", "czarny", "szary",
    "brazowy", "rozowy", "fioletowy", "granatowy", "bezowy", "kremowy", "turkusowy",
    "zloty", "srebrny", "miedziany", "oliwkowy", "lawendowy", "koralowy", "lazurowy",
    # Ciało
    "glowa", "szyja", "ramie", "reka", "palec", "serce", "pluco", "watroba",
    "zoladek", "noga", "kolano", "stopa", "oko", "ucho", "nos", "usta", "zab",
    "jezyk", "wlos", "skora", "kregoslup", "zebro", "bark", "nadgarstek", "lokiec",
    "biodro", "lydka", "kostka", "czolo", "policzek", "broda", "kark",
    # Materiały
    "kamien", "skala", "piasek", "glina", "lod", "para", "dym", "drewno", "szklo",
    "plastik", "guma", "papier", "metal", "zloto", "srebro", "zelaz", "miedz",
    "cyna", "diament", "granit", "marmur", "beton", "cegla", "tkanina", "welna",
    "jedwab", "bawelna", "len", "nylon",
    # Miejsca
    "dom", "zamek", "kosciol", "szkola", "szpital", "apteka", "sklep", "rynek",
    "ulica", "most", "tunel", "lotnisko", "stacja", "port", "fabryka", "muzeum",
    "teatr", "kino", "biblioteka", "ogrod", "park", "plac", "osiedle", "wiezowiec",
    "latarnia", "studnia", "mlyn", "wiatrak", "elektrownia", "kopalnia", "stocznia",
    "hangar", "magazyn", "silos", "chlewnia", "obora",
    # Zawody
    "lekarz", "nauczyciel", "inzynier", "robotnik", "piekarz", "kucharz", "kelner",
    "kierowca", "pilot", "marynarz", "zolnierz", "policjant", "strazak", "adwokat",
    "ksiegowy", "programista", "artysta", "malarz", "pisarz", "poeta", "muzyk",
    "aktor", "fotograf", "architekt", "dentysta", "farmaceuta", "weterynar",
    "rolnik", "gornik", "hutnik", "elektryk", "hydraulik", "murarz",
    # Dni i miesiące
    "poniedzialek", "wtorek", "sroda", "czwartek", "piatek", "sobota", "niedziela",
    "styczen", "luty", "marzec", "kwiecien", "maj", "czerwiec", "lipiec",
    "sierpien", "wrzesien", "pazdziernik", "listopad", "grudzien",
    # Ubrania i akcesoria
    "klucz", "torba", "plecak", "walizka", "parasol", "kapelusz", "buty",
    "skarpety", "spodnie", "koszula", "sukienka", "sweter", "kurtka", "plaszcz",
    "zegarek", "pierscien", "naszyjnik", "kolczyk", "bransoletka",
    "portfel", "pasek", "krawat", "rekawiczki", "szalik", "czapka",
    # Pojazdy
    "rower", "motor", "samochod", "autobus", "tramwaj", "pociag", "statek",
    "samolot", "helikopter", "rakieta", "czolg", "okret", "lodka", "kajak",
    "hulajnoga", "motocykl", "ciagnik", "kombajn", "koparka", "dzwig",
    # Instrumenty
    "gitara", "pianino", "skrzypce", "trabka", "flet", "beben", "harfa",
    "akordeon", "klarnet", "saksofon", "organy", "banjo", "ukulele",
    # Sport i gry
    "pilka", "siatka", "kosz", "stadion", "basen", "boisko", "kort",
    "ring", "trampolina", "szachy", "warcaby", "karta", "kostka", "domino",
    "puzzle", "bumerang", "badminton", "tenis", "squash",
    # Elektronika
    "telefon", "komputer", "tablet", "telewizor", "radio", "aparat", "drukarka",
    "skaner", "klawiatura", "monitor", "sluchawki", "glosnik", "bateria", "kabel",
    "router", "modem", "dysk", "pendrive", "kamera", "projektor",
    # Narzędzia i różne
    "mlot", "gwozdz", "sruba", "nakretka", "obcagi", "pilnik", "wiertlo",
    "drabina", "wiadro", "miotla", "grabie", "szpadel", "motyka", "siekiera",
    "latarka", "swieca", "noz", "widelec", "lyzka", "garnek", "patelnia",
    "talerz", "miska", "szklanka", "kubek", "dzbanek", "butelka", "puszka",
    "slok", "beczka", "odkurzacz", "szczotka", "grzebien", "nozyczki", "igla",
    "nitka", "guzik", "linijka", "olowek", "dlugopis", "mazak", "kredka", "notes",
    "teczka", "zeszyt", "kartka", "koperta", "stempel", "znaczek", "mapa",
    "kompas", "luneta", "lupa", "termometr", "barometr", "waga", "zegar",
]

WORDS = list(dict.fromkeys(_RAW))


def generate_slug(existing: set | None = None) -> str:
    if existing is None:
        existing = set()
    for length in range(2, 6):
        for _ in range(10):
            slug = "-".join(random.sample(WORDS, length))
            if slug not in existing:
                return slug
    raise RuntimeError("Nie udało się wygenerować unikalnego slug (wyczerpano kombinacje 2-5 słów)")
