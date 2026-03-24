#!/bin/bash

# =================================================================
# Installatiescript voor Datalogger - Raspberry Pi OS (Trixie)
# Met Data Migratie Module (Bookworm -> Trixie)
# Bronnen: github.com/PludotGames/DataloggerTrixie
# =================================================================

# Stop direct bij fouten
set -e

# Voorkom interactieve vragen
export DEBIAN_FRONTEND=noninteractive

# -----------------------------------------------------------------
# CONFIGURATIE
# -----------------------------------------------------------------

# Bepaal de echte gebruiker (ook als het script via sudo wordt uitgevoerd)
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
elif [ -n "$LOGNAME" ] && [ "$LOGNAME" != "root" ]; then
    REAL_USER="$LOGNAME"
else
    REAL_USER=$(logname 2>/dev/null || whoami)
fi
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

REPO_URL="https://github.com/PludotGames/DataloggerTrixie.git"
REPO_DIR="$REAL_HOME/.datalogger_repo"
BASH_DEST="$REAL_HOME/bashscripts"
PYTHON_DEST="$REAL_HOME/pythonscripts"
WEB_DEST="$REAL_HOME/web"
VENV="$PYTHON_DEST/dhtenv"
AFBEELDINGEN_DIR="$REAL_HOME/Afbeeldingen"

# -----------------------------------------------------------------
# HULPFUNCTIES
# -----------------------------------------------------------------
print_titel() {
    echo -e "\n*************************************************************"
    echo "  $1"
    echo "*************************************************************"
}

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
print_titel "Datalogger Installatie & Migratie (Trixie)"

echo "GEPLANDE MAPPENSTRUCTUUR:"
echo " - Gebruiker:      $REAL_USER ($REAL_HOME)"
echo " - Scripts & Docs: $BASH_DEST"
echo " - Python Logica:  $PYTHON_DEST"
echo " - Web Design:     $WEB_DEST"
echo " - Afbeeldingen:   $AFBEELDINGEN_DIR"
echo "============================================================="
echo ""
echo "BRONREPOSITORY:"
echo " $REPO_URL"
echo "============================================================="

# Hardware Veiligheid Check
echo -e "\n   BELANGRIJK: HARDWARE VEILIGHEID!"
echo "Sluit NOOIT sensoren aan terwijl de Pi aan staat."
echo "-------------------------------------------------------------"
echo "Aansluitschema DHT22:"
echo "  VCC  -> Pin 1  (3.3V)"
echo "  Data -> Pin 15 (GPIO 22)"
echo "  GND  -> Pin 14 (Ground)"
echo "-------------------------------------------------------------"

if ! stel_vraag "Is de hardware veilig aangesloten en wil je de installatie starten?"; then
    echo "Installatie afgebroken."
    exit 0
fi

# -----------------------------------------------------------------
# STAP 1: Repository ophalen & Bestanden organiseren
# -----------------------------------------------------------------
if stel_vraag "Stap 1: Bestanden ophalen van GitHub en organiseren?"; then
    print_titel "STAP 1: REPOSITORY & BESTANDEN ORGANISEREN"

    # Zorg dat git aanwezig is
    if ! command -v git &>/dev/null; then
        echo "git niet gevonden, wordt geinstalleerd..."
        sudo apt-get install -y git
    fi

    # Clone of update de repository
    if [ -d "$REPO_DIR/.git" ]; then
        echo "Repository bestaat al, bijwerken..."
        git -C "$REPO_DIR" pull --quiet
        echo "Repository bijgewerkt."
    else
        echo "Repository ophalen van GitHub..."
        rm -rf "$REPO_DIR"
        git clone --quiet "$REPO_URL" "$REPO_DIR"
        echo "Repository gekloond."
    fi

    # Doelmappen aanmaken en eigendom toewijzen aan de echte gebruiker
    mkdir -p "$BASH_DEST" "$PYTHON_DEST" "$WEB_DEST" "$AFBEELDINGEN_DIR"
    chown -R "$REAL_USER:$REAL_USER" "$BASH_DEST" "$PYTHON_DEST" "$WEB_DEST" "$REPO_DIR" "$AFBEELDINGEN_DIR"
    echo "Map $AFBEELDINGEN_DIR aangemaakt voor gegenereerde grafieken."

    # Installatiescript en README naar bashscripts
    cp "$0" "$BASH_DEST/install_datalogger.sh" 2>/dev/null || true
    [ -f "$REPO_DIR/README.md" ] && cp "$REPO_DIR/README.md" "$BASH_DEST/" && echo "README.md gekopieerd."

    # Python scripts vanuit de repository
    if [ -d "$REPO_DIR/pythonscripts" ]; then
        cp "$REPO_DIR/pythonscripts/"*.py "$PYTHON_DEST/" 2>/dev/null || true
        echo "Python scripts gekopieerd van GitHub naar $PYTHON_DEST."
    else
        echo "Geen pythonscripts map gevonden in de repository (overgeslagen)."
    fi

    # Webbestanden vanuit de repository
    if [ -d "$REPO_DIR/web" ]; then
        cp -r "$REPO_DIR/web/"* "$WEB_DEST/" 2>/dev/null || true
        echo "Webbestanden gekopieerd van GitHub naar $WEB_DEST."
    else
        echo "Geen web map gevonden in de repository (overgeslagen)."
    fi

    echo "Bestanden zijn georganiseerd in $REAL_HOME."
