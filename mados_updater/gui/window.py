"""Main window for madOS Updater GUI."""

import sys
import threading

from gi.repository import Gtk, GLib, Gio

from .colors import NORD_BG, NORD_BG_LIGHT, NORD_FG, NORD_ACCENT
from .theme import NORD_CSS
from .pages.base import create_page_header, show_error, show_confirmation

from ..mados_updater import MadOSUpdater


class UpdaterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="madOS Updater")
        self.set_default_size(600, 500)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.updater = MadOSUpdater(progress_callback=self._on_progress)
        self.current_page = "status"
        self.update_available = False
        self.update_info = None

        self._build_ui()
        self._apply_css()
        self._load_status()

    def _apply_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(NORD_CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gtk.StyleContext.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _build_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_bg_color(NORD_BG)
        self.add(box)

        header = Gtk.HeaderBar()
        header.set_title("madOS Updater")
        header.set_show_close_button(True)
        self.set_titlebar(header)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        box.pack_start(self.stack, True, True, 0)

        self.stack.add_titled(self._build_status_page(), "status", "Estado")
        self.stack.add_titled(self._build_update_page(), "update", "Actualizar")
        self.stack.add_titled(self._build_rollback_page(), "rollback", "Restaurar")

        self.nav_bar = self._build_nav_bar()
        box.pack_start(self.nav_bar, False, False, 0)

    def _build_nav_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.set_margin_start(16)
        bar.set_margin_end(16)
        bar.set_margin_top(8)
        bar.set_margin_bottom(12)

        self.btn_status = Gtk.Button.new_with_label("Estado")
        self.btn_status.connect("clicked", lambda x: self._show_page("status"))

        self.btn_update = Gtk.Button.new_with_label("Actualizar")
        self.btn_update.connect("clicked", lambda x: self._show_page("update"))

        self.btn_rollback = Gtk.Button.new_with_label("Restaurar")
        self.btn_rollback.connect("clicked", lambda x: self._show_page("rollback"))

        bar.pack_start(self.btn_status)
        bar.pack_start(self.btn_update)
        bar.pack_start(self.btn_rollback)

        return bar

    def _build_status_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        page.set_vexpand(True)

        header = create_page_header("Estado del Sistema", "Verificar actualizaciones")
        page.pack_start(header, False, False, 0)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_margin_top(16)

        self.status_version = Gtk.Label()
        self.status_version.set_markup("<b>Versión:</b> cargando...")
        self.status_version.set_halign(Gtk.Align.START)
        content.pack_start(self.status_version, False, False, 0)

        self.status_repo = Gtk.Label()
        self.status_repo.set_markup("<b>Repositorio:</b> cargando...")
        self.status_repo.set_halign(Gtk.Align.START)
        content.pack_start(self.status_repo, False, False, 0)

        self.status_update = Gtk.Label()
        self.status_update.set_markup("<b>Actualización:</b> verificando...")
        self.status_update.set_halign(Gtk.Align.START)
        content.pack_start(self.status_update, False, False, 0)

        self.status_snapshots = Gtk.Label()
        self.status_snapshots.set_markup("<b>Snapshots locales:</b> 0")
        self.status_snapshots.set_halign(Gtk.Align.START)
        content.pack_start(self.status_snapshots, False, False, 0)

        btn_check = Gtk.Button.new_with_label("Verificar Actualizaciones")
        btn_check.get_style_context().add_class("suggested-action")
        btn_check.set_margin_top(20)
        btn_check.connect("clicked", lambda x: self._check_updates())
        content.pack_start(btn_check, False, False, 0)

        page.pack_start(content, True, True, 0)
        return page

    def _build_update_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        page.set_vexpand(True)

        header = create_page_header("Actualización", "Descargar e instalar")
        page.pack_start(header, False, False, 0)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_margin_top(16)

        self.update_info_label = Gtk.Label()
        self.update_info_label.set_markup(
            "No hay actualizaciones disponibles.\n"
            "Usa 'Verificar Actualizaciones' en la página de Estado."
        )
        self.update_info_label.set_halign(Gtk.Align.START)
        content.pack_start(self.update_info_label, False, False, 0)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_fraction(0.0)
        content.pack_start(self.progress_bar, False, False, 0)

        self.progress_label = Gtk.Label()
        self.progress_label.set_markup(
            '<span size="10000" foreground="#8FBCBB">Preparando...</span>'
        )
        self.progress_label.set_halign(Gtk.Align.START)
        content.pack_start(self.progress_label, False, False, 0)

        scrolled, self.log_view = self._create_log_view()
        content.pack_start(scrolled, True, True, 0)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_margin_top(12)

        self.btn_download = Gtk.Button.new_with_label("Descargar")
        self.btn_download.set_sensitive(False)
        self.btn_download.connect("clicked", lambda x: self._download_update())

        self.btn_install = Gtk.Button.new_with_label("Instalar")
        self.btn_install.set_sensitive(False)
        self.btn_install.connect("clicked", lambda x: self._install_update())

        btn_box.pack_end(self.btn_install, False, False, 0)
        btn_box.pack_end(self.btn_download, False, False, 0)

        content.pack_start(btn_box, False, False, 0)
        page.pack_start(content, True, True, 0)
        return page

    def _build_rollback_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        page.set_vexpand(True)

        header = create_page_header("Restaurar Sistema", "Volver a un punto anterior")
        page.pack_start(header, False, False, 0)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_margin_top(16)

        self.snapshot_list = Gtk.ListBox()
        self.snapshot_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        content.pack_start(self.snapshot_list, True, True, 0)

        btn_refresh = Gtk.Button.new_with_label("Actualizar Lista")
        btn_refresh.set_margin_top(12)
        btn_refresh.connect("clicked", lambda x: self._refresh_snapshots())
        content.pack_start(btn_refresh, False, False, 0)

        self.btn_do_rollback = Gtk.Button.new_with_label("Restaurar Seleccionado")
        self.btn_do_rollback.get_style_context().add_class("destructive-action")
        self.btn_do_rollback.set_sensitive(False)
        self.btn_do_rollback.set_margin_top(12)
        self.btn_do_rollback.connect("clicked", lambda x: self._do_rollback())
        content.pack_start(self.btn_do_rollback, False, False, 0)

        page.pack_start(content, True, True, 0)
        return page

    def _create_log_view(self):
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(150)

        log_view = Gtk.TextView()
        log_view.set_editable(False)
        log_view.set_cursor_visible(False)
        log_view.set_margin_start(8)
        log_view.set_margin_end(8)
        log_view.set_margin_top(8)
        log_view.set_margin_bottom(8)

        scrolled.add(log_view)
        return scrolled, log_view

    def _show_page(self, page_name):
        self.current_page = page_name
        self.stack.set_visible_child_name(page_name)

        if page_name == "rollback":
            self._refresh_snapshots()

    def _on_progress(self, message: str, percent: int):
        def _update():
            self.progress_bar.set_fraction(percent / 100.0)
            self.progress_label.set_markup(
                f'<span size="10000" foreground="#D8DEE9">{message}</span>'
            )
            self._append_log(message)

        GLib.idle_add(_update)

    def _append_log(self, message: str):
        def _append():
            buffer = self.log_view.get_buffer()
            end_iter = buffer.get_end_iter()
            buffer.insert(end_iter, f"{message}\n")
            mark = buffer.create_mark("end", end_iter, False)
            self.log_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

        GLib.idle_add(_append)

    def _load_status(self):
        def _load():
            current_version = self.updater.state.get_current_version()
            repo_url = self.updater.config.get("updater", "repo_url")
            channel = self.updater.config.get("updater", "channel")

            GLib.idle_add(
                lambda: self.status_version.set_markup(f"<b>Versión:</b> {current_version}")
            )
            GLib.idle_add(
                lambda: self.status_repo.set_markup(f"<b>Repositorio:</b> {repo_url} ({channel})")
            )

        thread = threading.Thread(target=_load)
        thread.daemon = True
        thread.start()

    def _check_updates(self):
        self._show_page("update")
        self.log_view.get_buffer().set_text("")

        def _check():
            result = self.updater.check()

            if result:
                release = self.updater.github.fetch_releases_json()
                if release:
                    current = self.updater.state.get_current_version()
                    self.update_available = True
                    self.update_info = release
                    GLib.idle_add(
                        lambda: self.update_info_label.set_markup(
                            f"<b>Actualización disponible:</b> {current} → {release.version}\n"
                            f"<b>Fecha:</b> {release.release_date}\n"
                            f"<b>Cambios:</b> {release.changelog[:200]}..."
                        )
                    )
                    GLib.idle_add(lambda: self.btn_download.set_sensitive(True))
            else:
                GLib.idle_add(
                    lambda: self.update_info_label.set_markup("<b>El sistema está actualizado.</b>")
                )

            GLib.idle_add(
                lambda: self.status_update.set_markup(
                    f"<b>Actualización:</b> {'Disponible' if result else 'Al día'}"
                )
            )

        thread = threading.Thread(target=_check)
        thread.daemon = True
        thread.start()

    def _download_update(self):
        self.btn_download.set_sensitive(False)
        self.btn_install.set_sensitive(False)

        def _download():
            success = self.updater.download()
            GLib.idle_add(lambda: self.btn_install.set_sensitive(success))

        thread = threading.Thread(target=_download)
        thread.daemon = True
        thread.start()

    def _install_update(self):
        if not show_confirmation(
            self,
            "Confirmar Actualización",
            "¿Aplicar la actualización? Se creará un snapshot local antes de modificar el sistema.",
        ):
            return

        self.btn_install.set_sensitive(False)

        def _install():
            success = self.updater.install()
            if success:
                GLib.idle_add(
                    lambda: self.update_info_label.set_markup(
                        "<b>¡Actualización completada!</b>\nReinicie el sistema para aplicar los cambios."
                    )
                )
            else:
                GLib.idle_add(
                    lambda: self.update_info_label.set_markup(
                        "<b>Error en la actualización.</b>\nPuede restaurar desde un snapshot."
                    )
                )

        thread = threading.Thread(target=_install)
        thread.daemon = True
        thread.start()

    def _refresh_snapshots(self):
        while True:
            row = self.snapshot_list.get_row_at_index(0)
            if row is None:
                break
            self.snapshot_list.remove(row)

        def _load():
            snapshots = self.updater.snapshot_mgr.list_local_snapshots()

            for snap in reversed(snapshots[-10:]):
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                box.set_margin_start(12)
                box.set_margin_end(12)
                box.set_margin_top(8)
                box.set_margin_bottom(8)

                type_label = Gtk.Label()
                type_class = snap["type"]
                type_label.set_markup(
                    f'<span size="10000" background="#4C566A" padding="4,2">{snap["type"]}</span>'
                )
                box.pack_start(type_label, False, False, 0)

                info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                desc_label = Gtk.Label()
                desc_label.set_markup(f"<b>{snap['description']}</b>")
                desc_label.set_halign(Gtk.Align.START)
                info_box.pack_start(desc_label, False, False, 0)

                date_label = Gtk.Label()
                date_label.set_markup(
                    f'<span size="10000" foreground="#8FBCBB">{snap["date"]} {snap["time"]}</span>'
                )
                date_label.set_halign(Gtk.Align.START)
                info_box.pack_start(date_label, False, False, 0)

                box.pack_start(info_box, True, True, 0)

                row.add(box)
                GLib.idle_add(lambda r=row: self.snapshot_list.add(r))

            GLib.idle_add(
                lambda: self.status_snapshots.set_markup(
                    f"<b>Snapshots locales:</b> {len(snapshots)}"
                )
            )

        def on_select(listbox, row):
            self.btn_do_rollback.set_sensitive(row is not None)

        self.snapshot_list.connect("row-selected", on_select)

        thread = threading.Thread(target=_load)
        thread.daemon = True
        thread.start()

    def _do_rollback(self):
        row = self.snapshot_list.get_selected_row()
        if not row:
            return

        snapshot_data = row.get_children()[0]
        snapshot_num = None

        for i, snap in enumerate(reversed(self.updater.snapshot_mgr.list_local_snapshots()[-10:])):
            if i == self.snapshot_list.get_selected_row().get_index():
                snapshot_num = snap["number"]
                break

        if snapshot_num is None:
            return

        if not show_confirmation(
            self,
            "Confirmar Restauración",
            f"¿Restaurar al snapshot #{snapshot_num}? Los cambios desde ese punto se perderán.",
        ):
            return

        def _rollback():
            success = self.updater.snapper.rollback_with_default(int(snapshot_num))
            if success:
                GLib.idle_add(
                    lambda: show_error(
                        self, "Restauración Completada", "El sistema se restaurará al reiniciar."
                    )
                )

        thread = threading.Thread(target=_rollback)
        thread.daemon = True
        thread.start()


def run_gui():
    app = Gtk.Application(application_id="com.mados.updater")
    app.connect("activate", lambda a: a.add_window(UpdaterWindow(a)))
    app.run(sys.argv)


if __name__ == "__main__":
    run_gui()
