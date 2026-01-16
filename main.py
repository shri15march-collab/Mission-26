import json
import os
from datetime import datetime, timedelta
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import StringProperty

# --- Professional Mission Theme ---
Window.clearcolor = (0.05, 0.05, 0.08, 1)

Builder.load_string("""
<MenuScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: '12dp'
        spacing: '10dp'
        
        BoxLayout:
            size_hint_y: None
            height: '60dp'
            Label:
                text: "Mission 26."
                font_size: '30sp'
                bold: True
                color: (0, 0.9, 0.8, 1)
                halign: 'left'
                text_size: self.size
                valign: 'middle'
            Button:
                text: "STATS"
                size_hint: None, None
                size: '70dp', '48dp'
                pos_hint: {'center_y': .5}
                background_color: (0.5, 0.4, 0.8, 1)
                on_release: root.manager.current = 'stats'
            Button:
                text: "+"
                size_hint: None, None
                size: '48dp', '48dp'
                pos_hint: {'center_y': .5}
                background_color: (0, 0.9, 0.8, 1)
                on_release: root.open_add()
        
        TextInput:
            id: search_input
            hint_text: "Search missions..."
            size_hint_y: None
            height: '45dp'
            multiline: False
            background_color: (0.1, 0.12, 0.18, 1)
            foreground_color: (1, 1, 1, 1)
            hint_text_color: (0.5, 0.5, 0.6, 1)
            padding: [10, 12]
            on_text: root.refresh_list(root.current_filter)

        BoxLayout:
            size_hint_y: None
            height: '45dp'
            spacing: '5dp'
            Button:
                text: "All"
                on_release: root.refresh_list("all")
            Button:
                text: "Today"
                on_release: root.refresh_list("today")
            Button:
                text: "Upcoming"
                on_release: root.refresh_list("upcoming")
            Button:
                text: "Missed"
                on_release: root.refresh_list("missed")

        ScrollView:
            BoxLayout:
                id: container
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: '16dp'
                padding: [0, 10]

<StatsScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: '30dp'
        spacing: '20dp'
        Label:
            text: "Mission Data"
            font_size: '28sp'
            bold: True
            color: (0, 0.9, 0.8, 1)
            size_hint_y: None
            height: '60dp'
        
        BoxLayout:
            orientation: 'vertical'
            spacing: '12dp'
            Label:
                id: total_label
                text: "Total Objectives: 0"
                font_size: '20sp'
            Label:
                id: mastered_label
                text: "Accomplished: 0"
                font_size: '20sp'
                color: (0, 1, 0.5, 1)
            Label:
                id: active_label
                text: "Active Missions: 0"
                font_size: '20sp'
                color: (1, 0.8, 0, 1)

        Widget:
            size_hint_y: 1

        Button:
            text: "RETURN TO HQ"
            size_hint_y: None
            height: '55dp'
            background_color: (0, 0.7, 0.5, 1)
            on_release: root.manager.current = 'menu'

<AddSubjectScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: '25dp'
        spacing: '15dp'
        Label:
            id: screen_title
            text: "Mission Setup"
            font_size: '24sp'
            bold: True
            color: (0, 0.9, 0.8, 1)
        
        TextInput:
            id: s_name
            hint_text: "Mission Name"
            multiline: False
            size_hint_y: None
            height: '50dp'
        TextInput:
            id: s_date
            hint_text: "Deployment Date (YYYY-MM-DD)"
            multiline: False
            size_hint_y: None
            height: '50dp'
        TextInput:
            id: s_intervals
            hint_text: "Intervals (e.g. 1, 7, 14, 30)"
            multiline: False
            size_hint_y: None
            height: '50dp'

        Widget:
            size_hint_y: 1

        Button:
            text: "LAUNCH MISSION"
            size_hint_y: None
            height: '55dp'
            background_color: (0, 0.7, 0.5, 1)
            on_release: root.save_data()
        
        Button:
            text: "ABORT"
            size_hint_y: None
            height: '45dp'
            background_color: (0.6, 0.2, 0.2, 1)
            on_release: root.go_back()
""")

