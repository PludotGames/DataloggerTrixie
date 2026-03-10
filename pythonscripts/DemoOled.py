import psutil
import socket
import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import ImageFont
import RPi.GPIO as GPIO
import math

# Setup OLED display
serial = i2c(port=1, address=0x3C)
device = sh1106(serial)

# Rotary encoder pins
CLK_PIN = 19
DT_PIN = 26
SW_PIN = 13

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)#!/usr/bin/env python3
"""
OLED Display met Burn-in Preventie
- Screensaver na inactiviteit
- Pixel shifting
- Automatisch dimmen
"""
import psutil
import socket
import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
import RPi.GPIO as GPIO
import math
import random

# Setup OLED display
serial = i2c(port=1, address=0x3C)
device = sh1106(serial)

# Rotary encoder pins
CLK_PIN = 19
DT_PIN = 26
SW_PIN = 13

# Setup GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Global variables
current_screen = 0
num_screens = 6
clk_last_state = GPIO.input(CLK_PIN)
rotation_counter = 0
STEPS_PER_SCREEN = 1
animation_frame = 0
last_screen = -1
last_display_update = 0
DISPLAY_UPDATE_INTERVAL = 1.0
last_rotation_time = 0
ROTATION_DEBOUNCE = 0.05

# BURN-IN PREVENTIE SETTINGS
last_activity_time = time.time()
SCREENSAVER_TIMEOUT = 120  # 2 minuten inactiviteit → screensaver
screensaver_active = False
pixel_shift_x = 0
pixel_shift_y = 0
PIXEL_SHIFT_MAX = 2  # Max pixels om te verschuiven
shift_change_interval = 10  # Verander shift elke 10 seconden
last_shift_change = time.time()

# Contrast/helderheid cyclus
contrast_level = 255  # Start op volle helderheid
DIM_AFTER = 60  # Dim na 1 minuut
last_dim_update = time.time()

def reset_activity():
    """Reset activity timer (bij interactie)"""
    global last_activity_time, screensaver_active, contrast_level
    last_activity_time = time.time()
    if screensaver_active:
        screensaver_active = False
        contrast_level = 255
        device.contrast(contrast_level)
        print("Screensaver gedeactiveerd")

def update_pixel_shift():
    """Update pixel shift om burn-in te voorkomen"""
    global pixel_shift_x, pixel_shift_y, last_shift_change

    current_time = time.time()
    if current_time - last_shift_change >= shift_change_interval:
        pixel_shift_x = random.randint(-PIXEL_SHIFT_MAX, PIXEL_SHIFT_MAX)
        pixel_shift_y = random.randint(-PIXEL_SHIFT_MAX, PIXEL_SHIFT_MAX)
        last_shift_change = current_time

def update_contrast():
    """Dim display na inactiviteit"""
    global contrast_level, last_dim_update

    if screensaver_active:
        return

    current_time = time.time()
    time_inactive = current_time - last_activity_time

    # Geleidelijk dimmen na DIM_AFTER seconden
    if time_inactive > DIM_AFTER:
        target_contrast = 100  # Dim naar 100
        if contrast_level > target_contrast:
            contrast_level = max(target_contrast, contrast_level - 5)
            device.contrast(contrast_level)
    else:
        # Terug naar vol als recent actief
        if contrast_level < 255:
            contrast_level = min(255, contrast_level + 10)
            device.contrast(contrast_level)

def check_screensaver():
    """Check of screensaver moet activeren"""
    global screensaver_active, contrast_level

    time_inactive = time.time() - last_activity_time

    if not screensaver_active and time_inactive > SCREENSAVER_TIMEOUT:
        screensaver_active = True
        contrast_level = 80  # Extra dim voor screensaver
        device.contrast(contrast_level)
        print("Screensaver geactiveerd")

def draw_screensaver(draw):
    """Teken minimalistische screensaver"""
    # Bouncing clock met tijd
    current_time = time.strftime("%H:%M")

    # Gebruik pixel shift voor beweging
    x = 30 + pixel_shift_x * 10
    y = 25 + pixel_shift_y * 10

    # Zorg dat text binnen scherm blijft
    x = max(0, min(80, x))
    y = max(0, min(50, y))

    draw.text((x, y), current_time, fill="white")

    # Klein icoon dat beweegt
    icon_x = 100 + (pixel_shift_x * 5)
    icon_y = 10 + (pixel_shift_y * 5)
    draw.ellipse([icon_x, icon_y, icon_x+5, icon_y+5], outline="white")

