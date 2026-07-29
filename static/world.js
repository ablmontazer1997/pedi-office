// The plan of the world. Edited by world-editor.html, read by world.html.
// One file, so the page and the editor can never disagree about what exists.
window.WORLD = {
 "layout": [
  [
   "office",
   "gym",
   "music"
  ],
  [
   "studio",
   "cafe",
   "home",
   "jp"
  ],
  [
   "range",
   "lobby",
   "hall"
  ]
 ],
 "tall": null,
 "pad": 64,
 "gap": 64,
 "boss": {
  "room": "studio",
  "x": 134,
  "y": 142,
  "name": "Ali Akbar"
 },
 "chars": [
  "01",
  "04",
  "06",
  "09",
  "12",
  "15",
  "18"
 ],
 "stations": [
  [
   112,
   236
  ],
  [
   320,
   236
  ],
  [
   528,
   236
  ],
  [
   112,
   404
  ],
  [
   320,
   404
  ],
  [
   528,
   404
  ]
 ],
 "cast": [],
 "rooms": [
  {
   "id": "office",
   "nm": "CONTROL ROOM",
   "fa": "اتاق فرمان",
   "w": 640,
   "h": 448,
   "door": 320,
   "L": [
    "Control_Room_layer_1.png",
    "Control_Room_layer_2.png"
   ],
   "anim": [
    [
     "server",
     596,
     300
    ]
   ],
   "spots": [
    {
     "x": 200,
     "y": 330,
     "a": "idle",
     "d": 1,
     "l": "نگاه به مانیتورها"
    },
    {
     "x": 430,
     "y": 330,
     "a": "phone",
     "d": 3,
     "l": "چک کردن گوشی"
    }
   ]
  },
  {
   "id": "gym",
   "nm": "GYM",
   "fa": "باشگاه",
   "w": 608,
   "h": 480,
   "door": 330,
   "L": [
    "Gym_layer_1_32x32.png",
    "Gym_layer_2_32x32.png"
   ],
   "anim": [
    [
     "tapis",
     352,
     182
    ],
    [
     "tapis",
     360,
     282
    ]
   ],
   "spots": [
    {
     "x": 482,
     "y": 140,
     "a": "punch",
     "d": 1,
     "l": "کیسه بوکس"
    },
    {
     "x": 498,
     "y": 140,
     "a": "punch",
     "d": 1,
     "l": "کیسه بوکس"
    },
    {
     "x": 503,
     "y": 164,
     "a": "punch",
     "d": 1,
     "l": "کیسه بوکس"
    },
    {
     "x": 330,
     "y": 230,
     "a": "idle",
     "d": 3,
     "l": "دمبل سبک",
     "p": "dumbbell"
    },
    {
     "x": 384,
     "y": 250,
     "a": "walk",
     "d": 1,
     "l": "دویدن روی تردمیل",
     "on": true,
     "run": true
    },
    {
     "x": 392,
     "y": 350,
     "a": "walk",
     "d": 1,
     "l": "دویدن روی تردمیل",
     "on": true,
     "run": true
    }
   ]
  },
  {
   "id": "music",
   "nm": "MUSIC ROOM",
   "fa": "اتاق موسیقی",
   "w": 640,
   "h": 448,
   "door": 320,
   "L": [
    "Music_Room_layer_1.png",
    "Music_Room_layer_2.png"
   ],
   "anim": [
    [
     "sprout",
     600,
     300
    ]
   ],
   "spots": [
    {
     "x": 113,
     "y": 300,
     "a": "idle",
     "d": 1,
     "l": "پیانو زدن",
     "snd": "piano"
    },
    {
     "x": 225,
     "y": 132,
     "a": "idle",
     "d": 1,
     "l": "پیانو زدن",
     "snd": "piano"
    },
    {
     "x": 295,
     "y": 132,
     "a": "idle",
     "d": 1,
     "l": "پیانو زدن",
     "snd": "piano"
    },
    {
     "x": 428,
     "y": 132,
     "a": "idle",
     "d": 1,
     "l": "درام زدن",
     "snd": "drum"
    },
    {
     "x": 520,
     "y": 132,
     "a": "idle",
     "d": 1,
     "l": "درام زدن",
     "snd": "drum"
    },
    {
     "x": 322,
     "y": 290,
     "a": "idle",
     "d": 1,
     "l": "چنگ زدن",
     "snd": "harp"
    },
    {
     "x": 433,
     "y": 284,
     "a": "idle",
     "d": 1,
     "l": "گیتار زدن",
     "snd": "guitar"
    },
    {
     "x": 503,
     "y": 284,
     "a": "idle",
     "d": 1,
     "l": "گیتار باس",
     "snd": "guitar"
    },
    {
     "x": 170,
     "y": 392,
     "a": "idle",
     "d": 1,
     "l": "تنبک زدن",
     "snd": "conga"
    },
    {
     "x": 350,
     "y": 390,
     "a": "idle",
     "d": 1,
     "l": "پای میکروفن",
     "snd": "sing"
    },
    {
     "x": 469,
     "y": 400,
     "a": "idle",
     "d": 1,
     "l": "کیبورد زدن",
     "snd": "keys"
    },
    {
     "x": 533,
     "y": 400,
     "a": "idle",
     "d": 1,
     "l": "کیبورد زدن",
     "snd": "keys"
    }
   ]
  },
  {
   "id": "studio",
   "nm": "TV STUDIO",
   "fa": "استودیو",
   "w": 352,
   "h": 320,
   "door": 176,
   "L": [
    "Tv_Studio_Design_layer_1_32x32.png",
    "Tv_Studio_Design_layer_2_32x32.png",
    "Tv_Studio_Design_layer_3_32x32.png"
   ],
   "anim": [],
   "spots": [
    {
     "x": 131,
     "y": 164,
     "a": "idle",
     "d": 1,
     "l": "پشت میز پخش"
    },
    {
     "x": 228,
     "y": 100,
     "a": "idle",
     "d": 1,
     "l": "پشت میز پخش"
    },
    {
     "x": 112,
     "y": 216,
     "a": "sit",
     "d": 1,
     "l": "روی صندلی مهمان",
     "on": true
    },
    {
     "x": 175,
     "y": 216,
     "a": "sit",
     "d": 1,
     "l": "روی صندلی مهمان",
     "on": true
    },
    {
     "x": 80,
     "y": 262,
     "a": "idle",
     "d": 1,
     "l": "پشت دوربین"
    }
   ]
  },
  {
   "id": "cafe",
   "nm": "ICE CREAM SHOP",
   "fa": "بستنی فروشی",
   "w": 384,
   "h": 320,
   "door": 192,
   "L": [
    "Ice_Cream_Shop_Design_layer_1_32x32.png",
    "Ice_Cream_Shop_Design_layer_2_32x32.png",
    "Ice_Cream_Shop_Design_layer_3_32x32.png"
   ],
   "anim": [
    [
     "coffee",
     44,
     172
    ],
    [
     "coffee",
     324,
     172
    ]
   ],
   "spots": [
    {
     "x": 52,
     "y": 214,
     "a": "sit",
     "d": 0,
     "l": "بستنی خوردن",
     "on": true,
     "p": "icecream"
    },
    {
     "x": 110,
     "y": 214,
     "a": "sit",
     "d": 1,
     "l": "بستنی خوردن",
     "on": true,
     "p": "icecream"
    },
    {
     "x": 274,
     "y": 214,
     "a": "sit",
     "d": 0,
     "l": "بستنی خوردن",
     "on": true,
     "p": "icecream"
    },
    {
     "x": 350,
     "y": 258,
     "a": "idle",
     "d": 1,
     "l": "بستنی خوردن",
     "p": "icecream"
    },
    {
     "x": 160,
     "y": 176,
     "a": "idle",
     "d": 1,
     "l": "سفارش دادن"
    },
    {
     "x": 206,
     "y": 176,
     "a": "idle",
     "d": 1,
     "l": "صف صندوق"
    }
   ]
  },
  {
   "id": "home",
   "nm": "LOUNGE",
   "fa": "لانژ",
   "w": 448,
   "h": 428,
   "door": 200,
   "L": [
    "Generic_Home_1_Layer_1_32x32.png",
    "Generic_Home_1_Layer_2_32x32.png"
   ],
   "anim": [
    [
     "cat",
     188,
     170
    ],
    [
     "sprout",
     64,
     208
    ]
   ],
   "spots": [
    {
     "x": 120,
     "y": 196,
     "a": "sit",
     "d": 0,
     "l": "نشستن کنار میز",
     "on": true
    },
    {
     "x": 186,
     "y": 196,
     "a": "sit",
     "d": 1,
     "l": "نشستن کنار میز",
     "on": true
    },
    {
     "x": 236,
     "y": 150,
     "a": "phone",
     "d": 3,
     "l": "وقت تلف کردن"
    },
    {
     "x": 96,
     "y": 130,
     "a": "idle",
     "d": 1,
     "l": "آشپزخانه"
    },
    {
     "x": 290,
     "y": 190,
     "a": "sleep",
     "d": 0,
     "l": "چرت",
     "on": true
    }
   ]
  },
  {
   "id": "jp",
   "nm": "JAPANESE HOUSE",
   "fa": "خانه ژاپنی",
   "w": 608,
   "h": 428,
   "door": 176,
   "L": [
    "Japanese_Home_1_Layer_1_32x32.png",
    "Japanese_Home_1_Layer_2_32x32.png"
   ],
   "anim": [
    [
     "sprout",
     154,
     224
    ],
    [
     "cat",
     320,
     268
    ]
   ],
   "spots": [
    {
     "x": 96,
     "y": 250,
     "a": "sit",
     "d": 0,
     "l": "چای ژاپنی",
     "on": true
    },
    {
     "x": 150,
     "y": 250,
     "a": "sit",
     "d": 1,
     "l": "چای ژاپنی",
     "on": true
    },
    {
     "x": 216,
     "y": 194,
     "a": "idle",
     "d": 1,
     "l": "تماشای حیاط"
    },
    {
     "x": 400,
     "y": 262,
     "a": "phone",
     "d": 3,
     "l": "مطالعه"
    },
    {
     "x": 470,
     "y": 180,
     "a": "sleep",
     "d": 0,
     "l": "استراحت",
     "on": true
    }
   ]
  },
  {
   "id": "range",
   "nm": "SHOOTING RANGE",
   "fa": "سالن تیراندازی",
   "w": 320,
   "h": 332,
   "door": 150,
   "L": [
    "Shooting_Range_Design_layer_1_32x32.png",
    "Shooting_Range_Design_layer_2_32x32.png"
   ],
   "anim": [
    [
     "seccam",
     44,
     28
    ]
   ],
   "spots": [
    {
     "x": 72,
     "y": 212,
     "a": "gun",
     "d": 1,
     "l": "تمرین نشانه‌گیری"
    },
    {
     "x": 118,
     "y": 212,
     "a": "gun",
     "d": 1,
     "l": "تمرین نشانه‌گیری"
    },
    {
     "x": 164,
     "y": 212,
     "a": "gun",
     "d": 1,
     "l": "تمرین نشانه‌گیری"
    },
    {
     "x": 210,
     "y": 250,
     "a": "idle",
     "d": 1,
     "l": "انتظار نوبت"
    }
   ]
  },
  {
   "id": "lobby",
   "nm": "LOBBY",
   "fa": "لابی",
   "w": 448,
   "h": 352,
   "door": 224,
   "L": [
    "Condominium_Design_layer_1_32x32.png",
    "Condominium_Design_layer_2_32x32.png"
   ],
   "anim": [
    [
     "clock",
     64,
     160
    ],
    [
     "sprout",
     380,
     180
    ]
   ],
   "spots": [
    {
     "x": 186,
     "y": 186,
     "a": "idle",
     "d": 1,
     "l": "خواندن تابلو اعلانات"
    },
    {
     "x": 120,
     "y": 262,
     "a": "phone",
     "d": 3,
     "l": "منتظر آسانسور"
    },
    {
     "x": 320,
     "y": 262,
     "a": "idle",
     "d": 3,
     "l": "قدم زدن"
    }
   ]
  },
  {
   "id": "hall",
   "nm": "CORRIDOR",
   "fa": "راهرو",
   "w": 448,
   "h": 192,
   "door": 224,
   "L": [
    "Condominium_Design_2_layer_1_32x32.png",
    "Condominium_Design_2_layer_2_32x32.png"
   ],
   "anim": [
    [
     "cat",
     196,
     120
    ]
   ],
   "spots": [
    {
     "x": 100,
     "y": 140,
     "a": "idle",
     "d": 1,
     "l": "در زدن"
    },
    {
     "x": 300,
     "y": 140,
     "a": "phone",
     "d": 3,
     "l": "چک کردن پیام"
    }
   ]
  }
 ]
};