fi

# -----------------------------------------------------------------
# STAP 2: Systeem Update & Software
# -----------------------------------------------------------------
if stel_vraag "Stap 2: Systeem updaten en software (Apache, PHP, MariaDB) installeren?"; then
    print_titel "STAP 2: SYSTEEM & SOFTWARE UPDATE"
    echo "Dit kan even duren (geen interactie vereist)..."

    sudo apt-get update -y

    sudo apt-get upgrade -y \
        -o Dpkg::Options::="--force-confdef" \
        -o Dpkg::Options::="--force-confold"

    sudo apt-get install -y \
        apache2 \
        php \
        php-mysql \
        mariadb-server \
        python3-venv \
        python3-pip \
        libopenblas-dev \
        python3-dev \
        pkg-config \
        libgpiod3

    # Services activeren
    sudo systemctl enable --now apache2 mariadb 2>/dev/null || true

    echo "Alle software is geinstalleerd en services zijn gestart."
fi

# -----------------------------------------------------------------
# STAP 3: Database Configuratie
# -----------------------------------------------------------------
if stel_vraag "Stap 3: MariaDB beveiligen en Database + Tabel inrichten?"; then
    print_titel "STAP 3: DATABASE CONFIGURATIE"

    ROOT_DB_PASS="stemdb"

    # --- Detectie: is MariaDB al geconfigureerd? ---
    # Test of root zonder wachtwoord kan inloggen (= verse installatie)
    # Als dat lukt -> beveiligen + inrichten
    # Als dat mislukt -> MariaDB is al beveiligd, alleen DB/tabel aanmaken
    DB_REEDS_BEVEILIGD=false
    if sudo mariadb -u root -e "SELECT 1;" &>/dev/null; then
        DB_REEDS_BEVEILIGD=false
        echo "Verse MariaDB installatie gedetecteerd -> beveiligen en inrichten..."
    elif sudo mariadb -u root -p"${ROOT_DB_PASS}" -e "SELECT 1;" &>/dev/null; then
        DB_REEDS_BEVEILIGD=true
        echo "MariaDB al beveiligd met wachtwoord '$ROOT_DB_PASS' -> alleen DB/tabel controleren..."
    else
        echo ""
        echo "MariaDB is al beveiligd met een onbekend wachtwoord."
        read -p "  Voer het huidige MariaDB root wachtwoord in: " ROOT_DB_PASS
        DB_REEDS_BEVEILIGD=true
    fi

    # --- 3a: MariaDB beveiligen (alleen bij verse installatie) ---
    if [ "$DB_REEDS_BEVEILIGD" = false ]; then
        echo "MariaDB beveiligen..."
        sudo mariadb -u root <<_SECURE_
-- Anonieme gebruikers verwijderen
DELETE FROM mysql.user WHERE User='';
-- Remote root login verbieden
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
-- Test database verwijderen
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\_%';
-- Root wachtwoord instellen
ALTER USER 'root'@'localhost' IDENTIFIED BY '${ROOT_DB_PASS}';
-- Privileges herladen
FLUSH PRIVILEGES;
_SECURE_
        echo "MariaDB is beveiligd (root wachtwoord ingesteld op: $ROOT_DB_PASS)."
    else
        echo "Beveiliging overgeslagen (al geconfigureerd)."
    fi

    # --- 3b: Database, gebruiker en tabel aanmaken (altijd, IF NOT EXISTS is veilig) ---
    echo "Database en tabel controleren/aanmaken..."
    sudo mariadb -u root -p"${ROOT_DB_PASS}" <<_EOF_
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
    echo ""
    echo "  MariaDB root wachtwoord : $ROOT_DB_PASS"
    echo "  Logger gebruiker        : logger / paswoord"