def draw_progress_bar(draw, x, y, width, height, percentage, fill_color="white"):
    """Teken progress bar met pixel shift"""
    x += pixel_shift_x
    y += pixel_shift_y
    draw.rectangle([x, y, x + width, y + height], outline=fill_color, fill=None)
    fill_width = int((width - 2) * (percentage / 100))
    if fill_width > 0:
        draw.rectangle([x + 1, y + 1, x + 1 + fill_width, y + height - 1], fill=fill_color)

def draw_circular_progress(draw, cx, cy, radius, percentage, thickness=3):
    """Teken circulaire progress met pixel shift"""
    cx += pixel_shift_x
    cy += pixel_shift_y
    angle = int(360 * (percentage / 100))
    for i in range(thickness):
        r = radius - i
        for deg in range(0, angle, 3):
            rad = math.radians(deg - 90)
            x1 = cx + int(r * math.cos(rad))
            y1 = cy + int(r * math.sin(rad))
            draw.point((x1, y1), fill="white")

def draw_header(draw, title, icon=""):
    """Teken header met pixel shift"""
    y_offset = pixel_shift_y
    draw.rectangle([0, y_offset, 128, 12 + y_offset], fill="white")
    draw.text((2 + pixel_shift_x, 2 + y_offset), f"{icon} {title}", fill="black")

def draw_text(draw, pos, text, fill="white"):
    """Helper voor text met pixel shift"""
    x, y = pos
    draw.text((x + pixel_shift_x, y + pixel_shift_y), text, fill=fill)

def get_ip():
    """Verkrijg IP-adres"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "N/A"

def get_network_info():
    """Krijg netwerk informatie"""
    hostname = socket.gethostname()
    ip = get_ip()
    try:
        net_io = psutil.net_io_counters()
        bytes_sent = net_io.bytes_sent / (1024 * 1024)
        bytes_recv = net_io.bytes_recv / (1024 * 1024)
    except:
        bytes_sent = 0
        bytes_recv = 0
    return hostname, ip, bytes_sent, bytes_recv

def get_cpu_info():
    """Krijg CPU informatie"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_freq = psutil.cpu_freq()
    try:
        cpu_temp = psutil.sensors_temperatures().get('cpu_thermal', [])[0].current
    except:
        cpu_temp = 0
    cpu_count = psutil.cpu_count()
    return cpu_percent, cpu_freq.current if cpu_freq else 0, cpu_temp, cpu_count

def get_memory_info():
    """Krijg geheugen informatie"""
    memory = psutil.virtual_memory()
    total_mb = memory.total / (1024 * 1024)
    used_mb = memory.used / (1024 * 1024)
    available_mb = memory.available / (1024 * 1024)
    return memory.percent, total_mb, used_mb, available_mb

def get_disk_info():
    """Krijg schijf informatie"""
    disk = psutil.disk_usage('/')
    total_gb = disk.total / (1024 * 1024 * 1024)
    used_gb = disk.used / (1024 * 1024 * 1024)
    free_gb = disk.free / (1024 * 1024 * 1024)
    return disk.percent, total_gb, used_gb, free_gb

def get_process_info():
    """Krijg top processen"""
    processes = []
    for proc in psutil.process_iter(['name', 'cpu_percent']):
        try:
            processes.append((proc.info['name'], proc.info['cpu_percent']))
        except:
            pass
    processes.sort(key=lambda x: x[1], reverse=True)
    return processes[:3]

def get_uptime():
    """Krijg uptime"""
    uptime_seconds = time.time() - psutil.boot_time()
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    return days, hours, minutes

