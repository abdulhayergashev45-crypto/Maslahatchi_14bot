"""
DTM Ball Bazasi - O'zbekiston OTMlari
2023-2024 yil kirish ballari (grant va kontrakt)
"""

# Format:
# "OTM nomi": {
#   "yo'nalish": {
#     "fanlar": ["Fan1", "Fan2"],  # qaysi fanlar kombinatsiyasi
#     "grant_ball": minimal grant bali,
#     "kontrakt_ball": minimal kontrakt bali,
#     "kontrakt_narx": yillik narx (million so'm),
#     "muddat": yillar
#   }
# }

DTM_BALLARI = {
    "TDTU": {
        "full_name": "Toshkent Davlat Texnika Universiteti",
        "city": "Toshkent",
        "site": "tdtu.uz",
        "yonalishlar": [
            {"nom": "Dasturiy injiniring", "fanlar": ["Matematika", "Fizika"], "grant": 181, "kontrakt": 130, "narx": 14.5, "muddat": 4},
            {"nom": "Kompyuter muhandisligi", "fanlar": ["Matematika", "Fizika"], "grant": 178, "kontrakt": 128, "narx": 14.5, "muddat": 4},
            {"nom": "Elektr energetikasi", "fanlar": ["Matematika", "Fizika"], "grant": 165, "kontrakt": 120, "narx": 12.0, "muddat": 4},
            {"nom": "Qurilish muhandisligi", "fanlar": ["Matematika", "Fizika"], "grant": 158, "kontrakt": 115, "narx": 11.5, "muddat": 4},
            {"nom": "Kimyo texnologiyasi", "fanlar": ["Kimyo", "Matematika"], "grant": 162, "kontrakt": 118, "narx": 12.0, "muddat": 4},
            {"nom": "Neft va gaz muhandisligi", "fanlar": ["Matematika", "Fizika"], "grant": 160, "kontrakt": 118, "narx": 13.0, "muddat": 4},
            {"nom": "Mexanika va mashinasozlik", "fanlar": ["Matematika", "Fizika"], "grant": 155, "kontrakt": 112, "narx": 11.0, "muddat": 4},
            {"nom": "Metallurgiya", "fanlar": ["Matematika", "Fizika"], "grant": 148, "kontrakt": 108, "narx": 10.5, "muddat": 4},
        ]
    },
    "TATU": {
        "full_name": "Toshkent Axborot Texnologiyalari Universiteti",
        "city": "Toshkent",
        "site": "tuit.uz",
        "yonalishlar": [
            {"nom": "Sun'iy intellekt", "fanlar": ["Matematika", "Fizika"], "grant": 188, "kontrakt": 145, "narx": 16.0, "muddat": 4},
            {"nom": "Kiberxavfsizlik", "fanlar": ["Matematika", "Fizika"], "grant": 185, "kontrakt": 142, "narx": 15.5, "muddat": 4},
            {"nom": "Dasturiy ta'minot muhandisligi", "fanlar": ["Matematika", "Fizika"], "grant": 183, "kontrakt": 140, "narx": 15.0, "muddat": 4},
            {"nom": "Telekommunikatsiya texnologiyalari", "fanlar": ["Matematika", "Fizika"], "grant": 172, "kontrakt": 130, "narx": 13.5, "muddat": 4},
            {"nom": "Axborot tizimlari", "fanlar": ["Matematika", "Fizika"], "grant": 170, "kontrakt": 128, "narx": 13.0, "muddat": 4},
            {"nom": "Media texnologiyalari", "fanlar": ["Matematika", "Fizika"], "grant": 162, "kontrakt": 120, "narx": 12.0, "muddat": 4},
        ]
    },
    "NUU": {
        "full_name": "O'zbekiston Milliy Universiteti",
        "city": "Toshkent",
        "site": "nuu.uz",
        "yonalishlar": [
            {"nom": "Matematika", "fanlar": ["Matematika", "Fizika"], "grant": 175, "kontrakt": 130, "narx": 9.0, "muddat": 4},
            {"nom": "Fizika", "fanlar": ["Matematika", "Fizika"], "grant": 172, "kontrakt": 128, "narx": 9.0, "muddat": 4},
            {"nom": "Kimyo", "fanlar": ["Kimyo", "Matematika"], "grant": 168, "kontrakt": 125, "narx": 9.5, "muddat": 4},
            {"nom": "Biologiya", "fanlar": ["Biologiya", "Kimyo"], "grant": 165, "kontrakt": 122, "narx": 9.0, "muddat": 4},
            {"nom": "Informatika", "fanlar": ["Matematika", "Fizika"], "grant": 170, "kontrakt": 126, "narx": 10.0, "muddat": 4},
            {"nom": "Tarix", "fanlar": ["Tarix", "Ona tili"], "grant": 160, "kontrakt": 115, "narx": 8.0, "muddat": 4},
            {"nom": "O'zbek tili va adabiyoti", "fanlar": ["Ona tili", "Adabiyot"], "grant": 158, "kontrakt": 112, "narx": 7.5, "muddat": 4},
            {"nom": "Geografiya", "fanlar": ["Geografiya", "Tarix"], "grant": 152, "kontrakt": 108, "narx": 8.0, "muddat": 4},
        ]
    },
    "TTA": {
        "full_name": "Toshkent Tibbiyot Akademiyasi",
        "city": "Toshkent",
        "site": "tma.uz",
        "yonalishlar": [
            {"nom": "Davolash ishi", "fanlar": ["Biologiya", "Kimyo"], "grant": 190, "kontrakt": 155, "narx": 22.0, "muddat": 6},
            {"nom": "Pediatriya", "fanlar": ["Biologiya", "Kimyo"], "grant": 188, "kontrakt": 152, "narx": 22.0, "muddat": 6},
            {"nom": "Stomatologiya", "fanlar": ["Biologiya", "Kimyo"], "grant": 192, "kontrakt": 160, "narx": 25.0, "muddat": 5},
            {"nom": "Tibbiy profilaktika", "fanlar": ["Biologiya", "Kimyo"], "grant": 182, "kontrakt": 145, "narx": 20.0, "muddat": 6},
            {"nom": "Farmatsiya", "fanlar": ["Kimyo", "Biologiya"], "grant": 185, "kontrakt": 148, "narx": 20.0, "muddat": 5},
        ]
    },
    "SamDTU": {
        "full_name": "Samarqand Davlat Tibbiyot Universiteti",
        "city": "Samarqand",
        "site": "sammi.uz",
        "yonalishlar": [
            {"nom": "Davolash ishi", "fanlar": ["Biologiya", "Kimyo"], "grant": 185, "kontrakt": 148, "narx": 20.0, "muddat": 6},
            {"nom": "Stomatologiya", "fanlar": ["Biologiya", "Kimyo"], "grant": 188, "kontrakt": 152, "narx": 22.0, "muddat": 5},
            {"nom": "Farmatsiya", "fanlar": ["Kimyo", "Biologiya"], "grant": 180, "kontrakt": 142, "narx": 18.0, "muddat": 5},
        ]
    },
    "TDIU": {
        "full_name": "Toshkent Davlat Iqtisodiyot Universiteti",
        "city": "Toshkent",
        "site": "tsue.uz",
        "yonalishlar": [
            {"nom": "Iqtisodiyot", "fanlar": ["Matematika", "Ingliz tili"], "grant": 168, "kontrakt": 125, "narx": 10.0, "muddat": 4},
            {"nom": "Menejment", "fanlar": ["Matematika", "Ingliz tili"], "grant": 165, "kontrakt": 122, "narx": 10.5, "muddat": 4},
            {"nom": "Moliya", "fanlar": ["Matematika", "Ingliz tili"], "grant": 170, "kontrakt": 128, "narx": 11.0, "muddat": 4},
            {"nom": "Buxgalteriya hisobi", "fanlar": ["Matematika", "Ingliz tili"], "grant": 162, "kontrakt": 118, "narx": 9.5, "muddat": 4},
            {"nom": "Marketing", "fanlar": ["Matematika", "Ingliz tili"], "grant": 160, "kontrakt": 116, "narx": 10.0, "muddat": 4},
            {"nom": "Savdo ishi", "fanlar": ["Matematika", "Ingliz tili"], "grant": 155, "kontrakt": 112, "narx": 9.0, "muddat": 4},
        ]
    },
    "TDYU": {
        "full_name": "Toshkent Davlat Yuridik Universiteti",
        "city": "Toshkent",
        "site": "tsul.uz",
        "yonalishlar": [
            {"nom": "Huquqshunoslik", "fanlar": ["Tarix", "Ona tili"], "grant": 182, "kontrakt": 145, "narx": 14.0, "muddat": 4},
            {"nom": "Xalqaro huquq", "fanlar": ["Tarix", "Ingliz tili"], "grant": 185, "kontrakt": 148, "narx": 15.0, "muddat": 4},
            {"nom": "Fuqarolik huquqi", "fanlar": ["Tarix", "Ona tili"], "grant": 178, "kontrakt": 138, "narx": 13.5, "muddat": 4},
        ]
    },
    "TDPU": {
        "full_name": "Toshkent Davlat Pedagogika Universiteti",
        "city": "Toshkent",
        "site": "tdpu.uz",
        "yonalishlar": [
            {"nom": "Boshlang'ich ta'lim", "fanlar": ["Ona tili", "Matematika"], "grant": 155, "kontrakt": 112, "narx": 7.0, "muddat": 4},
            {"nom": "Matematika o'qitish", "fanlar": ["Matematika", "Fizika"], "grant": 160, "kontrakt": 115, "narx": 7.5, "muddat": 4},
            {"nom": "Ingliz tili o'qitish", "fanlar": ["Ingliz tili", "Ona tili"], "grant": 165, "kontrakt": 122, "narx": 8.0, "muddat": 4},
            {"nom": "Informatika o'qitish", "fanlar": ["Matematika", "Fizika"], "grant": 158, "kontrakt": 115, "narx": 7.5, "muddat": 4},
            {"nom": "Fizika o'qitish", "fanlar": ["Fizika", "Matematika"], "grant": 155, "kontrakt": 112, "narx": 7.0, "muddat": 4},
            {"nom": "Maktabgacha ta'lim", "fanlar": ["Ona tili", "Tarix"], "grant": 150, "kontrakt": 108, "narx": 6.5, "muddat": 4},
        ]
    },
    "WIUT": {
        "full_name": "Westminster International University in Tashkent",
        "city": "Toshkent",
        "site": "wiut.uz",
        "yonalishlar": [
            {"nom": "Business Management", "fanlar": ["Ingliz tili", "Matematika"], "grant": 175, "kontrakt": 135, "narx": 28.0, "muddat": 4},
            {"nom": "Finance and Economics", "fanlar": ["Ingliz tili", "Matematika"], "grant": 178, "kontrakt": 138, "narx": 28.0, "muddat": 4},
            {"nom": "Computing", "fanlar": ["Ingliz tili", "Matematika"], "grant": 172, "kontrakt": 132, "narx": 26.0, "muddat": 4},
            {"nom": "Media and Communications", "fanlar": ["Ingliz tili", "Ona tili"], "grant": 168, "kontrakt": 128, "narx": 25.0, "muddat": 4},
        ]
    },
    "INHA": {
        "full_name": "INHA University in Tashkent",
        "city": "Toshkent",
        "site": "inha.uz",
        "yonalishlar": [
            {"nom": "Computer Science and Engineering", "fanlar": ["Matematika", "Ingliz tili"], "grant": 185, "kontrakt": 148, "narx": 30.0, "muddat": 4},
            {"nom": "Mechanical Engineering", "fanlar": ["Matematika", "Fizika"], "grant": 180, "kontrakt": 142, "narx": 28.0, "muddat": 4},
            {"nom": "Business Administration", "fanlar": ["Matematika", "Ingliz tili"], "grant": 175, "kontrakt": 138, "narx": 28.0, "muddat": 4},
        ]
    },
    "Turin": {
        "full_name": "Turin Politexnika Universiteti Toshkentda",
        "city": "Toshkent",
        "site": "polito.uz",
        "yonalishlar": [
            {"nom": "Sanoat muhandisligi", "fanlar": ["Matematika", "Fizika"], "grant": 178, "kontrakt": 138, "narx": 32.0, "muddat": 4},
            {"nom": "Sanoat dizayni", "fanlar": ["Matematika", "Ingliz tili"], "grant": 172, "kontrakt": 132, "narx": 30.0, "muddat": 4},
            {"nom": "Energetika muhandisligi", "fanlar": ["Matematika", "Fizika"], "grant": 175, "kontrakt": 135, "narx": 30.0, "muddat": 4},
        ]
    },
    "SamDU": {
        "full_name": "Samarqand Davlat Universiteti",
        "city": "Samarqand",
        "site": "samdu.uz",
        "yonalishlar": [
            {"nom": "Matematika", "fanlar": ["Matematika", "Fizika"], "grant": 162, "kontrakt": 118, "narx": 7.5, "muddat": 4},
            {"nom": "Fizika", "fanlar": ["Matematika", "Fizika"], "grant": 158, "kontrakt": 115, "narx": 7.5, "muddat": 4},
            {"nom": "Kimyo", "fanlar": ["Kimyo", "Matematika"], "grant": 155, "kontrakt": 112, "narx": 7.5, "muddat": 4},
            {"nom": "Tarix", "fanlar": ["Tarix", "Ona tili"], "grant": 152, "kontrakt": 108, "narx": 7.0, "muddat": 4},
            {"nom": "Ingliz filologiyasi", "fanlar": ["Ingliz tili", "Ona tili"], "grant": 165, "kontrakt": 122, "narx": 8.0, "muddat": 4},
        ]
    },
    "BuxDU": {
        "full_name": "Buxoro Davlat Universiteti",
        "city": "Buxoro",
        "site": "buxdu.uz",
        "yonalishlar": [
            {"nom": "Matematika", "fanlar": ["Matematika", "Fizika"], "grant": 155, "kontrakt": 112, "narx": 6.5, "muddat": 4},
            {"nom": "Kimyo", "fanlar": ["Kimyo", "Matematika"], "grant": 150, "kontrakt": 108, "narx": 6.5, "muddat": 4},
            {"nom": "Biologiya", "fanlar": ["Biologiya", "Kimyo"], "grant": 148, "kontrakt": 105, "narx": 6.5, "muddat": 4},
            {"nom": "Tarix", "fanlar": ["Tarix", "Ona tili"], "grant": 145, "kontrakt": 102, "narx": 6.0, "muddat": 4},
        ]
    },
    "FarDU": {
        "full_name": "Farg'ona Davlat Universiteti",
        "city": "Farg'ona",
        "site": "fdu.uz",
        "yonalishlar": [
            {"nom": "Matematika", "fanlar": ["Matematika", "Fizika"], "grant": 152, "kontrakt": 110, "narx": 6.0, "muddat": 4},
            {"nom": "Kimyo texnologiyasi", "fanlar": ["Kimyo", "Matematika"], "grant": 148, "kontrakt": 106, "narx": 6.5, "muddat": 4},
            {"nom": "Biologiya", "fanlar": ["Biologiya", "Kimyo"], "grant": 145, "kontrakt": 103, "narx": 6.0, "muddat": 4},
        ]
    },
    "JIDU": {
        "full_name": "Jahon Iqtisodiyoti va Diplomatiya Universiteti",
        "city": "Toshkent",
        "site": "uwed.uz",
        "yonalishlar": [
            {"nom": "Xalqaro iqtisodiyot", "fanlar": ["Ingliz tili", "Matematika"], "grant": 182, "kontrakt": 145, "narx": 16.0, "muddat": 4},
            {"nom": "Xalqaro munosabatlar", "fanlar": ["Ingliz tili", "Tarix"], "grant": 185, "kontrakt": 148, "narx": 16.0, "muddat": 4},
            {"nom": "Diplomatiya", "fanlar": ["Ingliz tili", "Tarix"], "grant": 188, "kontrakt": 152, "narx": 17.0, "muddat": 4},
        ]
    },
}