fi

# -----------------------------------------------------------------
# STAP 4: Python Omgeving (venv)
# -----------------------------------------------------------------
if stel_vraag "Stap 4: Python Virtual Environment (venv) instellen?"; then
    print_titel "STAP 4: PYTHON OMGEVING"

    sudo -u "$REAL_USER" python3 -m venv "$VENV"
    echo "Virtual environment aangemaakt in $VENV."

    echo "Libraries installeren (Adafruit DHT, Matplotlib, MySQL)..."
    sudo -u "$REAL_USER" "$VENV/bin/python" -m pip install --upgrade pip --quiet
    sudo -u "$REAL_USER" "$VENV/bin/python" -m pip install --quiet \
        adafruit-circuitpython-dht \
        matplotlib \
        mysql-connector-python

    echo "Alle Python libraries zijn geinstalleerd."
fi

# -----------------------------------------------------------------
# INTERSPECTIE: DATA MIGRATIE
# -----------------------------------------------------------------
print_titel "DATA MIGRATIE MODULE"
if stel_vraag "Wil je nu data importeren van een andere (Bookworm) Raspberry Pi?"; then
    IP_TRIXIE=$(hostname -I | awk '{print $1}')

    echo "-------------------------------------------------------------"
    echo "STAP A - VOER DIT UIT OP DE OUDE PI (BRON / BOOKWORM):"
    echo ""
    echo "  1. Backup maken:"
    echo "     sudo mysqldump -u root -p temperatures > ~/temperaturesdump_\$(date +%Y%m%d%H%M).sql"
    echo ""
    echo "  2. Kopieren naar deze Pi:"
    echo "     scp ~/temperaturesdump_*.sql $REAL_USER@$IP_TRIXIE:~/"
    echo "-------------------------------------------------------------"
    echo "STAP B - VOER DIT UIT OP DEZE PI (TRIXIE) NA DE OVERDRACHT:"
    echo ""
    echo "  mariadb -u root -p temperatures < ~/temperaturesdump_*.sql"
    echo "-------------------------------------------------------------"
    echo ""

    # Zoek automatisch naar .sql bestanden in de home map
    SQL_BESTANDEN=("$REAL_HOME"/*.sql)
    if [ -e "${SQL_BESTANDEN[0]}" ]; then
        echo "Gevonden .sql bestanden in je home map:"
        for f in "${SQL_BESTANDEN[@]}"; do
            echo "  -> $(basename "$f")"
        done
        echo ""
        if stel_vraag "Wil je nu een van deze bestanden importeren?"; then
            read -p "Voer de volledige bestandsnaam in (bijv. ~/temperaturesdump_202501.sql): " SQL_BESTAND
            SQL_BESTAND="${SQL_BESTAND/#\~/$REAL_HOME}"
            if [ -f "$SQL_BESTAND" ]; then
                echo "Importeren van $SQL_BESTAND ..."
                sudo mariadb temperatures < "$SQL_BESTAND"
                RIJEN=$(sudo mariadb -N -e "SELECT COUNT(*) FROM temperatures.temperaturedata;" 2>/dev/null || echo "?")
                echo "Import geslaagd! Aantal rijen in tabel: $RIJEN"
            else
                echo "Bestand niet gevonden: $SQL_BESTAND (later handmatig importeren)."
            fi
        fi
    else
        read -p "Druk op [Enter] zodra je klaar bent met de overdracht en verder wil gaan..."
    fi
fi

# -----------------------------------------------------------------
# STAP 5: Webserver Inrichten
# -----------------------------------------------------------------
if stel_vraag "Stap 5: Web-ontwerp naar de webroot (/var/www/html) kopieren?"; then
    print_titel "STAP 5: WEBSERVER CONFIGURATIE"

    # Benodigde mappen aanmaken (inclusief Assets voor grafieken)
    sudo mkdir -p /var/www/html/Assets

    # Standaard Apache index.html verwijderen indien aanwezig
    if [ -f /var/www/html/index.html ]; then
        echo "Standaard Apache index.html gevonden, wordt verwijderd..."
        sudo rm /var/www/html/index.html
    fi

    # Webbestanden kopieren naar de webroot
    if [ -d "$WEB_DEST" ] && [ "$(ls -A "$WEB_DEST" 2>/dev/null)" ]; then
        sudo cp -r "$WEB_DEST/"* /var/www/html/ 2>/dev/null || true
        echo "Webbestanden gekopieerd naar /var/www/html/."
    else
        echo "Geen webbestanden gevonden in $WEB_DEST (overgeslagen)."
    fi

    # Rechten instellen voor de webserver
    sudo chown -R www-data:www-data /var/www/html/
    sudo chmod -R 775 /var/www/html/

    sudo systemctl reload apache2
    echo "Webserver is ingericht."
fi

# -----------------------------------------------------------------
# STAP 6: Automatisering (Cron via crontab)
# -----------------------------------------------------------------
if stel_vraag "Stap 6: Cronjobs instellen in jouw persoonlijke crontab?"; then
    print_titel "STAP 6: AUTOMATISERING (CRON)"

    # Bestaande crontab ophalen maar oude regels van dit project verwijderen
    # (zodat herinstallatie geen dubbele regels geeft)
    sudo -u "$REAL_USER" crontab -l 2>/dev/null > /tmp/temp_cron || true
    grep -v "pythonscripts" /tmp/temp_cron | grep -v "afbeeldingen" | grep -v "Assets" > /tmp/temp_cron2 || true
    mv /tmp/temp_cron2 /tmp/temp_cron

    # Absolute paden uitbreiden zodat cron ze kan vinden (cron heeft geen shell-omgeving)
    VENV_ABS=$(realpath "$VENV")
    PYTHON_ABS=$(realpath "$PYTHON_DEST")
    AFBEELDINGEN_ABS=$(realpath "$AFBEELDINGEN_DIR")

    cat >> /tmp/temp_cron <<CRONEOF

# --- DHT22 Datalogger (automatisch ingesteld door install_datalogger.sh) ---
# Elke 15 minuten: sensor uitlezen en opslaan in de database
0,15,30,45 * * * * ${VENV_ABS}/bin/python ${PYTHON_ABS}/temperatuurlogger.py

# Elke 15 minuten: daggrafiek genereren
1,16,31,46 * * * * ${VENV_ABS}/bin/python ${PYTHON_ABS}/MatplotlibDagTemperatuur.py

# Elke 15 minuten: weekgrafiek genereren
2,17,32,47 * * * * ${VENV_ABS}/bin/python ${PYTHON_ABS}/MatplotlibWeekTemperatuur.py

# Elke 15 minuten: all-time temperatuurgrafiek genereren
3,18,33,48 * * * * ${VENV_ABS}/bin/python ${PYTHON_ABS}/MatplotlibAllTimeTemp.py

# Elke 15 minuten: all-time vochtigheidsgraafiek genereren
4,19,34,49 * * * * ${VENV_ABS}/bin/python ${PYTHON_ABS}/MatplotLibAllTimeVocht.py

# Elke 15 minuten: grafieken kopiëren naar de webserver (na generatie)
5,20,35,50 * * * * cp ${AFBEELDINGEN_ABS}/*.png /var/www/html/Assets/ 2>/dev/null || true

CRONEOF

    sudo -u "$REAL_USER" crontab /tmp/temp_cron
    rm /tmp/temp_cron

    sudo systemctl enable cron 2>/dev/null || true
    sudo systemctl start cron 2>/dev/null || true

    echo "Cronjobs toegevoegd aan je crontab."
    echo "Grafieken worden elke 15 minuten gekopieerd van $AFBEELDINGEN_DIR naar /var/www/html/Assets/."
    echo "Controleer met: crontab -l"
fi

# -----------------------------------------------------------------
# INSTALLATIE VOLTOOID
# -----------------------------------------------------------------
print_titel "INSTALLATIE VOLTOOID!"
IP=$(hostname -I | awk '{print $1}')
echo "Dashboard     : http://$IP"
echo "Database      : temperatures | gebruiker: logger | ww: paswoord"
echo "Python venv   : $VENV"
echo "Afbeeldingen  : $AFBEELDINGEN_DIR -> /var/www/html/Assets/"
echo ""
echo "Handige commando's:"
echo "  Data bekijken : $VENV/bin/python $PYTHON_DEST/toondata.py"
echo "  Crontab check : crontab -l"
echo "  Tabel resetten: mariadb -u logger -p -e \"TRUNCATE TABLE temperatures.temperaturedata;\""
echo "============================================================="
