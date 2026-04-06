"""GTK CSS Theme for madOS Updater GUI (Nord Dark)."""

NORD_CSS = """
@import url('resource:/org/gnome/shell/theme/gdm.css');

* {
    background-color: #2E3440;
    color: #D8DEE9;
    font-family: "Cantarell", "Segoe UI", sans-serif;
    font-size: 14px;
}

window {
    background-color: #2E3440;
    color: #D8DEE9;
}

box {
    background-color: #2E3440;
}

.titlebar {
    background-color: #3B4252;
    color: #D8DEE9;
}

headerbar {
    background-color: #3B4252;
    color: #D8DEE9;
    border-bottom: 1px solid #434C5E;
}

headerbar title {
    font-weight: bold;
}

button {
    background-color: #4C566A;
    color: #D8DEE9;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
}

button:hover {
    background-color: #5E81AC;
}

button:active {
    background-color: #81A1C1;
}

button:disabled {
    background-color: #434C5E;
    color: #8FBCBB;
}

button.suggested-action {
    background-color: #5E81AC;
    color: #ECEFF4;
}

button.suggested-action:hover {
    background-color: #81A1C1;
}

button.destructive-action {
    background-color: #BF616A;
    color: #ECEFF4;
}

button.destructive-action:hover {
    background-color: #D08770;
}

entry {
    background-color: #3B4252;
    color: #D8DEE9;
    border: 1px solid #4C566A;
    border-radius: 6px;
    padding: 8px;
}

entry:focus {
    border-color: #81A1C1;
}

label {
    background-color: transparent;
    color: #D8DEE9;
}

label.dim-label {
    color: #8FBCBB;
}

label.title {
    font-size: 24px;
    font-weight: bold;
    color: #ECEFF4;
}

label.subtitle {
    font-size: 16px;
    color: #D8DEE9;
}

label.success {
    color: #A3BE8C;
}

label.warning {
    color: #EBCB8B;
}

label.error {
    color: #BF616A;
}

progressbar {
    background-color: #3B4252;
    color: #81A1C1;
}

progressbar progress {
    background-color: #5E81AC;
    border-radius: 6px;
}

progressbar trough {
    background-color: #3B4252;
    border-radius: 6px;
}

list {
    background-color: #2E3440;
    border: none;
}

listrow {
    background-color: #2E3440;
    border-bottom: 1px solid #3B4252;
}

listrow:hover {
    background-color: #3B4252;
}

listrow:selected {
    background-color: #4C566A;
}

scrolledwindow {
    background-color: #2E3440;
}

viewport {
    background-color: #2E3440;
}

dialog {
    background-color: #2E3440;
}

messagedialog {
    background-color: #2E3440;
}

stack {
    background-color: #2E3440;
}

stacksidebar {
    background-color: #3B4252;
}

stacksidebar sidebar {
    background-color: #3B4252;
}

infobar {
    background-color: #4C566A;
    border-radius: 6px;
    padding: 8px;
}

.actionbar {
    background-color: #3B4252;
    padding: 12px;
    border-top: 1px solid #434C5E;
}

.card {
    background-color: #3B4252;
    border-radius: 8px;
    padding: 16px;
    margin: 8px;
}

.card-title {
    font-weight: bold;
    font-size: 16px;
    color: #ECEFF4;
}

.page-header {
    padding: 20px;
    background-color: #3B4252;
    border-bottom: 1px solid #434C5E;
}

.page-header title {
    font-size: 22px;
    font-weight: bold;
    color: #ECEFF4;
}

.page-content {
    padding: 20px;
}

.nav-button {
    min-width: 120px;
    padding: 10px 20px;
}

.status-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
}

.status-badge.up-to-date {
    background-color: #A3BE8C33;
    color: #A3BE8C;
}

.status-badge.update-available {
    background-color: #EBCB8B33;
    color: #EBCB8B;
}

.status-badge.error {
    background-color: #BF616A33;
    color: #BF616A;
}

.snapshot-list-item {
    padding: 12px;
    border-bottom: 1px solid #434C5E;
}

.snapshot-list-item:hover {
    background-color: #3B4252;
}

.snapshot-description {
    font-weight: bold;
    color: #D8DEE9;
}

.snapshot-date {
    color: #8FBCBB;
    font-size: 12px;
}

.snapshot-type {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
    background-color: #4C566A;
    color: #D8DEE9;
}

.snapshot-type.pre {
    background-color: #5E81AC33;
    color: #81A1C1;
}

.snapshot-type.post {
    background-color: #A3BE8C33;
    color: #A3BE8C;
}

.snapshot-type.single {
    background-color: #B48EAD33;
    color: #B48EAD;
}
"""