# Barcha fanlar ro'yxati
FANLAR = [
    "Matematika", "Fizika", "Kimyo", "Biologiya",
    "Ingliz tili", "Ona tili", "Tarix", "Geografiya",
    "Adabiyot", "Informatika"
]

def find_universities(fan1: str, fan2: str, ball: int) -> dict:
    """
    Ikki fan va ball bo'yicha mos OTM va yo'nalishlarni topish
    Returns: {"grant": [...], "kontrakt": [...], "mos_emas": [...]}
    """
    grant_mos = []
    kontrakt_mos = []
    
    # Fanlar kombinatsiyasi (ikki variant)
    combo1 = {fan1, fan2}
    
    for otm_id, otm in DTM_BALLARI.items():
        for yon in otm["yonalishlar"]:
            yon_fanlar = set(yon["fanlar"])
            
            # Fan mos kelishini tekshirish (kamida 1 fan mos bo'lsa)
            if not (yon_fanlar & combo1):
                continue
            
            item = {
                "otm": otm["full_name"],
                "otm_id": otm_id,
                "city": otm["city"],
                "site": otm["site"],
                "yonalish": yon["nom"],
                "fanlar": yon["fanlar"],
                "grant_ball": yon["grant"],
                "kontrakt_ball": yon["kontrakt"],
                "narx": yon["narx"],
                "muddat": yon["muddat"],
            }
            
            if ball >= yon["grant"]:
                grant_mos.append(item)
            elif ball >= yon["kontrakt"]:
                kontrakt_mos.append(item)
    
    # Ballga yaqinlik bo'yicha saralash
    grant_mos.sort(key=lambda x: x["grant_ball"], reverse=True)
    kontrakt_mos.sort(key=lambda x: x["kontrakt_ball"], reverse=True)
    
    return {
        "grant": grant_mos[:8],
        "kontrakt": kontrakt_mos[:8],
    }

