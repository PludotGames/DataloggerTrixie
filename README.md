
---

# 📦 DHT22 Datalogger & Migratie Project (Trixie)

Dit project configureert een Raspberry Pi (OS Trixie) als een **volautomatische datalogger** voor temperatuur en luchtvochtigheid met een DHT22 sensor. Data wordt opgeslagen in een MariaDB database en visueel weergegeven via een webinterface.

Het installatiescript automatiseert **alles**, inclusief:

* software installatie
* database setup
* Python omgeving
* webserver configuratie
* cron automatisering
* optionele data migratie (Bookworm → Trixie)

---

## 📁 Mappenstructuur (na installatie)

```
~/bashscripts/        # Installatiescript + README
~/pythonscripts/      # Python scripts + virtual environment (dhtenv)
~/web/                # Jouw website bestanden
```

---

## ⚙️ Installatiestappen (Script Overzicht)

### 🔹 STAP 1: Repository & Bestanden

* GitHub repository wordt automatisch gedownload of geüpdatet
* Bestanden worden verdeeld over:

  * `~/bashscripts`
  * `~/pythonscripts`
  * `~/web`

---

### 🔹 STAP 2: Systeem & Software

Installeert en configureert:

* Apache2 (webserver)
* PHP + MySQL ondersteuning
* MariaDB server
* Python tools (`venv`, `pip`)
* Extra libraries (voor DHT en grafieken)

---

### 🔹 STAP 3: Database Configuratie

Automatisch ingesteld:

* Database: `temperatures`

* Gebruiker:

  * username: `logger`
  * password: `paswoord`

* Tabel:

```
temperaturedata (
    dateandtime DATETIME,
    sensor VARCHAR(32),
    temperature DOUBLE,
    humidity DOUBLE
)
```

👉 Script detecteert zelf:

* nieuwe installatie → beveiligt MariaDB
* bestaande installatie → laat instellingen intact

---

### 🔹 STAP 4: Python Virtual Environment

* Locatie:

```
~/pythonscripts/dhtenv
```

* Geïnstalleerde libraries:

  * `adafruit-circuitpython-dht`
  * `matplotlib`
  * `mysql-connector-python`

---

## 🔄 DATA MIGRATIE (optioneel)

Tijdens installatie kun je oude data importeren.

### Op oude Pi (Bookworm):

```
mysqldump -u root -p temperatures > ~/temperaturesdump_$(date +%Y%m%d%H%M).sql
```

### Kopiëren:

```
scp ~/temperaturesdump_*.sql gebruiker@IP-NIEUWE-PI:~/
```

### Importeren op Trixie:

```
mariadb -u root -p temperatures < ~/temperaturesdump_*.sql
```

👉 Script kan automatisch `.sql` bestanden detecteren en importeren.

---

### 🔹 STAP 5: Webserver

* Webbestanden → `/var/www/html/`
* Map voor grafieken:

```
/var/www/html/afbeeldingen/
```

* Rechten:

```
www-data:www-data
```

---

### 🔹 STAP 6: Automatisering (Cron)

De datalogger draait volledig automatisch via **crontab**.

Elke 15 minuten:

```
# Data loggen
0,15,30,45 * * * * ~/pythonscripts/dhtenv/bin/python ~/pythonscripts/temperatuurlogger.py

# Grafieken genereren
1,16,31,46 * * * * ~/pythonscripts/dhtenv/bin/python ~/pythonscripts/MatplotlibDagTemperatuur.py
2,17,32,47 * * * * ~/pythonscripts/dhtenv/bin/python ~/pythonscripts/MatplotlibWeekTemperatuur.py
3,18,33,48 * * * * ~/pythonscripts/dhtenv/bin/python ~/pythonscripts/MatplotlibAllTimeTemp.py
4,19,34,49 * * * * ~/pythonscripts/dhtenv/bin/python ~/pythonscripts/MatplotLibAllTimeVocht.py
```

---

## 🌐 Toegang tot Dashboard

Na installatie:

```
http://<IP-van-je-Raspberry-Pi>
```

---

## 🚀 Snelle Start

```
git clone https://github.com/PludotGames/DataloggerTrixie.git
cd DataloggerTrixie

chmod +x install_datalogger.sh
./install_datalogger.sh
```

---

## ⚠️ Hardware Waarschuwing

Sluit de sensor **NOOIT aan terwijl de Pi aan staat**.

---

## 🔌 Aansluitschema (DHT22)

| DHT22 | Raspberry Pi    | Functie |
| ----- | --------------- | ------- |
| VCC   | Pin 1 (3.3V)    | Voeding |
| DATA  | Pin 15 (GPIO22) | Signaal |
| GND   | Pin 14          | Massa   |

---

## 🛠️ Handige Commando's

### Data bekijken

```
~/pythonscripts/dhtenv/bin/python ~/pythonscripts/toondata.py
```

### Crontab bekijken

```
crontab -l
```

### Database resetten

```
mariadb -u logger -p -e "TRUNCATE TABLE temperatures.temperaturedata;"
```

---

## ✅ Installatie Voltooid

Je systeem draait nu volledig automatisch:

* sensor uitlezen ✅
* data opslaan ✅
* grafieken genereren ✅
* webinterface updaten ✅

---

If you want, I can also make a **short student version (1 page)** or a **super clean GitHub-style README with badges + screenshots** 👍
