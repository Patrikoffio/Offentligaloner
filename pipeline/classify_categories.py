#!/usr/bin/env python3
"""
Regelbaserad klassificering av generalized_titles i 23 kategorier.

Hämtar alla titlar från DB, klassificerar med nyckelord och domänkunskap,
sparar resultaten i pipeline/category_proposals.json.

Användning:
  python pipeline/classify_categories.py            # kör klassning, spara förslag
  python pipeline/classify_categories.py --apply    # skriv godkänt resultat till DB
  python pipeline/classify_categories.py --sample   # visa 40 slumpade + ny fördelning
"""

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

import psycopg2

PROPOSALS_FILE = Path(__file__).parent / "category_proposals.json"

CATEGORIES = [
    "Avfall och Återvinning",
    "Brand och Räddningstjänst",
    "Ekonomi och Administration",
    "Energi och Klimat",
    "Fastighet och Lokalvård",
    "Forskning och Utveckling",
    "HR och Personal",
    "Invandring, Integration och Mångfald",
    "IT och Digitalisering",
    "Juridik och Säkerhet",
    "Kommunikation och Medborgarkontakt",
    "Kommunövergripande och Strategiska funktioner",
    "Kultur och Fritid",
    "Miljö och Naturvård",
    "Politisk ledning och Stöd",
    "Projektledning och Utvecklingsarbete",
    "Revision och Tillsyn",
    "Samhällsbyggnad och Infrastruktur",
    "Socialt arbete och Stöd",
    "Transport och Trafikplanering",
    "Upphandling och Inköp",
    "Utbildning och Pedagogik",
    "Vård och Omsorg",
]


def normalize(title: str) -> str:
    return title.lower().strip()


