# کاراکتر شیت ایزومتریک — پرامپتِ پارامتریک با کنترلِ زاویهٔ خم‌شدن

هدف: بتوانی یک کاراکتر را با هویتِ ثابت، در همهٔ جهت‌ها و همهٔ اکشن‌ها بسازی، و زاویهٔ خم‌شدنِ بدن موقعِ راه‌رفتن را عددی بدهی.

---

## ۰) روشِ کار (سه مرحله، پشتِ سرِ هم)

۱. **مدل‌شیت** بساز: یک کاراکتر، ۸ جهت، حالتِ ایستاده. این تصویر می‌شود مرجعِ همهٔ تولیدهای بعدی.
۲. همان تصویر را به‌عنوانِ **reference/image prompt** بده و **هر ردیفِ اکشن** را جدا تولید کن. یک شیتِ ۲۰ اکشنی در یک تولید همیشه هویت را می‌شکند.
۳. **سیکلِ راه‌رفتن** را با پارامترِ زاویه بساز، فریم‌به‌فریم، با همان seed.

قانونِ طلایی: هویت را در متن تکرار نکن، از تصویرِ مرجع بیاور. متن فقط اکشن و زاویه را عوض کند.

---

## ۱) بلاکِ هویت (ثابت در تمامِ تولیدها)

```
CHARACTER: {name}, {age_read} year old {gender_read}, {body_type} build,
{height_read} proportions ({HEADS} heads tall),
hair: {hair}, skin: {skin},
outfit: {top} + {bottom} + {shoes}, accessories: {accessories},
palette: {hex1}, {hex2}, {hex3}, {hex4} (locked, no other hues),
silhouette cue: {one distinctive shape that reads at 32px}
```

نکتهٔ مهم: «silhouette cue» را جدی بگیر. در ایزومتریکِ کوچک، کاراکتر از روی سیلوئت شناخته می‌شود نه از روی جزئیات. یک کلاه، یک شالِ بلند، یک کولهٔ گرد، یک مدلِ موی مشخص.

---

## ۲) بلاکِ دوربین و پروجکشن

```
VIEW: orthographic isometric, camera azimuth 45°, elevation {ELEV}°,
no perspective, no lens distortion, no vanishing point,
sprite anchored at bottom-center of the cell, feet on the ground line,
uniform key light from upper-left at 45°, soft ambient fill, one soft contact shadow ellipse
```

- `ELEV = 26.57` برای ایزومتریکِ بازی‌ها (نسبتِ ۲:۱، همانی که کفِ اتاقِ خودت دارد)
- `ELEV = 30` برای ایزومتریکِ واقعیِ هندسی
- هر دو را با هم قاطی نکن. کفِ botworld روی ۲:۱ است، پس ۲۶.۵۷ درست است.

---

## ۳) کنترلِ زاویهٔ خم‌شدن (اصلِ ماجرا)

مدل‌های تصویر «۱۲ درجه» را خوب نمی‌فهمند، ولی «شانه چقدر جلوترِ لگن است» را عالی می‌فهمند. پس زاویه را همیشه با معادلِ دیداری‌اش بده:

| زاویه از خطِ عمود | شانه جلوتر از لگن (واحد: طولِ تنه) | معادل به سرِ کاراکتر | حسِ حرکت |
|---|---|---|---|
| ۰ تا ۲ | ۰ تا ۰٫۰۳ | تقریبا هیچ | ایستاده، نفس‌کشیدن |
| ۵ | ۰٫۰۹ | ۰٫۲ سر | قدم‌زدنِ آرام |
| ۸ تا ۱۰ | ۰٫۱۴ تا ۰٫۱۸ | ۰٫۴ سر | راه‌رفتنِ عادی |
| ۱۲ تا ۱۵ | ۰٫۲۱ تا ۰٫۲۷ | ۰٫۶ سر | راه‌رفتنِ تند، عجله |
| ۱۸ تا ۲۲ | ۰٫۳۲ تا ۰٫۴۰ | ۰٫۹ سر | دویدن |
| ۲۵ تا ۳۰ | ۰٫۴۷ تا ۰٫۵۸ | ۱٫۳ سر | اسپرینت، هل‌دادنِ بارِ سنگین |
| منفی ۵ تا منفی ۱۰ | عقب‌تر | ۰٫۴ سر به عقب | حملِ جعبهٔ سنگین جلوی بدن، ترمزِ ناگهانی |

