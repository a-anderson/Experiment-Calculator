import streamlit as st
from streamlit_navigation_bar import st_navbar
import pages as pg

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

pages = ["Power - Binary", "Power - Normal", "Significance - Binary", "Significance - Normal", "SRM Test"]

styles = {
    "nav": {
        "background-color": "royalblue",
        "font-size": "large",
    },
    "img": {
        "padding-right": "14px",
    },
    "span": {
        "color": "white",
        "padding": "14px",
    },
    "active": {
        "background-color": "white",
        "color": "var(--text-color)",
        "font-weight": "bold",
        "padding": "14px",
    }
}
options = {
    "show_menu": False,
    "show_sidebar": False,
}

page = st_navbar(
    pages,
    styles=styles,
    options=options,
)

functions = {
    "Power - Binary": (pg.show_power, "binary"),
    "Power - Normal": (pg.show_power, "normal"),
    "Significance - Binary": (pg.show_significance, "binary"),
    "Significance - Normal": (pg.show_significance, "normal"),
    "SRM Test": (pg.show_srm_test, None),
}

go_to, arg = functions.get(page, (None, None))

if go_to:
    if arg:
        go_to(arg)
    else: 
        go_to()