def classify(title: str) -> str:  # noqa: C901  (komplex funktion avsiktligt)
    t = normalize(title)

    # ------------------------------------------------------------------ #
    # 1. VÅRD OCH OMSORG
    # ------------------------------------------------------------------ #
    vard_keywords = [
        "sjukskötersk", "underskötersk", "sjukgymnast",
        "fysioterapeut", "arbetsterapeut", "dietist", "logoped",
        "psykolog", "psykiater", "psykiatri",
        "barnmorsk", "barnläkare", "tandläkare",
        "tandhygienist", "tandskötersk", "tandtekniker", "optiker",
        "ortoptist", "biomedicinsk", "röntgen", "apotekare", "farmaceut",
        "receptarie", "ögonläkare", "kirurg", "anestesi", "intensivvård",
        "geriatrik", "geriatrisk",
        "medicinsk", "medicin",
        "vårdbiträde", "vårdare", "vårdpedagog",
        "vårdpersonal", "vårdutvecklare", "vårdadministratör",
        "vårdenhetschef", "vårdcentralchef", "vårdinformatör",
        "vård- och omsorgs",
        "omsorgspedagog", "omsorgshandläggare",
        "omsorgsutvecklare", "omsorgssamordnare", "omsorgschef",
        "enhetschef (vård", "enhetschef (lss", "enhetschef (hemtjänst",
        "enhetschef (äldreomsorg", "enhetschef (stöd/omsorg",
        "enhetschef (hälso", "enhetschef (handikappomsorg",
        "enhetschef (biträdande, vård",
        "enhetschef (mar", "enhetschef (mas",
        "enhetschef (kost/lokal",
        "enhetschef (lokalvård",
        "patientkoordinator", "patientansvarig", "patientsamordnare",
        "sjukresehantläggare", "sjukresehandläggare",
        "hemtjänstassistent", "hemtjänstchef", "hemtjänstsamordnare",
        "hemtjänstpersonal", "hemtjänst", "hemsjukvård",
        "nattpersonal", "nattpatrull", "nattassistent",
        "personlig assistent", "personligassistent", "lss-assistent",
        "lss-",
        "daglig verksamhet", "dagverksamhet", "dagcentrum",
        "boendestödjare", "boendeassistent", "boendechef",
        "boendepedagog", "boendekonsulent",
        "demens", "demensvård", "äldreomsorg", "äldrevård",
        "äldreassistent", "äldreomsorgs", "äldrevårds",
        "stödassistent", "stödpedagog",
        "handikapp", "funktionsnedsättning", "funktionshinder",
        "habilitering", "habiliteringsassistent",
        "sjukhus", "klinik", "poliklinik",
        "avdelningsskötersk",
        "primärvård", "primärvårds",
        "distriktsskötersk", "distriktsläkare", "husläkare", "familjeläkare",
        "akutmottagning", "akutsjukvård",
        "provtagning", "blodprovtagning",
        "laboratorieassistent",
        "cytologi", "histologi", "patolog",
        "sjukhusfysiker", "medicinteknisk",
        "audionom", "hörselvård",
        "palliativ", "hospice",
        "aktiveringssamordnare (vård",
        "anhörigkonsulent", "anhörigrådgivare",
        "anhörigsamordnare", "anhörigstödjare", "anhörigombud",
        "äldrekonsulent", "äldrelots", "äldresamordnare", "äldrestödjare",
        "äldreombudsman",
        "aktiverare", "aktiveringsbiträde", "aktiveringsledare",
        "aktivitetssamordnare", "aktivitetsstödjare",
        "anaplastolog",
        "aktivitets- och servicevärd", "aktivitetsvärd",
        "aktivitetshandledare",
        "allergikonsulent",
        "alkohol- och drogbehandlare", "alkohol- och drogrådgivare",
        "alkohol- och drogsamordnare", "alkohol- och drogterapeut",
        "alkoholrådgivare", "alkoholterapeut",
        "andt-samordnare",
        "medicinansvarig",
        "medicinskt ansvarig",
        " mas ", "mas/mar", " mar ",
        "anläggningsarbetare (va)",
        "rehabilitering", "rehab",
        "äldrekonsulent", "äldrelots",
        "1:e sjukhusfysiker", "förste sjukhusfysiker",
        # Specialistsjuksköterskor och tandskötare (suffix-mönster)
        # OBS: "skötersk" täcker sjuksköterska/tandsköterska men INTE badskötare/anläggningsskötare
        # Dessa hanteras via regex nedan
        # Behandlingspersonal inom vård/omsorg/psykiatri (INTE socialt arbete)
        "behandlingsassistent", "behandlingspedagog", "behandlingspersonal",
        "behandlingsbiträde", "behandlingsledare", "behandlingssamordnare",
        "behandlingssekreterare", "behandlingscoach", "behandlingsansvarig",
        # Elevhälsa (medicinsk del)
        # Anhörigstrateg
        "anhörigstrateg",
        # Övriga vård
        "neonatal", "onkolog", "kardiolog", "neuro", "ortoped",
        "kemo", "cytostati", "operationssjuk", "narkossjuk",
        "iva-",
        "psykoterapeut",
        "terapeut",
        "kurator",
    ]
    for kw in vard_keywords:
        if kw in t:
            return "Vård och Omsorg"

    # Läkare
    if "läkare" in t or "läkar" in t:
        return "Vård och Omsorg"

    # Sköterskor: fånga *sköterska/*skötersk men INTE bad-, anläggnings-, vagn-skötare
    # Positiv lista på prefix som ger vård
    vard_skotare_prefix = [
        "sjuk", "under", "tand", "skol", "special", "distrikt", "barnsjuk",
        "avdelnings", "operations", "narkos", "intensiv", "akut", "äldre",
        "kardiologi", "onkologi", "geriatrik", "psykiatri", "ögon",
        "stomis", "iva", "neuro",
    ]
    if "skötersk" in t:
        for pfx in vard_skotare_prefix:
            if pfx in t:
                return "Vård och Omsorg"
        # Om "skötersk" finns men ingen vård-prefix: troligen vård ändå (t.ex. "Sköterska")
        if t.strip().startswith("skötersk") or "skötersk" in t.split("(")[0]:
            return "Vård och Omsorg"

    # Skötare: bara vård-skötare (inte bad-, anläggnings-)
    vard_skotare_full = ["barnskötare", "djursjukskötare"]
    for kw in vard_skotare_full:
        if kw in t:
            return "Vård och Omsorg"

    # ------------------------------------------------------------------ #
    # 2. UTBILDNING OCH PEDAGOGIK
    # ------------------------------------------------------------------ #
    utb_keywords = [
        "lärare", "lärar",
        "förskollärare", "förskolepedagog",
        "skolskötersk", "skolpsykolog", "skolkurator", "skolläkare",
        "skolassistent", "skolvakt", "skolvärd", "skolchef",
        "rektor", "biträdande rektor", "skolledare",
        "pedagogisk", "pedagoger",
        "barnskötare", "barnpedagog", "barnomsorgs",
        "förskola", "fritidspedagog", "fritidsassistent",
        "fritidshem",
        "elevassistent", "elevhälsa", "elevhälso", "elevstödjare", "elevcoach",
        "studie- och yrkesvägledare", "yrkesvägledare", "studievägledare",
        "utbildningschef", "utbildningsadministratör",
        "utbildningssamordnare",
        "utbildningsledare", "utbildningsutvecklare",
        "utbildningsplanerare",
        "lektör", "adjunkt",
        "specialpedagog", "speciallärare", "talpedagog",
        "matematikutvecklare",
        "skolbibliotekarie",
        "yrkeslärare", "yrkesinstruktör",
        "modersmålslärare", "modersmålsstödjare",
        "studiehandledare",
        "grundskolelärare", "gymnasielärare", "mellanstadielärare",
        "lågstadielärare", "högstadielärare",
        "idrottslärare", "slöjdlärare", "musiklärare",
        "dagbarnvårdare", "familjedaghem",
        "kursledare", "kursinstruktör",
        "vuxenutbildning", "komvux",
        "sfi-lärare", "sfi lärare", "svenska för invandrare",
        "särskolelärare", "grundsärskola", "gymnasiesärskola",
        "skolintendent",
        "måltidspedagog",
        "barnombudsman",
        "barnkultur",
        "pedagog",
    ]
    for kw in utb_keywords:
        if kw in t:
            return "Utbildning och Pedagogik"

    # ------------------------------------------------------------------ #
    # 3. SOCIALT ARBETE OCH STÖD
    # ------------------------------------------------------------------ #
    social_keywords = [
        "socialsekreterare", "socialrådgivare", "socialhandläggare",
        "socialkonsulent", "socialpedagog", "socialterapeut",
        "social sekreterare", "social handläggare",
        "socialtjänst", "socialförvaltning", "socialchef",
        "barnhandläggare", "barnsekreterare", "barnutredare",
        "familjebehandlare", "familjerådgivare", "familjeterapeu",
        "familjepedagog", "familjesamordnare", "familjecoach",
        "familjehemssekreterare", "familjehemskonsulent",
        "familjehem", "familjevård",
        "fältassistent", "fältarbetare", "fältsekreterare",
        "fältenhetschef",
        "biståndsbedömare", "biståndshandläggare",
        "biståndssekreterare", "biståndssamordnare",
        "ekonomiskt bistånd", "försörjningsstöd",
        "arbetsmarknad",
        "arbetsmarknadshandläggare",
        "arbetsmarknadsenhet", "arbetsmarknadssekreterare",
        "jobbcoach", "arbetslivscoach", "karriärcoach",
        "missbruk", "beroendevård", "beroendekonsulent",
        "nykterhetsvård", "narkotika",
        "ungdomshandläggare", "ungdomsstödjare", "ungdomscoach",
        "ungdomssekreterare", "ungdomsutvecklare",
        "barn och ungdom", "barn- och ungdoms",
        "kontaktperson", "kontaktfamilj",
        "lss-handläggare", "lss handläggare",
        "god man",
        # Förvaltare = legal förvaltare (inte fastighetsförvaltare)
        "förmyndare",
        "gode man",
        "integrationspedagog", "integrationshandläggare",
        "etableringshandläggare", "etableringslots",
        "flyktinghandläggare",
        "ensamkommande",
        "mottagningssekreterare",
        "social omsorg",
        "brottsförebyggande",
        "budget- och skuldrådgivare", "skuldrådgivare",
        "skuldsanering", "konsumentrådgivare",
        "stödarbetare", "stödsamordnare",
        "hem- och konsumentkunskap",
        "anhörig- och frivilligsamordnare",
        # Behandlare inom socialt arbete/öppenvård
        "behandlare", "vuxenbehandlare", "barnbehandlare",
        "öppenvårdsbehandlare", "missbruksbehandlare", "ungdomsbehandlare",
        "familjebehandlare", "socialarbetare",
        # Case manager, familjeassistent
        "case manager",
        "familjeassistent",
        "boendepersonal",
        # Socionomtitlar
        "socionom",
        "socialt ansvarig",
        "sas ",
        "familjerättssekreterare", "familjerätt",
        "överförmyndar",
        # Folkhälsa hör hit
        "folkhälsostrateg", "folkhälsosamordnare", "folkhälsokonsulent",
        "folkhälsohandläggare", "folkhälsoutvecklare", "folkhälsoansvarig",
        "arbetscoach", "arbetsmarknadskonsulent",
        "sysselsättningshandläggare",
        "familjestödsassistent", "familjestöd",
    ]
    for kw in social_keywords:
        if kw in t:
            return "Socialt arbete och Stöd"

    # ------------------------------------------------------------------ #
    # 4. EKONOMI OCH ADMINISTRATION
    # ------------------------------------------------------------------ #
    ekon_keywords = [
        "ekonom", "ekonomiassistent", "ekonomibiträde", "ekonomichef",
        "ekonomicontroller", "ekonomihandläggare", "ekonomisamordnare",
        "ekonomikonsult", "ekonomirådgivare",
        "redovisningsekonom", "redovisningschef", "redovisningsassistent",
        "redovisningsansvarig", "redovisning",
        "controller",
        "finanschef", "finanskontroller",
        "löneadministratör", "lönehandläggare", "lönespecialist",
        "lönekonsult", "löneekonom", "löneassistent",
        "kassör", "kassakontrollant",
        "budgetekonom", "budgetsamordnare",
        "bokförare", "bokföring",
        "assistent", "administratör",
        "sekreterare", "nämndsekreterare", "kommunsekreterare",
        "förvaltningssekreterare",
        "diarie", "registrator", "diarieföring",
        "arkivarie", "arkivassistent", "arkivhandläggare",
        "arkivchef", "arkivsamordnare",
        "kontorsassistent", "kontorspersonal", "kansliassistent",
        "kontorschef", "kanslipersonal",
        "kanslisekreterare",
        "fakturering", "fakturahantering",
        "inköpsassistent", "inköpsadministratör",
        "receptionist", "reception",
        "kundtjänst", "servicehandläggare",
        "ärendehandläggare",
        "statistiker",
        "utredare",
        "analytiker",
        "verksamhetscontroller",
        "taxehandläggare", "avgiftshandläggare",
        "administrativ",
    ]
    for kw in ekon_keywords:
        if kw in t:
            return "Ekonomi och Administration"

    # ------------------------------------------------------------------ #
    # 5. HR OCH PERSONAL
    # ------------------------------------------------------------------ #
    hr_keywords = [
        "personalchef", "personalansvarig", "personaladministratör",
        "personalhandläggare", "personalsamordnare", "personalspecialist",
        "personalstrateg", "personalkonsulent", "personalutvecklare",
        "personalsekreterare", "personalrådgivare",
        "hr-chef", "hr-partner", "hr-specialist", "hr-strateg",
        "hr-konsult", "hr-handläggare", "hr-samordnare", "hr-koordinator",
        "hr-administratör", "hr-assistent", "hr-analytiker",
        "hr-direktör", "hr-generalist",
        "hr chef", "hr partner", "hr specialist", "hr strateg",
        "lönekoordinator",
        "rekryterar", "rekryterings",
        "rekryteringsansvarig", "rekryteringsspecialist",
        "bemanningschef", "bemanningsplanerare", "bemanningssamordnare",
        "arbetsgivar", "arbetsrätts",
        "kompetensförsörjning", "kompetensutveckling",
        "medarbetarundersökning",
        "förhandlare", "förhandlings",
        "arbetsmiljö", "företagshälsovård",
        "hälsoinspiratör", "friskvård",
        "introduktionsansvarig",
    ]
    for kw in hr_keywords:
        if kw in t:
            return "HR och Personal"

    # ------------------------------------------------------------------ #
    # 6. IT OCH DIGITALISERING
    # ------------------------------------------------------------------ #
    it_keywords = [
        "it-chef", "it-samordnare", "it-strateg", "it-specialist",
        "it-tekniker", "it-arkitekt", "it-konsult", "it-koordinator",
        "it-handläggare", "it-projektledare", "it-drifttekniker",
        "it-ansvarig", "it-support", "it-säkerhet",
        "it chef", "it samordnare", "it strateg", "it specialist",
        "systemförvaltare", "systemutvecklare", "systemadministratör",
        "systemanalytiker", "systemarkitekt", "systemdesigner",
        "systemtekniker", "systemintegratör",
        "programmerare", "programutvecklare",
        "webmaster", "webbansvarig", "webbadministratör",
        "webbutvecklare", "webbdesigner", "webbproducent",
        "databasadministratör", "databasansvarig",
        "nätverkstekniker", "nätverksadministratör",
        "helpdesk", "itsupport", "servicedesk",
        "digitaliserings",
        "digitaliseringsstrateg",
        "digitaliseringsansvarig", "digitaliseringsledare",
        "digitaliseringssamordnare",
        "informationssäkerhet", "cybersäkerhet",
        "mjukvaruutvecklare", "applikationsförvaltare",
        "gis-samordnare", "gis-tekniker", "gis-analytiker",
        "gis samordnare", "gis tekniker", "gis analytiker",
        "adb-samordnare", "adb-tekniker",
        "kravanalytiker", "testledare", "testare",
        "3d-grafiker",
        "ux-designer", "ux-specialist",
        "supporttekniker",
        "it och digitaliser",
        "ansvarig digi kanaler",
        "drifttekniker",
        "tekniker (it", "systemtekniker (it",
        "drifttekniker (it", "arbetsplatstekniker (it",
        "digitaliseringstekniker",
        "it-tekniker", "it-infrastruktur",
    ]
    for kw in it_keywords:
        if kw in t:
            return "IT och Digitalisering"

    # ------------------------------------------------------------------ #
    # 7. FASTIGHET OCH LOKALVÅRD
    # ------------------------------------------------------------------ #
    fastighet_keywords = [
        "fastighets",
        "fastighetschef", "fastighetsansvarig",
        "fastighetsförvaltare", "fastighetssamordnare",
        "fastighetshandläggare", "fastighetsskötare",
        "fastighetstekniker", "fastighetsvakt", "fastighetsingenjör",
        "vaktmästare", "lokalvårdare", "lokalvård",
        "städ", "städare", "städerskor", "städledare",
        "städansvarig", "städpersonal", "städservice",
        "rengörings",
        "servicebiträde",
        "kock", "kokerska", "köksbiträde", "köksmästare",
        "kökspersonal", "kökschef", "köksledare", "köksansvarig",
        "köksskötare",
        "måltidspersonal", "måltidsansvarig",
        "matvärd", "mathantverkare", "mathantverkschef",
        "restaurangchef", "restaurangpersonal",
        "servitör", "servitris",
        "husmor",
        "lokalsamordnare",
        "lokalbokning",
        "konferensvärd", "konsertvärd",
        "bagare", "konditor", "bageri",
        "internservice", "intern service",
        "reparatör", "rörläggare", "snickare", "elektriker",
        "vvs-tekniker", "ventilationstekniker",
        "installationstekniker",
        "trädgårdsarbetare", "trädgårdsmästare",
        "cafeteria", "café", "kafeteria",
        "tryckare",
        "servicevärd",
        "lokalansvarig",
        "1:e kock", "förste kock",
        "1:e/förste kock",
        "serveringsbiträde", "serveringspersonal",
    ]
    for kw in fastighet_keywords:
        if kw in t:
            return "Fastighet och Lokalvård"

    # ------------------------------------------------------------------ #
    # 8. SAMHÄLLSBYGGNAD OCH INFRASTRUKTUR
    # ------------------------------------------------------------------ #
    samhall_keywords = [
        "stadsplanerare", "stadsarkitekt", "stadsbyggnad",
        "stadsbyggnadschef",
        "bygglovshandläggare", "bygglovschef", "bygglovsansvarig",
        "bygginspektör", "byggnadsinspektör",
        "planarkitekt", "planhandläggare", "planstrateg",
        "planchef", "planeringschef",
        "lantmätare", "lantmäteri",
        "mätningsingenjör", "mättekniker", "geodet",
        "kartingenjör", "karthandläggare", "kartassistent",
        "gatuingenjör", "gatuplanerare", "gaturenhållare",
        "gatuansvarig", "gatuchef",
        "parkingenjör", "parkchef", "parkplanerare",
        "park och natur",
        "mark- och exploatering", "exploateringshandläggare",
        "exploateringsingenjör", "exploateringschef",
        "infrastruktur", "infrastrukturplanerare",
        "va-tekniker", "va-ingenjör", "va-chef", "va-planerare",
        "vatten och avlopp",
        "gata och park",
        "anläggningschef", "anläggningssamordnare",
        "anläggningstekniker", "anläggningsutvecklare",
        "anläggningsansvarig",
        "anläggningsingenjör",
        "hamn", "hamnchef", "hamnfogde",
        "broingenjör",
        "beläggningsingenjör",
        "kart och gis",
        "geodesi",
        "teknisk chef",
        "teknikchef",
        "kommuningenjör",
        "byggprojektledare",
        "projekteringsledare",
        "besiktningsman",
        "nätchef",
        "airport officer",
        "anläggningsarbetare",
        "anläggnings- och parkarbetare",
        "anläggningsreparatör",
        "1:e rörläggare", "förste rörläggare",
        "mark och exploatering",
        "samhällsbyggnadschef", "miljö- och samhällsbyggnadschef",
        "sektorschef (miljö", "sektorschef (samhäll",
        "planeringsingenjör",
        "park- och trädgårdsarbetare", "park- och skogsarbetare",
        "park- och naturingenjör",
        "mark- och naturvård",
    ]
    for kw in samhall_keywords:
        if kw in t:
            return "Samhällsbyggnad och Infrastruktur"

    # ------------------------------------------------------------------ #
    # 9. MILJÖ OCH NATURVÅRD
    # ------------------------------------------------------------------ #
    miljo_keywords = [
        "miljöchef", "miljöhandläggare", "miljöinspektör",
        "miljösamordnare",
        "miljöstrateg", "miljökonsult", "miljöspecialist",
        "miljöingenjör",
        "miljökoordinator", "miljöansvarig", "miljökommunikatör",
        "naturvård", "naturvårdare", "naturvårdshandläggare",
        "ekolog", "biolog", "naturbiolog",
        "livsmedelsinspektör", "livsmedelshandläggare",
        "livsmedelskontrollant",
        "hälsoskyddsinspektör", "hälsoskyddshandläggare",
        "djurskyddsinspektör",
        "hållbarhetsstrateg", "hållbarhetsansvarig", "hållbarhetschef",
        "hållbarhetssamordnare", "hållbarhetskommunikatör",
        "vattenskyddshandläggare",
        "markingenjör", "markhandläggare",
        "skogsförvaltare", "skogsvaktare",
        "antikvarie",
        "kemist",
    ]
    for kw in miljo_keywords:
        if kw in t:
            return "Miljö och Naturvård"

    # ------------------------------------------------------------------ #
    # 10. AVFALL OCH ÅTERVINNING
    # ------------------------------------------------------------------ #
    avfall_keywords = [
        "avfallshandläggare", "avfallssamordnare", "avfallschef",
        "avfallsingenjör", "avfallsansvarig", "avfalls",
        "återvinning", "återvinnings",
        "sopbilsförare", "sopförare", "renhållningschaufför",
        "renhållningsarbetare", "renhållnings",
        "deponi", "deponichef",
        "kretslopps",
        "avloppsrenings",
        "sopsorterings",
        "renhållning",
    ]
    for kw in avfall_keywords:
        if kw in t:
            return "Avfall och Återvinning"

    # ------------------------------------------------------------------ #
    # 11. BRAND OCH RÄDDNINGSTJÄNST
    # ------------------------------------------------------------------ #
    brand_keywords = [
        "brandman", "brandmän", "brandmästare", "brandförmän",
        "brandingenjör", "brandchef", "brandmyndighet",
        "räddningstjänst", "räddningschef", "räddningsledare",
        "insatsledare", "insatschef",
        "sotare", "skorstensfejare",
        "beredskapssamordnare",
        "civilskydd",
        "brandskyddsinspektör", "brandskyddshandläggare",
        "olycksförebyggande",
        "räddnings",
        "säkerhets- och beredskap",
        "ambulansdirigent",
        "beredskapshandläggare", "beredskaps- och säkerhetssamordnare",
        "beredskapsstrateg", "beredskapschef", "beredskapsarbetare",
        "beredskapssamordnare",
        "kris- och beredskap", "krisberedskap",
        "trygghets- och beredskapsstrateg",
        "handläggare (beredskap",
        "specialist krisberedskap",
    ]
    for kw in brand_keywords:
        if kw in t:
            return "Brand och Räddningstjänst"

    # ------------------------------------------------------------------ #
    # 12. JURIDIK OCH SÄKERHET
    # ------------------------------------------------------------------ #
    juridik_keywords = [
        "jurist", "juridisk", "rättshandläggare",
        "alkoholhandläggare", "alkoholinspektör",
        "tillståndshandläggare", "tillståndschef",
        "säkerhetschef", "säkerhetshandläggare", "säkerhetssamordnare",
        "säkerhetsstrateg", "säkerhetsansvarig",
        "brottsförebygg",
        "inkasso",
        "upphandlingsjurist",
        "avtalscontroller",
        "ombudsman", "kommunombud",
        "dataskyddsombud", "dataskydd",
        "integritetsskydd",
        "tillsynshandläggare", "tillsynsansvarig",
        "ordningsvakt", "säkerhetsvakt",
        "kriminal",
        "gdpr",
        "stadsjurist", "kommunjurist",
    ]
    for kw in juridik_keywords:
        if kw in t:
            return "Juridik och Säkerhet"

    # ------------------------------------------------------------------ #
    # 13. KOMMUNIKATION OCH MEDBORGARKONTAKT
    # ------------------------------------------------------------------ #
    komm_keywords = [
        "kommunikatör", "kommunikationsansvarig", "kommunikationschef",
        "kommunikationsstrateg", "kommunikationssamordnare",
        "kommunikationskonsult", "kommunikationshandläggare",
        "kommunikationskoordinator",
        "informatör", "informationschef", "informationsansvarig",
        "informationssamordnare", "informationsstrateg",
        "pressekreterare", "pressansvarig", "pressassistent",
        "mediaansvarig", "medieansvarig",
        "webbredaktör", "webbredaktionsansvarig",
        "sociala medier", "socialmedia",
        "kundansvarig", "kundkoordinator",
        "kundcenterchef", "kundcentret",
        "kontaktcenter",
        "medborgar", "medborgarkontakt", "medborgarservice",
        "marknadsförare", "marknadsförings", "marknadschef",
        "marknadskoordinator",
        "pr-ansvarig", "varumärkes",
        "evenemangschef", "evenemang",
        "nyhetsbrev",
        "redaktör", "redaktions",
        "grafisk formgivare", "grafisk designer",
        "fotograf",
        "ansvarig digi kanaler",
        "publik",
    ]
    for kw in komm_keywords:
        if kw in t:
            return "Kommunikation och Medborgarkontakt"

    # ------------------------------------------------------------------ #
    # 14. KULTUR OCH FRITID
    # ------------------------------------------------------------------ #
    kultur_keywords = [
        "bibliotekarie", "biblioteksassistent", "bibliotekschef",
        "bibliotekssamordnare", "biblioteksutvecklare", "bibliotekskonsulent",
        "museum", "museiintendent", "museichef", "museiassistent",
        "kulturchef", "kulturhandläggare", "kultursamordnare",
        "kulturkonsulent", "kulturutvecklare", "kulturassistent",
        "kulturansvarig", "kulturstrateg",
        "kulturpedagog", "kultursekreterare",
        "teater", "teaterpedagog",
        "scentekniker",
        "konserthus", "konsertmästare",
        "musikskola", "kulturskola", "musikpedagog",
        "fritidschef", "fritidssamordnare", "fritidskonsulent",
        "fritidshandläggare", "fritidsansvarig", "fritidsutvecklare",
        "fritidsgård", "fritidsgårdsassistent", "fritidsgårdsled",
        "fritidsledare",
        "idrottschef", "idrottshandläggare", "idrottssamordnare",
        "idrottsansvarig", "idrottskonsulent", "idrottsutvecklare",
        "idrottsinstruktör", "idrottsledare",
        "badhus", "simhall", "simbassäng", "simhallsassistent",
        "simhallsföreståndare", "simlärare", "bassängvakt",
        "simtränare",
        "kultur och fritid",
        "frilufts",
        "parklek", "lekparks",
        "föreningsansvarig", "föreningssamordnare",
        "turism", "turismutvecklare", "turistbyråchef",
        "kongressbyrå",
        "ansvarig konferensvärd",
        "ansvarig konsertvärd",
        "1:e bibl",
        "scen",
        "konstnär",
        "konsthall",
        "fotbollsinstruktör", "fotbollstränare", "fotboll",
        "handbollstränare", "handboll",
        "friidrottsinstruktör",
        "sportinstruktör", "sportkonsulent",
        "aktivitetsledare", "aktivitetsutvecklare",
        "aktivitetsansvarig",
    ]
    for kw in kultur_keywords:
        if kw in t:
            return "Kultur och Fritid"

    # ------------------------------------------------------------------ #
    # 15. TRANSPORT OCH TRAFIKPLANERING
    # ------------------------------------------------------------------ #
    transport_keywords = [
        "trafikplanerare", "trafikingenjör", "trafikhandläggare",
        "trafikchef", "trafiksamordnare", "trafikansvarig",
        "trafikanalytiker", "trafikstrateg",
        "kollektivtrafikansvarig", "kollektivtrafiksamordnare",
        "chaufför", "chauffeur",
        "skolskjuts", "färdtjänst", "sjukresor",
        "bilförare", "transportchef", "transportledare",
        "transportör", "transportsamordnare",
        "logistik", "logistikchef",
        "maskinförare",
        "lastbilsförare",
        "fordonstekniker", "fordonsansvarig",
        "taxiförare",
        "flyg",
        "parkering", "p-vakt", "parkeringsvakt",
        "bussförare",
        "trafikcontroller",
    ]
    for kw in transport_keywords:
        if kw in t:
            return "Transport och Trafikplanering"

    # ------------------------------------------------------------------ #
    # 16. UPPHANDLING OCH INKÖP
    # ------------------------------------------------------------------ #
    upphandling_keywords = [
        "upphandlare", "upphandlingschef", "upphandlingsansvarig",
        "upphandlingssamordnare", "upphandlingsstrateg",
        "upphandlingskonsult", "upphandlingshandläggare",
        "upphandlingskoordinator", "upphandlingsspecialist",
        "inköpschef", "inköpare", "inköpssamordnare",
        "inköpsansvarig", "inköpskoordinator", "inköpsstrateg",
        "kategoriansvarig",
        "avropsssamordnare",
        "avtalscontroller",
    ]
    for kw in upphandling_keywords:
        if kw in t:
            return "Upphandling och Inköp"

    # ------------------------------------------------------------------ #
    # 17. REVISION OCH TILLSYN
    # ------------------------------------------------------------------ #
    revision_keywords = [
        "revisionshandläggare", "revisionsassistent",
        "revisionschef", "revisionsansvarig",
        "intern revisor", "revisorn",
        "kontrollansvarig",
        "granskare",
        "revision",
        "internrevisor",
    ]
    for kw in revision_keywords:
        if kw in t:
            return "Revision och Tillsyn"

    # ------------------------------------------------------------------ #
    # 18. ENERGI OCH KLIMAT
    # ------------------------------------------------------------------ #
    energi_keywords = [
        "energichef", "energiingenjör", "energisamordnare",
        "energihandläggare", "energistrateg", "energiansvarig",
        "energikonsult", "energieffektivisering",
        "energispecialist", "energirådgivare",
        "energi- och klimat",
        "fjärrvärmechef", "fjärrvärme",
        "klimatstrateg", "klimathandläggare",
        "klimatchef",
        "sol- och vindkraft",
        "bioenerg",
        "vattenrening", "vattenverk",
    ]
    for kw in energi_keywords:
        if kw in t:
            return "Energi och Klimat"

    # ------------------------------------------------------------------ #
    # 19. INVANDRING, INTEGRATION OCH MÅNGFALD
    # ------------------------------------------------------------------ #
    integration_keywords = [
        "integrationsansvarig", "integrationschef",
        "integrationsstrateg", "integrationssamordnare",
        "integrationsutvecklare", "integrationskonsulent",
        "mångfaldsstrateg", "mångfaldsansvarig", "mångfaldssamordnare",
        "diskrimineringsansvarig", "diskrimineringskonsulent",
        "flyktingsamordnare", "flyktingkonsulent",
        "mottagningsansvarig", "migrationshandläggare",
        "flyktingmottagare", "flyktinghandledare",
        "etableringsansvarig", "etableringsutvecklare",
    ]
    for kw in integration_keywords:
        if kw in t:
            return "Invandring, Integration och Mångfald"

    # ------------------------------------------------------------------ #
    # 20. PROJEKTLEDNING OCH UTVECKLINGSARBETE
    # ------------------------------------------------------------------ #
    projekt_keywords = [
        "projektledare", "projektchef", "projektsamordnare",
        "projektkoordinator", "projektassistent", "projektansvarig",
        "programledare", "programchef",
        "processledare", "processutvecklare",
        "verksamhetsutvecklare", "verksamhetsstrateg",
        "verksamhetsanalytiker",
        "förändringsledare", "förändringsledning",
        "innovationsansvarig", "innovationschef", "innovationsstrateg",
        "affärsutvecklare", "affärsansvarig",
        "affärsstrateg", "affärsrådgivare",
        "strategisk planerare",
        "analysledare",
    ]
    for kw in projekt_keywords:
        if kw in t:
            return "Projektledning och Utvecklingsarbete"

    # ------------------------------------------------------------------ #
    # 21. FORSKNING OCH UTVECKLING
    # ------------------------------------------------------------------ #
    forskning_keywords = [
        "forskare", "forskning",
        "forskningschef", "forskningssamordnare",
        "doktorand", "postdoktor",
        "laboratorieingenjör", "laborant",
        "metodutvecklare",
        "fou-samordnare", "fou-chef", "fou-",
        "yrkeshygien",
    ]
    for kw in forskning_keywords:
        if kw in t:
            return "Forskning och Utveckling"

    # ------------------------------------------------------------------ #
    # 22. POLITISK LEDNING OCH STÖD
    # ------------------------------------------------------------------ #
    politik_keywords = [
        "politisk sekreterare", "politisk rådgivare",
        "kommunalråd", "landstingsråd", "regionråd",
        "nämndordförande", "nämndsekret",
        "fullmäktige", "fullmäktigesekreterare",
        "politiska",
        "kommunstyrelseordförande",
        "oppositionslandstingsråd",
        "kommunpolitiker",
        "partisekreterare",
        "oppositionsråd",
    ]
    for kw in politik_keywords:
        if kw in t:
            return "Politisk ledning och Stöd"

    # ------------------------------------------------------------------ #
    # 23. KOMMUNÖVERGRIPANDE OCH STRATEGISKA FUNKTIONER (sista utväg)
    # ------------------------------------------------------------------ #
    strat_keywords = [
        "kommundirektör", "kommunchef",
        "tf kommundirektör", "biträdande kommundirektör",
        "stadsdirektör", "regiondirektör",
        "koncernchef",
        "strategisk samordnare",
        "stabschef",
        "direktör",
        "kanslidirektör",
        "förvaltningsledning",
        "övergripande samordnare",
    ]
    for kw in strat_keywords:
        if kw in t:
            return "Kommunövergripande och Strategiska funktioner"

    # ------------------------------------------------------------------ #
    # FALLBACK
    # ------------------------------------------------------------------ #
    # Generiska roller landar i Ekonomi och Administration
    fallback_admin = [
        "chef", "samordnare", "handläggare", "assistent",
        "koordinator", "controller", "planerare",
        "ansvarig", "ledare", "konsulent",
    ]
    for kw in fallback_admin:
        if kw in t:
            return "Ekonomi och Administration"

    return "Ekonomi och Administration"