فرمولش ساده است: `شانه‌جلوتر = tan(زاویه) × طولِ تنه`. اگر خواستی خودت زاویهٔ دلخواه بسازی، همین را حساب کن و در پرامپت هم عدد و هم معادلِ دیداری را بنویس.

بلاکِ حرکت:

```
MOTION:
  forward torso lean {LEAN}° from vertical
    (shoulder line sits {LEAN_VISUAL} ahead of the hip line),
  lateral sway {SWAY}° at the peak of each step,
  hip rotation {HIP}° with counter shoulder rotation {SHOULDER}°,
  stride length {STRIDE} of hip height, vertical bob {BOB} of head height,
  head stays level, gaze horizon-locked,
  arms swing opposite to legs, elbow bend {ELBOW}°
```

مقادیرِ پیشنهادی برای هر حالت:

| حالت | LEAN | SWAY | HIP | SHOULDER | STRIDE | BOB | ELBOW |
|---|---|---|---|---|---|---|---|
| قدم‌زدن | ۵ | ۲ | ۶ | ۴ | ۰٫۵ | ۰٫۰۴ | ۲۰ |
| راه‌رفتنِ عادی | ۹ | ۳ | ۱۰ | ۸ | ۰٫۷ | ۰٫۰۶ | ۳۵ |
| عجله | ۱۴ | ۴ | ۱۴ | ۱۲ | ۰٫۹ | ۰٫۰۸ | ۵۵ |
| دویدن | ۲۰ | ۵ | ۱۸ | ۱۶ | ۱٫۲ | ۰٫۱۲ | ۸۵ |
| یواشکی | ۲۲ همراهِ زانوی خم | ۱ | ۴ | ۳ | ۰٫۴ | ۰٫۰۲ | ۴۵ |
| خسته | ۱۲ همراهِ سرِ پایین و شانهٔ افتاده | ۴ | ۶ | ۲ | ۰٫۴ | ۰٫۰۳ | ۱۵ |
| حملِ جعبه | منفی ۸ | ۲ | ۶ | ۰ | ۰٫۵ | ۰٫۰۳ | ۹۰ ثابت |

---

## ۴) ماتریسِ کامل اکشن‌ها

هر اکشن، تعدادِ فریم و اینکه لوپ است یا نه:

**جابه‌جایی** (۸ جهت لازم دارند)
idle ۴ لوپ · idle-look-around ۶ لوپ · walk ۸ لوپ · walk-carry ۸ لوپ · run ۸ لوپ · sneak ۸ لوپ · turn-in-place ۴ یک‌بار · push ۶ لوپ · pull ۶ لوپ · stairs-up ۸ لوپ · stairs-down ۸ لوپ · jump ۶ یک‌بار · land ۳ یک‌بار · slip-fall ۶ یک‌بار

**کار و اداره** (معمولا ۴ جهت کافی است)
sit-down ۴ گذر · sit-idle ۴ لوپ · sit-type ۶ لوپ · sit-lean-back ۴ لوپ · sit-write ۶ لوپ · stand-up ۴ گذر · stand-at-desk ۴ لوپ · whiteboard-write ۶ لوپ · present-point ۴ لوپ · hold-tablet ۴ لوپ · phone-call ۶ لوپ · drink ۶ یک‌بار · eat ۶ لوپ · pick-up ۵ یک‌بار · put-down ۵ یک‌بار · carry-box-idle ۴ لوپ · open-door ۶ یک‌بار · knock ۴ یک‌بار · use-printer ۶ لوپ · plug-cable ۵ یک‌بار

