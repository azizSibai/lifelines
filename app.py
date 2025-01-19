import time
import pygame
import requests
import geocoder
import geopy.distance
from plyer import gps
from firebase_admin import credentials, firestore, initialize_app
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.audio import SoundLoader

# Initialize Firebase
cred = credentials.Certificate("SheltersCredentials.json")
initialize_app(cred)

# Firebase references
db = firestore.client()
shelters_ref = db.collection("shelters")

# Function to get current location using geocoder
def get_current_location():
    try:
        geo = geocoder.ip('me')
        if geo.latlng:
            return float(geo.lat), float(geo.lng)
    except Exception as e:
        print(f"Error fetching location: {e}")
    return None, None  # Return None when location isn't available

# Function to fetch live disaster alerts from GDACS
def get_disaster_alerts():
    url = "https://www.gdacs.org/xml/rss.xml"  # GDACS RSS Feed
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text  # You need to parse this properly
    except requests.RequestException as e:
        print(f"Error fetching alerts: {e}")
    return []

# Function to check if an alert is relevant
def is_alert_relevant(alert, user_location):
    alert_location = alert["location"]
    distance = geopy.distance.geodesic(user_location, alert_location).km
    return distance <= alert["affected_radius_km"]

# Function to check for urgent alerts and trigger the warning sound
def check_alerts(user_location):
    alerts = get_disaster_alerts()  # Replace with actual alert parsing logic
    for alert in alerts:
        if alert["severity"] == "High" and is_alert_relevant(alert, user_location):
            play_warning_sound()
            return f"⚠️ Urgent Alert: {alert['type']} detected nearby!"
    return "✅ No urgent alerts in your area."

# Function to play a warning sound
def play_warning_sound():
    sound = SoundLoader.load("alarm.wav")
    if sound:
        sound.play()

# Function to fetch shelter data from Firebase
def fetch_shelters():
    shelters = []
    docs = shelters_ref.stream()
    for doc in docs:
        shelters.append(doc.to_dict())
    return shelters

# Function to display shelters sorted by distance
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
        self.layout = GridLayout(cols=1, padding=20, spacing=10)

        lat, lng = get_current_location()
        if lat is None or lng is None:
            self.label = Label(text="📍 Fetching location...", font_size=20, bold=True)
        else:
            self.label = Label(text=f"📍 Current Location: {lat}, {lng}", font_size=20, bold=True)

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

    def update_result_label(self, text, _dt):
        self.result_label.text = text

    def show_shelters(self, instance):
        user_location = get_current_location()
        shelter_info = display_shelters(user_location)
        Clock.schedule_once(lambda dt: self.update_result_label(shelter_info, dt))

    def show_alerts(self, instance):
        user_location = get_current_location()
        alert_message = check_alerts(user_location)
        Clock.schedule_once(lambda dt: self.update_result_label(alert_message, dt))

# Run the app
if __name__ == "__main__":
    EmergencyApp().run()