def fetch_titles(cur) -> list[dict]:
    cur.execute("""
        SELECT id, title, category AS current_category
        FROM generalized_titles
        ORDER BY id
    """)
    return [{"id": r[0], "title": r[1], "current_category": r[2]} for r in cur.fetchall()]


def show_sample(titles: list[dict], proposals: dict[int, str]) -> None:
    print("\n=== 40 slumpade klassificeringsresultat ===\n")
    changed_titles = [
        t for t in titles
        if proposals.get(t["id"]) != t["current_category"]
    ]
    sample = random.sample(changed_titles, min(40, len(changed_titles)))
    sample.sort(key=lambda t: t["title"])

    print(f"  {'#':>3}  {'Titel':<55}  {'Gammal':<38}  →  Ny")
    print("  " + "-"*160)
    for i, t in enumerate(sample, 1):
        old = t["current_category"] or "(ingen)"
        new = proposals.get(t["id"], old)
        print(f"  {i:>3}  {t['title'][:55]:<55}  {old[:38]:<38}  →  {new}")

    total_changed = sum(
        1 for t in titles if proposals.get(t["id"]) != t["current_category"]
    )
    print(f"\n  Totalt: {total_changed}/{len(titles)} titlar byter kategori\n")

    print("=== Ny kategorifördelning ===\n")
    dist: dict[str, int] = {}
    for cat in proposals.values():
        dist[cat] = dist.get(cat, 0) + 1
    for cat, n in sorted(dist.items(), key=lambda x: -x[1]):
        bar = "█" * (n // 20)
        print(f"  {cat:<52}  {n:>5}  {bar}")


def apply_proposals(cur, proposals: dict[int, str]) -> None:
    print(f"Skriver {len(proposals)} kategorier till generalized_titles...")
    updated = 0
    for tid, kat in proposals.items():
        cur.execute(
            "UPDATE generalized_titles SET category = %s WHERE id = %s",
            (kat, tid),
        )
        updated += cur.rowcount
    print(f"  {updated} rader uppdaterade.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply", action="store_true",
        help="Skriv godkänt resultat till DB",
    )
    parser.add_argument(
        "--sample", action="store_true",
        help="Visa 40 slumpade + fördelning",
    )
    parser.add_argument(
        "--db-url",
        default=os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
        ),
    )
    args = parser.parse_args()

    conn = psycopg2.connect(args.db_url)
    cur = conn.cursor()
    titles = fetch_titles(cur)
    print(f"Hämtade {len(titles)} titlar från databasen.")

    if args.apply:
        if not PROPOSALS_FILE.exists():
            print(
                "FEL: category_proposals.json saknas. Kör utan --apply först.",
                file=sys.stderr,
            )
            return 1
        with open(PROPOSALS_FILE) as f:
            proposals: dict[int, str] = {int(k): v for k, v in json.load(f).items()}
        apply_proposals(cur, proposals)
        conn.commit()
        print("Klart.")
        return 0

    if args.sample:
        if not PROPOSALS_FILE.exists():
            print(
                "FEL: category_proposals.json saknas. Kör utan --sample först.",
                file=sys.stderr,
            )
            return 1
        with open(PROPOSALS_FILE) as f:
            proposals = {int(k): v for k, v in json.load(f).items()}
        show_sample(titles, proposals)
        return 0

    # Normalt flöde: klassificera med regelbaserad logik
    print(f"Klassificerar {len(titles)} titlar med regelbaserad logik...")
    proposals_int: dict[int, str] = {}
    for t in titles:
        proposals_int[t["id"]] = classify(t["title"])

    # Spara som str-nycklar (JSON-standard)
    proposals_str: dict[str, str] = {str(k): v for k, v in proposals_int.items()}
    with open(PROPOSALS_FILE, "w", encoding="utf-8") as f:
        json.dump(proposals_str, f, ensure_ascii=False, indent=2)
    print(f"\nFörslag sparade i {PROPOSALS_FILE}")

    # Statistik
    total_changed = sum(
        1 for t in titles if proposals_int.get(t["id"]) != t["current_category"]
    )
    print(f"Totalt {total_changed}/{len(titles)} titlar byter kategori.")

    dist: dict[str, int] = {}
    for cat in proposals_int.values():
        dist[cat] = dist.get(cat, 0) + 1

    print("\n=== NY KATEGORIFÖRDELNING ===")
    for cat, n in sorted(dist.items(), key=lambda x: -x[1]):
        print(f"  {n:5d}  {cat}")

    # Ändrade per gammal kategori
    old_to_new: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for t in titles:
        new_cat = proposals_int[t["id"]]
        old_cat = t["current_category"] or "NULL"
        old_to_new[old_cat][new_cat] += 1

    print("\n=== VART GÅR TITLAR FRÅN 'Kommunövergripande...' ===")
    ks = "Kommunövergripande och Strategiska funktioner"
    for new_cat, cnt in sorted(old_to_new[ks].items(), key=lambda x: -x[1]):
        print(f"  {cnt:5d}  → {new_cat}")

    # 30 slumpade exempel (ändrade)
    print("\n=== 30 SLUMPADE EXEMPEL (gammal → ny) ===")
    changed = [
        (t["id"], t["title"], t["current_category"], proposals_int[t["id"]])
        for t in titles
        if proposals_int[t["id"]] != t["current_category"]
    ]
    random.seed(42)
    sample = random.sample(changed, min(30, len(changed)))
    for tid, title, old_cat, new_cat in sample:
        print(f"\n  [{tid}] {title[:65]}")
        print(f"        {old_cat}")
        print(f"        → {new_cat}")

    print("\nKör med --sample för mer detaljer, --apply för att skriva till DB.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