class MenuScreen(Screen):
    current_filter = StringProperty("all")

    def on_enter(self):
        self.refresh_list(self.current_filter)

    def open_add(self):
        App.get_running_app().editing_index = None
        self.manager.current = 'add_subject'

    def refresh_list(self, filter_type="all"):
        self.current_filter = filter_type
        container = self.ids.container
        container.clear_widgets()
        
        app = App.get_running_app()
        data = app.load_data()
        today = datetime.now().date()
        search_query = self.ids.search_input.text.lower()

        if not data:
            container.add_widget(Label(text="No active missions.", color=(0.5, 0.5, 0.6, 1)))
            return

        for i, item in enumerate(data):
            try:
                if search_query and search_query not in item['name'].lower():
                    continue

                raw_date = item['date'].strip().split(' ')[0]
                s_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                intervals = [int(x.strip()) for x in item['intervals'].split(',')]
                percent = float(item.get('percent', 0))
                
                stage = min(int((percent / 100) * len(intervals)), len(intervals) - 1)
                next_rev = s_date + timedelta(days=intervals[stage])

                if filter_type == "today" and next_rev != today: continue
                if filter_type == "upcoming" and next_rev <= today: continue
                if filter_type == "missed" and (next_rev >= today or percent >= 100): continue

                card = BoxLayout(orientation='vertical', size_hint_y=None, height='190dp', padding='15dp', spacing='8dp')
                with card.canvas.before:
                    Color(0.12, 0.15, 0.2, 1)
                    card.rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[12])
                card.bind(pos=self._update_bg, size=self._update_bg)

                head = BoxLayout(size_hint_y=None, height='35dp')
                name_btn = Button(text=f"{item['name'].upper()}", bold=True, font_size='18sp', 
                                 background_color=(0,0,0,0), color=(1,1,1,1), halign='left')
                name_btn.bind(size=name_btn.setter('text_size'))
                name_btn.bind(on_release=lambda x, it=item: self.show_schedule(it))
                
                edit_btn = Button(text="EDIT", size_hint_x=None, width='55dp', background_color=(0.2, 0.4, 0.7, 1))
                edit_btn.bind(on_release=lambda x, idx=i: self.open_edit(idx))
                
                head.add_widget(name_btn)
                head.add_widget(edit_btn)
                card.add_widget(head)
                
                nice_date = next_rev.strftime("%b %d, %Y")
                is_overdue = next_rev < today and percent < 100
                status_text = f"Objective Due: {nice_date}" if not is_overdue else f"OVERDUE: {nice_date}"
                status_color = (1, 0.3, 0.3, 1) if is_overdue else (0, 0.9, 0.8, 1)
                
                card.add_widget(Label(text=status_text, color=status_color, halign='left', text_size=(Window.width*0.7, None)))
                card.add_widget(ProgressBar(max=100, value=percent, size_hint_y=None, height='15dp'))

                btns = BoxLayout(spacing='10dp', size_hint_y=None, height='42dp')
                done = Button(text="Check Off", background_color=(0, 0.6, 0.3, 1), bold=True)
                done.bind(on_release=lambda x, idx=i: self.mark_done(idx))
                dele = Button(text="DEL", size_hint_x=None, width='55dp', background_color=(0.7, 0.2, 0.2, 1))
                dele.bind(on_release=lambda x, idx=i: self.delete_item(idx))
                
                btns.add_widget(done)
                btns.add_widget(dele)
                card.add_widget(btns)
                container.add_widget(card)
            except: continue

    def _update_bg(self, ins, val):
        ins.rect.pos = ins.pos
        ins.rect.size = ins.size

    def show_schedule(self, item):
        try:
            raw_date = item['date'].strip().split(' ')[0]
            start_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            intervals = [int(x.strip()) for x in item['intervals'].split(',')]
            content = BoxLayout(orientation='vertical', padding=15, spacing=10)
            content.add_widget(Label(text=f"Mission Log: {item['name']}", font_size='20sp', bold=True, color=(0, 0.9, 0.8, 1)))
            
            scroll = ScrollView()
            list_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
            list_box.bind(minimum_height=list_box.setter('height'))
            
            for i, days in enumerate(intervals):
                rev_date = start_date + timedelta(days=days)
                row = BoxLayout(size_hint_y=None, height='30dp')
                row.add_widget(Label(text=f"Revision {i+1}:", halign='left', size_hint_x=0.4))
                row.add_widget(Label(text=rev_date.strftime("%b %d, %Y"), halign='right', color=(0.9, 0.9, 0.9, 1)))
                list_box.add_widget(row)
            
            scroll.add_widget(list_box)
            content.add_widget(scroll)
            close_btn = Button(text="Close", size_hint_y=None, height='45dp', background_color=(0.3, 0.3, 0.4, 1))
            popup = Popup(title="Mission Roadmap", content=content, size_hint=(0.9, 0.75))
            close_btn.bind(on_release=popup.dismiss)
            content.add_widget(close_btn)
            popup.open()
        except: pass

    def open_edit(self, idx):
        app = App.get_running_app()
        app.editing_index = idx
        self.manager.current = 'add_subject'

    def mark_done(self, idx):
        app = App.get_running_app()
        data = app.load_data()
        ints = data[idx]['intervals'].split(',')
        inc = 100 / len(ints)
        data[idx]['percent'] = min(100, round(float(data[idx].get('percent', 0)) + inc, 1))
        app.save_data(data)
        self.refresh_list(self.current_filter)

    def delete_item(self, idx):
        app = App.get_running_app()
        data = app.load_data()
        data.pop(idx)
        app.save_data(data)
        self.refresh_list(self.current_filter)

