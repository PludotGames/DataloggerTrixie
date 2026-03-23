import mysql.connector
import matplotlib.pyplot as plt
from datetime import datetime

# Database configuration


def fetch_temperature_data():
    """Fetch temperature data from MySQL database"""
    try:
        # Connect to database
        conn = mysql.connector.connect(host="localhost", user="logger", passwd="paswoord", db="temperatures")
        cursor = conn.cursor()

        # Query to get temperature data
        # Adjust table and column names to match your schema
        query = """
            SELECT dateandtime, temperature, humidity
            FROM temperaturedata
            ORDER BY dateandtime DESC LIMIT 672;
        """

        cursor.execute(query)
        results = cursor.fetchall()

        # Close connection
        cursor.close()
        conn.close()

        return results

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None

def plot_temperatures(data):
    """Plot temperature data"""
    if not data:
        print("No data to plot")
        return

    # Separate timestamps and temperatures
    timestamps = [row[0] for row in data]
    temperatures = [row[1] for row in data]
    humidity = [row[2] for row in data]

    fig, ax1 = plt.subplots(figsize=(12, 6))
     # Plot temperature on primary y-axis
    ax1.plot(timestamps, temperatures, linestyle='-',
             linewidth=1, color='blue', label='Temperature')
    ax1.set_xlabel('Timestamp', fontsize=12)
    ax1.set_ylabel('Temperature (°C)', fontsize=12, color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)

    # Create secondary y-axis for humidity
    ax2 = ax1.twinx()
    ax2.plot(timestamps, humidity, linestyle='-',
             linewidth=1, color='red', label='Humidity')
    ax2.set_ylabel('Humidity (%)', fontsize=12, color='black')
    ax2.tick_params(axis='y', labelcolor='black')

    # Add title
    plt.title('Temperature and Humidity Readings Over Time', fontsize=16, fontweight='bold')

    # Add combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    # Adjust layout to prevent label cutoff
    fig.tight_layout()
    #Export plot
    plt.draw()
    fig.savefig('/var/www/html/Assets/WeekTemperatuur.png', dpi=100)

def main():
    """Main function"""
    print("Fetching temperature data from database...")
    data = fetch_temperature_data()

    if data:
        print(f"Retrieved {len(data)} temperature readings")
        plot_temperatures(data)
    else:
        print("Failed to retrieve data")

if __name__ == "__main__":
    main()
