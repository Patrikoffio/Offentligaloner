#!/usr/bin/env python3
"""
Semantisk klassificering av 5 654 svenska kommunala/regionala yrkestitlar i 24 kategorier.
Klassificeringsbesluten är inbyggda direkt i logiken baserat på LLM-bedömning.
"""
import json
import re
from collections import Counter

# De 24 kategorierna
CATEGORIES = [
    "Samhällsbyggnad och Infrastruktur",
    "IT och Digitalisering",
    "Vård och Omsorg",
    "Utbildning och Pedagogik",
    "Socialt arbete och Stöd",
    "Kultur och Fritid",
    "Miljö och Naturvård",
    "Ekonomi och Administration",
    "HR och Personal",
    "Kommunövergripande och Strategiska funktioner",
    "Juridik och Säkerhet",
    "Politisk ledning och Stöd",
    "Fastighet och Lokalvård",
    "Kommunikation och Medborgarkontakt",
    "Folkhälsa och Hälsofrämjande arbete",
    "Forskning och Utveckling",
    "Avfall och Återvinning",
    "Brand och Räddningstjänst",
    "Energi och Klimat",
    "Invandring, Integration och Mångfald",
    "Transport och Trafikplanering",
    "Projektledning och Utvecklingsarbete",
    "Upphandling och Inköp",
    "Revision och Tillsyn",
]

