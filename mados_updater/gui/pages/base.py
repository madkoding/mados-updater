"""Base helpers for GUI pages."""

from gi.repository import Gtk, GLib

from .colors import (
    NORD_BG,
    NORD_BG_LIGHT,
    NORD_FG,
    NORD_FG_DIM,
    NORD_ACCENT,
    NORD_SUCCESS,
    NORD_WARNING,
    NORD_ERROR,
)


def create_page_header(title: str, subtitle: str = "") -> Gtk.Box:
    header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    header.set_margin_start(24)
    header.set_margin_end(24)
    header.set_margin_top(20)
    header.set_margin_bottom(16)

    title_label = Gtk.Label()
    title_label.set_markup(f'<span size="18000" weight="bold">{title}</span>')
    title_label.set_halign(Gtk.Align.START)
    header.pack_start(title_label, False, False, 0)

    if subtitle:
        subtitle_label = Gtk.Label()
        subtitle_label.set_markup(
            f'<span size="12000" foreground="{NORD_FG_DIM}">{subtitle}</span>'
        )
        subtitle_label.set_halign(Gtk.Align.START)
        header.pack_start(subtitle_label, False, False, 0)

    return header


def create_nav_buttons(
    back_callback=None,
    next_callback=None,
    back_label="Atrás",
    next_label="Siguiente",
    back_enabled=True,
    next_enabled=True,
) -> Gtk.Box:
    nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    nav_box.set_margin_start(24)
    nav_box.set_margin_end(24)
    nav_box.set_margin_top(16)
    nav_box.set_margin_bottom(16)

    back_btn = Gtk.Button.new_with_label(back_label)
    back_btn.set_sensitive(back_enabled)
    if back_callback:
        back_btn.connect("clicked", back_callback)

    next_btn = Gtk.Button.new_with_label(next_label)
    next_btn.get_style_context().add_class("suggested-action")
    next_btn.set_sensitive(next_enabled)
    if next_callback:
        next_btn.connect("clicked", next_callback)

    nav_box.pack_end(next_btn, False, False, 0)
    nav_box.pack_start(back_btn, False, False, 0)

    return nav_box


def create_card(title: str = "", child: Gtk.Widget = None) -> Gtk.Box:
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    card.set_margin_start(8)
    card.set_margin_end(8)
    card.set_margin_top(8)
    card.set_margin_bottom(8)

    if title:
        title_label = Gtk.Label()
        title_label.set_markup(f'<span weight="bold">{title}</span>')
        title_label.set_halign(Gtk.Align.START)
        title_label.set_margin_start(16)
        title_label.set_margin_top(12)
        card.pack_start(title_label, False, False, 0)

    if child:
        if isinstance(child, Gtk.Container):
            card.pack_start(child, True, True, 0)
        else:
            card.pack_start(child, False, False, 0)

    return card


def create_status_badge(status: str) -> Gtk.Label:
    badge = Gtk.Label()
    if status == "up-to-date":
        badge.set_markup(
            f'<span size="10000" background="#A3BE8C33" foreground="#A3BE8C" '
            f'padding="4,2">{status.replace("-", " ").title()}</span>'
        )
    elif status == "update-available":
        badge.set_markup(
            f'<span size="10000" background="#EBCB8B33" foreground="#EBCB8B" '
            f'padding="4,2">{status.replace("-", " ").title()}</span>'
        )
    elif status == "error":
        badge.set_markup(
            f'<span size="10000" background="#BF616A33" foreground="#BF616A" '
            f'padding="4,2">{status.title()}</span>'
        )
    else:
        badge.set_markup(f'<span size="10000">{status}</span>')
    return badge


def create_progress_box() -> tuple[Gtk.ProgressBar, Gtk.Label]:
    progress = Gtk.ProgressBar()
    progress.set_show_text(True)
    progress.set_fraction(0.0)

    label = Gtk.Label()
    label.set_markup(f'<span size="10000" foreground="{NORD_FG_DIM}">Preparando...</span>')
    label.set_halign(Gtk.Align.START)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    box.pack_start(progress, False, False, 0)
    box.pack_start(label, False, False, 0)

    return progress, label


def update_progress(progress: Gtk.ProgressBar, label: Gtk.Label, message: str, fraction: float):
    def _update():
        progress.set_fraction(fraction)
        label.set_markup(f'<span size="10000" foreground="{NORD_FG}">{message}</span>')
        while GLib.MainContext.default().iteration(False):
            pass

    GLib.idle_add(_update)


def create_log_view() -> Gtk.ScrolledWindow:
    log_view = Gtk.TextView()
    log_view.set_editable(False)
    log_view.set_cursor_visible(False)
    log_view.set_margin_start(16)
    log_view.set_margin_end(16)
    log_view.set_margin_top(8)
    log_view.set_margin_bottom(8)
    log_view.get_style_context().add_class("log-view")

    scrolled = Gtk.ScrolledWindow()
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled.add(log_view)
    scrolled.set_min_content_height(200)

    return scrolled, log_view


def append_log(log_view: Gtk.TextView, message: str):
    def _append():
        buffer = log_view.get_buffer()
        end_iter = buffer.get_end_iter()
        buffer.insert(end_iter, message + "\n")
        mark = buffer.create_mark("end", end_iter, False)
        log_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

    GLib.idle_add(_append)


def show_error(parent: Gtk.Window, title: str, message: str):
    dialog = Gtk.MessageDialog(
        parent=parent,
        type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()


def show_confirmation(parent: Gtk.Window, title: str, message: str) -> bool:
    dialog = Gtk.MessageDialog(
        parent=parent,
        type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text=title,
    )
    dialog.format_secondary_text(message)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.YES