def display_overview(draw, frame):
    """Scherm 0: Overzicht"""
    draw_header(draw, "SYSTEM", "◆")

    cpu_usage = psutil.cpu_percent()
    try:
        cpu_temp = psutil.sensors_temperatures().get('cpu_thermal', [])[0].current
    except:
        cpu_temp = 0
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    draw_circular_progress(draw, 20, 32, 12, cpu_usage)
    draw_text(draw, (10, 46), "CPU")
    draw_text(draw, (6, 54), f"{cpu_usage:.0f}%")

    draw_circular_progress(draw, 64, 32, 12, memory.percent)
    draw_text(draw, (54, 46), "RAM")
    draw_text(draw, (50, 54), f"{memory.percent:.0f}%")

    draw_circular_progress(draw, 108, 32, 12, disk.percent)
    draw_text(draw, (97, 46), "DISK")
    draw_text(draw, (98, 54), f"{disk.percent:.0f}%")

def display_network(draw, frame):
    """Scherm 1: Netwerk"""
    draw_header(draw, "NETWORK", "◈")

    hostname, ip, sent, recv = get_network_info()

    draw_text(draw, (2, 16), "Host:")
    draw_text(draw, (35, 16), hostname[:12])

    x, y = 2 + pixel_shift_x, 26 + pixel_shift_y
    draw.rectangle([x, y, x+124, y+11], outline="white")
    draw_text(draw, (4, 28), ip)

    draw_text(draw, (2, 42), "↑ TX")
    max_val = max(sent, recv, 100)
    draw_progress_bar(draw, 30, 42, 96, 8, (sent / max_val) * 100)

    draw_text(draw, (2, 52), "↓ RX")
    draw_progress_bar(draw, 30, 52, 96, 8, (recv / max_val) * 100)

def display_cpu(draw, frame):
    """Scherm 2: CPU"""
    draw_header(draw, "CPU", "◉")

    cpu_percent, cpu_freq, cpu_temp, cpu_count = get_cpu_info()

    draw_circular_progress(draw, 64, 38, 20, cpu_percent, thickness=4)
    draw_text(draw, (50, 34), f"{cpu_percent:.1f}%")

    draw_text(draw, (2, 16), f"Freq: {cpu_freq:.0f} MHz")

    draw_text(draw, (2, 26), "Temp:")
    temp_percent = min((cpu_temp / 80) * 100, 100)
    draw_progress_bar(draw, 40, 26, 86, 8, temp_percent)
    draw_text(draw, (100, 16), f"{cpu_temp:.1f}°C")

    draw_text(draw, (2, 56), f"Cores: {cpu_count}")
    draw_text(draw, (100, 56), f"[2/{num_screens}]")

def display_memory(draw, frame):
    """Scherm 3: Geheugen"""
    draw_header(draw, "MEMORY", "◊")

    percent, total, used, available = get_memory_info()

    draw_text(draw, (40, 18), f"{percent:.1f}%")
    x, y = 38 + pixel_shift_x, 16 + pixel_shift_y
    draw.rectangle([x, y, x+52, y+12], outline="white")

    draw_text(draw, (2, 32), "Total:")
    draw_text(draw, (50, 32), f"{total:.0f} MB")

    draw_text(draw, (2, 42), "Used:")
    draw_progress_bar(draw, 50, 42, 76, 8, percent)

    draw_text(draw, (2, 52), "Free:")
    draw_progress_bar(draw, 50, 52, 76, 8, (available / total) * 100)

    draw_text(draw, (100, 56), f"[3/{num_screens}]")

def display_disk(draw, frame):
    """Scherm 4: Disk"""
    draw_header(draw, "STORAGE", "◐")

    percent, total, used, free = get_disk_info()

    draw_circular_progress(draw, 32, 38, 18, percent, thickness=5)
    draw_text(draw, (20, 34), f"{percent:.0f}%")

    draw_text(draw, (60, 20), f"Total:")
    draw_text(draw, (95, 20), f"{total:.1f}GB")

    draw_text(draw, (60, 32), f"Used:")
    draw_text(draw, (95, 32), f"{used:.1f}GB")

    draw_text(draw, (60, 44), f"Free:")
    draw_text(draw, (95, 44), f"{free:.1f}GB")

    draw_text(draw, (100, 56), f"[4/{num_screens}]")

