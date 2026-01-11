import sys
import database
import sqlite3
from PyQt5.QtWidgets import (
                             QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QStackedWidget,
                             QLineEdit, QDateEdit, QTextEdit, QComboBox, QFormLayout, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QTextBrowser, QSpinBox, QFileDialog)
from PyQt5.QtCore import Qt, QSize, QDate, pyqtSignal, QPointF, QRect
from PyQt5.QtWebEngineWidgets import QWebEngineView
import qtawesome as qta
from PyQt5.QtGui import QDoubleValidator, QFont, QPixmap, QPainter, QPainterPath, QColor
import google.generativeai as genai
import json
from markdown_it import MarkdownIt
from datetime import datetime
from collections import defaultdict
import speech_recognition as sr
import subprocess
import threading
import os
import tempfile
import json

class NavButton(QPushButton):
    """Custom button for qtawesome icons with hover and active states"""
    def __init__(self, icon_name, label_text="", active=False):
        super().__init__()
        self.setFixedSize(65, 65)
        self.setCursor(Qt.PointingHandCursor)
        
        # Set the qtawesome Icon
        self.setIcon(qta.icon(icon_name, color='white'))
        self.setIconSize(QSize(28, 28))
        
        if label_text:
            self.setText(label_text)
            # This aligns icon on top and text on bottom
            self.setStyleSheet("text-align: bottom; padding-bottom: 5px;")

        # --- THE STYLING (QSS) ---
        self.active_style = """
            NavButton {
                background-color: #1a1052; 
                border-radius: 15px; 
                border: 1px solid #3d3dff;
                color: #8a8aff;
                font-size: 10px;
                font-weight: bold;
            }
        """
        
        self.default_style = """
            NavButton {
                background-color: transparent;
                border-radius: 15px;
                border: 1px solid transparent;
                color: #555;
                font-size: 10px;
            }
            NavButton:hover {
                background-color: #121212;
                border: 1px solid #444; /* Subtle glow border */
                color: #ffffff;
            }
        """

        self.setStyleSheet(self.active_style if active else self.default_style)