def classify(title: str) -> str:
    """Klassificerar en titel semantiskt i en av 24 kategorier."""
    t = title.strip()
    tl = t.lower()

    # ----------------------------------------------------------------
    # HJÄLPFUNKTIONER
    # ----------------------------------------------------------------
    def contains(*words):
        return any(w in tl for w in words)

    def starts(*words):
        return any(tl.startswith(w) for w in words)

    def exact_match(*titles_list):
        return tl in [x.lower() for x in titles_list]

    # ----------------------------------------------------------------
    # SPECIALFALL – exakta matcher och välkända kantfall
    # ----------------------------------------------------------------
    # TA BORT-poster
    if tl in ["ta bort"]:
        return "Ekonomi och Administration"

    # ----------------------------------------------------------------
    # 1. BRAND OCH RÄDDNINGSTJÄNST
    # ----------------------------------------------------------------
    if contains("brand", "räddningstjänst", "brandman", "brandbefäl", "brandförman",
                "brandingenjör", "brandinspektör", "brandmästare", "brandskydd",
                "räddningsbefäl", "räddningschef", "räddningstjänstpersonal",
                "insatsledare", "styrkeledare", "inre befäl", "yttre befäl",
                "frivillig brandman", "rib-", "brandsäkerhet", "brandtekniker",
                "brandvakt", "larmoperatör", "larmchef", "larminstallatör",
                "larmtekniker", "civilförsvarssamordnare"):
        # Undantag: brandskyddshandläggare/samordnare som är säkerhets-
        if contains("brandskyddshandläggare", "brandsäkerhetsstrateg", "brandskyddssamordnare"):
            return "Juridik och Säkerhet"
        return "Brand och Räddningstjänst"

    # ----------------------------------------------------------------
    # 2. VÅRD OCH OMSORG
    # ----------------------------------------------------------------
    # Läkare och läkartitlar
    if contains("läkare", "överläkare", "underläkare", "st-läkare", "chefsläkare",
                "läkarchef", "regionläkare", "kommunläkare", "distriktsläkare",
                "sjukhusläkare", "smittskyddsläkare"):
        if contains("lärare") and not contains("läkare"):
            pass  # Lärare faller igenom
        else:
            return "Vård och Omsorg"

    if contains("sjuksköterska", "sjuksköterskechef", "sjuksköterskassistent",
                "distriktssköterska", "specialistsjuksköterska", "sjuksköterskeassistent",
                "sjukvårdsbiträde", "sjukvårdsrådgivning", "kommunsjuksköterska"):
        return "Vård och Omsorg"

    if contains("undersköterska", "underskötserka", "underskötska"):
        return "Vård och Omsorg"

    if contains("vårdbiträde", "vårdenhetschef", "vård- och omsorgsarbetare",
                "vård- och omsorgsassistent", "vård- och omsorgschef",
                "vård- och omsorgsdirektör", "vårdare", "vårdutvecklare",
                "vårdkoordinator", "vårdsamordnare", "vårdcontroller",
                "vårdhundsförare", "vårdadministratör", "vårdpersonal",
                "vårddirektör", "vårdchef"):
        # Undantag: lärare med vård i sig
        if contains("vårdlärare", "vård- och omsorgsämne", "vård- och omsorgsprogrammet",
                    "omvårdnadslärare"):
            return "Utbildning och Pedagogik"
        return "Vård och Omsorg"

    if contains("barnmorska", "barnmorsk"):
        return "Vård och Omsorg"

    if contains("tandläkare", "tandläkarassistent", "tandhygienist", "tandsköterska",
                "tandtekniker", "tandvård", "tandteknikerassistent", "övertandläkare",
                "st-tandläkare", "sjukhustands", "odontologisk", "ortodonti",
                "cheftandläkare", "bedömningstandläkare", "klinikapotekare",
                "chefstandläkare", "klinikapotekare"):
        return "Vård och Omsorg"

    if contains("fysioterapeut", "sjukgymnast", "fysioterapi", "sjukgymnastik",
                "arbetsterapeut", "arbetsterapibiträde", "arbetsterapichef",
                "habiliteringssjuksköterska", "habiliterings", "logoped",
                "rehabassistent", "rehabiliteringsassistent", "rehabiliteringschef",
                "rehabiliteringskonsulent", "rehabiliteringspedagog",
                "rehabiliteringsbiträde", "rehabiliteringsingenjör",
                "rehabkoordinator", "rehabsamordnare", "rehabvägledare",
                "rehabcoach", "rehabträd"):
        # logoped kan vara i vård
        return "Vård och Omsorg"

    if contains("optiker", "optometrist", "synpedagog", "hörselpedagog",
                "hörselingenjör", "hörseltekniker", "hörselvårdsingenjör",
                "hörselvårdstekniker", "ögonprotetiker", "ögonsjuksköterska",
                "ögon-", "audiologi", "audiononom"):
        return "Vård och Omsorg"

    if contains("psykolog", "psykoterapeut"):
        # Skolpsykolog → Utbildning, Socialpsykolog → Socialt, övriga → Vård
        if contains("skolpsykolog", "förskolepsykolog", "elevhälsopsykolog"):
            return "Utbildning och Pedagogik"
        if contains("(skola)", "(ptp)", "(stp)", "(student)", "skolan") or tl.endswith("psykolog (skola)"):
            return "Utbildning och Pedagogik"
        if contains("socialpsykolog", "ifo-psykolog"):
            return "Socialt arbete och Stöd"
        return "Vård och Omsorg"

    if contains("kurator") and not contains("skolkurator", "chefskurator"):
        if contains("skola", "gymnasi", "elevhälsa", "elevhälso"):
            return "Utbildning och Pedagogik"
        if contains("socialtjänst", "ifo", "socialpsykatri", "familjerätt"):
            return "Socialt arbete och Stöd"
        return "Vård och Omsorg"

    if tl.startswith("kurator"):
        return "Vård och Omsorg"

    if contains("barnskötare", "barnsköterska"):
        return "Utbildning och Pedagogik"

    if contains("mentalskötare", "mentalsköterska", "skötare"):
        # Skötare utan pedagogik → Vård
        if contains("pedagogisk", "lärare", "pedagog"):
            return "Utbildning och Pedagogik"
        return "Vård och Omsorg"

    if contains("hemtjänst", "hemvård", "hemsjukvård", "hemterapeut",
                "hemvårdare", "hemtjänsthandläggare", "hemtjänstkoordinator"):
        return "Vård och Omsorg"

    if contains("omvårdnad", "omvårdare", "omvårdnadsassistent",
                "omvårdnadsbiträde", "omvårdnadsledare"):
        if contains("lärare", "läraren", "omvårdnadslärare"):
            return "Utbildning och Pedagogik"
        return "Vård och Omsorg"

    if contains("omsorgschef", "omsorgsbiträde", "omsorgsassistent",
                "omsorgshandledare", "omsorgshandläggare", "omsorgspedagog",
                "omsorgspersonal", "omsorgssamordnare", "omsorgschaufför"):
        return "Vård och Omsorg"

    if contains("geriatrik", "palliativ", "demenssjuksköterska", "demensvård",
                "demenssamordnare", "demenskonsulent", "demensvårdsutvecklare",
                "silviasjuksköterska", "silviasyster", "äldreboende"):
        return "Vård och Omsorg"

    if contains("medicinsk sekreterare", "medicinsk vårdadministratör",
                "medicinsk rådgivare", "medicinsk biolog", "medicintekniker",
                "medicinteknisk ingenjör", "biomedicinsk analytiker",
                "biomedicinskt analytiker", "biokemist", "klinisk farmacevt",
                "klinikapotekare", "klinikassistent", "kliniksamordnare",
                "kliniksekreterare", "klinikadministratör"):
        return "Vård och Omsorg"

    if contains("röntgen", "strål", "radiologen", "radiologi", "radioterapiassistent",
                "sonograf", "ultraljud", "perfusionist", "kardiologi",
                "anestesi", "intensivvård", "iva-", "iva "):
        return "Vård och Omsorg"

    if contains("dietist", "nutritionskonsulent", "dietkock", "dietkokerska"):
        if contains("lärare", "pedagog"):
            return "Utbildning och Pedagogik"
        return "Vård och Omsorg"

    if contains("farmaceut", "receptarie", "apotekare", "läkemedel"):
        return "Vård och Omsorg"

    if contains("stödassistent", "stödbiträde") and contains(
            "lss", "funktionsnedsättning", "omsorg", "boende", "daglig verksamhet",
            "socialpsyk", "gruppboende", "natt", "habilitering"):
        return "Vård och Omsorg"

    if contains("personlig assistent", "personlig vårdare"):
        return "Vård och Omsorg"

    if contains("habiliteringsassistent", "habiliteringsbiträde", "habiliteringspersonal",
                "habiliteringspersonal", "habiliterare", "habiliteringskonsulent",
                "habiliteringsutvecklare"):
        return "Vård och Omsorg"

    if contains("lss-handläggare", "lss-utredare", "lss-samordnare", "lss-chef",
                "lss-/socialpsyk", "lss-/psyk"):
        return "Socialt arbete och Stöd"

    if contains("obduktionstekniker", "gipstekniker", "sterilbiträde",
                "sterilhygieniker", "steriltekniker", "laboratorieassistent",
                "laboratoriebiträde", "laboratoriefysiker", "laboratorieingenjör",
                "laboratoriechef", "laboratorietekniker", "sjukhusfysiker",
                "sjukhusoptiker", "sjukhusgenetiker", "sjukhuskemist",
                "mikrobiolog", "cytodiagnostiker", "anaplastolog",
                "biobanksamordnare", "epidemiolog", "sjukvårdsbiträde",
                "sjukhusstäderska", "sjukhustekn", "korsettekniker",
                "ortopedingenjör", "ortopedskotekniker", "ortopedtekniker",
                "ortoptist", "ergonom"):
        return "Vård och Omsorg"

    if contains("fotvård", "fotterapeut", "massageterapeut", "massör"):
        return "Vård och Omsorg"

    if contains("stomiterapeut", "stomisköterska", "uroterapeut", "urokonsulent",
                "uro-/tarmterapeut", "inkontinenssamordnare"):
        return "Vård och Omsorg"

    if contains("smittskydd", "infektions", "hygiensjuksköterska", "patientsäkerhet"):
        return "Vård och Omsorg"

    if contains("endoskopi", "neuro", "onkologi", "kirurgi", "urologi",
                "hematologi", "geriatrik", "internmedicin", "diabetesjuksköterska",
                "diabetessköterska", "diabetesvård", "dialyssjuksköterska",
                "smärtsjuksköterska", "reumatologi"):
        return "Vård och Omsorg"

    if contains("patientkoordinator", "patientmedhjälpare", "patienttransportör",
                "patientvaktmästare"):
        return "Vård och Omsorg"

    if contains("sjukhusapotekare", "sjukhusdirektör", "sjukhusfotograf",
                "sjukhusläkare", "sjukhus"):
        if contains("lärare"):
            return "Utbildning och Pedagogik"
        return "Vård och Omsorg"

    if contains("neonatal", "bb-", "förlossning", "förlossningsvård"):
        return "Vård och Omsorg"

    if contains("äldreomsorg", "äldreomsorgs", "äldrekonsulent", "äldrelots",
                "äldreombudsman", "äldrepedagog", "äldresamordnare",
                "äldreomsorgschef", "äldresjuksköterska", "äldrestödjare",
                "äldreomsorgshandläggare", "äldreomsorgskonslent",
                "äldreomsorgshandl"):
        return "Vård och Omsorg"

    if contains("handikapp- och omsorg", "handikappkonsulent", "omsorgsbiträde",
                "omsorgsanst"):
        return "Vård och Omsorg"

    if contains("vårdpedagog", "vårdutvecklingssamordnare", "vård- och stödsamordnare"):
        return "Vård och Omsorg"

    if tl in ["biträde (vård)", "biträde"]:
        return "Vård och Omsorg"

    if contains("vård- och omsorgspersonal"):
        return "Vård och Omsorg"

    # Verksamhetschef + vård
    if tl.startswith("verksamhetschef") and contains(
            "hälso", "sjukvård", "vård", "omsorg", "läkare", "sjuksköterska",
            "barnmorska", "tandläkare", "folktandvård", "psyk", "rehabilitering"):
        return "Vård och Omsorg"

    # ----------------------------------------------------------------
    # 3. UTBILDNING OCH PEDAGOGIK
    # ----------------------------------------------------------------
    if contains("lärare", "lärarcoach", "lärarvikarie", "läraraspirant",
                "lärarassistent", "lärarbibliotekarie", "lärarresurs"):
        # Lärare med vård-suffix hanteras ovan
        if tl.startswith("it-lärare") or contains("it-pedagog", "ikt-pedagog"):
            return "IT och Digitalisering"
        return "Utbildning och Pedagogik"

    if contains("förskollärare", "förskolärare", "förskoleassistent",
                "förskoleadministratör", "förskollärare", "förskolechef",
                "förskolekoordinator", "förskolesamordnare", "förskoleresurs",
                "förskoleutvecklare", "förskolepedagog", "förskolepsykolog",
                "förskolehandläggare", "förskoleintendent", "förskolestöd",
                "förskolelärare", "öppen förskola"):
        return "Utbildning och Pedagogik"

    if contains("barnskötare", "barnsköterska"):
        return "Utbildning och Pedagogik"

    if contains("rektor", "rektorsassistent", "rektorsadministratör", "rektorsstöd"):
        return "Utbildning och Pedagogik"

    if contains("gymnasielärare", "gymnasiechef", "gymnasierektor", "gymnasiebibliotekarie",
                "gymnasiehandläggare", "gymnasiesamordnare", "gymnasieskola"):
        return "Utbildning och Pedagogik"

    if contains("grundlärare", "grundskollärare", "grundskolchef", "grundskolechef",
                "grundskollärare", "grundskolrektor"):
        return "Utbildning och Pedagogik"

    if contains("ämneslärare", "adjunkt", "lektor") and not contains("sjukhuslektor"):
        return "Utbildning och Pedagogik"

    if contains("specialpedagog", "speciallärare", "anpassningslärare"):
        return "Utbildning och Pedagogik"

    if contains("studie- och yrkesvägledare", "studie-och yrkesvägledare",
                "studievägledare", "yrkesvägledare", "syo-", "studiecoach",
                "studieorganisatör", "studierektor", "studiesamordnare"):
        return "Utbildning och Pedagogik"

    if contains("fritidspedagog", "fritidslärare", "fritidshemsassistent",
                "fritidshemschef", "fritidshemssamordnare", "fritidsledare",
                "fritidsassistent", "fridsassistent", "fritsidsledare"):
        # Fritidsledare i fritidsgård → Kultur
        if contains("fritidsgård", "fritids- och kultur", "fritidsgårds"):
            return "Kultur och Fritid"
        return "Utbildning och Pedagogik"

    if contains("skoladministratör", "skolassistent", "skolchef", "skoldirektör",
                "skolekonom", "skolenhetschef", "skolhandläggare", "skolintendent",
                "skolkurator", "skolledare", "skollogoped", "skolläkare",
                "skolmåltidsbiträde", "skolpsykolog", "skolresurs", "skolsamordnare",
                "skolsekreterare", "skolskjutshandläggare", "skolskjutssamordnare",
                "skolsköterska", "skolsocionom", "skolutvecklare",
                "skolvaktmästare", "skolvärd", "skolöverläkare"):
        if contains("skolvaktmästare"):
            return "Fastighet och Lokalvård"
        if contains("skolsköterska"):
            return "Utbildning och Pedagogik"
        if contains("skolstädare"):
            return "Fastighet och Lokalvård"
        return "Utbildning och Pedagogik"

    if contains("elevassistent", "elevbiträde", "elevcoach", "elevhandledare",
                "elevhemsassistent", "elevhemsföreståndare", "elevhemsvärd",
                "elevhälsochef", "elevhälsopedagog", "elevhälsosamordnare",
                "elevkonsulent", "elevkoordinator", "elevmentor", "elevombud",
                "elevpedagog", "elevresurs", "elevsamordnare", "elevstödjare",
                "elevvärd", "elevvårdschef"):
        return "Utbildning och Pedagogik"

    if contains("yrkeslärare", "yrkesinformatör", "yrkeshandledare"):
        return "Utbildning och Pedagogik"

    if contains("montessorilärare", "montessoripedagog"):
        return "Utbildning och Pedagogik"

    if contains("vuxenutbildning", "vuxenutbildningschef", "vuxenpedagog",
                "vuxenstödjare", "vuxencoach", "vuxenbiblotekarie"):
        if contains("chef", "rektor", "samordnare", "administratör", "handläggare"):
            return "Utbildning och Pedagogik"
        if not contains("bibliotek"):
            return "Utbildning och Pedagogik"

    if contains("sfi-lärare", "sfi lärare", "lärare (sfi"):
        return "Utbildning och Pedagogik"

    if contains("modersmålslärare", "modermålslärare", "hemspråkslärare",
                "studiehandledare", "modersmålspedagog", "modersmålsstödjare",
                "modersmålstränare"):
        return "Utbildning och Pedagogik"

    if contains("bildningschef", "bildningsdirektör", "utbildningschef",
                "utbildningsdirektör", "utbildningsledare", "utbildningssamordnare",
                "utbildningsstrateg", "utbildningsutvecklare", "utbildningskoordinator",
                "utbildningsansvarig", "utbildningsassistent", "utbildningskonsulent",
                "utbildningskonsult", "utbildningshandläggare", "utbildningsledare",
                "utbildningssekreterare", "utbildningsinstruktör"):
        return "Utbildning och Pedagogik"

    if contains("skolbussförare", "skjutssamordnare"):
        # Skolbussförare: kör elever → Transport
        if contains("bussförare"):
            return "Transport och Trafikplanering"
        return "Utbildning och Pedagogik"

    if contains("fritidsgårdschef", "fritidsgårdsföreståndare", "fritidsgårdsledare",
                "fritidsgårdssamordnare"):
        return "Kultur och Fritid"

    if contains("pedagogisk assistent", "pedagogisk handledare", "pedagogisk handläggare",
                "pedagogisk ledare", "pedagogisk resurs", "pedagogisk samordnare",
                "pedagogisk utvecklare", "pedagogisk utvecklingledare",
                "pedagogisk utvecklingsresurs", "pedagogisk-/konstnärlig",
                "pedagogista", "pedagogresurs", "pedagogassistent", "pedagog"):
        if contains("fritid") and not contains("fritidspedagog"):
            return "Kultur och Fritid"
        return "Utbildning och Pedagogik"

    if contains("resurspedagog", "resursassistent", "resurslärare"):
        return "Utbildning och Pedagogik"

    if contains("klassassistent", "klasslärare", "klassmentor"):
        return "Utbildning och Pedagogik"

    if contains("dagbarnvårdare"):
        return "Utbildning och Pedagogik"

    if contains("musikskolechef", "kulturskolechef", "kulturskolepedagog",
                "kulturskolelärare", "kulturskolledare", "kulturskollärare"):
        return "Utbildning och Pedagogik"

    if contains("hörselpedagog") and contains("lärare"):
        return "Utbildning och Pedagogik"

    if contains("talpedagog", "tal- och språkpedagog", "talstödstolk",
                "teckenspråkslärare", "teckenkommunikatör", "syn- och hörselkonsulent",
                "syn- och hörselinstruktör", "synpedagog"):
        return "Utbildning och Pedagogik"

    if contains("dramapedagog", "dramalärare", "drama-/teaterpedagog"):
        return "Utbildning och Pedagogik"

    if contains("lärteamstödjare", "in class support", "klassmorfar", "klassmormor",
                "heltidsmentor"):
        return "Utbildning och Pedagogik"

    if contains("matematikutvecklare", "skolutvecklare", "ikt-ansvarig",
                "ikt-assistent", "ikt-pedagog", "ikt-samordnare", "ikt-strateg",
                "ikt-stödjare", "ikt-utvecklare"):
        return "Utbildning och Pedagogik"

    if contains("barnpedagog", "barntillsynspedagog", "barnstödjare"):
        return "Utbildning och Pedagogik"

    if contains("språk-, skriv- och läsutvecklare", "läsutvecklare",
                "språkutvecklare", "skrivutvecklare"):
        return "Utbildning och Pedagogik"

    if contains("npf-pedagog", "nta-samordnare"):
        return "Utbildning och Pedagogik"

    if tl in ["vuxen i skolan"]:
        return "Utbildning och Pedagogik"

    # Verksamhetschef + skola/förskola/utbildning
    if tl.startswith("verksamhetschef") and contains(
            "grundskola", "förskola", "gymnasiet", "skola", "utbildning", "lärande",
            "barn- och ungdom", "pedagogik", "skolhälsovård"):
        return "Utbildning och Pedagogik"

    if contains("slöjdlärare", "slöjd"):
        if contains("lärare", "pedagog"):
            return "Utbildning och Pedagogik"

    if tl in ["slöjdlärare"]:
        return "Utbildning och Pedagogik"

    # ----------------------------------------------------------------
    # 4. SOCIALT ARBETE OCH STÖD
    # ----------------------------------------------------------------
    if contains("socialsekreterare", "socialarbetare", "socialpedagog",
                "socialassistent", "socialkoordinator", "socialkonsulent",
                "socialdirektör", "socialchef", "socialutredare", "socialvägledare",
                "socialrättshandläggare", "socialrådgivare", "socialt ansvarig",
                "socialadministratör"):
        return "Socialt arbete och Stöd"

    if contains("biståndshandläggare", "biståndsbedömare"):
        return "Socialt arbete och Stöd"

    if contains("familjehemskonsulent", "familjehemshandledare",
                "familjehemshandläggare", "familjehemssekreterare",
                "familjehem"):
        return "Socialt arbete och Stöd"

    if contains("familjebehandlare", "familjeassistent", "familjepedagog",
                "familjerättsassistent", "familjerättssekreterare",
                "familjerättssocionom", "familjerådgivare", "familjerådslagssamordnare",
                "familjestödjare", "familjestödsassistent", "familjeterapeut",
                "familjeutredare", "familjecoach", "familjehandledare"):
        return "Socialt arbete och Stöd"

    if contains("socionom"):
        return "Socialt arbete och Stöd"

    if contains("ekonomiskt bistånd", "försörjningsstöd", "ekonomisk rådgivare",
                "budget- och skuldrådgivare", "skuldrådgivare", "skuldsanerare",
                "konsumentrådgivare", "konsumentvägledare", "konsumentsekreterare",
                "inkassohandläggare", "konsumentjuridisk rådgivare",
                "konsument- och budgetrådgivare"):
        return "Socialt arbete och Stöd"

    if contains("missbruksbehandlare", "alkohol- och drogbehandlare",
                "alkohol- och drogsamordnare", "alkohol- och drogterapeut",
                "alkohol- och drogrådgivare", "alkoholterapeut",
                "alkoholrådgivare", "narkotikasamordnare",
                "drogförebyggare", "drogrådgivare", "drogterapeut",
                "drogsamordnare", "beroendestödjare", "beroendeterapeut",
                "alkoholinspektör"):
        return "Socialt arbete och Stöd"

    if contains("flyktingassistent", "flyktinghandledare", "flyktinghandläggare",
                "flyktingmottagare", "flyktingsamordnare", "flyktingsekreterare",
                "flyktingstödjare", "flyktingvägledare"):
        return "Invandring, Integration och Mångfald"

    if contains("boendestödjare", "boendestöd", "boendestödspedagog",
                "boendestödspersonal", "boendepedagog"):
        if contains("socialpsyk", "psyk", "vuxen"):
            return "Socialt arbete och Stöd"
        if contains("lss", "funktionsnedsättning", "habilitering"):
            return "Vård och Omsorg"
        return "Socialt arbete och Stöd"

    if contains("bostod", "bostöd", "bostödsassistent"):
        return "Socialt arbete och Stöd"

    if contains("ombudsman") and contains("äldre", "funktionsnedsatt"):
        return "Vård och Omsorg"

    if contains("behandlare", "behandlingsassistent", "behandlingspedagog",
                "behandlingspersonal", "behandlingssamordnare", "behandlingssekreterare",
                "behandlingscoach", "behandlingsledare"):
        return "Socialt arbete och Stöd"

    if contains("stödassistent") and not contains(
            "vård", "omsorg", "habilitering", "funktionsnedsättning",
            "lss", "gruppboende", "natt"):
        return "Socialt arbete och Stöd"

    if contains("individ- och familjeomsorg", "ifo-", "ifo "):
        return "Socialt arbete och Stöd"

    if contains("barnsekreterare", "barnutredare"):
        return "Socialt arbete och Stöd"

    if contains("placeringshandläggare", "placeringskoordinator",
                "placeringssamordnare", "placeringssekreterare"):
        return "Socialt arbete och Stöd"

    if contains("kontaktperson") and not contains("kundtjänst", "servicecenter"):
        if contains("lss", "sol", "socialtjänst", "ifo"):
            return "Socialt arbete och Stöd"
        return "Socialt arbete och Stöd"

    if contains("kontaktfamilj"):
        return "Socialt arbete och Stöd"

    if contains("jourhem", "jourhems"):
        return "Socialt arbete och Stöd"

    if contains("gode man", "förmyndare", "förvaltare") and not contains(
            "fastighetsförvaltare", "markförvaltare", "jordbruksförvaltare"):
        return "Socialt arbete och Stöd"

    if contains("überförmyndare", "överförmyndar"):
        return "Juridik och Säkerhet"

    if contains("socialt arbete", "socialt ansvarig socionom"):
        return "Socialt arbete och Stöd"

    if contains("brottsförebyggan"):
        return "Socialt arbete och Stöd"

    if contains("sysselsättningshandledare", "sysselsättningssamordnare",
                "aktiveringsbiträde", "aktiveringsledare", "aktiveringssamordnare",
                "aktivitetsledare", "aktivitetslots", "aktivitetssamordnare",
                "aktivitetsstödjare", "aktivitetsutvecklare"):
        return "Socialt arbete och Stöd"

    if contains("välfärdssamordnare"):
        return "Socialt arbete och Stöd"

    if contains("anhörigkonsulent", "anhörigsamordnare", "anhörig- och",
                "anhörigombud", "anhörigrådgivare", "anhörigstödjare",
                "anhörigstrateg"):
        return "Vård och Omsorg"

    if contains("personligt ombud"):
        return "Socialt arbete och Stöd"

    if contains("umgängesstödjare"):
        return "Socialt arbete och Stöd"

    if contains("intensivstödjare"):
        return "Socialt arbete och Stöd"

    if contains("fältsekreterare", "fältarbetare", "fältassistent"):
        return "Socialt arbete och Stöd"

    if contains("vuxenbehandlare"):
        return "Socialt arbete och Stöd"

    if contains("dödsbohandläggare", "dödsboutredare"):
        return "Socialt arbete och Stöd"

    if contains("LSS") and not tl.startswith("it-"):
        if contains("handläggare", "utredare", "samordnare", "chef"):
            return "Socialt arbete och Stöd"

    if contains("handikapp") and not contains("idrottshall"):
        return "Socialt arbete och Stöd"

    if contains("funktionshinder", "funktionsnedsättning", "funktionsrättskonsulent",
                "funktionshinderombudsman", "funktionshinderkonsulent"):
        if contains("handläggare", "konsulent", "ombudsman", "rättskon",
                    "samordnare", "chef"):
            return "Socialt arbete och Stöd"
        return "Vård och Omsorg"

    if contains("samordnare") and contains("vård i nära relationer", "vnr",
                                            "våld i nära"):
        return "Socialt arbete och Stöd"

    # ----------------------------------------------------------------
    # 5. IT OCH DIGITALISERING
    # ----------------------------------------------------------------
    if contains("it-administratör", "it-arkitekt", "it-ansvarig", "it-assistent",
                "it-avtalsstrateg", "it-chef", "it-controller", "it-direktör",
                "it-driftsansvarig", "it-driftschef", "it-driftsledare",
                "it-driftstekniker", "it-ekonom", "it-förvaltare", "it-guide",
                "it-handledare", "it-handläggare", "it-infrastrukturarkitekt",
                "it-infrastrukturansvarig", "it-infrastrukturspecialist",
                "it-infrastrukturstrateg", "it-infrastrukturtekniker",
                "it-ingenjör", "it-konsult", "it-koordinator", "it-kundansvarig",
                "it-ledare", "it-medarbetare", "it-nätverksspecialist",
                "it-nätverkstekniker", "it-pedagog", "it-processansvarig",
                "it-projektledare", "it-samordnare", "it-sekreterare",
                "it-specialist", "it-strateg", "it-stöd", "it-support",
                "it-supportansvarig", "it-supportchef", "it-supportspecialist",
                "it-supporttekniker", "it-systemadministratör", "it-systemansvarig",
                "it-systemdriftsansvarig", "it-systemförvaltare", "it-systemspecialist",
                "it-systemtekniker", "it-systemutvecklare", "it-säkerhetsansvarig",
                "it-säkerhetschef", "it-säkerhetskoordinator", "it-säkerhetssamordnare",
                "it-säkerhetsspecialist", "it-säkerhetsstrateg", "it-säkerhetstekniker",
                "it-tekniker", "it-tjänsteansvarig", "it-upphandlare", "it-utbildare",
                "it-utredare", "it-utvecklare", "it-utvecklingsledare", "it-vaktmästare",
                "it- och digitaliserings", "it- och kanslichef", "it- och"):
        return "IT och Digitalisering"

    if contains("systemutvecklare", "systemadministratör", "systemansvarig",
                "systemarkitekt", "systemcontroller", "systemekonom",
                "systemerare", "systemförvaltare", "systemförvaltningsledare",
                "systemhandläggare", "systemingenjör", "systemintegratör",
                "systemkoordinator", "systemsamordnare", "systemspecialist",
                "systemstrateg", "systemtekniker"):
        # Lönesystem → HR
        if contains("lön", "löne-", "hr-"):
            return "HR och Personal"
        return "IT och Digitalisering"

    if contains("digitaliseringsansvarig", "digitaliseringsarkitekt",
                "digitaliseringschef", "digitaliseringshandläggare",
                "digitaliseringskoordinator", "digitaliseringsledare",
                "digitaliseringspedagog", "digitaliseringssamordnare",
                "digitaliseringsstrateg", "digitaliseringstekniker",
                "digitaliseringsutvecklare"):
        return "IT och Digitalisering"

    if contains("digital strateg", "digital transformationsledare",
                "digital utvecklare", "digital utvecklingsstrateg",
                "digital verksamhetsutvecklare", "digital coach",
                "digital producent", "digital samordnare"):
        return "IT och Digitalisering"

    if contains("nätverksadministratö", "nätverksansvarig", "nätverksingenjör",
                "nätverkskoordinator", "nätverkssamordnare", "nätverksstrateg",
                "nätverkstekniker"):
        return "IT och Digitalisering"

    if contains("cybersäkerhetsspecialist", "informationssäkerhetsansvarig",
                "informationssäkerhetssamordnare", "informationssäkerhetsspecialist",
                "informationssäkerhetsstrateg", "informationssäkerhet"):
        return "IT och Digitalisering"

    if contains("adb-samordnare", "adb-tekniker"):
        return "IT och Digitalisering"

    if contains("dataadministratör", "dataansvarig", "dataassistent",
                "databasadministratör", "datahandledare", "dataingenjör",
                "datapedagog", "datasupport", "datatekniker", "data engineer",
                "data scientist"):
        return "IT och Digitalisering"

    if contains("dataskyddsombud", "dataskyddssamordnare"):
        return "Juridik och Säkerhet"

    if contains("servicedesk", "servicedeskansvarig", "servicedesktekniker",
                "helpdesk"):
        return "IT och Digitalisering"

    if contains("webbmaster", "webmaster", "webbansvarig", "webbassistent",
                "webbdesigner", "webbinformatör", "webbkommunikatör",
                "webbmaster", "webbredaktör", "webbsamordnare", "webbstrateg",
                "webbtekniker", "webbtidningsredaktör", "webbutvecklare",
                "webmaster/e-tjänstutvecklare", "webredaktör", "webadministratör",
                "webmaster"):
        return "IT och Digitalisering"

    if contains("e-arkivarie"):
        return "Ekonomi och Administration"

    if contains("e-handelsadministratör", "e-handelsansvarig", "e-handelssamordnare"):
        return "IT och Digitalisering"

    if contains("e-hälsosamordnare") and not contains("mas"):
        return "IT och Digitalisering"

    if contains("e-samordnare", "e-strateg", "e-tjänstesamordnare",
                "e-tjänstutvecklare", "e-utvecklare"):
        return "IT och Digitalisering"

    if contains("enterprise architect", "enterprisearkitekt", "lösningsarkitekt",
                "informationsarkitekt", "kravanalytiker") and not contains("bygg", "mark"):
        return "IT och Digitalisering"

    if contains("bredbandskoordinator", "bredbandssamordnare", "bredbandsstrateg",
                "bredbandstekniker", "fiberprojektör", "fibertekniker",
                "stadsnätsamordnare", "stadsnätskoordinator", "stadsnätstekniker",
                "telekommunikation", "telefoniadministratör", "telefoniansvarig",
                "telefoniförvaltare", "telefonisamordnare", "telekomsamordnare",
                "telesamordnare", "teletekniker"):
        return "IT och Digitalisering"

    if contains("pc-tekniker"):
        return "IT och Digitalisering"

    if contains("identity and access specialist"):
        return "IT och Digitalisering"

    if contains("incident manager"):
        return "IT och Digitalisering"

    if contains("chief information officer", "cio"):
        if "cio" in tl:
            return "IT och Digitalisering"

    if contains("chief information security officer", "ciso"):
        return "IT och Digitalisering"

    if contains("chief technical officer", "cto"):
        if "cto" in tl:
            return "IT och Digitalisering"

    if contains("masterdataspecialist"):
        return "IT och Digitalisering"

    if contains("portföljledare") and contains("it", "digital"):
        return "IT och Digitalisering"

    if contains("it-tekniker/vaktmästare", "it-vaktmästare"):
        return "IT och Digitalisering"

    if contains("medie- och it-pedagog"):
        return "IT och Digitalisering"

    # ----------------------------------------------------------------
    # 6. KOMMUNÖVERGRIPANDE OCH STRATEGISKA FUNKTIONER
    # ----------------------------------------------------------------
    if contains("kommundirektör", "kommundirektörs"):
        return "Kommunövergripande och Strategiska funktioner"

    if contains("stadssekreterare"):
        return "Kommunövergripande och Strategiska funktioner"

    if tl == "kommunsekreterare" or tl.startswith("kommunsekreterare"):
        return "Kommunövergripande och Strategiska funktioner"

    if tl in ["kanslichef", "kanslichef (biträdande)"]:
        return "Kommunövergripande och Strategiska funktioner"

    if contains("kommunstyrelsens förvaltningschef"):
        return "Kommunövergripande och Strategiska funktioner"

    if tl == "nämndsekreterare" or contains("nämndsekreterare"):
        return "Kommunövergripande och Strategiska funktioner"

    if contains("kanslichef") and not contains("it-", "miljö", "kommunika"):
        return "Kommunövergripande och Strategiska funktioner"

    if tl in ["kommunchef"]:
        return "Kommunövergripande och Strategiska funktioner"

    # ----------------------------------------------------------------
    # 7. EKONOMI OCH ADMINISTRATION
    # ----------------------------------------------------------------
    if contains("ekonom", "ekonomi", "ekonomichef", "ekonomidirektör",
                "ekonomicontroller", "ekonomihandläggare", "ekonomiassistent",
                "ekonomiadministratör", "ekonomiansvarig", "ekonomibiträde",
                "ekonomikonsult", "ekonomipersonal", "ekonomisamordnare",
                "ekonomisekreterare", "ekonomispecialist", "ekonomistrateg",
                "ekonomianalytiker"):
        # Undantag: kök/mat-biträde med ekonomibiträde = Fastighet
        if contains("ekonomibiträde") and contains("kök", "mat", "lokalvård", "städ"):
            return "Fastighet och Lokalvård"
        # IT-ekonom → IT
        if contains("it-ekonom"):
            return "IT och Digitalisering"
        return "Ekonomi och Administration"

    if contains("controller", "controllerstrateg", "controllerchef"):
        if contains("hr-controller", "personal-controller"):
            return "HR och Personal"
        if contains("it-controller"):
            return "IT och Digitalisering"
        return "Ekonomi och Administration"

    if contains("redovisning"):
        return "Ekonomi och Administration"

    if contains("budget"):
        if contains("rådgivare", "sekreterare") and not contains("chef", "controller"):
            return "Socialt arbete och Stöd"
        return "Ekonomi och Administration"

    if contains("kamrer", "kassaansvarig", "kassabiträde"):
        return "Ekonomi och Administration"

    if contains("administratör", "administration", "administrativ"):
        if contains("it-administratör", "systemadministratör", "databasadministratör",
                    "nätverksadministratör"):
            return "IT och Digitalisering"
        if contains("hr-administratör", "personaladministratör", "löneadministratör",
                    "pa-administratör"):
            return "HR och Personal"
        return "Ekonomi och Administration"

    if contains("registrator"):
        return "Ekonomi och Administration"

    if contains("diarieförare"):
        return "Ekonomi och Administration"

    if contains("sekreterare") and not contains(
            "nämndsekreterare", "kommunsekreterare", "förvaltningssekreterare",
            "kanslihandläggare", "pressekreterar", "politisk sekreterare",
            "familjerättssekreterare", "barnsekreterare", "socialsekreterare",
            "placeringssekreterare", "familjehemssekreterare"):
        return "Ekonomi och Administration"

    if contains("koordinator") and not contains(
            "hr-koordinator", "bemanningskoordinator", "kundservice",
            "trafikkoordinator", "integrationskoordinator",
            "elevhälsokoordinator", "inkontinenssamordnare"):
        # Generell koordinator → Ekonomi/Admin
        return "Ekonomi och Administration"

    if contains("assistent") and not contains(
            "elevassistent", "lärarassistent", "barnmorske", "sjukvårdsassistent",
            "hälso", "rehab", "laboratorieassistent", "hr-assistent",
            "personalassistent", "rekryteringsassistent"):
        if contains("kök", "måltid", "kost"):
            return "Fastighet och Lokalvård"
        return "Ekonomi och Administration"

    if contains("handläggare") and not contains(
            "socialsekreterare", "biståndshandläggare", "bygglovshandläggare",
            "miljöhandläggare", "upphandlingshandläggare", "lss-handläggare",
            "flyktinghandläggare", "integrationshandläggare"):
        # Generell handläggare → Admin
        return "Ekonomi och Administration"

    if contains("utredare") and not contains(
            "miljöutredare", "trafikutredare", "upphandlingsutredare"):
        return "Ekonomi och Administration"

    if contains("kanslist", "kanslihandläggare", "kansliassistent",
                "kanslihandläggare"):
        return "Ekonomi och Administration"

    if contains("kontorist", "kontorsansvarig", "kontorsassistent", "kontorschef",
                "kontorspersonal", "kontorsserviceassistent", "kontorsservicesamordnare",
                "kontorstekniker", "kontorsvaktmästare"):
        return "Ekonomi och Administration"

    if contains("arkivarie", "arkivassistent", "dokumentcontroller",
                "dokumenthanteringsansvarig", "dokumentsamordnare",
                "dokumentationsutvecklare"):
        if contains("e-arkivarie"):
            return "Ekonomi och Administration"
        return "Ekonomi och Administration"

    if contains("postv", "postvaktmästare"):
        return "Ekonomi och Administration"

    if contains("löne"):
        if contains("lönekonsult", "lönespecialist", "lönehandläggare",
                    "löneadministratör", "löneassistent", "lönechef",
                    "lönecontroller", "löneekonom", "lönesamordnare",
                    "lönesystemsansvarig", "lönepartner"):
            return "HR och Personal"
        return "HR och Personal"

    if contains("pension"):
        if contains("pensionshandläggare", "pensionsadministratör",
                    "pensionssamordnare", "pensionssekreterare"):
            return "HR och Personal"

    if contains("bemanningsplanerare", "bemanningsansvarig", "bemanningsassistent",
                "bemanningschef", "bemanningscontroller", "bemanningskonsult",
                "bemanningskoordinator", "bemanningsledare", "bemanningspersonal",
                "bemanningsrekryterare", "bemanningsresurs", "bemanningssamordnare",
                "bemanningsspecialist", "bemannings- och systemadministratör"):
        return "HR och Personal"

    if contains("vikariesamordnare", "vikariesamordnare", "vikarieanskaffare",
                "vikarieförmedlare", "vikarieplanerare", "vikariesamordnare"):
        return "HR och Personal"

    # ----------------------------------------------------------------
    # 8. HR OCH PERSONAL
    # ----------------------------------------------------------------
    if contains("hr-specialist", "hr-strateg", "hr-konsult", "hr-partner",
                "hr-analytiker", "hr-ansvarig", "hr-chef", "hr-assistent",
                "hr-administratör", "hr-controller", "hr-direktör", "hr-expert",
                "hr-generalist", "hr-handläggare", "hr-koordinator",
                "hr-samordnare", "hr-sekreterare", "hr-systemansvarig",
                "hr-utvecklare", "personalkonsulent", "personalstrateg",
                "personaldirektör", "personalchef", "personalhandläggare",
                "personalsekreterare", "personalassistent", "personalspecialist",
                "personaladministratör", "personalsamordnare", "personalekonom",
                "personalhandledare", "pa-konsult", "pa-lönesamordnare",
                "pa-systemförvaltare"):
        return "HR och Personal"

    if contains("rekryterare", "rekryteringsassistent", "rekryteringskonsult",
                "rekryteringskoordinator", "rekryteringspartner",
                "rekryteringssamordnare", "rekryteringsspecialist"):
        return "HR och Personal"

    if contains("employer branding"):
        return "HR och Personal"

    if contains("arbetsrättsjurist", "förhandlare", "förhandlingschef",
                "förhandlingsansvarig", "förhandlingsstrateg",
                "förhandlingssamordnare"):
        if contains("mark", "fastighet"):
            return "Samhällsbyggnad och Infrastruktur"
        return "HR och Personal"

    if contains("kompetensutvecklare", "kompetenssamordnare", "kompetenskoordinator",
                "kompetensstrateg", "kompetens- och utbildningssamordnare"):
        return "HR och Personal"

    if contains("chefs- och ledarutvecklare", "chefsutveckling"):
        return "HR och Personal"

    if contains("ledarskapsstrateg"):
        return "HR och Personal"

    if contains("företagshälsovård", "företagsläkare", "företagssköterska",
                "organisationspsykolog", "organisationskonsult"):
        return "HR och Personal"

    # ----------------------------------------------------------------
    # 9. JURIDIK OCH SÄKERHET
    # ----------------------------------------------------------------
    if contains("jurist", "juridik"):
        if contains("upphandlingsjurist"):
            return "Upphandling och Inköp"
        if contains("arbetsrättsjurist"):
            return "HR och Personal"
        return "Juridik och Säkerhet"

    if contains("säkerhetssamordnare", "säkerhetsansvarig", "säkerhetschef",
                "säkerhetsdirektör", "säkerhetsstrateg", "säkerhetshandläggare",
                "säkerhetsintendent", "säkerhetsoperatör", "säkerhetspartner",
                "säkerhetskontrollant", "säkerhetstekniker",
                "säkerhetsskyddschef", "säkerhetsskydds",
                "beredskapssamordnare", "beredskapschef", "beredskapshandläggare",
                "beredskapsstrateg", "beredskapsarbetare",
                "kris- och beredskapssamordnare", "kris- och beredskapsstrateg",
                "kris- och säkerhetssamordnare"):
        if contains("brand"):
            return "Brand och Räddningstjänst"
        if contains("informationssäkerhet"):
            return "IT och Digitalisering"
        return "Juridik och Säkerhet"

    if contains("trygghets- och säkerhetschef", "trygghets- och säkerhetsdirektör",
                "trygghets- och säkerhetssamordnare", "trygghets- och säkerhetsstrateg",
                "trygghets- och beredskapsstrateg", "trygghetschef",
                "trygghetskoordinator", "trygghetslarmssamordnare",
                "trygghetspedagog", "trygghetssamordnare", "trygghetsstrateg",
                "trygghetsvärd", "trygghetsvärdinna"):
        return "Juridik och Säkerhet"

    if contains("tillsynshandläggare", "tillståndshandläggare", "tillståndsinspektör",
                "tillsyningsman", "tillsynsjurist", "tillsynsman"):
        return "Juridik och Säkerhet"

    if contains("dataskyddsombud", "dataskyddssamordnare"):
        return "Juridik och Säkerhet"

    if contains("totalförsvarssamordnare"):
        return "Juridik och Säkerhet"

    if contains("larmansvarig", "larmassistent", "larmkoordinator",
                "larmoperatör", "larmsamordnare", "larm- och säkerhetsansvarig",
                "larmadministratör"):
        return "Juridik och Säkerhet"

    if contains("ordningsvakt", "ordningsvakt"):
        return "Juridik och Säkerhet"

    if contains("riskingenjör", "risksamordnare"):
        return "Juridik och Säkerhet"

    if contains("brottsförebyggande strateg"):
        return "Juridik och Säkerhet"

    # ----------------------------------------------------------------
    # 10. SAMHÄLLSBYGGNAD OCH INFRASTRUKTUR
    # ----------------------------------------------------------------
    if contains("stadsplanerare", "stadsplaneringsarkitekt", "stadsplaneringschef",
                "stadsarkitekt", "stadsantikvarie", "stadsarkivarie",
                "stadsbyggnadschef", "stadsbyggnadsdirektör", "stadsbyggnadskoordinator",
                "stadsbyggnadsstrateg", "stadsingenjör"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("planarkitekt", "planassistent", "planchef", "planerare",
                "planeringsarkitekt", "planeringschef", "planeringsingenjör",
                "planeringsledare", "planeringssamordnare", "planeringssekreterare",
                "planeringsstrateg", "planeringsutvecklare", "planhandläggare",
                "planingenjör", "plankoordinator", "plansamordnare", "planstrateg",
                "fysisk planerare", "fysisk samhällsplanerare",
                "samhällsplanerare", "samhällsbyggnadschef", "samhällsbyggnadsdirektör",
                "samhällsbyggnadsstrateg", "samhällsutvecklare",
                "samhällsutvecklingschef", "samhällsutvecklingsdirektör",
                "samhällsutvecklingsstrateg", "samhällsplaneringstrateg",
                "strategisk samhällsplanerare", "strategisk planarkitekt"):
        if contains("infrastruktur") and not contains("samhällsbyggnad"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("trafik", "transport") and not contains("detaljplan"):
            return "Transport och Trafikplanering"
        return "Samhällsbyggnad och Infrastruktur"

    if contains("bygglov", "byggnads", "byggnadsinspektör", "byggnadsingenjör",
                "byggnadsantikvarie", "byggnadstekniker", "byggnadsledare",
                "byggantikvarie", "byggchef", "byggledare", "byggprojektledare",
                "byggsamordnare", "byggprojektchef", "bygg- och anläggningsarbetare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("exploatering", "mark- och exploatering", "markförhandlare",
                "markförvaltare", "markhandläggare", "markingenjör", "markstrateg",
                "markupplåtare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("lantmätare", "lantmäterichef", "lantmäterihandläggare",
                "lantmäteriingenjör", "förrättningslantmätare", "förrättningsassistent",
                "förrättningshandläggare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("gis-", "gis "):
        if contains("ingenjör", "tekniker", "assistent", "handläggare",
                    "administratör", "samordnare", "strateg", "chef", "utvecklare"):
            return "Samhällsbyggnad och Infrastruktur"

    if contains("kart-", "kartingenjör", "kartläggare", "kartassistent",
                "karttekniker", "kartläggare", "mät-", "mätingenjör",
                "mätningsingenjör", "mättekniker", "mätningstekniker",
                "mbk-ingenjör", "mbk-samordnare", "mätaretekniker",
                "mätarjusterare", "mätarmontör", "mätartekniker"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("geotekniker", "geolog", "kulturgeolog"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("bebyggelseantikvarie", "kommunantikvarie", "kommunarkitekt"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("gatuingenjör", "gatuinspektör", "gatutekniker", "gatuarbetare",
                "gatuchef", "gatubelysning", "gatu- och"):
        if contains("trafikingenjör"):
            return "Transport och Trafikplanering"
        return "Samhällsbyggnad och Infrastruktur"

    if contains("vägingenjör", "vägarbetare", "vägförman", "väghyvelförare",
                "vägtekniker", "vägvakt", "väg- och trafikingenjör"):
        if contains("trafikingenjör"):
            return "Transport och Trafikplanering"
        return "Samhällsbyggnad och Infrastruktur"

    if contains("anläggningsarbetare", "anläggningsansvarig", "anläggningschef",
                "anläggningsreparatör", "anläggningssamordnare", "anläggningstekniker",
                "anläggningsutvecklare", "nyanläggningsarbetare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("va-ingenjör", "va-ansvarig", "va-chef", "va-handläggare",
                "va-koordinator", "va-projektledare", "va-projektör", "va-strateg",
                "va-tekniker", "va-utredare", "va- och renhållningschef",
                "va- och avfallschef"):
        if contains("renhållning", "avfall"):
            return "Avfall och Återvinning"
        return "Samhällsbyggnad och Infrastruktur"

    if contains("rörläggare", "rörläggningsarbetare", "rörmontör", "rörnätschef",
                "rörnätsman", "rörnätstekniker", "rörinspektör", "vattenrörläggare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("parkingenjör", "parkmästare", "parkansvarig", "parkarbetare",
                "parkchef", "parkförman", "parkförvaltare", "parkintendent",
                "parkrenh", "parktekniker", "park- och", "parkanläggare",
                "grönytetekniker", "stadsträdgårdsmästare", "trädgårdsingenjör",
                "trädgårdsmästare", "trädgårdsarbetare", "trädgårdsförman",
                "trädgårdssamordnare", "trädgårdstekniker", "landskapsarkitekt",
                "landskapsingenjör", "landskapsstrateg", "landskapsvårdsarbetare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("el- och automationsingenjör", "el- och automationstekniker",
                "el- och belysningsingenjör", "el- och styringenjör",
                "elanläggningsansvarig", "elansvarig", "elektriker",
                "elektronikingenjör", "elnätschef", "elsäkerhetsansvarig",
                "eltekniker", "elingenjör", "elkonstruktör", "elmontör",
                "installationselektriker", "industrielektriker",
                "distributionselektriker", "belysningsansvarig",
                "belysningsingenjör", "belysningsplanerare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("stensättare", "brobyggare", "schemaplanerare") and contains("mark"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("infrastruktur") and not contains(
            "it-infrastruktur", "infrastrukturspecialist (it)"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("projekteringschef", "projekteringsledare", "projekteringstekniker",
                "projekteringsingenjör"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("utsättare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("ventilationstekniker", "vvs-ingenjör", "vvs-inspektör",
                "vvs-tekniker"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("kalkyl ingenjör", "kalkylingenjör"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("besiktningsman") and not contains("bil"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("geodata"):
        return "Samhällsbyggnad och Infrastruktur"

    # ----------------------------------------------------------------
    # 11. KOMMUNIKATION OCH MEDBORGARKONTAKT
    # ----------------------------------------------------------------
    if contains("kommunikatör", "kommunikationsstrateg", "kommunikationsansvarig",
                "kommunikationsassistent", "kommunikationschef", "kommunikationsdirektör",
                "kommunikationshandläggare", "kommunikationssamordnare",
                "kommunikationsspecialist", "kommunikationstekniker",
                "kommunikationsutvecklare", "kommunikatör",
                "kommunikations- och"):
        if contains("data", "it-", "nätverks"):
            return "IT och Digitalisering"
        return "Kommunikation och Medborgarkontakt"

    if contains("informatör", "informationsansvarig", "informationsassistent",
                "informationsbiträde", "informationschef", "informationsdesigner",
                "informationsförvaltare", "informationshanterare",
                "informationsproducent", "informationssamordnare",
                "informationsstrateg", "informationstekniker", "informationsutvecklare",
                "informationsvärd", "kommuninformatör"):
        if contains("informationssäkerhet"):
            return "IT och Digitalisering"
        return "Kommunikation och Medborgarkontakt"

    if contains("pressekreterare", "pressansvarig", "presschef", "pr-/pressansvarig"):
        return "Kommunikation och Medborgarkontakt"

    if contains("kundtjänst", "kundservice", "kundcenter", "kontaktcenter",
                "medborgarservice", "kommunvägledare", "kommunvärd",
                "servicecentermedarbetare", "servicechef", "servicehandläggare",
                "servicekoordinator", "servicemedarbetare", "servicerådgivare",
                "servicesamordnare", "servicevägledare", "servicevärd",
                "servicepersonal"):
        return "Kommunikation och Medborgarkontakt"

    if contains("grafisk formgivare", "grafisk kommunikatör", "grafisk producent",
                "grafisk tekniker", "copywriter", "originalare", "layouter",
                "journalist", "redaktör", "innehållsproducent"):
        return "Kommunikation och Medborgarkontakt"

    if contains("digital kommunikatör"):
        return "Kommunikation och Medborgarkontakt"

    if contains("marknadskommunikatör", "marknadsansvarig", "marknadsassistent",
                "marknadschef", "marknadsförare", "marknadskoordinator",
                "marknadssamordnare", "marknadsstrateg", "marknadsutvecklare"):
        return "Kommunikation och Medborgarkontakt"

    if contains("varumärkesansvarig", "varumärkesstrateg", "varumärkesutvecklare"):
        return "Kommunikation och Medborgarkontakt"

    if contains("social media", "sociala medier-specialist"):
        return "Kommunikation och Medborgarkontakt"

    if contains("störningsinformatör"):
        return "Kommunikation och Medborgarkontakt"

    if contains("samhällsinformatör", "samhällskommunikatör"):
        return "Kommunikation och Medborgarkontakt"

    if contains("kommunikations- och digitaliseringschef"):
        return "Kommunikation och Medborgarkontakt"

    # ----------------------------------------------------------------
    # 12. MILJÖ OCH NATURVÅRD
    # ----------------------------------------------------------------
    if contains("miljöinspektör", "miljö- och hälsoskyddsinspektör",
                "miljöhandläggare", "miljöingenjör", "miljöpedagog",
                "miljöplanerare", "miljöprojektledare", "miljöstrateg",
                "miljösamordnare", "miljösekreterare", "miljöutredare",
                "miljöutvecklare", "miljövårdsinspektör", "miljöchef",
                "miljödirektör", "miljöcontroller", "miljökoordinator",
                "miljösakkunnig", "miljötekniker", "miljöassistent",
                "miljöarbetare", "miljöadministratör", "miljöavdelningschef",
                "hälsovårdsinspektör", "livsmedelsinspektör",
                "livsmedels- och hälsoskyddsinspektör",
                "miljö- och livsmedelsinspektör", "hälsoskydds"):
        if contains("byggnads"):
            return "Samhällsbyggnad och Infrastruktur"
        return "Miljö och Naturvård"

    if contains("ekolog", "kommunekolog", "kommunbiolog", "naturvårdshandläggare",
                "naturvårdsplanerare", "naturvårdare", "naturförvaltare",
                "naturguide", "naturparkmästare", "naturpedagog", "naturskoleassistent",
                "naturskoleföreståndare", "naturskolepedagog", "naturumföreståndare",
                "naturvägledare", "natur- och miljöstrateg", "natur- och friluftsplanerare",
                "natur- och skogsförvaltare", "fiskbiolog", "fiskerikonsulent",
                "biolog", "mikrobiolog", "kemist", "fiskbiolog", "molekylärbiolog"):
        if contains("medicinsk", "klinisk"):
            return "Vård och Omsorg"
        return "Miljö och Naturvård"

    if contains("hållbarhetsansvarig", "hållbarhetschef", "hållbarhetscontroller",
                "hållbarhetsdirektör", "hållbarhetssamordnare", "hållbarhetsspecialist",
                "hållbarhetsstrateg", "hållbarhetsutvecklare", "hållbarhetsam"):
        return "Miljö och Naturvård"

    if contains("klimat- och miljöstrateg", "klimatanpassningsstrateg",
                "klimatsamordnare", "miljö- och klimatstrateg", "miljö- och hållbarhetsstrateg"):
        return "Miljö och Naturvård"

    if contains("kretsloppsutredare"):
        return "Miljö och Naturvård"

    if contains("djurskyddsinspektör", "djurskötare", "djurvårdare", "djurparksansvarig",
                "djurförman", "viltvårdare", "jägmästare", "skogsmästare",
                "skogsarbetare", "skogsansvarig", "skogsförvaltare", "skogstekniker",
                "skogssamordnare", "skogsvårdare", "skog- och naturvårdsförvaltare",
                "jordbruksarbetare", "jordbruksförvaltare", "lantbruksarbetare"):
        return "Miljö och Naturvård"

    if contains("antikvarie") and not contains("bygg", "stad"):
        return "Kultur och Fritid"

    # ----------------------------------------------------------------
    # 13. ENERGI OCH KLIMAT
    # ----------------------------------------------------------------
    if contains("energiingenjör", "energirådgivare", "energisamordnare",
                "energistrateg", "energitekniker", "energitjänstansvarig",
                "energicontroller", "energi- och hållbarhetsansvarig",
                "energi- och klimatrådgivare", "energi- och klimatstrateg",
                "energi- och miljöstrateg", "energi-"):
        if contains("klimat") and not contains("miljö"):
            return "Energi och Klimat"
        return "Energi och Klimat"

    if contains("fjärrvärmetekniker", "elnätschef"):
        return "Energi och Klimat"

    if contains("elhandelsansvarig"):
        return "Energi och Klimat"

    # ----------------------------------------------------------------
    # 14. AVFALL OCH ÅTERVINNING
    # ----------------------------------------------------------------
    if contains("renhållningsarbetare", "renhållningschef", "renhållningshandläggare",
                "renhållningsingenjör", "renhållningsansvarig"):
        return "Avfall och Återvinning"

    if contains("sophämtare", "deponipersonal"):
        return "Avfall och Återvinning"

    if contains("återvinning"):
        return "Avfall och Återvinning"

    if contains("insamlingsarbetare"):
        return "Avfall och Återvinning"

    if contains("avfallssamordnare", "avfallschef", "avfallshandläggare"):
        return "Avfall och Återvinning"

    # ----------------------------------------------------------------
    # 15. TRANSPORT OCH TRAFIKPLANERING
    # ----------------------------------------------------------------
    if contains("trafikplanerare", "trafikingenjör", "trafikanalytiker",
                "trafikansvarig", "trafikassistent", "trafikchef",
                "trafikhandläggare", "trafikledare", "trafikmiljöingenjör",
                "trafikplaneringsingenjör", "trafikprojektör", "trafiksamordnare",
                "trafikstrateg", "trafiktekniker", "trafikupplysare", "trafikutredare",
                "trafikutvecklare", "trafikvärd", "trafikövervakare",
                "trafik- och gatuingenjör"):
        return "Transport och Trafikplanering"

    if contains("bussförare", "lastbilschaufför", "lastbilsförare",
                "busschaufför", "chaufför"):
        if contains("bibliotek", "bokbuss"):
            return "Kultur och Fritid"
        if contains("ambulans"):
            return "Vård och Omsorg"
        return "Transport och Trafikplanering"

    if contains("transportarbetare", "transportassistent", "transportchef",
                "transportledare", "transportplanerare", "transportsamordnare",
                "transportstrateg", "transportör"):
        return "Transport och Trafikplanering"

    if contains("kollektivtrafikkoordinator", "kollektivtrafiksamordnare",
                "kollektivtrafikstrateg"):
        return "Transport och Trafikplanering"

    if contains("parkeringsinspektör", "parkeringsvakt", "parkeringsövervakare"):
        return "Transport och Trafikplanering"

    if contains("trafiklärare"):
        return "Transport och Trafikplanering"

    if contains("fordonsansvarig", "fordonschef", "fordonsförare", "fordonshandläggare",
                "fordonsmekaniker", "fordonsreparatör", "fordonssamordnare",
                "fordonstekniker", "fordonsvårdare"):
        return "Transport och Trafikplanering"

    if contains("maskinförare", "maskin-/fordonsförare", "traktorförare",
                "grävmaskinförare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("mobilitetssamordnare"):
        return "Transport och Trafikplanering"

    if contains("färdtjänsthandläggare", "färdtjänstmedarbetare", "färdtjänstutredare"):
        return "Transport och Trafikplanering"

    if contains("sjukresehandläggare", "sjukresevärd"):
        return "Transport och Trafikplanering"

    if contains("resestrategi", "resekoordinator", "reseplanerare", "reseadministratör"):
        return "Transport och Trafikplanering"

    if contains("skeppare", "hamnarbetare", "hamningenjör", "hamnkapten",
                "hamnmästare", "hamnsäkerhetschef", "hamnvärd", "däcksman"):
        return "Transport och Trafikplanering"

    if contains("bilförare", "bilsamordnare", "bilpoolsamordnare", "bilpoolsansvarig",
                "bilvårdare", "biltvättare"):
        return "Transport och Trafikplanering"

    if contains("flygplatschef", "flygplatsmedarbetare", "flygsäkerhetsansvarig",
                "flygsäkerhetskoordinator", "airport officer", "ramppersonal"):
        return "Transport och Trafikplanering"

    # ----------------------------------------------------------------
    # 16. KULTUR OCH FRITID
    # ----------------------------------------------------------------
    if contains("bibliotekarie", "biblioteksassistent", "biblioteksbiträde",
                "bibliotekschef", "biblioteksinformatör", "bibliotekskanslist",
                "bibliotekskommunikatör", "bibliotekskonsulent", "bibliotekspedagog",
                "bibliotekssamordnare", "biblioteksstrateg", "bibliotekstekniker",
                "biblioteksutvecklare", "biblioteksvaktmästare", "biblioteksvärd",
                "biblioteksadministratör", "bildningschef", "bildningsdirektör"):
        return "Kultur och Fritid"

    if contains("kulturchef", "kulturadministratör", "kulturansvarig", "kulturarbetare",
                "kulturarrangör", "kulturassistent", "kulturbiträde",
                "kulturdirektör", "kulturentreprenör", "kulturförmedlare",
                "kulturguide", "kulturhandläggare", "kulturhuschef",
                "kulturhussamordnare", "kulturhustekniker", "kulturhusvärd",
                "kulturinformatör", "kulturkonsulent", "kulturkoordinator",
                "kulturpedagog", "kulturproducent", "kultursamordnare",
                "kultursekreterare", "kulturskolechef", "kulturskolepedagog",
                "kulturskolesekreterare", "kulturskolledare", "kulturskollärare",
                "kulturstrateg", "kulturstrategisk samordnare", "kulturstödhandläggare",
                "kulturtolk", "kulturutredare", "kulturutvecklare", "kulturvärd"):
        return "Kultur och Fritid"

    if contains("museiadministratör", "museiassistent", "museibonde", "museichef",
                "museiföreståndare", "museiintendent", "museikoordinator",
                "museipedagog", "museitekniker", "museivärd"):
        return "Kultur och Fritid"

    if contains("konst-", "konstansvarig", "konstchef", "konstförmedlare",
                "konsthallsguide", "konsthallstekniker", "konsthallsvärd",
                "konsthandläggare", "konstintendent", "konstkonsulent",
                "konstkoordinator", "konstlärare", "konstmuseichef",
                "konstnär", "konstnärlig ledare", "konstpedagog", "konststrateg",
                "konsttekniker"):
        return "Kultur och Fritid"

    if contains("antikvarie") and not contains("bebyggelse", "byggnads", "stads"):
        return "Kultur och Fritid"

    if contains("fritidschef", "fritidshandläggare", "fritidskonsulent",
                "fritidskoordinator", "fritidssamordnare", "fritidsstrateg",
                "fritidsutvecklare", "fritidstekniker", "fritidsvaktmästare",
                "idrottschef", "idrottsadministratör", "idrottskonsulent",
                "idrottsstrateg", "idrottsanläggningsarbetare", "idrottsutvecklare"):
        return "Kultur och Fritid"

    if contains("idrottslärare", "idrottspedagog"):
        # Idrottslärare i skolan → Utbildning
        if contains("skola", "gymnasi", "grundskola"):
            return "Utbildning och Pedagogik"
        return "Kultur och Fritid"

    if contains("idrotts- och fritidschef", "idrotts- och föreningsstrateg",
                "idrott- och fritidshandläggare"):
        return "Kultur och Fritid"

    if contains("idrottsplatsansvarig", "idrottsplatsarbetare", "idrottsplatstekniker",
                "idrottsplatsvaktmästare", "idrottshallsarbetare",
                "idrottshallsvaktmästare", "simhallsarbetare", "simhallschef",
                "simhallspersonal", "simlärare", "simlärarassistent",
                "badmästare", "badvakt", "hallanstvarig", "hallvaktmästare",
                "hallvärd", "sporthallspersonal", "sporthallsvaktmästare",
                "bowlingpersonal"):
        return "Kultur och Fritid"

    if contains("gyminstruktör", "gyminstruck", "gruppträningsinstruktör",
                "träningsinstruktör", "träningsledare", "dansinstruktör",
                "danslärare", "danspedagog", "dansproducent", "dansledare"):
        return "Kultur och Fritid"

    if contains("idrottstränare", "fotbollstränare", "fotbollsinstruktör",
                "friidrottstränare", "tennistränare", "tränare"):
        return "Kultur och Fritid"

    if contains("scenchef", "scenkonstpedagog", "scenmästare", "scenograf",
                "scentekniker", "scenarbetare", "scenvärd", "teaterchef",
                "teaterlärare", "teaterledare", "teaterpedagog", "teatertekniker",
                "teatervärd", "musiker", "extra musiker", "sångare",
                "musikterapeut", "musikpedagog", "musikhandledare", "musikledare",
                "musikproducent", "musikskolechef"):
        return "Kultur och Fritid"

    if contains("turistansvarig", "turistassistent", "turistbyråansvarig",
                "turistchef", "turistinformatör", "turistkommunikatör",
                "turistkoordinator", "turistsamordnare", "turistvärd",
                "turism"):
        return "Kultur och Fritid"

    if contains("evenemangsadministratör", "evenemangsansvarig", "evenemangsassistent",
                "evenemangskoordinator", "evenemangslots", "evenemangspersonal",
                "evenemangssamordnare", "evenemangssekreterare", "evenemangstekniker",
                "evenemangsutvecklare", "eventsamordnare"):
        return "Kultur och Fritid"

    if contains("föreningsadministratör", "föreningsansvarig", "föreningshandläggare",
                "föreningskonsulent", "föreningslots", "föreningssamordnare",
                "föreningsutvecklare"):
        return "Kultur och Fritid"

    if contains("friluftsamordnare", "friluftsstrateg", "friluftsvaktmästare",
                "friluftssamordnare"):
        return "Kultur och Fritid"

    if contains("fotografassistent", "fotograf", "filmare", "filmkonsulent",
                "filmpedagog", "film- och mediapedagog"):
        return "Kultur och Fritid"

    if contains("bokbusschaufför", "bokbussförare"):
        return "Kultur och Fritid"

    if contains("campingvärd", "campvärd"):
        return "Kultur och Fritid"

    if contains("gästhamnsvärd"):
        return "Kultur och Fritid"

    if contains("slotts-/guideansvarig", "forntidspedagog", "forngårdspedagog"):
        return "Kultur och Fritid"

    if contains("frilufts"):
        return "Kultur och Fritid"

    if contains("världsarvssamordnare"):
        return "Kultur och Fritid"

    if contains("cirkusassistent", "cirkusinstruktör", "cirkuslärare"):
        return "Kultur och Fritid"

    if contains("destinationskoordinator", "destinationsutvecklare",
                "destinationssäljare", "destinations- och näringlivsutvecklare",
                "dmo-ansvarig", "dmo-koordinator"):
        return "Kultur och Fritid"

    if contains("kongressansvarig"):
        return "Kultur och Fritid"

    if contains("kulturgeolog"):
        return "Kultur och Fritid"

    if contains("filialföreståndare"):
        return "Kultur och Fritid"

    # ----------------------------------------------------------------
    # 17. FOLKHÄLSA OCH HÄLSOFRÄMJANDE ARBETE
    # ----------------------------------------------------------------
    if contains("folkhälso", "folkhälsostrateg", "folkhälsosamordnare",
                "folkhälsopedagog", "folkhälsoplanerare", "folkhälsochef",
                "folkhälsoinspiratör", "folkhälsoutvecklare",
                "andt-samordnare", "preventionssamordnare",
                "folkhälsa"):
        return "Folkhälsa och Hälsofrämjande arbete"

    if contains("friskvårdsarbetare", "friskvårdsassistent", "friskvårdskonsulent",
                "friskvårdspedagog", "friskvårdspersonal", "friskvårdsutvecklare",
                "friskvårdare"):
        return "Folkhälsa och Hälsofrämjande arbete"

    if contains("hälsocoach", "hälsoinformatik", "hälsoinspiratör", "hälsokonsulent",
                "hälsopedagog", "hälsopromotor", "hälsosamordnare", "hälsostrateg",
                "hälsoutvecklare", "hälsovägledare", "hälso- och aktivitetssamordnare",
                "hälso- och jobbcoach", "hälsofrämjande"):
        if contains("sjukvård", "sjuksköterska"):
            return "Vård och Omsorg"
        return "Folkhälsa och Hälsofrämjande arbete"

    if contains("jämställdhets- och folkhälsosamordnare", "jämställdhetsutvecklare"):
        return "Folkhälsa och Hälsofrämjande arbete"

    # ----------------------------------------------------------------
    # 18. FORSKNING OCH UTVECKLING
    # ----------------------------------------------------------------
    if contains("forskare", "forskningsassistent", "forskningsdirektör",
                "forskningskoordinator", "forskningsledare", "forskningssekreterare",
                "forskningssjuksköterska", "fou-chef", "fou-direktör",
                "fou-handledare", "fou-koordinator", "fou-strateg",
                "epidemiolog", "statistiker", "statistikhandläggare",
                "statistikadministratör", "analytiker") and not contains(
            "kvalitetsanalytiker", "verksamhetsanalytiker"):
        return "Forskning och Utveckling"

    if contains("doktorand", "vetenskaplig ledare", "universitetslektor",
                "laborant"):
        return "Forskning och Utveckling"

    if contains("utdataanalytiker", "utdatasamordnare"):
        return "Forskning och Utveckling"

    # ----------------------------------------------------------------
    # 19. INVANDRING, INTEGRATION OCH MÅNGFALD
    # ----------------------------------------------------------------
    if contains("integrations", "integrationshandledare", "integrations-",
                "integrationshandläggare", "integrationskonsulent",
                "integrationskoordinator", "integrationsledare",
                "integrationspedagog", "integrationssamordnare",
                "integrationssekreterare", "integrationsstrateg",
                "integrationsstödjare", "integrationsutvecklare",
                "integrationsvägledare", "integratör",
                "integrations- och arbetsmarknadschef"):
        if contains("sfi") and not contains("lärare"):
            return "Invandring, Integration och Mångfald"
        return "Invandring, Integration och Mångfald"

    if contains("mångfaldssamordnare"):
        return "Invandring, Integration och Mångfald"

    if contains("flyktingassistent", "flyktinghandledare", "flyktinghandläggare",
                "flyktingmottagare", "flyktingsamordnare", "flyktingsekreterare",
                "flyktingstödjare", "flyktingvägledare"):
        return "Invandring, Integration och Mångfald"

    if contains("etablerings"):
        return "Invandring, Integration och Mångfald"

    if contains("introduktionsadministratör", "introduktionshandledare",
                "introduktionshandläggare", "introduktionssekreterare"):
        return "Invandring, Integration och Mångfald"

    if contains("tolk", "tolktjänst", "tolkförmedlare", "tolksamordnare"):
        return "Invandring, Integration och Mångfald"

    if contains("samisk koordinator", "minoritetssamordnare",
                "minoritetsspråkhandläggare"):
        return "Invandring, Integration och Mångfald"

    if contains("internationaliseringsamordnare", "internationell samordnare",
                "internationell strateg"):
        return "Invandring, Integration och Mångfald"

    if contains("kaa-handläggare", "kaa-samordnare"):
        return "Invandring, Integration och Mångfald"

    if contains("kartläggare (nyanlända)"):
        return "Invandring, Integration och Mångfald"

    # ----------------------------------------------------------------
    # 20. UPPHANDLING OCH INKÖP
    # ----------------------------------------------------------------
    if contains("upphandlare", "upphandlingadministratör", "upphandlingsansvarig",
                "upphandlingsassistent", "upphandlingschef", "upphandlingscontroller",
                "upphandlingshandläggare", "upphandlingsjurist",
                "upphandlingskoordinator", "upphandlingsledare",
                "upphandlingssamordnare", "upphandlingssekreterare",
                "upphandlingsstrateg"):
        return "Upphandling och Inköp"

    if contains("inköpare", "inköpsassistent", "inköpschef", "inköpscontroller",
                "inköpskoordinator", "inköpsledare", "inköpssamordnare",
                "inköpsstrateg", "inköp- och upphandlingschef"):
        return "Upphandling och Inköp"

    if contains("kategoriledare") and contains("inköp", "upphandl"):
        return "Upphandling och Inköp"

    if contains("e-handelsansvarig") and contains("inköp"):
        return "Upphandling och Inköp"

    # ----------------------------------------------------------------
    # 21. REVISION OCH TILLSYN
    # ----------------------------------------------------------------
    if contains("revisor", "revisionschef", "revisionsdirektör", "internrevisor",
                "granskningstjänsteman", "granskningshandläggare",
                "internkontrollansvarig", "granskare", "tillsynshandläggare",
                "tillsynsman", "tillsynsperson", "tillsyningsman"):
        return "Revision och Tillsyn"

    # ----------------------------------------------------------------
    # 22. POLITISK LEDNING OCH STÖD
    # ----------------------------------------------------------------
    if contains("politisk sekreterare", "politisk rådgivare", "politisk samordnare",
                "politisk stabschef"):
        return "Politisk ledning och Stöd"

    if contains("kommunalråd", "oppositionsråd", "kommunstyrelse (ordförande",
                "kommunstyrelse (vice", "ordförande", "ledamot", "ersättare",
                "förtroendevald", "förtroendeman", "vigselvärd"):
        if contains("kommunalråd", "oppositionsråd"):
            return "Politisk ledning och Stöd"
        return "Politisk ledning och Stöd"

    # ----------------------------------------------------------------
    # 23. PROJEKTLEDNING OCH UTVECKLINGSARBETE
    # ----------------------------------------------------------------
    if contains("projektledare") and not contains(
            "it-projektledare", "projektledare (it)", "projektledare (bygg)",
            "projektledare (anläggning)", "projektledare (exploatering)",
            "projektledare (mark", "projektledare (samhällsbyggnad)",
            "projektledare (vvs)", "projektledare (el)", "projektledare (underhåll)",
            "va-projektledare"):
        if contains("bygg", "anläggning", "exploatering", "mark",
                    "samhällsbyggnad", "vvs", "el", "underhåll"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("it", "digital", "system"):
            return "IT och Digitalisering"
        if contains("kultur", "konst"):
            return "Kultur och Fritid"
        return "Projektledning och Utvecklingsarbete"

    if tl.startswith("projektledare"):
        return "Projektledning och Utvecklingsarbete"

    if contains("verksamhetsutvecklare") and not contains(
            "it", "digital", "system", "mas", "mar"):
        return "Projektledning och Utvecklingsarbete"

    if tl.startswith("verksamhetsutvecklare"):
        if contains("digitalisering", "it-"):
            return "IT och Digitalisering"
        return "Projektledning och Utvecklingsarbete"

    if contains("processledare", "processansvarig", "processägare",
                "processamordnare"):
        return "Projektledning och Utvecklingsarbete"

    if contains("förändringsledare"):
        return "Projektledning och Utvecklingsarbete"

    if contains("förbättringsledare"):
        return "Projektledning och Utvecklingsarbete"

    if contains("innovationschef", "innovationskoordinator", "innovationsledare",
                "innovationsstrateg", "innovationsutvecklare"):
        return "Projektledning och Utvecklingsarbete"

    if contains("change manager"):
        return "Projektledning och Utvecklingsarbete"

    if contains("tjänstedesigner"):
        return "Projektledning och Utvecklingsarbete"

    if contains("kvalitetschef", "kvalitetscontroller", "kvalitetshandledare",
                "kvalitetskoordinator", "kvalitetsledare", "kvalitetspedagog",
                "kvalitetssamordnare", "kvalitetsstrateg", "kvalitetsstödjare",
                "kvalitetstekniker", "kvalitetsanalytiker", "kvalitetsansvarig",
                "kvalitetsutvecklare", "kvalitetsutredare"):
        return "Projektledning och Utvecklingsarbete"

    if contains("portföljledare"):
        return "Projektledning och Utvecklingsarbete"

    # ----------------------------------------------------------------
    # 24. FASTIGHET OCH LOKALVÅRD
    # ----------------------------------------------------------------
    if contains("fastighetsförvaltare", "fastighetsadministratör",
                "fastighetsansvarig", "fastighetsassistent", "fastighetschef",
                "fastighetsdirektör", "fastighetsekonom", "fastighetsförman",
                "fastighetshandläggare", "fastighetsingenjör", "fastighetsintendent",
                "fastighetskoordinator", "fastighetsreparatör", "fastighetssamordnare",
                "fastighetsskötare", "fastighetsstrateg", "fastighetstekniker",
                "fastighetsutvecklare", "fastighetsvärd", "fastighetsvärderare",
                "fastighet"):
        if contains("it-"):
            return "IT och Digitalisering"
        return "Fastighet och Lokalvård"

    if contains("lokalvårdare", "lokalvårdschef", "lokalvårdsledare",
                "städare", "städchef", "städcontroller", "städledare",
                "städmedarbetare", "städområdeschef", "städsamordnare",
                "städspecialist", "städutvecklare", "städvärd",
                "städ-/servicepersonal", "städansvarig"):
        return "Fastighet och Lokalvård"

    if contains("vaktmästare", "vaktmästarassistent"):
        return "Fastighet och Lokalvård"

    if contains("kock", "kokerska", "köksbiträde", "kökschef",
                "köksföreståndare", "köksledare", "köksmästare",
                "köksområdeschef", "kökssamordnare", "kockbiträde",
                "kostbiträde", "kostchef", "kostpersonal",
                "kostansvarig", "kostadministratör", "kostekonom",
                "kostplanerare", "kostsamordnare", "koststrateg",
                "kostutvecklare", "måltidsbiträde", "måltidschef",
                "måltidspersonal", "måltidsplanerare", "måltidssamordnare",
                "måltidsstrateg", "måltidsutvecklare", "måltidsvärd",
                "måltidsvärdinna", "ekonomibiträde",
                "köks- och måltidsarbetare", "köksansvarig",
                "storkökskock", "produktionsledare (centralkök)",
                "dietkock", "dietkokerska", "skolmåltidsbiträde",
                "skolmåltidskonsult", "restaurangansvarig", "restaurangbiträde",
                "bartender", "cafeteriabiträde", "cafeteriaföreståndare",
                "caféansvarig", "cafébiträde", "caféföreståndare",
                "cafépersonal", "cafévärd", "cafévärdinna",
                "kaffeansvarig", "frukostvärd", "serveringsbiträde",
                "serveringspersonal", "servitris", "kiosk",
                "husförvaltare", "husmor"):
        return "Fastighet och Lokalvård"

    if contains("kombitjänst kost", "kombitjänst vaktmästare"):
        return "Fastighet och Lokalvård"

    if contains("hyresadministratör", "hyresassistent", "hyresekonom",
                "hyreshandläggare", "boförvaltare"):
        return "Fastighet och Lokalvård"

    if contains("facility manager"):
        return "Fastighet och Lokalvård"

    if contains("tvättbiträde", "tvätteriarbetare", "tvätteribiträde",
                "tvättkontrollant", "tvättmaskinskötare", "sömmers",
                "sömnadsbiträde", "textilarbetare", "textilbiträde"):
        return "Fastighet och Lokalvård"

    if contains("husvärd", "husvärdinna", "bovärd", "bostadsassistent",
                "bostadsförvaltare", "liftskötare", "liftvärd"):
        return "Fastighet och Lokalvård"

    if contains("tapetserare", "snickare", "hantverkare", "reparatör",
                "verkmästare", "verkstadsarbetare", "verkstadsmekaniker",
                "verkstadsförman", "verkstadsföreståndare", "verkstadschef",
                "mekaniker", "metallarbet"):
        if contains("dental", "tand"):
            return "Vård och Omsorg"
        return "Fastighet och Lokalvård"

    if contains("målare"):
        return "Fastighet och Lokalvård"

    if contains("skorstensf", "skorstensfejare", "skorstensfejartekniker"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("stensättare"):
        return "Samhällsbyggnad och Infrastruktur"

    # ----------------------------------------------------------------
    # 25. ARBETSMARKNAD – klassificeras som Socialt arbete
    # ----------------------------------------------------------------
    if contains("arbetsmarknad"):
        return "Socialt arbete och Stöd"

    if contains("jobbcoach", "jobblotsare", "arbetsintegration", "arbetscoach"):
        return "Socialt arbete och Stöd"

    if contains("praktikkoordinator", "praktiksamordnare", "praktikuppföljare",
                "praosamordnare", "apl-samordnare"):
        return "Socialt arbete och Stöd"

    if contains("sysselsättning"):
        return "Socialt arbete och Stöd"

    if contains("arbetshandledare", "arbetsanskaffare", "arbetslivskonsulent",
                "arbetsanpassare", "arbetsgivarkoordin", "arbetskonsulent",
                "arbetskoordinator", "arbetslagsledare", "arbetslagsresurs",
                "arbetsspecialist", "arbetsinstruktör"):
        return "Socialt arbete och Stöd"

    # ----------------------------------------------------------------
    # 26. SPECIFIKA DOMÄNREGLER FÖR TITLAR SOM FASTNAR I FALLBACK
    # ----------------------------------------------------------------

    # Vård-relaterade utan explicit "vård"
    if contains("audionom", "audiometri"):
        return "Vård och Omsorg"
    if contains("ambulans"):
        return "Vård och Omsorg"
    if contains("avlösare"):
        return "Vård och Omsorg"
    if contains("ledsagare"):
        return "Vård och Omsorg"
    if contains("boendeassistent", "boendebiträde", "boendechef", "boendecoach",
                "boendehandledare", "boendekonsulent", "boendekoordinator",
                "boendelots", "boendepersonal", "boendesamordnare",
                "boendevägledare", "boendesekreterare", "boendestrateg"):
        if contains("integration", "flykting", "nyanlända"):
            return "Invandring, Integration och Mångfald"
        return "Socialt arbete och Stöd"
    if contains("boendeförmedlare", "bostadskoordinator", "bostadshandläggare",
                "bostadskonsulent", "bostadslots", "bostadssamordnare",
                "bostadssekreterare", "bostadssocialhandläggare",
                "bostadsutvecklare", "bostöd"):
        return "Socialt arbete och Stöd"
    if contains("bostadsanpassnings", "bab-handläggare"):
        return "Socialt arbete och Stöd"
    if contains("aktiverare", "aktiveringsbiträde", "aktiveringsledare",
                "aktiveringssamordnare", "aktivitetshandledare",
                "aktivitetsansvarig", "aktivitetsledare", "aktivitetslots",
                "aktivitetssamordnare", "aktivitetsstödjare",
                "aktivitetsutvecklare", "aktivitetsvärd", "aktivitetsassistent"):
        if contains("omsorg", "funktionsnedsättning", "lss", "daglig"):
            return "Vård och Omsorg"
        return "Socialt arbete och Stöd"
    if contains("case manager"):
        return "Socialt arbete och Stöd"
    if contains("peer support"):
        return "Socialt arbete och Stöd"
    if contains("samtalsstödjare", "samtalsledare", "samtalsterapeut"):
        return "Socialt arbete och Stöd"
    if contains("avgiftshandläggare", "avgiftsadministratör"):
        return "Socialt arbete och Stöd"
    if contains("anhörigvårdare"):
        return "Vård och Omsorg"
    if contains("biträde (vård"):
        return "Vård och Omsorg"
    if contains("biomedicinare"):
        return "Vård och Omsorg"
    if contains("alkoholhandläggare", "alkohol- och tobakshandläggare"):
        return "Juridik och Säkerhet"
    if contains("beroenderådgivare"):
        return "Socialt arbete och Stöd"
    if contains("arenachef", "arenakoordinator", "arenasamordnare", "arenatekniker"):
        return "Kultur och Fritid"
    if contains("arborist"):
        return "Samhällsbyggnad och Infrastruktur"
    if contains("arkitekt") and not contains("it-", "enterprisearkitekt", "systemarkitekt",
                                              "informationsarkitekt", "verksamhetsarkitekt"):
        return "Samhällsbyggnad och Infrastruktur"
    if contains("arkivarie", "arkivassistent", "arkivarbetare", "arkivbiträde",
                "arkivföreståndare", "arkivhandläggare", "arkivsamordnare",
                "arkivadministratör"):
        return "Ekonomi och Administration"
    if contains("arkeolog"):
        return "Kultur och Fritid"
    if contains("antikvarie") and contains("bebyggelse", "byggnads"):
        return "Samhällsbyggnad och Infrastruktur"
    if contains("kommunantikvarie", "stadsantikvarie", "bebyggelseantikvarie"):
        return "Samhällsbyggnad och Infrastruktur"
    if contains("antikvarie"):
        return "Kultur och Fritid"
    if contains("apoteksassistent", "apotekstekniker"):
        return "Vård och Omsorg"
    if contains("applikationskonsult", "applikationsspecialist"):
        return "IT och Digitalisering"
    if contains("automatikingenjör", "automationsingenjör", "automationsutvecklare"):
        return "Samhällsbyggnad och Infrastruktur"
    if contains("av-tekniker"):
        return "Kultur och Fritid"
    if contains("avfallshandläggare", "avfallsansvarig", "avfallsarbetare",
                "avfallshämtare", "avfallsingenjör", "avfallsrådgivare",
                "avfallsstrateg", "avfallstekniker", "avfallsutredare",
                "avfallsutvecklare"):
        return "Avfall och Återvinning"
    if contains("avtalsansvarig", "avtalscontroller", "avtalssamordnare",
                "avtalssekreterare"):
        return "Upphandling och Inköp"
    if contains("bad") and contains("mästare", "föreståndare", "chef",
                                    "biträde", "personal", "värd", "bevakare"):
        return "Kultur och Fritid"
    if contains("barn- och ungdoms"):
        if contains("chef", "strateg", "samordnare", "handläggare"):
            return "Utbildning och Pedagogik"
    if contains("barnbiblioteks"):
        return "Kultur och Fritid"
    if contains("barnombudsman", "barnrättstrateg"):
        return "Juridik och Säkerhet"
    if contains("barnassistent", "barnbiträde", "barnhandledare",
                "barnvårdare", "barntillsynspedagog"):
        return "Utbildning och Pedagogik"
    if contains("beteendevetare"):
        return "Socialt arbete och Stöd"
    if contains("bebyggelseantikvarie"):
        return "Samhällsbyggnad och Infrastruktur"
    if contains("beläggningsansvarig"):
        return "Samhällsbyggnad och Infrastruktur"
    if contains("beredare"):
        return "Ekonomi och Administration"
    if contains("beredningskoordinator"):
        return "Ekonomi och Administration"
    if contains("bemanningsadministratör", "bemanningsassistent",
                "bemanningscontroller", "bemanningspartner"):
        return "HR och Personal"
    if contains("bi-utvecklare"):
        return "IT och Digitalisering"
    if contains("biografmaskinist", "biografvaktmästare"):
        return "Kultur och Fritid"
    if contains("bilettförsäljare", "biljettförsäljare"):
        return "Kultur och Fritid"
    if contains("bilförman"):
        return "Transport och Trafikplanering"
    if contains("bokningsansvarig", "bokningskoordinator"):
        return "Kultur och Fritid"
    if contains("bokuppsättare"):
        return "Kultur och Fritid"
    if contains("båtförare"):
        return "Transport och Trafikplanering"
    if contains("behandlingsansvarig", "behandlingsbiträde"):
        return "Socialt arbete och Stöd"
    if contains("3d-grafiker"):
        return "Kommunikation och Medborgarkontakt"
    if contains("abonnentingenjör", "abonnenttekniker"):
        return "IT och Digitalisering"
    if contains("affärsansvarig", "affärsbiträde", "affärsrådgivare",
                "affärsstrateg", "affärsutvecklare"):
        return "Ekonomi och Administration"
    if contains("agenda samordnare"):
        return "Ekonomi och Administration"
    if contains("analysledare", "samhällsanalytiker"):
        return "Forskning och Utveckling"
    if contains("anläggningsingenjör"):
        return "Samhällsbyggnad och Infrastruktur"
    if contains("ansvarig convention bureau"):
        return "Kultur och Fritid"
    if contains("ansvarig digi kanaler"):
        return "Kommunikation och Medborgarkontakt"
    if contains("ansvarig internservice"):
        return "Ekonomi och Administration"
    if contains("ansvarig konferensvärd", "ansvarig konsertvärd"):
        return "Kultur och Fritid"
    if contains("antagningshandläggare", "antagningssamordnare", "antagningssekreterare"):
        return "Utbildning och Pedagogik"
    if contains("ateljerista"):
        return "Utbildning och Pedagogik"
    if contains("avdelningschef"):
        tl2 = tl
        if contains("vård", "omsorg", "hälso", "sjukvård", "psyk", "rehab"):
            return "Vård och Omsorg"
        if contains("förskola", "skola", "utbildning", "elevhälsa", "barnomsor",
                    "gymnasium", "grundskola", "lärande"):
            return "Utbildning och Pedagogik"
        if contains("it", "digital", "system"):
            return "IT och Digitalisering"
        if contains("miljö", "plan", "bygg", "teknik", "gata", "kart",
                    "samhällsbyggnad", "exploatering", "mark"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("ifo", "social", "lss", "familj"):
            return "Socialt arbete och Stöd"
        if contains("hr", "personal", "lön"):
            return "HR och Personal"
        if contains("ekonomi", "finans"):
            return "Ekonomi och Administration"
        if contains("kost", "städ", "lokalvård", "fastigh"):
            return "Fastighet och Lokalvård"
        if contains("kultur", "fritid", "bibliotek"):
            return "Kultur och Fritid"
        if contains("räddning", "brand"):
            return "Brand och Räddningstjänst"
        if contains("fou"):
            return "Forskning och Utveckling"
        return "Ekonomi och Administration"
    if contains("ärendehandledare", "ärendekoordinator"):
        return "Ekonomi och Administration"
    if contains("1:e kommunsekreterare", "1:e bibl"):
        if contains("bibl"):
            return "Kultur och Fritid"
        return "Kommunövergripande och Strategiska funktioner"
    if contains("1:e "):
        # Prefix 1:e/Förste + domän
        if contains("bibl"):
            return "Kultur och Fritid"
        if contains("kock", "kokerska"):
            return "Fastighet och Lokalvård"
        if contains("sjuksk", "sköterska", "sjuksköterska"):
            return "Vård och Omsorg"
        if contains("rörläggare"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("sjukhusfysiker"):
            return "Vård och Omsorg"
        if contains("linjenschef"):
            return "Ekonomi och Administration"
    if contains("projektchef"):
        return "Projektledning och Utvecklingsarbete"
    if contains("vaktmästarbiträde"):
        return "Fastighet och Lokalvård"
    if contains("chef (första linjen)"):
        return "Ekonomi och Administration"
    if contains("allergikonsulent"):
        return "Vård och Omsorg"
    if contains("ambulansdirigent"):
        return "Vård och Omsorg"
    if contains("arvodesamordnare", "arvodist"):
        return "Ekonomi och Administration"
    if contains("automationsutvecklare"):
        return "IT och Digitalisering"
    if contains("baransvarig"):
        return "Kultur och Fritid"
    if contains("bärhjälp"):
        return "Vård och Omsorg"
    if contains("barn- och elevstödsamordnare"):
        return "Utbildning och Pedagogik"
    if contains("barnskötarbiträde"):
        return "Utbildning och Pedagogik"
    if contains("bemanningkoordinator"):
        return "HR och Personal"
    if contains("bemötandechef"):
        return "Kommunikation och Medborgarkontakt"
    if contains("beställare/controller", "beställningsoperatör",
                "beställningsmottagare"):
        return "Ekonomi och Administration"
    if contains("biblioteksassistent", "biblioteksadministratör",
                "bibliotekskanslist"):
        return "Kultur och Fritid"
    if contains("bilpoolsansvarig", "bilpoolsamordnare", "bilsamordnare"):
        return "Transport och Trafikplanering"
    if contains("bokbusschaufför"):
        return "Kultur och Fritid"
    if contains("bokningsansvarig"):
        return "Kultur och Fritid"
    if contains("biträdande avdelningschef"):
        return "Ekonomi och Administration"

    # Enhetschef + domän → domän
    if contains("enhetschef"):
        if contains("vård", "omsorg", "hälso", "sjukvård", "sjuksköterska",
                    "hemtjänst", "lss", "psyk", "rehab", "hsl",
                    "funktionshinder", "habilitering", "äldreboende",
                    "äldreomsorg", "demens"):
            return "Vård och Omsorg"
        if contains("förskola", "skola", "utbildning", "elevhälsa",
                    "gymnasium", "grundskola", "fritids", "barnomsorg"):
            return "Utbildning och Pedagogik"
        if contains("it", "digital"):
            return "IT och Digitalisering"
        if contains("miljö", "plan", "bygg", "gata", "kart", "anläggning",
                    "samhällsbyggnad", "exploatering", "mark", "va", "lantmäteri"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("ifo", "social", "lss", "familj", "myndighetsutövning"):
            return "Socialt arbete och Stöd"
        if contains("hr", "personal", "lön"):
            return "HR och Personal"
        if contains("ekonomi", "finans"):
            return "Ekonomi och Administration"
        if contains("kost", "städ", "lokalvård", "fastigh", "måltid",
                    "vaktmästare"):
            return "Fastighet och Lokalvård"
        if contains("kultur", "fritid", "bibliotek", "idrotts", "bad",
                    "simhall", "park"):
            return "Kultur och Fritid"
        if contains("räddning", "brand", "rib"):
            return "Brand och Räddningstjänst"
        if contains("kontaktcenter", "kundtjänst", "servicecenter",
                    "medborgarservice"):
            return "Kommunikation och Medborgarkontakt"
        if contains("upphandling", "inköp"):
            return "Upphandling och Inköp"
        if contains("trafik"):
            return "Transport och Trafikplanering"
        if contains("projekt", "planering", "kvalitet", "strategi", "samhällsutveck",
                    "utveckling", "service", "stöd/samordning", "resursenhet",
                    "bemanning"):
            return "Projektledning och Utvecklingsarbete"
        return "Ekonomi och Administration"

    # Verksamhetschef + domän fallback
    if contains("verksamhetschef"):
        if contains("vård", "omsorg", "hälso", "sjukvård", "läkare",
                    "sjuksköterska", "barnmorska", "tandläkare", "folktandvård",
                    "psyk", "rehabilitering", "skolhälsovård", "hemtjänst",
                    "lss", "sol/hsl", "biomed", "sjukgymnastik"):
            return "Vård och Omsorg"
        if contains("förskola", "skola", "utbildning", "lärande",
                    "barn- och ungdom", "grundskola", "gymnasiet"):
            return "Utbildning och Pedagogik"
        if contains("kultur", "fritid", "ungdom"):
            return "Kultur och Fritid"
        if contains("ifo", "social", "socialtjänst"):
            return "Socialt arbete och Stöd"
        if contains("it", "digital", "investering"):
            return "IT och Digitalisering"
        if contains("teknik", "samhällsbyggnad"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("måltid", "lokalvård"):
            return "Fastighet och Lokalvård"
        return "Ekonomi och Administration"

    # Förvaltningschef + domän
    if contains("förvaltningschef"):
        if contains("vård", "omsorg", "lss", "hälso", "sjukvård"):
            return "Vård och Omsorg"
        if contains("skola", "utbildning", "förskola", "lärande"):
            return "Utbildning och Pedagogik"
        if contains("kultur", "fritid"):
            return "Kultur och Fritid"
        if contains("samhällsbyggnad", "teknik", "plan", "bygg"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("it"):
            return "IT och Digitalisering"
        return "Ekonomi och Administration"

    # Chef (X) mönstret
    if tl.startswith("chef ("):
        inner = tl[6:]
        if "it" in inner or "digital" in inner:
            return "IT och Digitalisering"
        if any(w in inner for w in ["hemtjänst", "hälsa", "vård", "omsorg",
                                    "psyk", "hsl", "lss", "personlig assistens"]):
            return "Vård och Omsorg"
        if any(w in inner for w in ["förskola", "skola", "gymnasie", "grundskola",
                                    "lärande", "familjedaghem", "flerspråk",
                                    "modersmål", "vuxenutbildning", "elevhälsa"]):
            return "Utbildning och Pedagogik"
        if any(w in inner for w in ["ifo", "individ", "social", "arbetsmarknad",
                                    "arbetsmarknadsenheten", "flyktings"]):
            return "Socialt arbete och Stöd"
        if any(w in inner for w in ["ekonomi", "administration", "lön", "finans",
                                    "verksamhetsstöd", "ledningsstöd", "ledningsstab"]):
            return "Ekonomi och Administration"
        if any(w in inner for w in ["hr", "personal", "personalsystem",
                                    "personalavdelning"]):
            return "HR och Personal"
        if any(w in inner for w in ["kultur", "fritid", "turism",
                                    "ekebyhovs", "ungdomsverksamhet", "scen",
                                    "kulturskola", "fritidsgård"]):
            return "Kultur och Fritid"
        if any(w in inner for w in ["fastighet", "måltid", "kost", "städ",
                                    "lokalvård", "måltidsservice"]):
            return "Fastighet och Lokalvård"
        if any(w in inner for w in ["samhällsutveckling", "infrastruktur",
                                    "investering", "plan", "bygg", "miljö"]):
            return "Samhällsbyggnad och Infrastruktur"
        if any(w in inner for w in ["kommunikation", "kontaktcenter",
                                    "kundservice", "medborgarservice",
                                    "servicecenter", "information"]):
            return "Kommunikation och Medborgarkontakt"
        if any(w in inner for w in ["kansliet", "kvalitet", "strategisk",
                                    "myndighets", "beslutsenhet", "stadsarkiv",
                                    "kommunledningskontoret", "ledningsstöd"]):
            return "Ekonomi och Administration"
        if any(w in inner for w in ["trygghet", "säkerhet", "beredskap"]):
            return "Juridik och Säkerhet"
        return "Ekonomi och Administration"

    # Övriga chef-titlar
    if contains("chef"):
        if contains("förvaltnings"):
            return "Ekonomi och Administration"
        if contains("räddnings", "brand"):
            return "Brand och Räddningstjänst"
        if contains("vård", "omsorg", "hälso", "sjukvård", "sjuksköterska",
                    "hemtjänst", "lss", "psyk", "rehab"):
            return "Vård och Omsorg"
        if contains("förskola", "skola", "utbildning", "elevhälsa"):
            return "Utbildning och Pedagogik"
        if contains("ifo", "social"):
            return "Socialt arbete och Stöd"
        if contains("it", "digital", "nätverks"):
            return "IT och Digitalisering"
        if contains("miljö", "plan", "bygg", "gata", "kart", "samhällsbyggnad"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("hr", "personal", "lön", "rekryter"):
            return "HR och Personal"
        if contains("ekonomi", "finans", "budget", "redovisning"):
            return "Ekonomi och Administration"
        if contains("kost", "städ", "lokalvård", "fastigh", "måltid"):
            return "Fastighet och Lokalvård"
        if contains("kultur", "fritid", "bibliotek", "idrotts", "bad",
                    "musik", "teater"):
            return "Kultur och Fritid"
        if contains("upphandling", "inköp"):
            return "Upphandling och Inköp"
        if contains("revision"):
            return "Revision och Tillsyn"
        if contains("juridik", "säkerhet", "trygghet", "beredskap"):
            return "Juridik och Säkerhet"
        if contains("trafik", "transport"):
            return "Transport och Trafikplanering"
        if contains("avfall", "renhållning"):
            return "Avfall och Återvinning"
        if contains("energi"):
            return "Energi och Klimat"
        if contains("folkhälsa"):
            return "Folkhälsa och Hälsofrämjande arbete"
        if contains("kommunikation", "kontaktcenter", "medborgare"):
            return "Kommunikation och Medborgarkontakt"
        return "Ekonomi och Administration"

    # Direktör + domän
    if contains("direktör"):
        if contains("vård", "omsorg", "hälso", "sjukvård", "sjukhus",
                    "primärvård", "folktandvård"):
            return "Vård och Omsorg"
        if contains("utbildning", "skola", "lärande"):
            return "Utbildning och Pedagogik"
        if contains("samhällsbyggnad", "stadsbyggnad", "samhällsutveckling"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("it", "digital"):
            return "IT och Digitalisering"
        if contains("hr", "personal"):
            return "HR och Personal"
        if contains("ekonomi", "finans"):
            return "Ekonomi och Administration"
        if contains("kultur", "fritid"):
            return "Kultur och Fritid"
        if contains("revision", "granskning"):
            return "Revision och Tillsyn"
        if contains("kommunikation"):
            return "Kommunikation och Medborgarkontakt"
        if contains("välfärd"):
            return "Vård och Omsorg"
        if contains("region", "stads", "kommun", "förbunds"):
            return "Ekonomi och Administration"
        return "Ekonomi och Administration"

    # Sektorchef/Sektionschef
    if contains("sektorchef", "sektionschef", "sektorschef"):
        if contains("vård", "omsorg", "hälso", "sjukvård"):
            return "Vård och Omsorg"
        if contains("skola", "utbildning", "lärande"):
            return "Utbildning och Pedagogik"
        if contains("miljö", "samhällsbyggnad", "samhällsutveckling"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("service"):
            return "Ekonomi och Administration"
        return "Ekonomi och Administration"

    # Områdeschef
    if contains("områdeschef"):
        if contains("vård", "omsorg", "äldreomsorg", "lss", "funktionshinder",
                    "socialt arbete", "särkilt boende"):
            return "Vård och Omsorg"
        if contains("ifo", "social"):
            return "Socialt arbete och Stöd"
        if contains("kost"):
            return "Fastighet och Lokalvård"
        return "Ekonomi och Administration"

    # Divisionschef
    if contains("divisionschef"):
        if contains("näringsliv", "kultur", "fritid"):
            return "Kultur och Fritid"
        if contains("räddning", "säkerhet"):
            return "Brand och Räddningstjänst"
        if contains("samhällsbyggnad"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("social", "omsorg"):
            return "Vård och Omsorg"
        return "Ekonomi och Administration"

    # Strategiska ledande poster
    if contains("kommunchef", "stadsdirektör", "stadschef",
                "stadsjurist", "stadsombudsman"):
        return "Kommunövergripande och Strategiska funktioner"

    if contains("regionchefläkare", "regiondirektör", "regionjurist",
                "regionläkare", "regionområdeschef", "regionsekreterare",
                "regionsjurist", "regionstrateg", "regionutvecklare",
                "regionöverläkare", "regionarkivarie",
                "regionutvecklingsdirektör"):
        return "Ekonomi och Administration"

    if contains("förbundschef"):
        return "Ekonomi och Administration"

    if contains("förvaltare") and not contains(
            "fastighetsförvaltare", "markförvaltare", "jordbruksförvaltare",
            "skog", "natur"):
        return "Ekonomi och Administration"

    if contains("förvaltningsadministratör", "förvaltningsassistent",
                "förvaltningscontroller", "förvaltningsdirektör",
                "förvaltningsekonom", "förvaltningshandläggare",
                "förvaltningsledare", "förvaltningssamordnare",
                "förvaltningssekreterare", "förvaltningsstrateg",
                "förvaltningsstädare", "förvaltningsjurist",
                "förvaltningshef"):
        if contains("it"):
            return "IT och Digitalisering"
        if contains("jurist"):
            return "Juridik och Säkerhet"
        return "Ekonomi och Administration"

    # Nämnd-
    if contains("nämndadministratör", "nämndregistrator",
                "nämndsamordnare", "nämnd- och utredningssekreterare",
                "nämndtjänsteman", "nämndsutredare",
                "nämndadministrativ chef"):
        return "Ekonomi och Administration"

    # Specifika titlar
    if contains("barnskötarbiträde"):
        return "Utbildning och Pedagogik"

    if contains("barnassistent"):
        return "Utbildning och Pedagogik"

    if contains("barnbiblioteksassistent"):
        return "Kultur och Fritid"

    if contains("barnombudsman"):
        return "Juridik och Säkerhet"

    if contains("barnrättstrateg"):
        return "Juridik och Säkerhet"

    if contains("barnvårdare"):
        return "Utbildning och Pedagogik"

    if contains("beläggningsansvarig"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("ateljerista"):
        return "Utbildning och Pedagogik"

    # Stödassistent generell → Socialt eller Vård
    if contains("stödassistent"):
        return "Vård och Omsorg"

    if contains("stödbiträde"):
        return "Vård och Omsorg"

    if contains("stödpedagog"):
        if contains("funktionsnedsättning", "lss"):
            return "Vård och Omsorg"
        return "Utbildning och Pedagogik"

    if contains("stödperson", "stödpersonal", "stödresurs"):
        return "Vård och Omsorg"

    if contains("stödvårdbiträde"):
        return "Vård och Omsorg"

    if contains("stödmentor"):
        return "Utbildning och Pedagogik"

    if contains("individstödjare"):
        return "Socialt arbete och Stöd"

    # Handledarroller
    if contains("handledare") and not contains(
            "förhandlare", "utredningshandläggare"):
        if contains("it", "digital", "system"):
            return "IT och Digitalisering"
        if contains("daglig verksamhet", "lss", "funktionsnedsättning",
                    "boende", "ensamkommande"):
            return "Vård och Omsorg"
        if contains("socialtjänst", "ifo", "familjebehandling"):
            return "Socialt arbete och Stöd"
        if contains("vuxenutbildning", "skola", "sfi"):
            return "Utbildning och Pedagogik"
        return "Socialt arbete och Stöd"

    # Vård + omvårdnad residual
    if contains("omvårdnadspersonal"):
        return "Vård och Omsorg"

    if contains("vårdpersonal"):
        return "Vård och Omsorg"

    # Hälso och sjukvård strateg/samordnare
    if contains("hälso- och sjukvård"):
        return "Vård och Omsorg"

    # Lokal-strategier
    if contains("lokalstrateg", "lokalförsörjnings", "lokalplanerare",
                "lokalansvarig", "lokalförvaltare", "lokalcontroller",
                "lokalsamordnare", "lokalresursplanerare"):
        return "Fastighet och Lokalvård"

    # Tjänsteman generell
    if contains("tjänsteman"):
        return "Ekonomi och Administration"

    # Medarbetare generell
    if tl in ["medarbetare", "medhjälpare"]:
        return "Ekonomi och Administration"

    # Praktikant/lärling
    if contains("praktikant", "lärling", "trainee"):
        return "Ekonomi och Administration"

    # Extraresurs/pool/resurs
    if tl in ["resursarbetare", "poolanställd", "vikarie"]:
        return "Ekonomi och Administration"

    if contains("feriearbetare", "feriejobb"):
        return "Ekonomi och Administration"

    # Val-relaterat
    if contains("valadministratör", "valhandläggare", "valideringshandläggare",
                "valkanslichef", "valsamordnare"):
        return "Juridik och Säkerhet"

    # Specifika IT
    if contains("serveradmin"):
        return "IT och Digitalisering"

    # Specifika transport
    if contains("skolskjutshandläggare", "skolskjutssamordnare"):
        return "Transport och Trafikplanering"

    if contains("spolbilförare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("renhållningsarbetare") and not contains("gatu"):
        return "Avfall och Återvinning"

    # Samhällsstrateg / samhällsutvecklare
    if contains("samhällsstrateg", "samhällsutvecklare", "samhällsutvecklingsstrateg"):
        return "Samhällsbyggnad och Infrastruktur"

    # Näringsliv
    if contains("näringsliv"):
        return "Ekonomi och Administration"

    # Kampservicetitlar
    if contains("kundansvarig", "kundkoordinator", "kundmottagare",
                "kundstrateg", "kundvägledare", "kundärendeutredare"):
        return "Kommunikation och Medborgarkontakt"

    # Hälso och sjukvård specifikt
    if contains("utskrivningssamordnare", "sjukresehandläggare", "nära vård samordnare"):
        return "Vård och Omsorg"

    # Specifika sociala
    if contains("grannskapsarbetare", "ombudsm"):
        return "Socialt arbete och Stöd"

    if contains("fosterförälder"):
        return "Socialt arbete och Stöd"

    # Hantverks- och drift-residual
    if contains("driftansvarig", "driftarbetare", "driftchef",
                "driftingenjör", "driftledare", "driftområdeschef",
                "driftreparatör", "driftsamordnare", "drifttekniker",
                "driftmaskinist", "driftoperatör", "driftplanerare",
                "driftutvecklare", "driftassistent"):
        if contains("it", "system"):
            return "IT och Digitalisering"
        if contains("va", "vatten"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("park", "grön", "natur"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("fastigh"):
            return "Fastighet och Lokalvård"
        if contains("räddning", "brand"):
            return "Brand och Räddningstjänst"
        return "Samhällsbyggnad och Infrastruktur"

    if contains("driftadministratör"):
        return "Ekonomi och Administration"

    if contains("förrådsansvarig", "förrådsarbetare", "förrådsassistent",
                "förrådsbiträde", "förrådsförvaltare", "förrådsman",
                "förrådstekniker"):
        return "Fastighet och Lokalvård"

    if contains("lageransvarig", "lagerarbetare", "lagerpersonal"):
        return "Fastighet och Lokalvård"

    if contains("materialförvaltare", "materialkonsulent"):
        return "Ekonomi och Administration"

    if contains("inredare", "inredningssamordnare"):
        return "Fastighet och Lokalvård"

    if contains("verksamhetsarkitekt"):
        if contains("it"):
            return "IT och Digitalisering"
        return "Projektledning och Utvecklingsarbete"

    if contains("utredningsadministratör", "utredningsassistent",
                "utredningschef", "utredningshandläggare",
                "utredningsingenjör", "utredningsledare",
                "utredningssekreterare", "utredningsstrateg"):
        return "Ekonomi och Administration"

    if contains("verksamhetshandläggare", "verksamhetsansvarig",
                "verksamhetsassistent", "verksamhetsledare",
                "verksamhetssamordnare", "verksamhetsstöd",
                "verksamhetsstödjare", "verksamhetspedagog"):
        return "Ekonomi och Administration"

    if contains("verksamhetssekreterare", "verksamhetsplanerare"):
        return "Ekonomi och Administration"

    if contains("verksamhetscontroller", "verksamhetsekonom",
                "verksamhetsjurist"):
        if contains("jurist"):
            return "Juridik och Säkerhet"
        return "Ekonomi och Administration"

    if contains("verksamhetskoordinator"):
        return "Ekonomi och Administration"

    if contains("schemakonsult", "schemaläggare", "schema- och bemannings",
                "schemaorganisatör", "schemaplanerare"):
        return "HR och Personal"

    if contains("visa"):
        pass

    if contains("inventerare"):
        return "Ekonomi och Administration"

    if contains("investeringskoordinator", "investeringsstrateg"):
        return "Ekonomi och Administration"

    if contains("förtroendeman", "fackligt förtroendevald"):
        return "HR och Personal"

    if contains("fackligt"):
        return "HR och Personal"

    if contains("företagskoordinator", "företagslots", "företagsrådgivare",
                "företagssäljare"):
        return "Ekonomi och Administration"

    if contains("näringlivsutvecklare", "näringlivsansvarig"):
        return "Ekonomi och Administration"

    if contains("arenachef", "arenakoordinator", "arenasamordnare",
                "arenatekniker", "arenachef"):
        return "Kultur och Fritid"

    if contains("abonnentingenjör"):
        return "IT och Digitalisering"

    if contains("fondhandläggare"):
        return "Ekonomi och Administration"

    if contains("försäkringshandläggare", "försäkringssamordnare"):
        return "Ekonomi och Administration"

    if contains("köksföreståndare"):
        return "Fastighet och Lokalvård"

    if contains("köksansvarig", "köksenhetschef", "köksområdeschef"):
        return "Fastighet och Lokalvård"

    if contains("kombitjänst"):
        return "Fastighet och Lokalvård"

    if contains("hallansvarig"):
        return "Kultur och Fritid"

    if contains("gode man"):
        return "Socialt arbete och Stöd"

    if contains("ärendehandledare"):
        return "Ekonomi och Administration"

    if contains("sektionsledare"):
        if contains("kost"):
            return "Fastighet och Lokalvård"
        return "Ekonomi och Administration"

    if contains("teamledare"):
        if contains("it", "afärsstöd"):
            return "IT och Digitalisering"
        if contains("trafik"):
            return "Transport och Trafikplanering"
        if contains("vård", "omsorg", "sjuksköterska"):
            return "Vård och Omsorg"
        return "Ekonomi och Administration"

    if contains("senior") and not contains("biståndshandläggare"):
        # Senior + roll → roll
        if contains("planteknik", "planarkitekt"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("hr-konsult", "hr-"):
            return "HR och Personal"
        if contains("förrättnings", "lantmätare", "markingenjör"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("socialsekreterare"):
            return "Socialt arbete och Stöd"
        if contains("upphandlare"):
            return "Upphandling och Inköp"
        if contains("rörnätstekniker"):
            return "Samhällsbyggnad och Infrastruktur"
        return "Ekonomi och Administration"

    if contains("biträdande") and "chef" in tl:
        # Biträdande + chef
        if contains("vård", "omsorg", "hälso", "sjuksköterska", "hemtjänst"):
            return "Vård och Omsorg"
        if contains("förskola", "skola", "utbildning", "rektor"):
            return "Utbildning och Pedagogik"
        if contains("samhällsbyggnad", "teknik"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("region", "förvaltning", "stabs", "stads", "myndighets",
                    "sjukvård", "direktör", "kommundirektör"):
            return "Ekonomi och Administration"
        return "Ekonomi och Administration"

    # Specialisttitlar
    if tl.startswith("specialist "):
        inner = tl[11:]
        if "hr" in inner or "personal" in inner:
            return "HR och Personal"
        if "it" in inner or "infrastruktur" in inner:
            return "IT och Digitalisering"
        if "informationssäkerhet" in inner:
            return "IT och Digitalisering"
        if "hållbarhet" in inner:
            return "Miljö och Naturvård"
        if "kvalitet" in inner or "internkontroll" in inner:
            return "Revision och Tillsyn"
        if "mark" in inner or "exploatering" in inner:
            return "Samhällsbyggnad och Infrastruktur"
        if "trafikplanering" in inner:
            return "Transport och Trafikplanering"
        if "kommunikation" in inner:
            return "Kommunikation och Medborgarkontakt"
        if "fastighetsförvaltning" in inner:
            return "Fastighet och Lokalvård"
        if "administration" in inner:
            return "Ekonomi och Administration"
        if "förändringsledning" in inner:
            return "Projektledning och Utvecklingsarbete"
        if "krisberedskap" in inner:
            return "Juridik och Säkerhet"
        return "Ekonomi och Administration"

    # Konsulent generell
    if contains("konsulent"):
        if contains("vård", "rehab", "hjälpmedel", "syn", "hörsel"):
            return "Vård och Omsorg"
        if contains("familj", "familjestöd", "familjehem"):
            return "Socialt arbete och Stöd"
        if contains("bibliotek", "hemslöjd"):
            return "Kultur och Fritid"
        if contains("näringsliv", "affärs"):
            return "Ekonomi och Administration"
        if contains("personalklubb"):
            return "HR och Personal"
        if contains("integration", "flykt"):
            return "Invandring, Integration och Mångfald"
        if contains("kostterapeut", "allergikonsulent"):
            return "Vård och Omsorg"
        if contains("handikappomsorg", "funktions"):
            return "Socialt arbete och Stöd"
        if contains("folkhälsa"):
            return "Folkhälsa och Hälsofrämjande arbete"
        if contains("naturvård"):
            return "Miljö och Naturvård"
        return "Ekonomi och Administration"

    if contains("internkonsult"):
        return "Ekonomi och Administration"

    if contains("samverkanschef", "samverkanskoordinator",
                "samverkansledare", "samverkansutvecklare"):
        return "Projektledning och Utvecklingsarbete"

    if contains("miljöskyddschef", "miljöskyddsinspektör"):
        return "Miljö och Naturvård"

    if contains("naturbruksarbetare"):
        return "Miljö och Naturvård"

    if contains("kolonifövaltare", "koloniförvaltare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("utemiljöarbetare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("stensättare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("brygga", "hamnarbetare", "hamnmästare"):
        return "Transport och Trafikplanering"

    if contains("liftskötare", "liftvärd"):
        return "Kultur och Fritid"

    if contains("volontärsamordnare"):
        return "Socialt arbete och Stöd"

    if contains("frivilligsamordnare"):
        return "Socialt arbete och Stöd"

    if contains("kamratstödjare"):
        return "Socialt arbete och Stöd"

    if contains("mentorskapsp", "mentor"):
        if contains("studie", "elev", "ungdom"):
            return "Utbildning och Pedagogik"
        return "Socialt arbete och Stöd"

    if contains("ungdoms"):
        if contains("bibliotekarie"):
            return "Kultur och Fritid"
        if contains("kultursam"):
            return "Kultur och Fritid"
        return "Kultur och Fritid"

    if contains("vuxendövtolk"):
        return "Invandring, Integration och Mångfald"

    if contains("samtalsgrupp"):
        return "Socialt arbete och Stöd"

    if contains("omvärldsstrateg"):
        return "Ekonomi och Administration"

    if contains("landsbygdssamordnare", "landsbygdsstrateg",
                "landsbygdsutvecklare"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("campus"):
        return "Utbildning och Pedagogik"

    if contains("ung kommunutvecklare"):
        return "Ekonomi och Administration"

    if contains("centrumutvecklare", "centrumvärd"):
        return "Ekonomi och Administration"

    if contains("skogsförvaltare", "skogsmästare", "skogsansvarig",
                "skogsarbetare", "skogstekniker", "skogssamordnare",
                "skogsvårdare"):
        return "Miljö och Naturvård"

    if contains("produktionschef", "produktionsledare", "produktionsplanerare",
                "produktionssamordnare", "produktionsassistent"):
        if contains("kök", "mat", "centralkök"):
            return "Fastighet och Lokalvård"
        if contains("scen", "musik", "film"):
            return "Kultur och Fritid"
        return "Projektledning och Utvecklingsarbete"

    if contains("programansvarig", "programchef", "programlagledare",
                "programledare", "programrektor", "programsamordnare",
                "programsekreterare", "programtekniker", "programvärd"):
        if contains("rektor"):
            return "Utbildning och Pedagogik"
        if contains("tv", "radio", "media"):
            return "Kommunikation och Medborgarkontakt"
        return "Ekonomi och Administration"

    if contains("logistikassistent", "logistiker", "logistikledare"):
        return "Transport och Trafikplanering"

    if contains("pianolärar", "pianopedagog", "fiolpedagog",
                "cellopedagog", "flöjtpedagog", "slagverkslärare",
                "slagverkspedagog", "instrumentalpedagog", "träblåspedagog"):
        return "Kultur och Fritid"

    if contains("musikterapeut"):
        return "Vård och Omsorg"

    if contains("sånglärare", "sångpedagog", "sångare"):
        return "Kultur och Fritid"

    if contains("rytmiklärare", "rytmikpedagog"):
        return "Kultur och Fritid"

    if contains("hörseltekniker", "hörselvårdstekniker", "ögonprotetiker"):
        return "Vård och Omsorg"

    if contains("syn- och hörselombud"):
        return "Vård och Omsorg"

    if contains("terapiassistent", "terapibiträde", "terapiinstruktör",
                "terapeut"):
        if contains("musik"):
            return "Vård och Omsorg"
        if contains("massage", "massage"):
            return "Vård och Omsorg"
        if contains("rehab", "arbets", "beteende", "yrkes"):
            return "Vård och Omsorg"
        return "Vård och Omsorg"

    if contains("välfärdsteknikansvarig", "välfärdstekniker",
                "välfärdsutvecklare"):
        return "IT och Digitalisering"

    if contains("träffpunktansvarig", "träffpunktsamordnare",
                "träffpunktsvärd", "träffpunktsutvecklare"):
        return "Socialt arbete och Stöd"

    if contains("fixare", "fixartjänst"):
        return "Fastighet och Lokalvård"

    if contains("möjliggörare"):
        return "Socialt arbete och Stöd"

    if contains("vuxenbehandlare"):
        return "Socialt arbete och Stöd"

    if contains("öppenvårdsbehandlare"):
        return "Vård och Omsorg"

    if contains("psykiatrihandläggare", "psykiatrisamordnare"):
        return "Vård och Omsorg"

    if contains("psykiatrisjuksköterska"):
        return "Vård och Omsorg"

    if contains("narkotikasamordnare"):
        return "Socialt arbete och Stöd"

    if contains("drogrådgivare", "drogterapeut", "drogsamordnare",
                "drogförebyggare"):
        return "Socialt arbete och Stöd"

    if contains("tandvårdsbiträde", "tandvårdsdirektör", "tandvårdsstrateg"):
        return "Vård och Omsorg"

    if contains("hörseltekniker"):
        return "Vård och Omsorg"

    if contains("uppföljningssamordnare", "uppföljningsansvarig"):
        return "Ekonomi och Administration"

    if contains("klinikadministratör", "klinikassistent",
                "kliniksamordnare", "kliniksekreterare"):
        return "Vård och Omsorg"

    if contains("naturvägledare"):
        return "Miljö och Naturvård"

    if contains("fotoarkivarie"):
        return "Kultur och Fritid"

    if contains("fotoassistent", "fotograf", "fotografassistent"):
        return "Kommunikation och Medborgarkontakt"

    if contains("designare", "grafiker"):
        return "Kommunikation och Medborgarkontakt"

    if contains("utskottshandläggare", "utskottssekreterare"):
        return "Ekonomi och Administration"

    if contains("röstmottagare"):
        return "Juridik och Säkerhet"

    if contains("studerande assistent"):
        return "Utbildning och Pedagogik"

    if contains("studentambassadör", "studentmedarbetare",
                "studentsamordnare", "studentstadssamordnare"):
        return "Utbildning och Pedagogik"

    if contains("vfu-samordnare"):
        return "Utbildning och Pedagogik"

    if contains("vns-medarbetare"):
        return "Vård och Omsorg"

    if contains("lotterikontrollant"):
        return "Juridik och Säkerhet"

    if contains("vigselsvärd", "vigselvärd"):
        return "Politisk ledning och Stöd"

    if contains("verksamhetsvaktmästare"):
        return "Fastighet och Lokalvård"

    if contains("skolvaktmästare"):
        return "Fastighet och Lokalvård"

    if contains("delfrågor"):
        return "Ekonomi och Administration"

    if contains("åtgärds"):
        return "Ekonomi och Administration"

    if contains("grönyta", "trädgård"):
        return "Samhällsbyggnad och Infrastruktur"

    if contains("brandsk"):
        if contains("handläggare", "samordnare"):
            return "Juridik och Säkerhet"
        return "Brand och Räddningstjänst"

    if contains("räddningsvärn", "räddnvärnsman"):
        return "Brand och Räddningstjänst"

    if contains("insatsledare"):
        return "Brand och Räddningstjänst"

    if contains("inre befäl"):
        return "Brand och Räddningstjänst"

    if contains("yttre befäl"):
        return "Brand och Räddningstjänst"

    if contains("kårchef"):
        return "Brand och Räddningstjänst"

    if contains("rustmästare"):
        return "Fastighet och Lokalvård"

    if contains("stallförman"):
        return "Fastighet och Lokalvård"

    if contains("hästskötare"):
        return "Miljö och Naturvård"

    if contains("campingvärd", "campvärd"):
        return "Kultur och Fritid"

    if contains("gästhamnsvärd"):
        return "Kultur och Fritid"

    if contains("turistvärd"):
        return "Kultur och Fritid"

    if contains("pendling"):
        return "Transport och Trafikplanering"

    if contains("städ") or contains("lokalvård"):
        return "Fastighet och Lokalvård"

    if contains("kök") or contains("kokersk") or contains("måltid"):
        return "Fastighet och Lokalvård"

    if contains("vaktmästare") or contains("fastighetsskötare"):
        return "Fastighet och Lokalvård"

    if contains("hantverkare", "reparatör", "snickare", "elektriker"):
        return "Fastighet och Lokalvård"

    # ----------------------------------------------------------------
    # RESIDUAL: Fallback baserat på vanliga mönster
    # ----------------------------------------------------------------
    if contains("strateg"):
        if contains("kommunikations"):
            return "Kommunikation och Medborgarkontakt"
        if contains("säkerhet", "trygghet", "beredskap"):
            return "Juridik och Säkerhet"
        if contains("energi"):
            return "Energi och Klimat"
        if contains("klimat"):
            return "Miljö och Naturvård"
        if contains("trafikstrateg"):
            return "Transport och Trafikplanering"
        if contains("it-strateg"):
            return "IT och Digitalisering"
        if contains("hr-strateg"):
            return "HR och Personal"
        if contains("folkhälsostrateg"):
            return "Folkhälsa och Hälsofrämjande arbete"
        if contains("inköpsstrateg", "upphandlings"):
            return "Upphandling och Inköp"
        if contains("planstrateg"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("miljöstrateg"):
            return "Miljö och Naturvård"
        if contains("samhällsstrateg"):
            return "Samhällsbyggnad och Infrastruktur"
        if contains("landsbygds"):
            return "Samhällsbyggnad och Infrastruktur"
        return "Ekonomi och Administration"

    if contains("samordnare"):
        return "Ekonomi och Administration"

    if contains("chef"):
        return "Ekonomi och Administration"

    if contains("direktör"):
        return "Ekonomi och Administration"

    # Slutligt fallback
    return "Ekonomi och Administration"


def main():
    input_path = "/tmp/titles_for_classification.json"
    output_path = "/Users/patriklarsson/Desktop/offentligaloner/pipeline/category_proposals.json"

    with open(input_path) as f:
        data = json.load(f)

    results = {}
    for item in data:
        tid = str(item["id"])
        title = item["title"]
        cat = classify(title)
        results[tid] = cat

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Klassificerade {len(results)} titlar")

    # Statistik
    counter = Counter(results.values())
    print("\nKategorifördelning (fallande):")
    for cat, count in counter.most_common():
        print(f"  {count:5d}  {cat}")

    # Kontroll: alla IDs med
    ids_input = {str(d["id"]) for d in data}
    ids_output = set(results.keys())
    missing = ids_input - ids_output
    if missing:
        print(f"\nSAKNAS: {len(missing)} titlar: {sorted(missing)[:10]}")
    else:
        print(f"\nAlla {len(results)} titlar klassificerade.")


if __name__ == "__main__":
    main()