class StatsScreen(Screen):
    def on_enter(self):
        data = App.get_running_app().load_data()
        total = len(data)
        mastered = len([i for i in data if float(i.get('percent', 0)) >= 100])
        active = total - mastered
        self.ids.total_label.text = f"Total Missions: {total}"
        self.ids.mastered_label.text = f"Accomplished: {mastered}"
        self.ids.active_label.text = f"In Progress: {active}"

class AddSubjectScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        if app.editing_index is not None:
            data = app.load_data()
            item = data[app.editing_index]
            self.ids.screen_title.text = "Modify Mission"
            self.ids.s_name.text = item['name']
            self.ids.s_date.text = item['date']
            self.ids.s_intervals.text = item['intervals']
        else:
            self.ids.screen_title.text = "New Mission"
            self.ids.s_name.text = ""
            self.ids.s_date.text = datetime.now().strftime("%Y-%m-%d")
            self.ids.s_intervals.text = "1, 7, 14, 30"

    def save_data(self):
        app = App.get_running_app()
        data = app.load_data()
        name = self.ids.s_name.text.strip()
        if not name: return
        
        entry = {
            "name": name,
            "date": self.ids.s_date.text.strip(),
            "intervals": self.ids.s_intervals.text.strip(),
            "percent": 0.0 if app.editing_index is None else data[app.editing_index].get('percent', 0.0)
        }
        
        if app.editing_index is not None:
            data[app.editing_index] = entry
        else:
            data.append(entry)
            
        app.save_data(data)
        self.manager.current = 'menu'

    def go_back(self):
        self.manager.current = 'menu'

class Mission26App(App):
    editing_index = None
    def build(self):
        self.data_path = os.path.join(self.user_data_dir, "m26_final_data.json")
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(AddSubjectScreen(name='add_subject'))
        sm.add_widget(StatsScreen(name='stats'))
        return sm

    def load_data(self):
        if not os.path.exists(self.data_path): return []
        try:
            with open(self.data_path, "r") as f:
                return json.load(f)
        except: return []

    def save_data(self, data):
        try:
            with open(self.data_path, "w") as f:
                json.dump(data, f, indent=4)
        except: pass

if __name__ == "__main__":
    Mission26App().run()