def display_uptime(draw, frame):
    """Scherm 5: Uptime"""
    draw_header(draw, "UPTIME", "◔")

    days, hours, minutes = get_uptime()
    processes = get_process_info()

    x, y = 2 + pixel_shift_x, 16 + pixel_shift_y
    draw.rectangle([x, y, x+124, y+16], outline="white")
    uptime_str = f"{days}d {hours:02d}h {minutes:02d}m"
    draw_text(draw, (18, 20), uptime_str)

    draw_text(draw, (2, 36), "Top Processes:")
    y_pos = 46
    for i, (name, cpu) in enumerate(processes[:2]):
        name_short = name[:12]
        draw_text(draw, (2, y_pos), f"• {name_short}")
        draw_text(draw, (90, y_pos), f"{cpu:.0f}%")
        y_pos += 9

    draw_text(draw, (100, 56), f"[5/{num_screens}]")

def rotary_encoder_check():
    """Check rotary encoder"""
    global current_screen, clk_last_state, rotation_counter, last_screen, last_rotation_time

    current_time = time.time()

    if current_time - last_rotation_time < ROTATION_DEBOUNCE:
        return

    clk_state = GPIO.input(CLK_PIN)
    dt_state = GPIO.input(DT_PIN)

    if clk_state != clk_last_state:
        last_rotation_time = current_time
        clk_last_state = clk_state
        reset_activity()  # Reset screensaver timer

        if clk_state == 0:
            if dt_state == 0:
                rotation_counter += 1
            else:
                rotation_counter -= 1

            if rotation_counter >= STEPS_PER_SCREEN:
                current_screen = (current_screen + 1) % num_screens
                rotation_counter = 0
                last_screen = -1
                print(f"→ Scherm {current_screen + 1}/{num_screens}")
                time.sleep(0.15)

            elif rotation_counter <= -STEPS_PER_SCREEN:
                current_screen = (current_screen - 1) % num_screens
                rotation_counter = 0
                last_screen = -1
                print(f"← Scherm {current_screen + 1}/{num_screens}")
                time.sleep(0.15)

try:
    print("🎨 OLED Display met Burn-in Preventie gestart!")
    print(f"⏱️  Screensaver na {SCREENSAVER_TIMEOUT}s inactiviteit")
    print(f"🔅 Dimmen na {DIM_AFTER}s inactiviteit")
    print(f"🔄 Pixel shift elke {shift_change_interval}s")
    print("Druk Ctrl+C om te stoppen")

    last_screen = -1

    while True:
        rotary_encoder_check()

        # Update burn-in preventie
        update_pixel_shift()
        update_contrast()
        check_screensaver()

        current_time = time.time()
        screen_changed = (current_screen != last_screen)
        time_to_update = (current_time - last_display_update >= DISPLAY_UPDATE_INTERVAL)

        if screen_changed or time_to_update or screensaver_active:
            animation_frame += 1
            last_display_update = current_time
            last_screen = current_screen

            with canvas(device) as draw:
                if screensaver_active:
                    draw_screensaver(draw)
                elif current_screen == 0:
                    display_overview(draw, animation_frame)
                elif current_screen == 1:
                    display_network(draw, animation_frame)
                elif current_screen == 2:
                    display_cpu(draw, animation_frame)
                elif current_screen == 3:
                    display_memory(draw, animation_frame)
                elif current_screen == 4:
                    display_disk(draw, animation_frame)
                elif current_screen == 5:
                    display_uptime(draw, animation_frame)

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n✨ Programma gestopt")
finally:
    device.clear()
    device.contrast(255)  # Reset contrast
    GPIO.cleanup()
    device.cleanup()