**اجتماعی**
wave ۶ · handshake ۶ · high-five ۵ · talk-gesture ۸ لوپ · listen-nod ۴ لوپ · laugh ۶ · clap ۴ لوپ · shrug ۴ · think-chin ۴ لوپ · facepalm ۵ · point-at ۳ · bow ۵

**حالت‌های روحی** (روی idle سوار می‌شوند)
happy · tired-slump · stressed · confused · angry · sad · celebrate ۸ · dance ۸ لوپ · sleep-at-desk ۴ لوپ

**سیستمی**
spawn-appear ۶ · despawn ۶ · get-item ۵ · use-item ۵ · ko-collapse ۷

جهت‌ها: `S, SE, E, NE, N, NW, W, SW`. اگر بودجهٔ تولید کم است، فقط `S, SE, E, NE, N` را بساز و چهارتای دیگر را آینه کن. فقط حواست باشد چیزهای نامتقارن (کوله روی یک شانه، ساعتِ مچ) با آینه‌کردن جابه‌جا می‌شوند.

---

## ۵) پرامپتِ مادر

```
{STYLE_PRESET}

CHARACTER: {بلاکِ هویت از بخش ۱}

VIEW: {بلاکِ دوربین از بخش ۲}

ACTION: {action_name}, {frame_index} of {frame_count} of the cycle,
facing {direction}, {phase_description}

MOTION: {بلاکِ حرکت از بخش ۳}

SHEET: single row of {frame_count} evenly spaced frames on a transparent background,
identical cell size {CELL_W}x{CELL_H} px, identical character scale and ground line
in every cell, {GUTTER} px gutter, no labels, no text, no numbers, no frame borders
```

`phase_description` برای هر فریمِ راه‌رفتن (سیکلِ ۸ فریمی):

۱ contact, right heel strikes · ۲ down, weight lowest, both feet on ground · ۳ pass, left leg swings under the body · ۴ up, weight highest on the right leg · ۵ contact mirrored, left heel strikes · ۶ down mirrored · ۷ pass mirrored · ۸ up mirrored

اگر فریم‌ها را جدا می‌سازی همین جمله‌ها را یکی‌یکی بگذار. اگر کلِ ردیف را یک‌جا می‌سازی، همه را با فلش پشتِ هم بنویس.

---

## ۶) پرامپتِ آمادهٔ راه‌رفتن (فقط جاهای خالی را پر کن)

```
Pixel art isometric character sprite sheet, {PX} px tall character, crisp hard pixels,
no anti-aliasing, no dithering on flat areas, limited palette of {N} colors.

CHARACTER: Rusty, 28 year old office worker, slim build, 6 heads tall,
short dark hair, warm mid tone skin, teal hoodie + dark grey jeans + white sneakers,
round backpack on the left shoulder,
palette: #1F3A5F #2EC4B6 #F7F7FF #2B2B2B, locked.

VIEW: orthographic isometric, azimuth 45°, elevation 26.57°, no perspective,
sprite anchored at bottom-center, feet on the ground line,
key light upper-left 45°, one soft contact shadow.

ACTION: walking, full 8 frame cycle left to right, facing SE,
frames: contact / down / pass / up / contact mirrored / down mirrored / pass mirrored / up mirrored.

MOTION: forward torso lean 9° from vertical (shoulder line sits about
0.4 head widths ahead of the hip line), lateral sway 3° at each step peak,
hip rotation 10° with counter shoulder rotation 8°, stride 0.7 of hip height,
vertical bob 0.06 of head height, head level and gaze horizon-locked,
arms swing opposite the legs with 35° elbow bend.

SHEET: one row, 8 frames, transparent background, identical 64x64 cells,
same scale and ground line in every cell, 0 px gutter,
no text, no labels, no borders, no background props.
```

برای عوض‌کردنِ شدتِ خم‌شدن فقط سه عدد در بلاکِ MOTION عوض می‌شود: `lean`، معادلِ دیداری‌اش، و `elbow`.

---

## ۷) نگاتیو پرامپت

