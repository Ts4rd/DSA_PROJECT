import pycountry
import requests
from io import BytesIO
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout, \
    QHBoxLayout, QLabel, QPushButton, QLineEdit, QStackedWidget, \
    QFrame, QScrollArea, QComboBox
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap
from WeatherRequest import WeatherThread
from LocationRequest import GeocodingThread
from Loading import LoadingOverlay
from message_display import show_error_message
from icon_color_changer import change_icon_color


class HomePage:
    def __init__(self, main_window, stack_widget: QStackedWidget, loading_overlay):
        self.header_page = None
        self.search_btn = None
        self.main_window = main_window
        self.lower_section = None
        self.feels_like_label = QLabel()
        self.top_section = None
        self.feels_like_celsius = None
        self.temp_celsius = None
        self.wind_speed = None
        self.temp_label = QLabel()
        self.wind_speed_measure = QLabel()
        self.font_color = "#edeef1"
        self.current_metrics = "m/s"
        self.current_temp_metrics = "Celsius"
        self.country = None
        self.thread = None
        self.loading_overlay = loading_overlay
        self.scroll_area = None
        self.city_name = None
        self.home_stack_widget = None
        self.home_page = None
        self.menu_btn = None
        self.result_label = None
        self.city_label = None
        self.search_input = None
        self.main_layout = None
        self.menu_panel = None
        self.weather_thread = None
        self.MENU_PANEL_WIDTH = 200
        self.stack_widget = stack_widget
        self.current_theme_dark = True

    def display(self):
        self.loading_overlay.show()

        self.home_page = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 0, 10, 0)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        banner = QWidget()
        banner_layout = QVBoxLayout()
        banner_layout.setContentsMargins(-5, -5, 0, 0)
        banner_layout.setSpacing(0)

        self.menu_btn = QPushButton()
        self.menu_btn.setIcon(QIcon("assets/icons/menu.png"))
        self.menu_btn.setIconSize(QSize(70, 50))
        self.menu_btn.clicked.connect(lambda: self.open_menu())
        self.menu_btn.setStyleSheet(f"color: {self.font_color}; background-color: transparent;")
        self.menu_btn.setFocusPolicy(Qt.NoFocus)
        change_icon_color(self.menu_btn, "assets/icons/menu.png", self.font_color)
        self.menu_panel = QWidget(self.home_page)
        self.menu_panel.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.menu_panel.setGeometry(0, 0, self.MENU_PANEL_WIDTH, self.MENU_PANEL_WIDTH)
        self.menu_panel.setContentsMargins(0, 0, 0, 0)

        # Semi-transparent menu panel
        self.menu_panel.setStyleSheet("background-color: rgba(0, 0, 0, 0.1); border-radius: 5px;")
        self.menu_panel.hide()

        menu_layout = QVBoxLayout()

        self.home_stack_widget = QStackedWidget()

        menu_buttons_widget = self.display_widgets()
        settings_window = self.display_settings()

        self.home_stack_widget.addWidget(menu_buttons_widget)
        self.home_stack_widget.addWidget(settings_window)

        menu_layout.addWidget(self.home_stack_widget)

        self.menu_panel.setLayout(menu_layout)

        # Add the menu button to the layout
        banner_layout.addWidget(self.menu_btn)

        banner.setLayout(banner_layout)

        top_layout.addWidget(banner, alignment=Qt.AlignLeft)

        # Header Page (Search Bar Section)
        self.header_page = QWidget()
        self.header_page.setContentsMargins(10, 0, 10, 0)
        self.header_page.setStyleSheet(f"background-color: transparent; border: 2px solid {self.font_color}; border-radius: 25px;")

        self.header_page.setFixedWidth(330)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        self.search_btn = QPushButton()
        self.search_btn.setIconSize(QSize(30, 30))
        self.search_btn.setFocusPolicy(Qt.NoFocus)
        self.search_btn.setStyleSheet('''
                    QPushButton {
                        font-size: 15px;
                        border: none;
                        margin: none;
                    }
                    QPushButton:hover {
                        opacity: 0.8;
                    }
                ''')
        self.search_btn.setIcon(QIcon("assets/icons/search_icon.png"))
        self.search_btn.setFixedSize(40, 30)
        self.search_btn.clicked.connect(self.get_weather)
        change_icon_color(self.search_btn, "assets/icons/search_icon.png", self.font_color)
        header_layout.addWidget(self.search_btn)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter the city")
        self.search_input.returnPressed.connect(self.get_weather)
        self.search_input.setStyleSheet(f"font-size: 15px; padding: 0px 5px; border: none; color: {self.font_color}")

        self.search_input.setFixedHeight(40)
        header_layout.addWidget(self.search_input)

        self.header_page.setFixedHeight(50)
        self.header_page.setLayout(header_layout)
        top_layout.addWidget(self.header_page, alignment=Qt.AlignRight)

        top_widget = QWidget()
        top_widget.setLayout(top_layout)
        top_widget.setStyleSheet("margin-top: 0px;")

        self.main_layout.addWidget(top_widget, alignment=Qt.AlignTop)

        self.get_current_location()

        self.home_page.setLayout(self.main_layout)

        self.loading_overlay.hide()

        return self.home_page

    def get_current_location(self):
        data = self.get_location()
        city = data['city']
        coordinates = data['loc'].split(',')
        self.fetch_weather_data(coordinates[0], coordinates[1])
        self.city_name = city
        self.country = data['country']

    def get_weather(self):
        city = self.search_input.text().title()
        if not city:
            show_error_message(self.home_page, "Empty field detected", "Please provide the\nname of the city")
            return

        self.fetch_geocoding_data(city)

    def fetch_geocoding_data(self, city):
        self.loading_overlay.show()
        self.thread = GeocodingThread(city)
        self.thread.data_ready.connect(self.handle_data_ready)
        self.thread.error_occurred.connect(lambda error: self.display_error(error))
        self.thread.start()

    def handle_data_ready(self, data):
        latitude = data['latitude']
        longitude = data['longitude']
        self.city_name = data['city']
        self.country = data['country']
        self.fetch_weather_data(latitude, longitude)

    def fetch_weather_data(self, latitude, longitude):
        self.loading_overlay.show()
        self.weather_thread = WeatherThread(latitude, longitude)
        self.weather_thread.data_ready.connect(self.display_weather)
        self.weather_thread.error_occurred.connect(self.display_error)
        self.weather_thread.start()

    def display_weather(self, data):
        self.loading_overlay.hide()
        self.main_layout.removeWidget(self.result_label)
        if hasattr(self, 'scroll_area') and self.scroll_area:
            self.main_layout.removeWidget(self.scroll_area)
            self.scroll_area.deleteLater()
            self.scroll_area = None

        # Create QScrollArea for scrolling weather details
        self.scroll_area = QScrollArea()
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setStyleSheet("border: none")
        self.scroll_area.setWidgetResizable(True)  # Allow scrollable content to resize

        temp_kelvin = data['main']['temp']
        self.temp_celsius = temp_kelvin
        self.feels_like_celsius = data['main']['feels_like']
        description = data['weather'][0]['description']
        humidity = data['main']['humidity']
        self.wind_speed = data['wind']['speed']
        pressure = data['main']['pressure']
        cloudiness = data['clouds']['all']
        icon_code = data['weather'][0].get('icon', '')
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"

        now = datetime.now()

        # Extract the current date and time separately
        current_day = now.strftime("%d")
        current_month = now.strftime("%B")
        current_time = now.strftime("%I:%M %p")
        current_weekday = now.strftime("%A")

        weather_layout = QVBoxLayout()
        weather_layout.setContentsMargins(0, 0, 0, 0)

        self.update_background(description)

        top_section = QWidget()
        top_section.setObjectName('top_widget')
        top_section.setStyleSheet('''
            QWidget#top_widget {
                background-color: rgba(255, 255, 255, 0.4);
                border-radius: 15px;            
            }
        ''')
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Create widgets for each data point
        top_left_section = QWidget()
        top_left_layout = QVBoxLayout()
        top_left_section.setContentsMargins(10, 0, 10, 0)

        date_label = QLabel(f"Today, {current_day} {current_month}")
        date_label.setStyleSheet(f"font-size: 15px; color: {self.font_color}")
        top_left_layout.addWidget(date_label)

        city_label_widget = QWidget()
        city_label_layout = QHBoxLayout()
        city_label_layout.setContentsMargins(0, 0, 0, 0)

        location_icon = QLabel()
        location_icon.setStyleSheet(f"color: {self.font_color}")
        location_icon.setFixedSize(30, 30)
        location_icon.setScaledContents(True)
        location_icon.setContentsMargins(0, 0, 0, 0)
        pixmap = QPixmap("assets/icons/location.png")
        location_icon.setPixmap(pixmap)
        change_icon_color(location_icon, "assets/icons/location.png",  self.font_color)
        city_label_layout.addWidget(location_icon)

        city_label = QLabel(f"{self.city_name}, {self.country}")
        city_label.setFont(QFont("Arial", 15))
        city_label.setStyleSheet(f"margin: 0px; color: {self.font_color}")
        city_label_layout.addWidget(city_label, alignment=Qt.AlignLeft)

        city_label_widget.setLayout(city_label_layout)
        top_left_layout.addWidget(city_label_widget, alignment=Qt.AlignLeft)

        week_day_label = QLabel(current_weekday)
        week_day_label.setFont(QFont("Arial", 23, QFont.Bold))
        week_day_label.setStyleSheet(f"color: {self.font_color}")
        top_left_layout.addWidget(week_day_label, alignment=Qt.AlignLeft)

        temperature_widget = QWidget()
        temperature_layout = QHBoxLayout()
        temperature_layout.setContentsMargins(0, 0, 0, 0)

        temp_widget = QWidget()
        temp_layout = QVBoxLayout()
        temp_layout.setContentsMargins(0, 0, 0, 0)

        self.on_temp_unit_changed(self.current_temp_metrics)
        self.temp_label.setFont(QFont("Arial", 45, QFont.Bold))
        self.temp_label.setStyleSheet(f"color: {self.font_color}")
        temp_layout.addWidget(self.temp_label, alignment=Qt.AlignLeft)

        current_weather_label = QLabel("Current Weather")
        current_weather_label.setFont(QFont("Arial", 12, QFont.Bold))
        current_weather_label.setStyleSheet(f"color: {self.font_color}")
        temp_layout.addWidget(current_weather_label, alignment=Qt.AlignLeft)

        time_label = QLabel(current_time)
        time_label.setFont(QFont("Arial", 12, QFont.Bold))
        time_label.setStyleSheet(f"color: {self.font_color}")
        temp_layout.addWidget(time_label, alignment=Qt.AlignLeft)

        temp_widget.setLayout(temp_layout)
        temperature_layout.addWidget(temp_widget, alignment=Qt.AlignLeft)

        feels_like_widget = QWidget()
        feels_like_layout = QVBoxLayout()
        feels_like_widget.setContentsMargins(50, 0, 0, 0)

        self.on_temp_unit_changed(self.current_temp_metrics)
        self.feels_like_label.setFont(QFont("Arial", 40))
        feels_like_layout.addWidget(self.feels_like_label, alignment=Qt.AlignTop)

        feels_like_label_def = QLabel(f"Feels Like")
        feels_like_label_def.setFont(QFont("Arial", 12, QFont.Bold))
        self.feels_like_label.setStyleSheet(f"color: {self.font_color}")
        feels_like_label_def.setStyleSheet(f"color: {self.font_color}")
        feels_like_layout.addWidget(feels_like_label_def, alignment=Qt.AlignTop)

        feels_like_widget.setLayout(feels_like_layout)
        temperature_layout.addWidget(feels_like_widget, alignment=Qt.AlignTop)

        temperature_widget.setLayout(temperature_layout)

        top_left_layout.addWidget(temperature_widget, alignment=Qt.AlignLeft)

        top_left_section.setLayout(top_left_layout)

        top_right_section = QWidget()
        top_right_layout = QVBoxLayout()

        try:
            icon_response = requests.get(icon_url)
            icon_response.raise_for_status()  # Ensure successful response
            icon_data = BytesIO(icon_response.content)  # Load icon data into BytesIO
            icon_pixmap = QPixmap()
            icon_pixmap.loadFromData(icon_data.read())  # Load QPixmap from icon data

            # Create a QLabel for the icon
            icon_label = QLabel()
            icon_label.setStyleSheet(f"color: {self.font_color}")
            icon_label.setPixmap(icon_pixmap)
            icon_label.setFixedSize(250, 250)
            icon_label.setScaledContents(True)

            top_right_layout.addWidget(icon_label)
        except requests.exceptions.RequestException as e:
            print(f"Failed to load weather icon: {e}")

        top_right_section.setLayout(top_right_layout)

        top_layout.addWidget(top_left_section)
        top_layout.addWidget(top_right_section)
        top_section.setLayout(top_layout)

        lower_section = QWidget()
        lower_section.setObjectName('low_widget')
        lower_section.setStyleSheet('''
            QWidget#low_widget {
            background-color: rgba(255, 255, 255, 0.4);
            border-radius: 15px;
            padding: 5px 20px 5px 20px;        
            }
        ''')
        lower_section.setMinimumHeight(150)
        lower_layout = QHBoxLayout()
        lower_section.setContentsMargins(0, 0, 0, 0)

        humidity_section = QWidget()
        humidity_layout = QVBoxLayout()
        humidity_layout.setContentsMargins(20, 0, 20, 0)

        humidity_label = QLabel("Humidity")
        humidity_icon = QLabel()
        humidity_icon.setFixedSize(50, 50)
        humidity_icon.setScaledContents(True)
        humidity_icon.setContentsMargins(0, 0, 0, 0)
        humidity_icon_pixmap = QPixmap("assets/icons/humidity.png")
        humidity_icon.setPixmap(humidity_icon_pixmap)
        humidity_icon.setStyleSheet(f"color: {self.font_color}")
        change_icon_color(humidity_icon, "assets/icons/humidity.png", self.font_color)
        humidity_measure = QLabel(f"{humidity}%")
        humidity_label.setStyleSheet(f"font-size: 15px; color: {self.font_color};")
        humidity_measure.setStyleSheet(f"font-size: 30px; color: {self.font_color}")

        humidity_layout.addWidget(humidity_label, alignment=Qt.AlignTop | Qt.AlignCenter)
        humidity_layout.addWidget(humidity_icon, alignment=Qt.AlignCenter)
        humidity_layout.addWidget(humidity_measure, alignment=Qt.AlignCenter)
        humidity_section.setLayout(humidity_layout)

        wind_speed_section = QWidget()
        wind_speed_layout = QVBoxLayout()
        wind_speed_layout.setContentsMargins(20, 0, 20, 0)

        wind_speed_label = QLabel("Wind Speed")
        wind_icon = QLabel()
        wind_icon.setFixedSize(50, 50)
        wind_icon.setScaledContents(True)
        wind_icon.setContentsMargins(0, 0, 0, 0)
        wind_icon_pixmap = QPixmap("assets/icons/air.png")
        wind_icon.setPixmap(wind_icon_pixmap)
        wind_icon.setStyleSheet(f"color: {self.font_color}")
        change_icon_color(wind_icon, "assets/icons/air.png", self.font_color)
        self.on_wind_speed_unit_changed(self.current_metrics)
        wind_speed_label.setStyleSheet(f"font-size: 15px; color: {self.font_color};")
        self.wind_speed_measure.setStyleSheet(f"font-size: 30px; color: {self.font_color}")

        wind_speed_layout.addWidget(wind_speed_label, alignment=Qt.AlignTop | Qt.AlignCenter)
        wind_speed_layout.addWidget(wind_icon, alignment=Qt.AlignCenter)
        wind_speed_layout.addWidget(self.wind_speed_measure, alignment=Qt.AlignCenter)
        wind_speed_section.setLayout(wind_speed_layout)
        wind_speed_section.setLayout(wind_speed_layout)

        pressure_section = QWidget()
        pressure_layout = QVBoxLayout()
        pressure_layout.setContentsMargins(20, 0, 20, 0)

        pressure_label = QLabel("Pressure")
        pressure_icon = QLabel()
        pressure_icon.setFixedSize(50, 50)
        pressure_icon.setScaledContents(True)
        pressure_icon.setContentsMargins(0, 0, 0, 0)
        pressure_icon_pixmap = QPixmap("assets/icons/air pressure.png")
        pressure_icon.setPixmap(pressure_icon_pixmap)
        pressure_icon.setStyleSheet(f"color: {self.font_color}")
        change_icon_color(pressure_icon, "assets/icons/air pressure.png", self.font_color)
        pressure_measure = QLabel(f"{pressure} hPa")
        pressure_label.setStyleSheet(f"font-size: 15px; color: {self.font_color};")
        pressure_measure.setStyleSheet(f"font-size: 30px; color: {self.font_color}")

        pressure_layout.addWidget(pressure_label, alignment=Qt.AlignTop | Qt.AlignCenter)
        pressure_layout.addWidget(pressure_icon, alignment=Qt.AlignCenter)
        pressure_layout.addWidget(pressure_measure, alignment=Qt.AlignCenter)
        pressure_section.setLayout(pressure_layout)

        cloudiness_section = QWidget()
        cloudiness_layout = QVBoxLayout()
        cloudiness_layout.setContentsMargins(20, 0, 20, 0)

        cloudiness_label = QLabel("Cloudiness")
        cloudiness_icon = QLabel()
        cloudiness_icon.setFixedSize(50, 50)
        cloudiness_icon.setScaledContents(True)
        cloudiness_icon.setContentsMargins(0, 0, 0, 0)
        cloudiness_icon_pixmap = QPixmap("assets/icons/cloud.png")
        cloudiness_icon.setPixmap(cloudiness_icon_pixmap)
        cloudiness_icon.setStyleSheet(f"color: {self.font_color}")
        change_icon_color(cloudiness_icon, "assets/icons/cloud.png", self.font_color)
        cloudiness_measure = QLabel(f"{cloudiness}%")
        cloudiness_label.setStyleSheet(f"font-size: 15px; color: {self.font_color};")
        cloudiness_measure.setStyleSheet(f"font-size: 30px; color: {self.font_color}")

        cloudiness_layout.addWidget(cloudiness_label, alignment=Qt.AlignTop | Qt.AlignCenter)
        cloudiness_layout.addWidget(cloudiness_icon, alignment=Qt.AlignCenter)
        cloudiness_layout.addWidget(cloudiness_measure, alignment=Qt.AlignCenter)
        cloudiness_section.setLayout(cloudiness_layout)

        description_section = QWidget()
        description_layout = QVBoxLayout()
        description_layout.setContentsMargins(20, 0, 20, 0)

        description_def = QLabel("Description")
        null_widget = QLabel()
        description_label = QLabel(f"{description.capitalize()}")
        description_def.setStyleSheet(f"font-size: 15px; color: {self.font_color};")
        description_label.setStyleSheet(f"font-size: 30px; color: {self.font_color}")
        description_layout.addWidget(description_def, alignment=Qt.AlignTop | Qt.AlignCenter)
        description_layout.addWidget(description_label, alignment=Qt.AlignTop | Qt.AlignCenter)
        description_layout.addWidget(null_widget, alignment=Qt.AlignCenter)
        description_section.setLayout(description_layout)

        lower_layout.addWidget(humidity_section, alignment=Qt.AlignTop)
        lower_layout.addWidget(wind_speed_section, alignment=Qt.AlignTop)
        lower_layout.addWidget(pressure_section, alignment=Qt.AlignTop)
        lower_layout.addWidget(cloudiness_section, alignment=Qt.AlignTop)
        lower_layout.addWidget(description_section, alignment=Qt.AlignTop)
        lower_section.setLayout(lower_layout)

        self.top_section = top_section
        self.lower_section = lower_section

        self.adjust_section_widths()

        weather_layout.addWidget(top_section, alignment=Qt.AlignCenter)
        weather_layout.addWidget(lower_section, alignment=Qt.AlignCenter)

        scroll_widget = QWidget()
        scroll_widget. setStyleSheet('''
            QWidget {
                background: transparent;
                border: none;
            }
        ''')

        scroll_widget.setContentsMargins(0, 0, 0, 0)
        scroll_widget.setLayout(weather_layout)

        # Add container widget to the scroll area
        self.scroll_area.setWidget(scroll_widget)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget {
                background: transparent;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: transparent;
            }
        """)

        # Add scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)
        self.loading_overlay.hide()

    def update_background(self, description):
        if "clear" in description:
            background_image = "assets/backgrounds/sunny.png"
        elif "clouds" in description:
            background_image = "assets/backgrounds/cloudy.png"
        elif "rain" in description or "drizzle" in description:
            background_image = "assets/backgrounds/rainy.jpg"
        elif "thunderstorm" in description:
            background_image = "assets/backgrounds/thunderstorm.jpg"
            self.font_color = "#000000"
        elif "snow" in description:
            background_image = "assets/backgrounds/snowy.png"
        elif "mist" in description or "fog" in description or "haze" in description:
            background_image = "assets/backgrounds/foggy.png"
        elif "tornado" in description:
            background_image = "assets/backgrounds/tornado.jpg"
            self.font_color = "#000000"
        elif "hurricane" in description:
            background_image = "assets/backgrounds/hurricane.jpg"
        elif "cold" in description:
            background_image = "assets/backgrounds/cold.jpg"
        elif "hot" in description:
            background_image = "assets/backgrounds/hot.jpg"
        elif "windy" in description:
            background_image = "assets/backgrounds/windy.jpg"
        elif "hail" in description:
            background_image = "assets/backgrounds/hail.jpg"
        else:
            background_image = "assets/backgrounds/default.png"

        self.main_window.setStyleSheet(f"""
            QMainWindow {{
                background-image: url({background_image});
                background-repeat: no-repeat;
                background-position: center;
                background-size: cover;
            }}
        """)

        self.update_top_section()
    
    def update_top_section(self):
        change_icon_color(self.menu_btn, "assets/icons/menu.png", self.font_color)
        change_icon_color(self.search_btn, "assets/icons/search_icon.png", self.font_color)
        self.header_page.setStyleSheet(f"background-color: transparent; border: 2px solid {self.font_color}; border-radius: 25px;")
        self.search_input.setStyleSheet(f"font-size: 15px; padding: 0px 5px; border: none; color: {self.font_color}")

    def adjust_section_widths(self):
        # Get the current widths of the top and lower sections
        top_width = self.top_section.sizeHint().width()
        lower_width = self.lower_section.sizeHint().width()

        # Determine the maximum width needed
        max_width = max(top_width, lower_width)

        # Set the maximum width for both sections
        self.top_section.setMinimumWidth(max_width)
        self.lower_section.setMinimumWidth(max_width)

    @staticmethod
    def set_transparent_background(widget):
        widget.setStyleSheet("background: transparent; border: none;")

    @staticmethod
    def get_location():
        response = requests.get("https://ipinfo.io/json")
        data = response.json()

        country_code = data["country"]
        country_name = pycountry.countries.get(alpha_2=country_code).name if country_code else None

        return {
            "city": data["city"],
            "loc": data["loc"],
            "country": country_name

        }

    def display_settings(self):
        settings_page = QWidget()
        settings_layout = QVBoxLayout()

        # Exit button to go back to the home page
        exit_settings_btn = QPushButton()
        exit_settings_btn.setIcon(QIcon("assets/icons/back.png"))
        exit_settings_btn.setIconSize(QSize(20, 20))
        exit_settings_btn.setFocusPolicy(Qt.NoFocus)
        exit_settings_btn.setStyleSheet("background-color: #fb1d11;")
        exit_settings_btn.setFixedSize(40, 30)
        exit_settings_btn.clicked.connect(lambda: self.home_stack_widget.setCurrentIndex(0))
        settings_layout.addWidget(exit_settings_btn, alignment=Qt.AlignLeft)

        # Temperature unit chooser
        temp_unit_label = QLabel("Choose Temperature Unit:")
        temp_unit_chooser = QComboBox()
        temp_unit_chooser.addItems(["Celsius", "Fahrenheit", "Kelvin"])
        temp_unit_chooser.setCurrentIndex(0)  # Default selection
        temp_unit_label.setStyleSheet("color: white;")
        temp_unit_chooser.setStyleSheet("font-size: 15px; background-color: white;")
        temp_unit_chooser.currentTextChanged.connect(self.on_temp_unit_changed)  # Connect to slot
        settings_layout.addWidget(temp_unit_label)
        settings_layout.addWidget(temp_unit_chooser)

        # Wind speed unit chooser
        wind_speed_unit_label = QLabel("Choose Wind Speed Unit:")
        wind_speed_unit_chooser = QComboBox()
        wind_speed_unit_chooser.addItems(["m/s", "km/h", "mph"])
        wind_speed_unit_chooser.setCurrentIndex(1)  # Default selection
        wind_speed_unit_label.setStyleSheet("color: white")
        wind_speed_unit_chooser.setStyleSheet("font-size: 15px; background-color: white;")
        wind_speed_unit_chooser.currentTextChanged.connect(self.on_wind_speed_unit_changed)  # Connect to slot
        settings_layout.addWidget(wind_speed_unit_label)
        settings_layout.addWidget(wind_speed_unit_chooser)

        # Set layout
        settings_page.setLayout(settings_layout)
        return settings_page

    def on_temp_unit_changed(self, value):
        self.current_temp_metrics = value
        if value == "Celsius":
            self.temp_label.setText(f"{self.temp_celsius: .2f} °C")
            self.feels_like_label.setText(f"{self.feels_like_celsius: .2f} °C")
        elif value == "Fahrenheit":
            fahrenheit = (self.temp_celsius * 9/5) + 32
            feels_like_fahrenheit = (self.feels_like_celsius * 9/5) + 32
            self.temp_label.setText(f"{fahrenheit: .2f} °F")
            self.feels_like_label.setText(f"{feels_like_fahrenheit: .2f} °F")
        else:
            kelvin = self.temp_celsius + 273.15
            feels_like_kelvin = self.feels_like_celsius + 273.15
            self.temp_label.setText(f"{kelvin: .2f} K")
            self.feels_like_label.setText(f"{feels_like_kelvin: .2f} K")

    def on_wind_speed_unit_changed(self, value):
        self.current_metrics = value
        if value == "m/s":
            self.wind_speed_measure.setText(f"{self.wind_speed: .2f} m/s")
        elif value == "km/h":
            kilometer = self.wind_speed * 3.6
            self.wind_speed_measure.setText(f"{kilometer: .2f} km/h")
        else:
            km = self.wind_speed/1.609
            self.wind_speed_measure.setText(f"{km: .2f} mph")

    def display_widgets(self):
        menu_layout = QVBoxLayout()
        # Settings button
        settings_btn = QPushButton("Settings")
        settings_btn.setIcon(QIcon("assets/icons/settings.png"))
        settings_btn.setIconSize(QSize(20, 20))
        settings_btn.setFocusPolicy(Qt.NoFocus)
        settings_btn.setFixedWidth(self.MENU_PANEL_WIDTH)
        settings_btn.clicked.connect(lambda: self.home_stack_widget.setCurrentIndex(1))
        settings_btn.setStyleSheet('''
                    QPushButton {
                        border: none;
                        color: white;
                        border-radius: 15px;
                        padding: 5px;
                        margin: 0px;
                        font-size: 15px;
                        background-color: inherent;
                    }
                    QPushButton:hover {
                        background-color: #5ba8f5;
                    }
                ''')
        menu_layout.addWidget(settings_btn, alignment=Qt.AlignCenter)

        menu_layout.addWidget(self.create_separator())

        logout_btn = QPushButton("Log out")
        logout_btn.setIcon(QIcon("assets/icons/exit.png"))
        logout_btn.setIconSize(QSize(20, 20))
        logout_btn.setFocusPolicy(Qt.NoFocus)
        logout_btn.setFixedWidth(self.MENU_PANEL_WIDTH)
        logout_btn.setStyleSheet('''
                    QPushButton {
                        border: none;
                        color: white;
                        border-radius: 15px;
                        padding: 5px;
                        margin: 0px;
                        font-size: 15px;
                        background-color: inherent;
                    }
                    QPushButton:hover {
                        background-color: #f78b8b;
                    }
                ''')
        logout_btn.clicked.connect(self.confirm_logout)
        menu_layout.addWidget(logout_btn, alignment=Qt.AlignCenter | Qt.AlignBottom)
        menu_layout.addStretch()
        menu = QWidget()
        menu.setLayout(menu_layout)

        return menu

    def confirm_logout(self):
        # Create a confirmation dialog
        confirmation = QMessageBox(self.home_page)
        confirmation.setStyleSheet("")
        confirmation.setIcon(QMessageBox.Warning)
        confirmation.setWindowTitle("Confirm Logout")
        confirmation.setText("Are you sure you want to log out?")
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        # Check the user's response
        response = confirmation.exec_()
        if response == QMessageBox.Yes:
            self.reset_home_widgets()
            self.get_current_location()
            self.stack_widget.setCurrentIndex(0)

    def reset_home_widgets(self):
        # Reset the search input
        self.search_input.clear()

        # Remove the scroll area if it exists
        if hasattr(self, 'scroll_area') and self.scroll_area:
            self.main_layout.removeWidget(self.scroll_area)
            self.scroll_area.deleteLater()
            self.scroll_area = None

    def open_menu(self):
        if self.menu_panel.isHidden():
            pos = self.menu_btn.mapToGlobal(QPoint(-9, -9))
            self.menu_panel.move(pos)
            self.menu_panel.show()
        else:
            self.menu_panel.hide()

    @staticmethod
    def create_separator():
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setFixedHeight(1)
        line.setStyleSheet("""
            background-color: gray;
            margin: 0px;
        """)
        return line

    def display_error(self, error_message):
        self.loading_overlay.hide()
        show_error_message(self.home_page, "An error occurred", error_message)