# ─── NAMANGAN UNIVERSITETLARI ──────────────────────────────────
NAMANGAN_OTMLAR = {
    "NamDU": {
        "full_name": "Namangan Davlat Universiteti",
        "city": "Namangan",
        "site": "namspi.uz",
        "yonalishlar": [
            {"nom": "Matematika", "fanlar": ["Matematika", "Fizika"], "grant": 158, "kontrakt": 112, "narx": 7.0, "muddat": 4},
            {"nom": "Fizika", "fanlar": ["Matematika", "Fizika"], "grant": 155, "kontrakt": 110, "narx": 7.0, "muddat": 4},
            {"nom": "Kimyo", "fanlar": ["Kimyo", "Matematika"], "grant": 152, "kontrakt": 108, "narx": 7.0, "muddat": 4},
            {"nom": "Biologiya", "fanlar": ["Biologiya", "Kimyo"], "grant": 150, "kontrakt": 106, "narx": 6.5, "muddat": 4},
            {"nom": "Ingliz filologiyasi", "fanlar": ["Ingliz tili", "Ona tili"], "grant": 162, "kontrakt": 118, "narx": 7.5, "muddat": 4},
            {"nom": "O'zbek tili va adabiyoti", "fanlar": ["Ona tili", "Adabiyot"], "grant": 150, "kontrakt": 105, "narx": 6.5, "muddat": 4},
            {"nom": "Tarix", "fanlar": ["Tarix", "Ona tili"], "grant": 148, "kontrakt": 104, "narx": 6.5, "muddat": 4},
            {"nom": "Geografiya", "fanlar": ["Geografiya", "Tarix"], "grant": 145, "kontrakt": 102, "narx": 6.0, "muddat": 4},
            {"nom": "Informatika", "fanlar": ["Matematika", "Fizika"], "grant": 160, "kontrakt": 115, "narx": 7.5, "muddat": 4},
            {"nom": "Jismoniy madaniyat", "fanlar": ["Biologiya", "Ona tili"], "grant": 140, "kontrakt": 98, "narx": 5.5, "muddat": 4},
        ]
    },
    "NamMQI": {
        "full_name": "Namangan Muhandislik-Qurilish Instituti",
        "city": "Namangan",
        "site": "namqi.uz",
        "yonalishlar": [
            {"nom": "Qurilish muhandisligi", "fanlar": ["Matematika", "Fizika"], "grant": 155, "kontrakt": 110, "narx": 9.0, "muddat": 4},
            {"nom": "Arxitektura", "fanlar": ["Matematika", "Fizika"], "grant": 158, "kontrakt": 112, "narx": 9.5, "muddat": 4},
            {"nom": "Yo'l qurilishi", "fanlar": ["Matematika", "Fizika"], "grant": 150, "kontrakt": 108, "narx": 8.5, "muddat": 4},
            {"nom": "Suv ta'minoti", "fanlar": ["Matematika", "Fizika"], "grant": 148, "kontrakt": 106, "narx": 8.0, "muddat": 4},
            {"nom": "Kommunal xo'jalik", "fanlar": ["Matematika", "Fizika"], "grant": 145, "kontrakt": 103, "narx": 8.0, "muddat": 4},
        ]
    },
    "NamTI": {
        "full_name": "Namangan Texnologiya Instituti",
        "city": "Namangan",
        "site": "namti.uz",
        "yonalishlar": [
            {"nom": "Yengil sanoat texnologiyasi", "fanlar": ["Kimyo", "Matematika"], "grant": 148, "kontrakt": 105, "narx": 8.0, "muddat": 4},
            {"nom": "Oziq-ovqat texnologiyasi", "fanlar": ["Kimyo", "Biologiya"], "grant": 145, "kontrakt": 102, "narx": 7.5, "muddat": 4},
            {"nom": "Kimyo texnologiyasi", "fanlar": ["Kimyo", "Matematika"], "grant": 150, "kontrakt": 108, "narx": 8.5, "muddat": 4},
            {"nom": "Standartlashtirish", "fanlar": ["Matematika", "Fizika"], "grant": 143, "kontrakt": 100, "narx": 7.5, "muddat": 4},
            {"nom": "Menejment", "fanlar": ["Matematika", "Ingliz tili"], "grant": 148, "kontrakt": 105, "narx": 8.0, "muddat": 4},
        ]
    },
    "NamMI": {
        "full_name": "Namangan Davlat Tibbiyot Instituti",
        "city": "Namangan",
        "site": "namtib.uz",
        "yonalishlar": [
            {"nom": "Davolash ishi", "fanlar": ["Biologiya", "Kimyo"], "grant": 182, "kontrakt": 145, "narx": 19.0, "muddat": 6},
            {"nom": "Pediatriya", "fanlar": ["Biologiya", "Kimyo"], "grant": 180, "kontrakt": 142, "narx": 19.0, "muddat": 6},
            {"nom": "Stomatologiya", "fanlar": ["Biologiya", "Kimyo"], "grant": 185, "kontrakt": 150, "narx": 22.0, "muddat": 5},
            {"nom": "Farmatsiya", "fanlar": ["Kimyo", "Biologiya"], "grant": 178, "kontrakt": 140, "narx": 17.0, "muddat": 5},
        ]
    },
    "NamPI": {
        "full_name": "Namangan Davlat Pedagogika Instituti",
        "city": "Namangan",
        "site": "nampi.uz",
        "yonalishlar": [
            {"nom": "Boshlang'ich ta'lim", "fanlar": ["Ona tili", "Matematika"], "grant": 148, "kontrakt": 105, "narx": 6.0, "muddat": 4},
            {"nom": "Matematika o'qitish", "fanlar": ["Matematika", "Fizika"], "grant": 152, "kontrakt": 108, "narx": 6.5, "muddat": 4},
            {"nom": "Ingliz tili o'qitish", "fanlar": ["Ingliz tili", "Ona tili"], "grant": 158, "kontrakt": 112, "narx": 7.0, "muddat": 4},
            {"nom": "Maktabgacha ta'lim", "fanlar": ["Ona tili", "Tarix"], "grant": 142, "kontrakt": 100, "narx": 5.5, "muddat": 4},
            {"nom": "Jismoniy tarbiya", "fanlar": ["Biologiya", "Ona tili"], "grant": 138, "kontrakt": 96, "narx": 5.5, "muddat": 4},
        ]
    },
    "ADMI": {
        "full_name": "Alisher Navoiy nomidagi Toshkent Davlat O'zbek tili va Adabiyoti Universiteti (ADMU/ADMI)",
        "city": "Toshkent",
        "site": "navoiy-uni.uz",
        "yonalishlar": [
            {"nom": "O'zbek tili va adabiyoti", "fanlar": ["Ona tili", "Adabiyot"], "grant": 168, "kontrakt": 125, "narx": 8.0, "muddat": 4},
            {"nom": "Jurnalistika", "fanlar": ["Ona tili", "Adabiyot"], "grant": 172, "kontrakt": 130, "narx": 9.0, "muddat": 4},
            {"nom": "Tarjima nazariyasi (ingliz)", "fanlar": ["Ingliz tili", "Ona tili"], "grant": 175, "kontrakt": 132, "narx": 9.5, "muddat": 4},
            {"nom": "Tarjima nazariyasi (rus)", "fanlar": ["Ona tili", "Tarix"], "grant": 165, "kontrakt": 122, "narx": 9.0, "muddat": 4},
            {"nom": "O'zbek filologiyasi", "fanlar": ["Ona tili", "Adabiyot"], "grant": 165, "kontrakt": 122, "narx": 8.0, "muddat": 4},
        ]
    },
}

# Asosiy bazaga Namangan va ADMI ni qo'shish
DTM_BALLARI.update(NAMANGAN_OTMLAR)