```
perspective, vanishing point, foreshortening, camera tilt, dutch angle,
front view, three quarter view, top down view,
inconsistent character size, floating feet, shifting ground line,
extra limbs, deformed hands, changing outfit, changing palette,
motion blur, speed lines, glow, bloom, gradients on flat areas,
anti-aliased edges, jpeg artifacts, drop shadow behind sprite,
text, numbers, labels, watermark, frame borders, grid lines,
white background, checkerboard background
```

---

## ۸) سه پریستِ استایل

**الف) پیکسل‌آرت هم‌خانوادهٔ LimeZu** (همانی که اتاقت با آن ساخته شده)
```
16-bit pixel art, {PX} px character height, 1 px hard outline in a darker shade
of the local color, 3 shades per material (base, shadow, highlight),
no anti-aliasing, no gradients, top-left light source, cozy warm palette
```

**ب) وکتورِ تمیزِ ایزومتریک**
```
flat vector isometric illustration, clean shapes, no outline,
two flat shades per material, soft long shadow, muted modern palette
```

**ج) رندرِ سه‌بعدیِ ایزومتریک**
```
stylized 3d render, orthographic isometric camera, soft clay material,
subtle ambient occlusion, single soft key light, neutral studio background removed
```

---

## ۹) ثباتِ کاراکتر بین تولیدها

- **seed را قفل کن** و فقط یک متغیر را در هر تولید عوض کن.
- مدل‌شیتِ مرحلهٔ اول را همیشه به‌عنوانِ تصویرِ مرجع بده، وزنِ ۰٫۶ تا ۰٫۸.
- رنگ‌ها را با کدِ hex بنویس و در نگاتیو `changing palette` بگذار.
- هر ردیف را جدا بساز، بعد در یک ویرایشگر کنارِ هم بچین. تولیدِ یک شیتِ کامل در یک تصویر، اندازه و خطِ زمین را به‌هم می‌ریزد.
- بعد از هر ردیف، **تستِ سیلوئت**: تصویر را تماما سیاه کن. اگر اکشن از روی سیلوئت خوانده نمی‌شود، ژست به‌درد نمی‌خورد، هرچقدر هم جزئیات قشنگ باشد.

---

## ۱۰) چک‌لیستِ تحویل

- [ ] لنگرِ همهٔ سل‌ها پایین‌وسط و خطِ زمین ثابت
- [ ] قدِ کاراکتر در همهٔ فریم‌ها یکسان (اختلافِ بیش از ۱ پیکسل یعنی لرزشِ اسپرایت)
- [ ] فریمِ اول و آخرِ اکشن‌های لوپ به هم وصل می‌شوند
- [ ] تعدادِ رنگ‌ها از سقفِ پالت رد نشده
- [ ] پس‌زمینه واقعا شفاف است نه سفید
- [ ] نامِ فایل: `{char}_{action}_{dir}_{frame}.png` مثل `rusty_walk_se_03.png`
- [ ] یک `sheet.json` کنارش: نامِ اکشن، تعدادِ فریم، fps، لوپ یا نه، آفستِ لنگر

---

## ۱۱) نکتهٔ ایزومتریک که معمولا فراموش می‌شود

در نمای ایزومتریک، خمِ رو به جلو در جهت‌های مختلف **متفاوت دیده می‌شود**. همان ۹ درجهٔ واقعی وقتی کاراکتر رو به `E` می‌رود کاملا در نما پیداست، ولی وقتی رو به `S` یا `N` می‌رود تقریبا محو می‌شود. اگر می‌خواهی خم‌شدن در همهٔ جهت‌ها یکسان **دیده** شود، برای جهت‌های رو به دوربین و پشت به دوربین زاویه را حدود ۱٫۴ برابر بده:

`زاویهٔ پرامپت = زاویهٔ هدف ÷ cos(آزیموتِ اختلاف)`

یعنی برای `S` و `N` عددِ ۹ را ۱۳ بنویس تا همان حسِ ۹ درجه را بدهد. برای `E` و `W` همان ۹ درست است.
