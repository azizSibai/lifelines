
import time
import pygame
import requests
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import geocoder
import geopy.distance
from plyer import gps
from firebase_admin import credentials, firestore, initialize_app
geo = geocoder.ip('me')
# Initialize Firebase (replace with your Firebase credentials path)
cred = credentials.Certificate("SheltersCredentials.json")
initialize_app(cred)
# Firebase references
db = firestore.client()
shelters_ref = db.collection("shelters")
# Initialize Pygame for sound
pygame.mixer.init()
alert_sound = pygame.mixer.Sound("alarm.wav")  # Replace with your alert sound file
# Function to play a warning sound
def play_warning_sound():
    alert_sound.play()
    time.sleep(alert_sound.get_length())  # Wait for the sound to finish
# Function to simulate GDACS API disaster alerts (replace with real API calls)
def get_disaster_alerts():
    global alertss
    alertss = [
        {"type": "Flood", "severity": "Medium", "location": (40.7128, -74.0060), "affected_radius_km": 100},
        {"type": "Earthquake", "severity": "High", "location": (25.28551, 51.5311), "affected_radius_km": 150},
    ]
    global x
    x=len(alertss)
    return alertss

def get_current_location():
    global location
    location = {"latitude": geo.lat, "longitude": geo.lng}
    return float(location["latitude"]), float(location["longitude"])

def is_alert_relevant(alerts, user_location, radius_km=50):
    for alert in range(x):
        user_location = get_current_location()
        alert_location = alertss[alert]["location"]
        distance = geopy.distance.geodesic(user_location, alert_location).km
        relevant = distance <= alertss[alert]["affected_radius_km"]
        if relevant == True:
            print("relevant", alertss[alert]["type"])
            return relevant
# Function to check for urgent alerts and trigger the warning sound
def check_alerts(user_location):
    alerts = get_disaster_alerts()
    for alert in alerts:
        if alert["severity"] == "High" and is_alert_relevant(alert, user_location):
            play_warning_sound()
            return f"⚠️ Urgent Alert: {alert['type']} detected nearby!"
    print(alert,alerts)
    return "✅ No urgent alerts in your area."
# Function to fetch shelter data from Firebase
def fetch_shelters():
    shelters = []
    docs = shelters_ref.stream()
    for doc in docs:
        shelters.append(doc.to_dict())
    return shelters
# Function to display shelter information (sorted by nearest to user)
def display_shelters(user_location):
    shelters = fetch_shelters()
    nearest_shelters = sorted(
        shelters, key=lambda x: geopy.distance.geodesic(user_location, (x['latitude'], x['longitude'])).km
    )
    shelter_text = "\n".join([f"🏠 {s['name']} - {s['capacity']} beds available" for s in nearest_shelters])
    return shelter_text if shelter_text else "No shelters available."
# Kivy UI Setup
class EmergencyApp(App):
    def build(self):
        cons=0
        get_current_location()
        self.layout = GridLayout(cols=1, padding=20, spacing=10)
        if location['latitude'] is None or location['longitude'] is None:
            self.label = Label(text="📍 Fetching location...", font_size=20, bold=True)
            self.layout.add_widget(self.label)
        else:
            self.label = Label(text=str(location), font_size=20, bold=True)
            self.layout.add_widget(self.label)

        self.shelter_button = Button(text="📌 Find Nearest Shelters", font_size=18, background_color=(0, 0.6, 1, 1))
        self.shelter_button.bind(on_press=self.show_shelters)
        self.layout.add_widget(self.shelter_button)
        self.alert_button = Button(text="🚨 Check for Alerts", font_size=18, background_color=(1, 0, 0, 1))
        self.alert_button.bind(on_press=self.show_alerts)
        self.layout.add_widget(self.alert_button)
        self.scroll_view = ScrollView()
        self.result_label = Label(text="", font_size=16, size_hint_y=None)
        self.result_label.bind(texture_size=self.result_label.setter('size'))
        self.scroll_view.add_widget(self.result_label)
        self.layout.add_widget(self.scroll_view)
        return self.layout
    def show_shelters(self, instance):
        user_location = get_current_location()
        shelter_info = display_shelters(user_location)
        self.result_label.text = shelter_info
    def show_alerts(self, instance):
        user_location = get_current_location()
        alert_message = check_alerts(user_location)
        self.result_label.text = alert_message
# Run the app

if __name__ == "__main__":
    EmergencyApp().run()
