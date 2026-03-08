#!/bin/bash

# =================================================================
# Installatiescript voor Datalogger - Raspberry Pi OS (Trixie)
# Met Data Migratie Module (Bookworm -> Trixie)
# =================================================================

# Stop direct bij fouten
set -e

# Voorkom interactieve vragen (Niet-interactieve modus)
export DEBIAN_FRONTEND=noninteractive
DPKG_OPTS='-o Dpkg::Options::="--force-confold"'

# Functie voor een duidelijke sectietitel
print_titel() {
    echo -e "\n*************************************************************"
    echo "  $1"
    echo "*************************************************************"
}

# Functie voor ja/nee vragen (Default is Nee)
stel_vraag() {
    read -p "$1 (j/N): " antwoord
    if [[ "${antwoord,,}" == "j" || "${antwoord,,}" == "ja" ]]; then
        return 0 
    else
        return 1
    fi
}

# -----------------------------------------------------------------
# START & OVERZICHT
# -----------------------------------------------------------------
clear
print_titel "Datalogger Installatie & Migratie"

REPO_DIR=$(pwd)
BASH_DEST="$HOME/bashscripts"
PYTHON_DEST="$HOME/pythonscripts"
WEB_DEST="$HOME/web"

echo "GEPLANDE MAPPENSTRUCTUUR:"
echo " - Scripts & Docs: $BASH_DEST"
echo " - Python Logica:  $PYTHON_DEST"
echo " - Web Design:     $WEB_DEST"
echo "============================================================="

# Hardware Veiligheid Check
echo -e "\n  BELANGRIJK: HARDWARE VEILIGHEID!"
echo "Zorg dat de Raspberry Pi VOLLEDIG IS UITGESCHAKELD en de"
echo "voedingskabel is losgekoppeld voordat je draden aansluit!"
echo "-------------------------------------------------------------"
echo "1. Is de DHT22 aangesloten op GPIO pin 22?"
echo "2. Is de sensor verbonden met 3.3V en GND?"
echo "-------------------------------------------------------------"

if ! stel_vraag "Is de hardware veilig aangesloten en wil je de installatie starten?"; then
    echo "Installatie afgebroken voor veiligheid."
    exit 0
fi

# -----------------------------------------------------------------
# STAP 1: Mappen en Bestanden organiseren
# -----------------------------------------------------------------
if stel_vraag "Stap 1: Bestanden organiseren naar de nieuwe mappenstructuur?"; then
    print_titel "STAP 1: BESTANDEN ORGANISEREN"
    mkdir -p "$BASH_DEST" "$PYTHON_DEST" "$WEB_DEST"
    
    cp "$REPO_DIR/install_datalogger.sh" "$BASH_DEST/" 2>/dev/null || true
    cp "$REPO_DIR/README.md" "$BASH_DEST/" 2>/dev/null || true
    cp "$REPO_DIR/pythonscripts/"*.py "$PYTHON_DEST/" 2>/dev/null || true
    cp "$REPO_DIR/web/"* "$WEB_DEST/" 2>/dev/null || true
    echo "Bestanden zijn verplaatst naar hun respectievelijke mappen."
fi

# -----------------------------------------------------------------
# STAP 2: Systeem Update & Software
# -----------------------------------------------------------------
if stel_vraag "Stap 2: Systeem updaten en software (Apache, PHP, MariaDB) installeren?"; then
    print_titel "STAP 2: SYSTEEM & SOFTWARE UPDATE"
    echo "Dit kan even duren (geen interactie vereist)..."
    sudo apt update -y && sudo apt upgrade -y $DPKG_OPTS
    sudo apt install apache2 php8.4 php8.4-mysql mariadb-server \
                     python3-venv python3-pip libopenblas-dev \
                     python3-dev pkg-config -y
fi

# -----------------------------------------------------------------
# STAP 3: Database Configuratie
# -----------------------------------------------------------------
if stel_vraag "Stap 3: MariaDB Database en Tabel inrichten?"; then
    print_titel "STAP 3: DATABASE CONFIGURATIE"
    sudo mariadb -u root <<_EOF_
CREATE DATABASE IF NOT EXISTS temperatures;
CREATE USER IF NOT EXISTS 'logger'@'localhost' IDENTIFIED BY 'paswoord';
GRANT ALL PRIVILEGES ON temperatures.* TO 'logger'@'localhost';
FLUSH PRIVILEGES;
USE temperatures;
CREATE TABLE IF NOT EXISTS temperaturedata (
    dateandtime DATETIME, 
    sensor VARCHAR(32), 
    temperature DOUBLE, 
    humidity DOUBLE
);
_EOF_
    echo "Database 'temperatures' en tabel 'temperaturedata' zijn gereed."
