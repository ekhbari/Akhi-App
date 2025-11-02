# main.py
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import mainthread
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.network.urlrequest import UrlRequest
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.button import Button
from core.manager import SourceManager
import threading
import os

# Optional: set window size for desktop testing
# Window.size = (360, 720)

KV = '''
ScreenManager:
    HomeScreen:
    ChaptersScreen:
    ReaderScreen:

<HomeScreen>:
    name: "home"
    BoxLayout:
        orientation: "vertical"
        padding: dp(8)
        spacing: dp(8)

        MDTopAppBar:
            title: "Akhi Manga"
            left_action_items: [["menu", lambda x: None]]

        MDTextField:
            id: search_field
            hint_text: "ابحث عن مانجا..."
            on_text_validate: root.on_search(self.text)
            size_hint_y: None
            height: dp(48)

        MDTabs:
            id: source_tabs
            on_tab_switch: root.on_tab_switch(*args)
            Tab:
                text: "مانجا ليك"
            Tab:
                text: "العاشق"

        ScrollView:
            id: results_scroll
            do_scroll_x: False
            do_scroll_y: True
            GridLayout:
                id: results_grid
                cols: 1
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height
                padding: dp(8)

<ChaptersScreen>:
    name: "chapters"
    BoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: root.manga_title if root.manga_title else "الفصول"
            left_action_items: [["arrow-left", lambda x: app.back_to_home()]]

        ScrollView:
            GridLayout:
                id: chapters_grid
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                padding: dp(8)
                spacing: dp(6)

<ReaderScreen>:
    name: "reader"
    BoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: root.chapter_title if root.chapter_title else ""
            left_action_items: [["arrow-left", lambda x: app.back_to_chapters()]]

        ScrollView:
            id: reader_scroll
            do_scroll_x: False
            do_scroll_y: True
            GridLayout:
                id: pages_layout
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                padding: dp(8)
                spacing: dp(6)
'''

class HomeScreen(Screen):
    def on_search(self, text):
        if not text.strip():
            return
        App = MDApp.get_running_app()
        App.search(text.strip())

    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        # optional: change active source
        App = MDApp.get_running_app()
        App.set_active_source(tab_text)

class ChaptersScreen(Screen):
    manga_title = ""
    manga_url = ""

    def set_manga(self, title, url):
        self.manga_title = title
        self.manga_url = url

class ReaderScreen(Screen):
    chapter_title = ""
    def set_chapter_title(self, title):
        self.chapter_title = title

class AkhiMangaApp(MDApp):
    def build(self):
        self.title = "Akhi Manga"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        self.manager = SourceManager()  # load sources
        self.active_source = self.manager.sources[0]  # default
        return Builder.load_string(KV)

    def set_active_source(self, tab_text):
        # map tab text to source index by name heuristics
        for src in self.manager.sources:
            if tab_text.lower() in src.name.lower():
                self.active_source = src
                return

    def search(self, query):
        sm = self.root
        home = sm.get_screen("home")
        grid = home.ids.results_grid
        grid.clear_widgets()
        # threaded search
        def _do():
            try:
                results = self.active_source.search(query)
            except Exception as e:
                results = []
            self._display_results(results)
        threading.Thread(target=_do, daemon=True).start()

    @mainthread
    def _display_results(self, results):
        sm = self.root
        home = sm.get_screen("home")
        grid = home.ids.results_grid
        if not results:
            grid.add_widget(Label(text="لا توجد نتائج", size_hint_y=None, height=40))
            return
        for item in results:
            b = Button(text=item.get("title", "بدون عنوان"), size_hint_y=None, height=56)
            b.bind(on_release=lambda inst, it=item: self.open_chapters(it))
            grid.add_widget(b)

    def open_chapters(self, item):
        sm = self.root
        chapters_screen = sm.get_screen("chapters")
        chapters_screen.set_manga(item.get("title"), item.get("url"))
        sm.current = "chapters"
        # load chapters threaded
        def _do():
            try:
                chapters = self.active_source.get_chapters(item.get("url"))
            except Exception as e:
                chapters = []
            self._display_chapters(chapters, item.get("title"))
        threading.Thread(target=_do, daemon=True).start()

    @mainthread
    def _display_chapters(self, chapters, manga_title):
        sm = self.root
        ch = sm.get_screen("chapters")
        ch.ids.chapters_grid.clear_widgets()
        ch.set_manga(manga_title, "")
        if not chapters:
            ch.ids.chapters_grid.add_widget(Label(text="لا توجد فصول", size_hint_y=None, height=40))
            return
        for c in chapters:
            b = Button(text=c.get("title", "فصل"), size_hint_y=None, height=48)
            b.bind(on_release=lambda inst, chap=c: self.open_reader(chap, manga_title))
            ch.ids.chapters_grid.add_widget(b)

    def open_reader(self, chapter, manga_title):
        sm = self.root
        reader = sm.get_screen("reader")
        reader.set_chapter_title(chapter.get("title"))
        sm.current = "reader"
        def _do():
            try:
                pages = self.active_source.get_images(chapter.get("url"))
            except Exception as e:
                pages = []
            self._display_pages(pages)
        threading.Thread(target=_do, daemon=True).start()

    @mainthread
    def _display_pages(self, pages):
        sm = self.root
        reader = sm.get_screen("reader")
        layout = reader.ids.pages_layout
        layout.clear_widgets()
        if not pages:
            layout.add_widget(Label(text="لا توجد صفحات", size_hint_y=None, height=40))
            return
        for p in pages:
            img = AsyncImage(source=p, size_hint_y=None, allow_stretch=True)
            img.height = 800  # will be resized; you can adjust or compute dynamically
            layout.add_widget(img)

    def back_to_home(self):
        self.root.current = "home"

    def back_to_chapters(self):
        self.root.current = "chapters"

if __name__ == "__main__":
    AkhiMangaApp().run()
      