GPIO.setup(SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Global variables
current_screen = 0
num_screens = 6
clk_last_state = GPIO.input(CLK_PIN)
rotation_counter = 0
STEPS_PER_SCREEN = 1 # Verhoogd naar 4 voor stabielere rotatie
animation_frame = 0
last_screen = -1  # Track if screen changed
last_display_update = 0
DISPLAY_UPDATE_INTERVAL = 1.0  # Update display every 1 second
last_rotation_time = 0
ROTATION_DEBOUNCE = 0.05  # 50ms tussen rotatie checks
animation_frame = 0

def draw_progress_bar(draw, x, y, width, height, percentage, fill_color="white"):
    """Teken een mooie progress bar"""
    # Border
    draw.rectangle([x, y, x + width, y + height], outline=fill_color, fill=None)
    # Fill
    fill_width = int((width - 2) * (percentage / 100))
    if fill_width > 0:
        draw.rectangle([x + 1, y + 1, x + 1 + fill_width, y + height - 1], fill=fill_color)

def draw_circular_progress(draw, cx, cy, radius, percentage, thickness=3):
    """Teken een circulaire progress indicator"""
    angle = int(360 * (percentage / 100))
    for i in range(thickness):
        r = radius - i
        for deg in range(0, angle, 3):
            rad = math.radians(deg - 90)
            x1 = cx + int(r * math.cos(rad))
            y1 = cy + int(r * math.sin(rad))
            draw.point((x1, y1), fill="white")

def draw_header(draw, title, icon=""):
    """Teken een stijlvolle header"""
    draw.rectangle([0, 0, 128, 12], fill="white")
    draw.text((2, 2), f"{icon} {title}", fill="black")

def draw_animated_dots(draw, x, y, frame):
    """Teken geanimeerde dots"""
    dots = ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"]
    dot = dots[frame % len(dots)]
    draw.text((x, y), dot, fill="white")

def get_ip():
    """Verkrijg het IP-adres"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "N/A"
    finally:
        s.close()
    return ip

def get_network_info():
    """Krijg netwerk informatie"""
    hostname = socket.gethostname()
    ip = get_ip()
    try:
        net_io = psutil.net_io_counters()
        bytes_sent = net_io.bytes_sent / (1024 * 1024)
        bytes_recv = net_io.bytes_recv / (1024 * 1024)
    except:
        bytes_sent = 0
        bytes_recv = 0
    return hostname, ip, bytes_sent, bytes_recv

def get_cpu_info():
    """Krijg CPU informatie"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_freq = psutil.cpu_freq()
    try:
        cpu_temp = psutil.sensors_temperatures().get('cpu_thermal', [])[0].current
    except:
        cpu_temp = 0
    cpu_count = psutil.cpu_count()
    return cpu_percent, cpu_freq.current if cpu_freq else 0, cpu_temp, cpu_count

def get_memory_info():
    """Krijg geheugen informatie"""
    memory = psutil.virtual_memory()
    total_mb = memory.total / (1024 * 1024)
    used_mb = memory.used / (1024 * 1024)
    available_mb = memory.available / (1024 * 1024)
    return memory.percent, total_mb, used_mb, available_mb

def get_disk_info():
    """Krijg schijf informatie"""
    disk = psutil.disk_usage('/')
    total_gb = disk.total / (1024 * 1024 * 1024)
    used_gb = disk.used / (1024 * 1024 * 1024)
    free_gb = disk.free / (1024 * 1024 * 1024)
    return disk.percent, total_gb, used_gb, free_gb

def get_process_info():
    """Krijg top processen"""
    processes = []
    for proc in psutil.process_iter(['name', 'cpu_percent']):
        try:
            processes.append((proc.info['name'], proc.info['cpu_percent']))
        except:
            pass
    processes.sort(key=lambda x: x[1], reverse=True)
    return processes[:3]

def get_uptime():
    """Krijg uptime"""
    uptime_seconds = time.time() - psutil.boot_time()
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    return days, hours, minutes

def display_overview(draw, frame):
    """Scherm 0: Stijlvol overzicht met gauges"""
    draw_header(draw, "SYSTEM", "◆")

    cpu_usage = psutil.cpu_percent()
    try:
        cpu_temp = psutil.sensors_temperatures().get('cpu_thermal', [])[0].current
    except:
        cpu_temp = 0
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # CPU Circular gauge
    draw_circular_progress(draw, 20, 32, 12, cpu_usage)
    draw.text((10, 46), "CPU", fill="white")
    draw.text((6, 54), f"{cpu_usage:.0f}%", fill="white")

    # Memory Circular gauge
    draw_circular_progress(draw, 64, 32, 12, memory.percent)
    draw.text((54, 46), "RAM", fill="white")
    draw.text((50, 54), f"{memory.percent:.0f}%", fill="white")

    # Disk Circular gauge
    draw_circular_progress(draw, 108, 32, 12, disk.percent)
    draw.text((97, 46), "DISK", fill="white")
    draw.text((98, 54), f"{disk.percent:.0f}%", fill="white")

    # Animated indicator
    draw_animated_dots(draw, 120, 2, frame)

def display_network(draw, frame):
    """Scherm 1: Netwerk met stijlvolle layout"""
    draw_header(draw, "NETWORK", "◈")

    hostname, ip, sent, recv = get_network_info()

    # Host info
    draw.text((2, 16), "Host:", fill="white")
    draw.text((35, 16), hostname[:12], fill="white")

    # IP with box
    draw.rectangle([2, 26, 126, 37], outline="white")
    draw.text((4, 28), ip, fill="white")

    # Data transfer bars
    draw.text((2, 42), "↑ TX", fill="white")
    max_val = max(sent, recv, 100)
    draw_progress_bar(draw, 30, 42, 96, 8, (sent / max_val) * 100)

    draw.text((2, 52), "↓ RX", fill="white")
    draw_progress_bar(draw, 30, 52, 96, 8, (recv / max_val) * 100)

    draw_animated_dots(draw, 120, 2, frame)

def display_cpu(draw, frame):
    """Scherm 2: CPU met temperature gauge"""
    draw_header(draw, "CPU", "◉")

    cpu_percent, cpu_freq, cpu_temp, cpu_count = get_cpu_info()

    # Large circular progress for CPU
    draw_circular_progress(draw, 64, 38, 20, cpu_percent, thickness=4)
    draw.text((50, 34), f"{cpu_percent:.1f}%", fill="white")

    # Info bars
    draw.text((2, 16), f"Freq: {cpu_freq:.0f} MHz", fill="white")

    # Temperature bar with gradient effect
    draw.text((2, 26), "Temp:", fill="white")
    temp_percent = min((cpu_temp / 80) * 100, 100)  # 80°C = 100%
    draw_progress_bar(draw, 40, 26, 86, 8, temp_percent)
    draw.text((100, 16), f"{cpu_temp:.1f}°C", fill="white")

    draw.text((2, 56), f"Cores: {cpu_count}", fill="white")
    draw.text((100, 56), f"[2/{num_screens}]", fill="white")

    draw_animated_dots(draw, 120, 2, frame)

def display_memory(draw, frame):
    """Scherm 3: Geheugen met visuele bars"""
    draw_header(draw, "MEMORY", "◊")

    percent, total, used, available = get_memory_info()

    # Large percentage display
    draw.text((40, 18), f"{percent:.1f}%", fill="white")
    draw.rectangle([38, 16, 90, 28], outline="white")

    # Vertical bar chart style
    draw.text((2, 32), "Total:", fill="white")
    draw.text((50, 32), f"{total:.0f} MB", fill="white")

    draw.text((2, 42), "Used:", fill="white")
    draw_progress_bar(draw, 50, 42, 76, 8, percent)

    draw.text((2, 52), "Free:", fill="white")
    draw_progress_bar(draw, 50, 52, 76, 8, (available / total) * 100)

    draw.text((100, 56), f"[3/{num_screens}]", fill="white")
    draw_animated_dots(draw, 120, 2, frame)

def display_disk(draw, frame):
    """Scherm 4: Disk met groot percentage display"""
    draw_header(draw, "STORAGE", "◐")

    percent, total, used, free = get_disk_info()

    # Big circular gauge
    draw_circular_progress(draw, 32, 38, 18, percent, thickness=5)
    draw.text((20, 34), f"{percent:.0f}%", fill="white")

    # Stats on right side
    draw.text((60, 20), f"Total:", fill="white")
    draw.text((95, 20), f"{total:.1f}GB", fill="white")

    draw.text((60, 32), f"Used:", fill="white")
    draw.text((95, 32), f"{used:.1f}GB", fill="white")

    draw.text((60, 44), f"Free:", fill="white")
    draw.text((95, 44), f"{free:.1f}GB", fill="white")

    draw.text((100, 56), f"[4/{num_screens}]", fill="white")
    draw_animated_dots(draw, 120, 2, frame)

def display_uptime(draw, frame):
    """Scherm 5: Uptime en processen"""
    draw_header(draw, "UPTIME", "◔")

    days, hours, minutes = get_uptime()
    processes = get_process_info()

    # Uptime in grote cijfers
    draw.rectangle([2, 16, 126, 32], outline="white")
    uptime_str = f"{days}d {hours:02d}h {minutes:02d}m"
    draw.text((18, 20), uptime_str, fill="white")

    # Top processen
    draw.text((2, 36), "Top Processes:", fill="white")
    y_pos = 46
    for i, (name, cpu) in enumerate(processes[:2]):
        name_short = name[:12]
        draw.text((2, y_pos), f"• {name_short}", fill="white")
        draw.text((90, y_pos), f"{cpu:.0f}%", fill="white")
        y_pos += 9

    draw.text((100, 56), f"[5/{num_screens}]", fill="white")
    draw_animated_dots(draw, 120, 2, frame)

def display_system_info(draw, frame):
    """Scherm 6: Extra systeem info"""
    draw_header(draw, "INFO", "◑")

    ip = get_ip()
    hostname = socket.gethostname()

    draw.text((2, 16), "Hostname:", fill="white")
    draw.text((2, 26), hostname[:18], fill="white")

    draw.text((2, 38), "IP Address:", fill="white")
    draw.rectangle([2, 48, 126, 59], outline="white")
    draw.text((20, 50), ip, fill="white")

    draw.text((100, 56), f"[6/{num_screens}]", fill="white")
    draw_animated_dots(draw, 120, 2, frame)

def rotary_encoder_check():
    """Check rotary encoder met simpele en betrouwbare methode"""
    global current_screen, clk_last_state, rotation_counter, last_screen, last_rotation_time

    current_time = time.time()

    # Extra debounce - skip if checked too recently
    if current_time - last_rotation_time < ROTATION_DEBOUNCE:
        return

    clk_state = GPIO.input(CLK_PIN)
    dt_state = GPIO.input(DT_PIN)

    # Detecteer verandering in CLK signaal
    if clk_state != clk_last_state:
        last_rotation_time = current_time
        clk_last_state = clk_state

        # Only process on falling edge (CLK going from HIGH to LOW)
        if clk_state == 0:
            if dt_state == 0:
                # Rechtsom
                rotation_counter += 1
            else:
                # Linksom
                rotation_counter -= 1

            # Verander scherm alleen na STEPS_PER_SCREEN stappen
            if rotation_counter >= STEPS_PER_SCREEN:
                # Rechtsom = volgende scherm
                current_screen = (current_screen + 1) % num_screens
                rotation_counter = 0  # CRITICAL: Reset counter completely
                last_screen = -1  # Force immediate update
                print(f"→ Scherm {current_screen + 1}/{num_screens}")
                time.sleep(0.15)  # Extra delay na scherm verandering

            elif rotation_counter <= -STEPS_PER_SCREEN:
                # Linksom = vorige scherm
                current_screen = (current_screen - 1) % num_screens
                rotation_counter = 0  # CRITICAL: Reset counter completely
                last_screen = -1  # Force immediate update
                print(f"← Scherm {current_screen + 1}/{num_screens}")
                time.sleep(0.15)  # Extra delay na scherm verandering

try:
    print("🎨 Stijlvol OLED Display gestart!")
    print("Draai aan de encoder om te navigeren...")
    print("Druk Ctrl+C om te stoppen")

    # Initial display
    last_screen = -1

    while True:
        # Check rotary encoder
        rotary_encoder_check()

        current_time = time.time()
        screen_changed = (current_screen != last_screen)
        time_to_update = (current_time - last_display_update >= DISPLAY_UPDATE_INTERVAL)

        # Only update display if screen changed OR enough time has passed
        if screen_changed or time_to_update:
            animation_frame += 1
            last_display_update = current_time
            last_screen = current_screen

            with canvas(device) as draw:
                if current_screen == 0:
                    display_overview(draw, animation_frame)
                elif current_screen == 1:
                    display_network(draw, animation_frame)
                elif current_screen == 2:
                    display_cpu(draw, animation_frame)
                elif current_screen == 3:
                    display_memory(draw, animation_frame)
                elif current_screen == 4:
                    display_disk(draw, animation_frame)
                elif current_screen == 5:
                    display_uptime(draw, animation_frame)

        time.sleep(0.01)  # 10ms delay

except KeyboardInterrupt:
    print("\n✨ Programma gestopt")
finally:
    device.clear()
    GPIO.cleanup()
    device.cleanup()