fi

# -----------------------------------------------------------------
# STAP 4: Python Omgeving (venv)
# -----------------------------------------------------------------
if stel_vraag "Stap 4: Python Virtual Environment (venv) instellen?"; then
    print_titel "STAP 4: PYTHON OMGEVING"
    python3 -m venv "$PYTHON_DEST/dhtvenv"
    echo "Libraries installeren (Matplotlib kan even duren)..."
    "$PYTHON_DEST/dhtvenv/bin/python" -m pip install --upgrade pip
    "$PYTHON_DEST/dhtvenv/bin/python" -m pip install adafruit-circuitpython-dht matplotlib mysql-connector-python
fi

# -----------------------------------------------------------------
# INTERSPECTIE: DATA MIGRATIE (BOOKWORM -> TRIXIE)
# -----------------------------------------------------------------
print_titel "DATA MIGRATIE MODULE"
if stel_vraag "Wil je nu data importeren van een andere (Bookworm) Raspberry Pi?"; then
    BACKUP_NAAM="temperaturesdump_$(date +%Y%m%d%H%M).sql"
    IP_TRIXIE=$(hostname -I | awk '{print $1}')

    echo "-------------------------------------------------------------"
    echo "VOER DEZE COMMANDO'S UIT OP DE BOOKWORM PI (BRON):"
    echo "1. Backup maken:"
    echo "   sudo mysqldump -u root -p temperatures > ~/temperaturesdump_$(date +%Y%m%d%H%M).sql"
    echo "   of"
    echo "   sudo mysqldump -u root -p temperatures > temperaturesdump_`date +%Y%m%d%H%M`.sql"
    echo "2. Kopieer naar deze Pi:"
    echo "   scp $BACKUP_NAAM $USER@$IP_TRIXIE:~/"
    echo "-------------------------------------------------------------"
    echo "VOER DIT COMMANDO UIT OP DEZE PI (TRIXIE - BESTEMMING):"
    echo "   mariadb -u root -p temperatures < ~/$BACKUP_NAAM"
    echo "-------------------------------------------------------------"
    
    read -p "Druk op [Enter] zodra de import is voltooid..."
else
    echo "Migratie overgeslagen. We gaan verder met een schone database."
fi

# -----------------------------------------------------------------
# STAP 5: Webserver Inrichten
# -----------------------------------------------------------------
if stel_vraag "Stap 5: Jouw web-ontwerp naar de webroot (/var/www/html) kopiëren?"; then
    print_titel "STAP 5: WEBSERVER CONFIGURATIE"
    sudo mkdir -p /var/www/html/afbeeldingen
    sudo cp -r "$WEB_DEST/"* /var/www/html/ 2>/dev/null || true
    sudo chown -R www-data:www-data /var/www/html/
    sudo chmod -R 775 /var/www/html/
    echo "Webserver is ingericht met jouw bestanden."
fi

# -----------------------------------------------------------------
# STAP 6: Automatisering (Cron)
# -----------------------------------------------------------------
if stel_vraag "Stap 6: Cronjobs instellen voor automatische logging?"; then
    print_titel "STAP 6: AUTOMATISERING"
    PYTHON_BIN="$PYTHON_DEST/dhtvenv/bin/python"
    LOGGER_SCRIPT="$PYTHON_DEST/temperatuurlogger.py"
    GRAFIEK_SCRIPT="$PYTHON_DEST/BewaarTempGrafiek.py"
    IMG_NAME="Raspi25Temperatuur.png"

    sudo bash -c "cat <<_EOF_ > /etc/cron.d/datalogger
# Logging elke 15 minuten (user $USER)
0,15,30,45 * * * * $USER $PYTHON_BIN $LOGGER_SCRIPT

# Grafiek genereren en verplaatsen (root)
2,17,32,47 * * * * root $PYTHON_BIN $GRAFIEK_SCRIPT && cp $HOME/$IMG_NAME /var/www/html/afbeeldingen/$IMG_NAME
_EOF_"
    echo "Cronjobs geactiveerd in /etc/cron.d/datalogger."
fi

print_titel "INSTALLATIE VOLTOOID!"
echo "Bezoek je website op: http://$(hostname -I | awk '{print $1}')"
echo "Beheer je scripts in: $BASH_DEST"