class AddExpenseView(QWidget):
    expense_added = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("color: white; background-color: #000;")
        self.is_recording = False
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
        except Exception:
            self.microphone = None
        self.stop_listening = None # For background listening
        self.temp_audio_file = os.path.join(tempfile.gettempdir(), "expense_voice.wav")
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main content area
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 10px;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        title = QLabel("Add New Expense")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white; margin-bottom: 10px;")
        content_layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setVerticalSpacing(10)

        # Date Input
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setStyleSheet("background-color: #000; color: white; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        form_layout.addRow(QLabel("Date:"), self.date_input)

        # Category Input
        self.category_input = QComboBox()
        self.category_input.addItems(["Food", "Transport", "Entertainment", "Utilities", "Rent", "Shopping", "Salary", "Other"])
        self.category_input.setStyleSheet("background-color: #000; color: white; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        form_layout.addRow(QLabel("Category:"), self.category_input)

        # Amount Input
        amount_container = QWidget()
        amount_label_layout = QHBoxLayout(amount_container)
        amount_label_layout.setContentsMargins(0, 0, 0, 0)
        amount_label = QLabel("Amount:")
        self.voice_price_btn = QPushButton()
        self.voice_price_btn.setFixedSize(30, 30)
        self.voice_price_btn.setIcon(qta.icon("fa5s.microphone", color='white'))
        self.voice_price_btn.setToolTip("Dictate Price")
        self.voice_price_btn.setStyleSheet("background-color: #1a1052; border-radius: 15px; border: 1px solid #3d3dff;")
        self.voice_price_btn.clicked.connect(self.toggle_voice_input)
        
        amount_label_layout.addWidget(amount_label)
        amount_label_layout.addWidget(self.voice_price_btn)
        amount_label_layout.addStretch()

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.setValidator(QDoubleValidator(0.00, 1000000.00, 2))
        self.amount_input.setStyleSheet("background-color: #000; color: white; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        form_layout.addRow(amount_container, self.amount_input)

        # Description Input
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Optional description")
        self.description_input.setFixedHeight(70)
        self.description_input.setStyleSheet("background-color: #000; color: white; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        form_layout.addRow(QLabel("Description:"), self.description_input)

        content_layout.addLayout(form_layout)

        add_button = QPushButton("Add Expense")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3dff;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5555ff;
            }
        """)
        add_button.clicked.connect(self.on_add_expense)
        content_layout.addWidget(add_button, alignment=Qt.AlignCenter)

        main_layout.addWidget(content_frame, alignment=Qt.AlignCenter)
        main_layout.addStretch()

    def toggle_voice_input(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        try:
            self.is_recording = True
            self.voice_price_btn.setStyleSheet("background-color: #ff3d3d; border-radius: 15px; border: 1px solid white;")
            self.voice_price_btn.setToolTip("Listening... Click to Stop")
            
            if self.microphone:
                # Use PyAudio if available (Windows/macOS/Linux)
                threading.Thread(target=self.listen_process, daemon=True).start()
            elif os.name != 'nt':
                # Linux fallback: use arecord if PyAudio is missing
                self.record_process = subprocess.Popen(['arecord', '-f', 'cd', '-t', 'wav', '-d', '5', self.temp_audio_file])
            else:
                raise Exception("Microphone support requires PyAudio on Windows.")
                
        except Exception as e:
            QMessageBox.critical(self, "Microphone Error", f"Could not access microphone: {e}")
            self.reset_voice_button()

    def listen_process(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            # Use QTimer to safely update UI from thread
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.process_audio_data(audio))
        except Exception as e:
            self.show_error_message("Recording Error", str(e))
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self.reset_voice_button)

    def stop_recording(self):
        if hasattr(self, 'record_process') and self.record_process:
            self.record_process.terminate()
            self.record_process.wait()
            self.record_process = None
            # For arecord fallback, we need to process the file manually
            self.is_recording = False
            self.voice_price_btn.setEnabled(False)
            self.voice_price_btn.setStyleSheet("background-color: #555; border-radius: 15px; border: 1px solid #3d3dff;")
            threading.Thread(target=self.process_audio_file, daemon=True).start()
        else:
            # PyAudio background thread handles completion
            self.is_recording = False
            self.voice_price_btn.setEnabled(False)
            self.voice_price_btn.setStyleSheet("background-color: #555; border-radius: 15px; border: 1px solid #3d3dff;")

    def process_audio_file(self):
        try:
            if not os.path.exists(self.temp_audio_file):
                return

            with sr.AudioFile(self.temp_audio_file) as source:
                audio = self.recognizer.record(source)
            self.process_audio_data(audio)
        except Exception as e:
            self.show_error_message("Processing Error", str(e))
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, self.reset_voice_button)

    def reset_voice_button(self):
        self.is_recording = False
        self.voice_price_btn.setEnabled(True)
        self.voice_price_btn.setStyleSheet("background-color: #1a1052; border-radius: 15px; border: 1px solid #3d3dff;")
        self.voice_price_btn.setToolTip("Dictate Price")

    def process_audio_data(self, audio):
        try:
            # Transcribe using Google (free)
            text = self.recognizer.recognize_google(audio)
            
            # Simple extraction: look for numbers
            import re
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", text)
            if numbers:
                price = numbers[0]
                self.amount_input.setText(price)
            else:
                self.show_error_message("Voice Input", f"No price detected in: '{text}'")
                
        except sr.UnknownValueError:
            self.show_error_message("Speech Recognition", "Could not understand audio.")
        except sr.RequestError as e:
            self.show_error_message("Speech Recognition", f"Could not request results; {e}")
        except Exception as e:
            self.show_error_message("Error", str(e))
        finally:
            self.reset_voice_button()

    def show_error_message(self, title, message):
        QMessageBox.warning(self, title, message)

    def on_add_expense(self):
        date = self.date_input.date().toString(Qt.ISODate)
        category = self.category_input.currentText()
        amount_str = self.amount_input.text()
        description = self.description_input.toPlainText()

        try:
            amount = float(amount_str)
            if amount <= 0:
                QMessageBox.warning(self, "Invalid Amount", "Amount must be greater than zero.")
                return
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid numeric amount.")
            return

        expense_data = {
            "date": date,
            "category": category,
            "amount": amount,
            "description": description
        }
        self.expense_added.emit(expense_data)
        self.clear_form()
        QMessageBox.information(self, "Success", "Expense added successfully!")

    def clear_form(self):
        self.date_input.setDate(QDate.currentDate())
        self.category_input.setCurrentIndex(0)
        self.amount_input.clear()
        self.description_input.clear()

class ViewExpensesView(QWidget):
    star_toggled = pyqtSignal(int, int)
    expense_deleted = pyqtSignal(int) # New signal for deleting an expense

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("color: white; background-color: #000;")
        self.all_expenses = [] # Cache for filtering
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header_layout = QHBoxLayout()
        title = QLabel("All Expenses")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Search and Filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search description...")
        self.search_input.setFixedWidth(200)
        self.search_input.setStyleSheet("background-color: #1a1a1a; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        self.search_input.textChanged.connect(self.on_filter_changed)
        header_layout.addWidget(self.search_input)
        
        self.cat_filter = QComboBox()
        self.cat_filter.addItems(["All Categories", "Food", "Transport", "Entertainment", "Utilities", "Rent", "Shopping", "Salary", "Other"])
        self.cat_filter.setStyleSheet("background-color: #1a1a1a; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        self.cat_filter.currentIndexChanged.connect(self.on_filter_changed)
        header_layout.addWidget(self.cat_filter)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)

        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(6) # Increased to 6
        self.expense_table.setHorizontalHeaderLabels(["Date", "Category", "Amount", "Description", "Star", "Delete"])
        self.expense_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.expense_table.verticalHeader().setVisible(False)
        self.expense_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #3d3dff;
                selection-background-color: #3d3dff;
            }
            QHeaderView::section {
                background-color: #080808;
                color: white;
                padding: 5px;
                border: 1px solid #1a1a1a;
            }
        """)
        layout.addWidget(self.expense_table)
        self.update_expense_list([]) # Initialize with empty list

    def on_filter_changed(self):
        search_text = self.search_input.text().lower()
        cat_text = self.cat_filter.currentText()
        
        filtered = []
        for exp in self.all_expenses:
            # exp structure: (id, date, category, amount, description, starred)
            match_search = search_text in exp[4].lower() or search_text in exp[2].lower()
            match_cat = cat_text == "All Categories" or cat_text == exp[2]
            
            if match_search and match_cat:
                filtered.append(exp)
        
        self._display_expenses(filtered)

    def _handle_star_toggle(self, expense_id, starred):
        self.star_toggled.emit(expense_id, starred)

    def _handle_delete(self, expense_id):
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                     "Are you sure you want to delete this expense?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.expense_deleted.emit(expense_id)

    def update_expense_list(self, expenses):
        self.all_expenses = expenses
        self.on_filter_changed()

    def _display_expenses(self, expenses):
        self.expense_table.setRowCount(len(expenses))
        for row, expense in enumerate(expenses):
            self.expense_table.setItem(row, 0, QTableWidgetItem(expense[1]))
            self.expense_table.setItem(row, 1, QTableWidgetItem(expense[2]))
            self.expense_table.setItem(row, 2, QTableWidgetItem(str(f"{expense[3]:.2f}")))
            self.expense_table.setItem(row, 3, QTableWidgetItem(expense[4]))

            # Star Button
            star_button = QPushButton()
            starred = expense[5]
            star_icon = "fa5s.star" if starred else "fa5.star"
            star_button.setIcon(qta.icon(star_icon, color='yellow'))
            star_button.setCursor(Qt.PointingHandCursor)
            star_button.setStyleSheet("background-color: transparent; border: none;")
            star_button.clicked.connect(lambda _, r=row: self._handle_star_toggle(expenses[r][0], expenses[r][5]))
            self.expense_table.setCellWidget(row, 4, star_button)

            # Delete Button
            delete_button = QPushButton()
            delete_button.setIcon(qta.icon("fa5s.trash-alt", color='#ff4d4d'))
            delete_button.setCursor(Qt.PointingHandCursor)
            delete_button.setStyleSheet("background-color: transparent; border: none;")
            delete_button.clicked.connect(lambda _, r=row: self._handle_delete(expenses[r][0]))
            self.expense_table.setCellWidget(row, 5, delete_button)
            
        self.expense_table.sortItems(0, Qt.DescendingOrder) # Sort by date

class CardsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("color: white; background-color: #000;")
        layout = QVBoxLayout(self)
        label = QLabel("Cards View (Coming Soon!)")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

class StarredView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("color: white; background-color: #000;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Starred Expenses")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(4)
        self.expense_table.setHorizontalHeaderLabels(["Date", "Category", "Amount", "Description"])
        self.expense_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.expense_table.verticalHeader().setVisible(False)
        self.expense_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #3d3dff;
                selection-background-color: #3d3dff;
            }
            QHeaderView::section {
                background-color: #080808;
                color: white;
                padding: 5px;
                border: 1px solid #1a1a1a;
            }
        """)
        layout.addWidget(self.expense_table)
        self.update_starred_list([]) # Initialize with empty list

    def update_starred_list(self, expenses):
        self.expense_table.setRowCount(len(expenses))
        for row, expense in enumerate(expenses):
            self.expense_table.setItem(row, 0, QTableWidgetItem(expense[1]))
            self.expense_table.setItem(row, 1, QTableWidgetItem(expense[2]))
            self.expense_table.setItem(row, 2, QTableWidgetItem(str(f"{expense[3]:.2f}")))
            self.expense_table.setItem(row, 3, QTableWidgetItem(expense[4]))
        self.expense_table.sortItems(0, Qt.DescendingOrder) # Sort by date

class GraphsView(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setStyleSheet("color: white; background-color: #000;")
        self.data_for_painting = []
        self.graph_title = ""
        self.graph_type = ""
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # Use the widget's margins for the graph
        main_layout.setSpacing(0)

        # Control panel for title and dropdown
        control_panel_layout = QHBoxLayout()
        control_panel_layout.setContentsMargins(20, 20, 20, 0) # Top margin for controls, no bottom margin
        
        title = QLabel("Expense Graphs")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        control_panel_layout.addWidget(title)
        
        self.graph_type_combo = QComboBox()
        self.graph_type_combo.addItems(["Bar Chart (Category)", "Line Chart (Monthly)", "Pie Chart (Not Implemented)"])
        self.graph_type_combo.setStyleSheet("background-color: #1a1a1a; color: white; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        control_panel_layout.addWidget(self.graph_type_combo)
        control_panel_layout.addStretch() # Push combo box to left if desired

        main_layout.addLayout(control_panel_layout)
        main_layout.addStretch() # This stretch will be the area for paintEvent

        self.graph_type_combo.currentIndexChanged.connect(self.update_graph)
        self.update_graph() # Initial graph display

    def update_graph(self):
        self.data_for_painting = []
        self.graph_title = ""
        self.graph_type = self.graph_type_combo.currentText()

        if self.graph_type == "Bar Chart (Category)":
            summary = database.get_category_summary(self.conn)
            if not summary:
                self.graph_title = "No data available to display graphs."
            else:
                self.data_for_painting = summary
                self.graph_title = 'Total Expenses by Category'
            
        elif self.graph_type == "Line Chart (Monthly)":
            summary = database.get_monthly_summary(self.conn)
            if not summary:
                self.graph_title = "No data available to display graphs."
            else:
                for month, total in summary:
                    self.data_for_painting.append({'month': month, 'amount': total})
                self.graph_title = 'Monthly Expenses Trend'
            
        elif self.graph_type == "Pie Chart (Not Implemented)":
            self.graph_title = "Pie Chart not implemented with QPainter."

        self.update() # Triggers paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        widget_rect = self.rect()
        if widget_rect.width() <= 0 or widget_rect.height() <= 0:
            return    

        
        # Margins to leave space for axis labels and title
        left_margin = 60
        right_margin = 20
        top_margin = 40  # Increased space for title
        bottom_margin = 80 # Increased space for X-axis labels

        plot_area_width = widget_rect.width() - left_margin - right_margin
        plot_area_height = widget_rect.height() - top_margin - bottom_margin

        # Ensure plot_area dimensions are not negative
        if plot_area_width <= 0 or plot_area_height <= 0:
            painter.drawText(widget_rect, Qt.AlignCenter, "Graph area too small.")
            return

        plot_rect = QRect(left_margin, top_margin, plot_area_width, plot_area_height)

        # Draw main title
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        title_rect = QRect(0, 0, widget_rect.width(), top_margin) # Adjusted title area
        painter.drawText(title_rect, Qt.AlignCenter, self.graph_title)
        painter.setFont(QFont("Arial", 8)) # Reset font for other labels
        
        if not self.data_for_painting and (self.graph_title == "No data available to display graphs." or self.graph_type == "Pie Chart (Not Implemented)"):
            painter.drawText(plot_rect, Qt.AlignCenter, self.graph_title)
            return

        # Draw X and Y axis lines
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.bottomRight()) # X-axis
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.topLeft()) # Y-axis
        
        # Y-axis label text
        painter.save()
        painter.translate(10, plot_rect.center().y()) # Position it to the left of the plot area
        painter.rotate(-90)
        # Adjust QRect for drawing rotated text and cast to int
        painter.drawText(QRect(int(-plot_rect.height()/2), int(-50/2), int(plot_rect.height()), int(50)), Qt.AlignCenter, "Amount")
        painter.restore()


        if self.graph_type == "Bar Chart (Category)":
            if not self.data_for_painting:
                painter.drawText(plot_rect, Qt.AlignCenter, "No data for Bar Chart.")
                return

            categories = [item[0] for item in self.data_for_painting]
            amounts = [item[1] for item in self.data_for_painting]

            if not amounts:
                painter.drawText(plot_rect, Qt.AlignCenter, "No data for Bar Chart.")
                return

            max_amount = max(amounts) if amounts else 1.0
            
            bar_width_ratio = 0.7
            num_bars = len(categories)
            
            if num_bars == 0:
                painter.drawText(plot_rect, Qt.AlignCenter, "No data for Bar Chart.")
                return

            bar_total_width = plot_rect.width() / num_bars
            actual_bar_width = bar_total_width * bar_width_ratio

            # Draw bars and X-axis labels
            for i, (category, amount) in enumerate(self.data_for_painting):
                x = plot_rect.left() + i * bar_total_width + (bar_total_width - actual_bar_width) / 2
                bar_height = (amount / max_amount) * plot_rect.height()
                y = plot_rect.bottom() - bar_height

                painter.setBrush(QColor("#3d3dff"))
                painter.drawRect(int(x), int(y), int(actual_bar_width), int(bar_height))
                
                # Draw category label (rotated to avoid overlap)
                painter.save()
                painter.translate(int(x + actual_bar_width / 2), plot_rect.bottom() + 5)
                painter.rotate(-45)
                # Ensure text rectangle is appropriately sized for rotation
                text_width = 80 # Max width for rotated text
                text_height = 20
                painter.drawText(QRect(-text_width // 2, 0, text_width, text_height), Qt.AlignLeft, category)
                painter.restore()

            # Draw Y-axis labels (min and max)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QColor(Qt.white))
            # Align right for Y-axis labels, centered vertically within their small rect
            painter.drawText(QRect(0, plot_rect.bottom() - 10, left_margin - 5, 20), Qt.AlignRight | Qt.AlignVCenter, "0")
            painter.drawText(QRect(0, plot_rect.top() - 10, left_margin - 5, 20), Qt.AlignRight | Qt.AlignVCenter, str(round(max_amount, 2)))
            
        elif self.graph_type == "Line Chart (Monthly)":
            if not self.data_for_painting:
                painter.drawText(plot_rect, Qt.AlignCenter, "No data for Line Chart.")
                return

            months = [item['month'] for item in self.data_for_painting]
            amounts = [item['amount'] for item in self.data_for_painting]
            
            if not amounts:
                painter.drawText(plot_rect, Qt.AlignCenter, "No data for Line Chart.")
                return

            max_amount = max(amounts) if amounts else 1.0
            min_amount = min(amounts) if amounts else 0.0

            # Scale for Y axis (handle case where max == min)
            y_range = max_amount - min_amount
            y_scale = plot_rect.height() / (y_range if y_range > 0 else 1.0)
            
            # Draw X-axis labels (rotated)
            num_months = len(months)
            if num_months > 0:
                x_step = plot_rect.width() / (num_months - 1 if num_months > 1 else 1)
                for i, month in enumerate(months):
                    x_pos = plot_rect.left() + i * x_step
                    painter.save()
                    painter.translate(int(x_pos), plot_rect.bottom() + 5)
                    painter.rotate(-45)
                    text_width = 80
                    text_height = 20
                    painter.drawText(QRect(-text_width // 2, 0, text_width, text_height), Qt.AlignLeft, month)
                    painter.restore()
            
            # Draw Y-axis labels
            painter.drawText(QRect(0, plot_rect.bottom() - 10, left_margin - 5, 20), Qt.AlignRight | Qt.AlignVCenter, str(round(min_amount, 2)))
            painter.drawText(QRect(0, plot_rect.top() - 10, left_margin - 5, 20), Qt.AlignRight | Qt.AlignVCenter, str(round(max_amount, 2)))

            # Draw lines and points
            painter.setPen(QColor("#3d3dff"))
            points = []
            if num_months > 0:
                for i, amount in enumerate(amounts):
                    x_pos = plot_rect.left() + i * x_step
                    y_pos = plot_rect.bottom() - ((amount - min_amount) * y_scale)
                    points.append(QPointF(x_pos, y_pos))

                if len(points) > 1:
                    for i in range(len(points) - 1):
                        painter.drawLine(points[i], points[i+1])
                elif len(points) == 1:
                    painter.drawEllipse(points[0], 3, 3) # Draw a point if only one data point

        else: # Pie Chart (Not Implemented)
            painter.drawText(plot_rect, Qt.AlignCenter, self.graph_title)

class SettingsView(QWidget):
    settings_changed = pyqtSignal()
    clear_all_requested = pyqtSignal() 
    backup_requested = pyqtSignal(str, str) # New signal: (email, password)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("color: white; background-color: #000;")
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setVerticalSpacing(15)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your Gemini API Key")
        self.api_key_input.setStyleSheet("background-color: #1a1a1a; color: white; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        form_layout.addRow(QLabel("Gemini API Key:"), self.api_key_input)
        
        self.model_input = QComboBox()
        self.model_input.addItems(["gemini-flash-latest", "gemini-pro", "Other"])
        self.model_input.setStyleSheet("background-color: #1a1a1a; color: white; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        form_layout.addRow(QLabel("Gemini Model:"), self.model_input)
        
        self.font_size_input = QSpinBox()
        self.font_size_input.setRange(8, 20)
        self.font_size_input.setStyleSheet("background-color: #1a1a1a; color: white; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        form_layout.addRow(QLabel("Font Size:"), self.font_size_input)
        
        self.logo_button = QPushButton("Select Logo Image")
        self.logo_button.setStyleSheet("background-color: #1a1a1a; color: white; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        self.logo_button.clicked.connect(self.select_logo)
        form_layout.addRow(QLabel("Custom Logo:"), self.logo_button)
        self.logo_path_label = QLabel("No logo selected.")
        form_layout.addRow(self.logo_path_label)

        layout.addLayout(form_layout)

        save_button = QPushButton("Save Settings")
        save_button.setStyleSheet("""
            QPushButton { background-color: #3d3dff; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #5555ff; }
        """)
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button, alignment=Qt.AlignCenter)

        layout.addSpacing(30)
        
        # Cloud Backup Section
        backup_title = QLabel("Cloud Backup (via Gmail)")
        backup_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00c853;")
        layout.addWidget(backup_title)
        
        backup_info = QLabel("Sends your .db file to your own email. Requires an 'App Password'.")
        backup_info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(backup_info)
        
        backup_form = QFormLayout()
        self.backup_email_input = QLineEdit()
        self.backup_email_input.setPlaceholderText("your-email@gmail.com")
        self.backup_email_input.setStyleSheet("background-color: #1a1a1a; border: 1px solid #00c853; padding: 5px; border-radius: 5px;")
        backup_form.addRow(QLabel("Gmail Address:"), self.backup_email_input)
        
        self.backup_pass_input = QLineEdit()
        self.backup_pass_input.setEchoMode(QLineEdit.Password)
        self.backup_pass_input.setPlaceholderText("Enter App Password")
        self.backup_pass_input.setStyleSheet("background-color: #1a1a1a; border: 1px solid #00c853; padding: 5px; border-radius: 5px;")
        backup_form.addRow(QLabel("App Password:"), self.backup_pass_input)
        
        layout.addLayout(backup_form)
        
        backup_button = QPushButton(" Backup to Cloud Now")
        backup_button.setIcon(qta.icon("fa5s.cloud-upload-alt", color='white'))
        backup_button.setStyleSheet("""
            QPushButton { background-color: #00c853; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #00e676; }
        """)
        backup_button.clicked.connect(self.on_backup_clicked)
        layout.addWidget(backup_button, alignment=Qt.AlignCenter)

        layout.addSpacing(30)
        
        # Danger Zone
        danger_title = QLabel("Danger Zone")
        danger_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff4d4d;")
        layout.addWidget(danger_title)
        
        clear_button = QPushButton("Clear All Expenses")
        clear_button.setStyleSheet("""
            QPushButton { background-color: transparent; color: #ff4d4d; padding: 10px; border-radius: 5px; font-weight: bold; border: 1px solid #ff4d4d; }
            QPushButton:hover { background-color: #ff4d4d; color: white; }
        """)
        clear_button.clicked.connect(self.on_clear_all)
        layout.addWidget(clear_button, alignment=Qt.AlignCenter)

        layout.addStretch()

    def on_backup_clicked(self):
        email = self.backup_email_input.text()
        password = self.backup_pass_input.text()
        if not email or not password:
            QMessageBox.warning(self, "Input Error", "Please provide both Gmail and App Password.")
            return
        self.backup_requested.emit(email, password)

    def on_clear_all(self):
        reply = QMessageBox.critical(self, 'Confirm Reset', 
                                     "DANGER: This will delete ALL expenses permanently. Continue?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.clear_all_requested.emit()

    def select_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Logo Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_path:
            self.logo_path_label.setText(file_path)

    def save_settings(self):
        api_key = self.api_key_input.text()
        model = self.model_input.currentText()
        font_size = self.font_size_input.value()
        logo_path = self.logo_path_label.text()
        backup_email = self.backup_email_input.text()
        
        config = {
            "GEMINI_API_KEY": api_key,
            "GEMINI_MODEL": model,
            "FONT_SIZE": font_size,
            "LOGO_PATH": logo_path,
            "BACKUP_EMAIL": backup_email
            }
        with open("config.json", "w") as f:
            json.dump(config, f)
        
        self.settings_changed.emit()
        QMessageBox.information(self, "Success", "Settings saved successfully!")

    def load_settings(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.api_key_input.setText(config.get("GEMINI_API_KEY", ""))
                self.model_input.setCurrentText(config.get("GEMINI_MODEL", "gemini-flash-latest"))
                self.font_size_input.setValue(config.get("FONT_SIZE", 12))
                self.logo_path_label.setText(config.get("LOGO_PATH", "No logo selected."))
                self.backup_email_input.setText(config.get("BACKUP_EMAIL", ""))
        except FileNotFoundError:
            pass 

class GeminiAssistView(QWidget):
    def __init__(self, dashboard_instance, parent=None):
        super().__init__(parent)
        self.dashboard_instance = dashboard_instance
        self.setStyleSheet("color: white; background-color: #000;")
        self.md = MarkdownIt()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Gemini Expense Assistant")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        self.question_input = QTextEdit()
        self.question_input.setPlaceholderText("Ask a question about your expenses...")
        self.question_input.setFixedHeight(70)
        self.question_input.setStyleSheet("background-color: #1a1a1a; color: white; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        layout.addWidget(self.question_input)

        ask_button = QPushButton("Ask Gemini")
        ask_button.setStyleSheet("""
            QPushButton {
                background-color: #3d3dff; 
                color: white; 
                padding: 10px; 
                border-radius: 5px; 
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5555ff;
            }
        """)
        ask_button.clicked.connect(self.ask_gemini)
        layout.addWidget(ask_button, alignment=Qt.AlignCenter)

        self.response_output = QWebEngineView()
        self.response_output.setStyleSheet("background-color: #1a1a1a; color: white; border: 1px solid #3d3dff; padding: 5px; border-radius: 5px;")
        layout.addWidget(self.response_output)

    def ask_gemini(self):
        question = self.question_input.toPlainText()
        if not question:
            QMessageBox.warning(self, "No Question", "Please enter a question to ask Gemini.")
            return

        api_key = self.load_api_key()
        if not api_key:
            QMessageBox.warning(self, "API Key Not Found", "Please set your Gemini API key in the Settings.")
            return

        genai.configure(api_key=api_key)
        
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                model_name = config.get("GEMINI_MODEL", "gemini-flash-latest")
        except FileNotFoundError:
            model_name = "gemini-flash-latest"
            
        model = genai.GenerativeModel(model_name)

        # Get summarized expense data
        monthly_summary = self.dashboard_instance.get_monthly_expenses_summary()
        category_summary = self.dashboard_instance.get_category_expenses_summary()
        yearly_summary = self.dashboard_instance.get_yearly_expenses_summary()
        
        prompt = f"""You are an expense assistant. Analyze the provided expense summaries to answer the user's question.
If the question is beyond the scope of these summaries, state that you can only answer questions based on the provided summaries.

{monthly_summary}
{category_summary}
{yearly_summary}

My question is: {question}"""

        try:
            self.response_output.setHtml("Thinking...")
            QApplication.processEvents()
            response = model.generate_content(prompt)
            html_response = self.md.render(response.text)
            
            html_with_mathjax = f"""
            <html>
            <head>
                <script type="text/javascript" async
                    src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.0/es5/tex-mml-chtml.js">
                </script>
                <style>
                    body {{
                        color: white;
                        background-color: #1a1a1a;
                    }}
                </style>
            </head>
            <body>
                {html_response}
            </body>
            </html>
            """
            self.response_output.setHtml(html_with_mathjax)
        except Exception as e:
            self.response_output.setHtml(f"An error occurred: {e}")

    def load_api_key(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                return config.get("GEMINI_API_KEY")
        except FileNotFoundError:
            return None

class DashboardView(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setStyleSheet("color: white; background-color: #000;")
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        title = QLabel("Financial Overview")
        title.setStyleSheet("font-size: 28px; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(title)

        # Stats Cards Layout
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(20)

        self.month_card = self.create_stat_card("Month Total", "$0.00", "fa5s.calendar-alt", "#3d3dff")
        self.today_card = self.create_stat_card("Today", "$0.00", "fa5s.clock", "#00c853")
        self.top_cat_card = self.create_stat_card("Top Category", "None", "fa5s.tag", "#ffab00")

        self.cards_layout.addWidget(self.month_card)
        self.cards_layout.addWidget(self.today_card)
        self.cards_layout.addWidget(self.top_cat_card)

        self.layout.addLayout(self.cards_layout)
        self.layout.addStretch()
        
        self.update_stats()

    def create_stat_card(self, title, value, icon, color):
        card = QFrame()
        card.setFixedHeight(150)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #1a1a1a;
                border-radius: 15px;
                border: 1px solid {color};
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon, color=color).pixmap(30, 30))
        card_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #aaa; font-size: 14px;")
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        card_layout.addWidget(value_label)
        
        # Store label for updating
        card.value_label = value_label
        return card

    def update_stats(self):
        stats = database.get_dashboard_stats(self.conn)
        self.month_card.value_label.setText(f"${stats['total_month']:.2f}")
        self.today_card.value_label.setText(f"${stats['total_today']:.2f}")
        self.top_cat_card.value_label.setText(stats['top_category'])

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Faïssal Dashboard")
        self.resize(1100, 750)
        
        # Use an absolute path based on the script location for the database
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_file = os.path.join(base_dir, "expense_manager.db")
        
        self.conn = database.create_connection(self.db_file)
        database.main(self.db_file) # Ensure table is created

        self.init_ui()
        self.load_expenses()
        self.load_starred_expenses()
        self.apply_settings()

    def apply_settings(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                font_size = config.get("FONT_SIZE", 12)
                self.setStyleSheet(f"background-color: #000000; font-size: {font_size}pt;")
                
                logo_path = config.get("LOGO_PATH")
                if logo_path and logo_path != "No logo selected.":
                    pixmap = QPixmap(logo_path)
                    if not pixmap.isNull():
                        circular_pixmap = self.get_circular_pixmap(pixmap, 64) # Use 64x64 for logo size
                        self.logo.setPixmap(circular_pixmap)
                        self.logo.setText("") # Clear "LOGO" text if image is set
                    else:
                        self.logo.setText("LOGO")
                else:
                    self.logo.setText("LOGO")
        except FileNotFoundError:
            self.setStyleSheet("background-color: #000000; font-size: 12pt;")
            self.logo.setText("LOGO")

    def get_all_expenses_for_gemini(self):
        return database.get_all_expenses(self.conn)

    def get_monthly_expenses_summary(self):
        """Returns a summary of total expenses per month."""
        summary = database.get_monthly_summary(self.conn)
        summary_str = "Monthly Expense Summary:\n"
        for month, total in summary:
            summary_str += f"- {month}: ${total:.2f}\n"
        return summary_str

    def get_category_expenses_summary(self):
        """Returns a summary of total expenses per category."""
        summary = database.get_category_summary(self.conn)
        summary_str = "Category Expense Summary:\n"
        for category, total in summary:
            summary_str += f"- {category}: ${total:.2f}\n"
        return summary_str

    def get_yearly_expenses_summary(self):
        """Returns a summary of total expenses per year."""
        summary = database.get_yearly_summary(self.conn)
        summary_str = "Yearly Expense Summary:\n"
        for year, total in summary:
            summary_str += f"- {year}: ${total:.2f}\n"
        return summary_str

    def load_expenses(self):
        """Load expenses from the database and update the view."""
        expenses = database.get_all_expenses(self.conn)
        self.view_expenses_widget.update_expense_list(expenses)
        self.dashboard_view_widget.update_stats()

    def load_starred_expenses(self):
        """Load starred expenses from the database and update the view."""
        expenses = database.get_starred_expenses(self.conn)
        self.starred_view_widget.update_starred_list(expenses)
        self.dashboard_view_widget.update_stats()
    
    def add_expense(self, expense_data):
        """Adds a new expense to the database and refreshes the view."""
        expense = (
            expense_data['date'],
            expense_data['category'],
            expense_data['amount'],
            expense_data['description'],
            0 # starred
        )
        database.add_expense(self.conn, expense, commit=True)
        self.load_expenses() # Reload and refresh the view
    
    def delete_expense(self, expense_id):
        """Deletes a specific expense from the database."""
        database.delete_expense(self.conn, expense_id)
        self.load_expenses()
        self.load_starred_expenses()

    def clear_database(self):
        """Clears all expenses from the database."""
        database.clear_all_expenses(self.conn)
        self.load_expenses()
        self.load_starred_expenses()
        QMessageBox.information(self, "Database Reset", "All data has been cleared successfully.")

    def perform_cloud_backup(self, email, password):
        """Sends the .db file to the user's email in a background thread."""
        threading.Thread(target=self._backup_worker, args=(email, password), daemon=True).start()

    def _backup_worker(self, email, password):
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.text import MIMEText
        from email import encoders

        try:
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = email
            msg['Subject'] = f"Expense Manager Backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            body = "Attached is your latest Expense Manager database backup."
            msg.attach(MIMEText(body, 'plain'))

            filename = os.path.basename(self.db_file)
            with open(self.db_file, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {filename}")
                msg.attach(part)

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email, password)
            server.send_message(msg)
            server.quit()
            
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: QMessageBox.information(self, "Backup Success", "Backup sent successfully to your Gmail!"))
        except Exception as e:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Backup Failed", f"Error: {e}\n\nNote: You must use a Google 'App Password', not your regular login password."))

    def toggle_star(self, expense_id, starred):
        """Toggles the starred status of an expense."""
        database.update_expense_star(self.conn, expense_id, 1 - starred)
        self.load_expenses()
        self.load_starred_expenses()


    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- SIDEBAR ---
        sidebar = QFrame()
        sidebar.setFixedWidth(90)
        sidebar.setStyleSheet("background-color: #080808; border-right: 1px solid #1a1a1a;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 25, 10, 25)
        sidebar_layout.setSpacing(20)

        # Logo Label
        self.logo = QLabel("LOGO")
        self.logo.setStyleSheet("color: white; font-weight: bold; font-size: 14px; border: none;")
        self.logo.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.logo)
        sidebar_layout.addSpacing(20)

        # --- NAVIGATION BUTTONS ---
        self.btn_dash = NavButton("fa5s.tachometer-alt", active=True)
        self.btn_cards = NavButton("fa5s.credit-card")
        self.btn_add = NavButton("fa5s.plus")
        self.btn_star = NavButton("fa5s.star")
        self.btn_graphs = NavButton("fa5s.chart-bar") # New Graphs Button
        self.btn_gemini = NavButton("fa5s.rocket")
        self.btn_settings = NavButton("fa5s.cog")

        sidebar_layout.addWidget(self.btn_dash, alignment=Qt.AlignCenter)
        sidebar_layout.addWidget(self.btn_add, alignment=Qt.AlignCenter) # Group Add near Dash
        sidebar_layout.addWidget(self.btn_star, alignment=Qt.AlignCenter)
        sidebar_layout.addWidget(self.btn_graphs, alignment=Qt.AlignCenter) # Add Graphs Button
        sidebar_layout.addWidget(self.btn_cards, alignment=Qt.AlignCenter)
        sidebar_layout.addWidget(self.btn_gemini, alignment=Qt.AlignCenter)
        
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.btn_settings, alignment=Qt.AlignCenter)

        main_layout.addWidget(sidebar)

        # --- MAIN CONTENT ---
        content_area = QVBoxLayout()
        
        # Header
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("border-bottom: 1px solid #1a1a1a; background-color: #000;")
        h_layout = QHBoxLayout(header)
        
        welcome = QLabel("Master Manager")
        welcome.setStyleSheet("color: white; font-weight: bold; font-size: 22px; border: none; padding-left: 15px;")
        
        # Header Right Icons
        header_right = QWidget()
        hr_layout = QHBoxLayout(header_right)
        
        search_btn = self.create_header_btn("fa5s.search")
        bell_btn = self.create_header_btn("fa5s.bell")
        profile_btn = self.create_header_btn("fa5s.user") 

        hr_layout.addWidget(search_btn)
        hr_layout.addWidget(bell_btn)
        hr_layout.addWidget(profile_btn)

        h_layout.addWidget(welcome)
        h_layout.addStretch()
        h_layout.addWidget(header_right)

        content_area.addWidget(header)
        
        # --- STACKED WIDGET FOR MAIN BODY CONTENT ---
        self.stacked_widget = QStackedWidget()
        content_area.addWidget(self.stacked_widget)
        
        # 1. Dashboard View
        self.dashboard_view_widget = DashboardView(self.conn, self)
        self.stacked_widget.addWidget(self.dashboard_view_widget)

        # 2. Add Expense View
        self.add_expense_widget = AddExpenseView(self)
        self.add_expense_widget.expense_added.connect(self.add_expense)
        self.stacked_widget.addWidget(self.add_expense_widget)

        # 3. View Expenses View
        self.view_expenses_widget = ViewExpensesView(self)
        self.view_expenses_widget.star_toggled.connect(self.toggle_star)
        self.view_expenses_widget.expense_deleted.connect(self.delete_expense)
        self.stacked_widget.addWidget(self.view_expenses_widget)
        
        # 4. Cards View
        self.cards_view_widget = CardsView(self)
        self.stacked_widget.addWidget(self.cards_view_widget)
        
        # 5. Starred View
        self.starred_view_widget = StarredView(self)
        self.stacked_widget.addWidget(self.starred_view_widget)
        
        # 6. Graphs View
        self.graphs_view_widget = GraphsView(self.conn, self) # Pass connection to GraphsView
        self.stacked_widget.addWidget(self.graphs_view_widget)

        # 7. Settings View
        self.settings_view_widget = SettingsView(self)
        self.settings_view_widget.settings_changed.connect(self.apply_settings)
        self.settings_view_widget.clear_all_requested.connect(self.clear_database)
        self.settings_view_widget.backup_requested.connect(self.perform_cloud_backup)
        self.stacked_widget.addWidget(self.settings_view_widget)
        
        # 8. Gemini Assist View
        self.gemini_assist_view_widget = GeminiAssistView(self)
        self.stacked_widget.addWidget(self.gemini_assist_view_widget)

        # Set initial view
        self.stacked_widget.setCurrentWidget(self.dashboard_view_widget)

        # Connect navigation buttons to switch views
        self.btn_dash.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.dashboard_view_widget))
        self.btn_add.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.add_expense_widget))
        self.btn_star.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.starred_view_widget))
        self.btn_graphs.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.graphs_view_widget))
        self.btn_cards.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.view_expenses_widget)) # Now shows expenses list
        self.btn_settings.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.settings_view_widget))
        self.btn_gemini.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.gemini_assist_view_widget))


        main_layout.addLayout(content_area)

    def create_header_btn(self, icon_name):
        btn = QPushButton()
        btn.setIcon(qta.icon(icon_name, color='white'))
        btn.setIconSize(QSize(22, 22))
        btn.setFixedSize(40, 40)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { border: none; background: transparent; }
            QPushButton:hover { background-color: #1a1a1a; border-radius: 20px; }
        """)
        return btn

    def get_circular_pixmap(self, pixmap, size):
        target = QPixmap(size, size)
        target.fill(Qt.transparent)

        painter = QPainter(target)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        path = QPainterPath()
        path.addRoundedRect(0, 0, size, size, size / 2, size / 2)
        painter.setClipPath(path)

        # Scale the original pixmap to fit the target size while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        
        # Calculate the top-left position to center the scaled pixmap
        x = int((size - scaled_pixmap.width()) / 2)
        y = int((size - scaled_pixmap.height()) / 2)
        
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()
        return target

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec_())
