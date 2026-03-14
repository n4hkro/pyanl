# pyANL – ANL Kitabxana Telegram Botu

Azərbaycan Milli Kitabxanasının (ANL) rəqəmsal kitablarını PDF formatında
yükləyən Telegram botu.

## Xüsusiyyətlər

- ANL kitab linkini göndərin, bot bütün səhifələri yükləyib PDF olaraq geri
  göndərir.
- Eyni anda bir neçə istifadəçi paralel şəkildə istifadə edə bilər
  (**aiogram** async framework).
- Yükləmə prosesi haqqında canlı status mesajları.

## Quraşdırma

```bash
# Depoyu klonlayın
git clone https://github.com/n4hkro/pyANL.git
cd pyANL

# Virtual mühit yaradın (tövsiyə olunur)
python -m venv venv
source venv/bin/activate   # Linux / macOS
# venv\Scripts\activate    # Windows

# Asılılıqları quraşdırın
pip install -r requirements.txt
```

## Konfiqurasiya

`.env.example` faylını `.env` olaraq kopyalayın və Telegram bot tokeninizi
daxil edin:

```bash
cp .env.example .env
```

`.env` faylını redaktə edin:

```
BOT_TOKEN=your-telegram-bot-token-here
```

> **Qeyd:** Bot tokenini [@BotFather](https://t.me/BotFather) vasitəsilə əldə
> edə bilərsiniz.

## İstifadə

Botu başladın:

```bash
# .env faylından tokeni yükləmək üçün
export $(cat .env | xargs)
python bot.py
```

Sonra Telegram-da bota ANL linki göndərin:

```
http://web2.anl.az:81/read/page.php?bibid=vtls000415938
```

Bot kitabın bütün səhifələrini yükləyəcək və sizə PDF faylı göndərəcək.

## Testlər

```bash
BOT_TOKEN=test python -m pytest tests/ -v
```

## Layihə Strukturu

```
├── bot.py              # Telegram bot (aiogram v3)
├── anl.py              # ANL kitabxana scraper (async)
├── config.py           # Konfiqurasiya
├── requirements.txt    # Python asılılıqları
├── .env.example        # Mühit dəyişənləri nümunəsi
├── .gitignore
├── tests/
│   └── test_anl.py     # Vahid testlər
└── README.md
```
