import io
import hashlib
import sys
import copy
import traceback

from sdl2 import *
import ctypes
import OpenGL.GL as gl

import imgui

from imgui.integrations.sdl2 import SDL2Renderer

from gui_windows import *
from sexpdata import loads, dumps
import spacy

database_name = "Untitled"
DB = eav.EAVDatabase()
if len(sys.argv) > 1:
    DB = eav.load_from_file(sys.argv[1])
    database_name = sys.argv[1]
nlp = spacy.load("en_core_web_sm")
matcher = nl.create_matcher(nlp)

def time_left(next_time):
    now = SDL_GetTicks()
    if next_time <= now:
        return 0
    else:
        return next_time - now

def draw_file_menu(show_save_as, show_load_db):
    if imgui.begin_menu("File", True):
        clicked_save, selected_save = imgui.menu_item(
            "Save",
        )

        if clicked_save:
            eav.save_to_file(DB, database_name)

        clicked_save_as, selected_save_as = imgui.menu_item(
            "Save As...",
        )

        if clicked_save_as:
            show_save_as = True

        clicked_load, selected_load = imgui.menu_item(
            "Load File...",
        )

        if clicked_load:
            show_load_db = True

        clicked_load_example, selected_load_example = imgui.menu_item(
            "Load Example Database",
        )

        if clicked_load_example:
            DB.load_examples()

        clicked_quit, selected_quit = imgui.menu_item(
            "Quit", 'Cmd+Q', False, True
        )

        if clicked_quit:
            exit(1)

        imgui.end_menu()
    return show_save_as, show_load_db

#     _                _ _           _   _               ___       _ _   _       _ _          _   _
#    / \   _ __  _ __ | (_) ___ __ _| |_(_) ___  _ __   |_ _|_ __ (_) |_(_) __ _| (_)______ _| |_(_) ___  _ __
#   / _ \ | '_ \| '_ \| | |/ __/ _` | __| |/ _ \| '_ \   | || '_ \| | __| |/ _` | | |_  / _` | __| |/ _ \| '_ \
#  / ___ \| |_) | |_) | | | (_| (_| | |_| | (_) | | | |  | || | | | | |_| | (_| | | |/ / (_| | |_| | (_) | | | |
# /_/   \_\ .__/| .__/|_|_|\___\__,_|\__|_|\___/|_| |_| |___|_| |_|_|\__|_|\__,_|_|_/___\__,_|\__|_|\___/|_| |_|
#         |_|   |_|

def push_settings():

    imgui.push_style_var(imgui.STYLE_WINDOW_PADDING, imgui.Vec2(5, 5))
    imgui.push_style_var(imgui.STYLE_WINDOW_ROUNDING, 5)
    imgui.push_style_var(imgui.STYLE_CHILD_WINDOW_ROUNDING, 0)
    imgui.push_style_var(imgui.STYLE_FRAME_PADDING, imgui.Vec2(11, 5))
    imgui.push_style_var(imgui.STYLE_FRAME_ROUNDING, 5)
    imgui.push_style_var(imgui.STYLE_ITEM_SPACING, imgui.Vec2(10, 10))
    imgui.push_style_var(imgui.STYLE_ITEM_INNER_SPACING, imgui.Vec2(5, 5))

    imgui.push_style_color(imgui.COLOR_TEXT, 0.00, 0.00, 0.00, 1.00)
    imgui.push_style_color(imgui.COLOR_TEXT, 0.00, 0.00, 0.00, 1.00)
    imgui.push_style_color(imgui.COLOR_WINDOW_BACKGROUND, 0.93, 0.94, 0.95, 1.00)
    imgui.push_style_color(imgui.COLOR_POPUP_BACKGROUND, 0.47, 0.56, 0.61, 1.00)
    imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND, 0.47, 0.56, 0.61, 1.00)
    imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND_HOVERED, 0.40, 0.50, 0.55, 1.00)
    imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND_ACTIVE, 0.54, 0.63, 0.68, 1.00)
    imgui.push_style_color(imgui.COLOR_TITLE_BACKGROUND, 0.26, 0.65, 0.96, 1.00)
    imgui.push_style_color(imgui.COLOR_TITLE_BACKGROUND_COLLAPSED, 0.26, 0.65, 0.96, 1.00)
    imgui.push_style_color(imgui.COLOR_TITLE_BACKGROUND_ACTIVE, 0.39, 0.71, 0.96, 1.00)
    imgui.push_style_color(imgui.COLOR_MENUBAR_BACKGROUND, 0.26, 0.65, 0.96, 1.00)
    imgui.push_style_color(imgui.COLOR_SCROLLBAR_GRAB_ACTIVE, 0.40, 0.40, 0.80, 0.40)
    imgui.push_style_color(imgui.COLOR_COMBO_BACKGROUND, 0.40, 0.50, 0.55, 1.00)
    imgui.push_style_color(imgui.COLOR_BUTTON, 0.00, 0.00, 0.00, 0.07)
    imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.90, 0.90, 0.90, 0.50)
    imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.54, 0.63, 0.68, 1.00)
    imgui.push_style_color(imgui.COLOR_HEADER, 0.00, 0.00, 0.00, 0.00)
    imgui.push_style_color(imgui.COLOR_HEADER_HOVERED, 0.05, 0.28, 0.63, 0.20)
    imgui.push_style_color(imgui.COLOR_HEADER_ACTIVE, 0.05, 0.28, 0.63, 0.26)

def impl_pysdl2_init():
    width, height = 1920, 1080
    window_name = "Atomic Database v2.0"

    if SDL_Init(SDL_INIT_EVERYTHING) < 0:
        print("Error: SDL could not initialize! SDL Error: " + SDL_GetError())
        exit(1)

    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24)
    SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 8)
    SDL_GL_SetAttribute(SDL_GL_ACCELERATED_VISUAL, 1)
    SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 1)
    SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, 16)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_FLAGS, SDL_GL_CONTEXT_FORWARD_COMPATIBLE_FLAG)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 4)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 1)
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE)

    SDL_SetHint(SDL_HINT_MAC_CTRL_CLICK_EMULATE_RIGHT_CLICK, b"1")

    window = SDL_CreateWindow(window_name.encode('utf-8'),
                              SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                              width, height,
                              SDL_WINDOW_OPENGL|SDL_WINDOW_RESIZABLE)

    if window is None:
        print("Error: Window could not be created! SDL Error: " + SDL_GetError())
        exit(1)

    gl_context = SDL_GL_CreateContext(window)
    if gl_context is None:
        print("Error: Cannot create OpenGL Context! SDL Error: " + SDL_GetError())
        exit(1)

    SDL_GL_MakeCurrent(window, gl_context)
    if SDL_GL_SetSwapInterval(1) < 0:
        print("Warning: Unable to set VSync! SDL Error: " + SDL_GetError())
        exit(1)

    return window, gl_context

#     _                _ _           _   _               ____  _             _
#    / \   _ __  _ __ | (_) ___ __ _| |_(_) ___  _ __   / ___|| |_ __ _ _ __| |_
#   / _ \ | '_ \| '_ \| | |/ __/ _` | __| |/ _ \| '_ \  \___ \| __/ _` | '__| __|
#  / ___ \| |_) | |_) | | | (_| (_| | |_| | (_) | | | |  ___) | || (_| | |  | |_
# /_/   \_\ .__/| .__/|_|_|\___\__,_|\__|_|\___/|_| |_| |____/ \__\__,_|_|   \__|
#         |_|   |_|


def run():
    global DB, database_name, TICK_INTERVAL, show_meta_attr, show_rules_db, show_eav_db, show_table_db
    font_extra = imgui.get_io().fonts.add_font_from_file_ttf(
        "AtomicDatabase/Roboto-Light.ttf", 20
    )
    font_extra2 = imgui.get_io().fonts.add_font_from_file_ttf(
        "AtomicDatabase/RobotoMono-Light.ttf", 20
    )
    window, gl_context = impl_pysdl2_init()
    renderer = SDL2Renderer(window)

    running = True
    event = SDL_Event()

    show_save_as = False
    show_load_db = False

    TICK_INTERVAL = 30
    next_time = SDL_GetTicks() + TICK_INTERVAL;

    io = imgui.get_io()
    while running:
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
                break
            renderer.process_event(event)
        renderer.process_inputs()

        imgui.new_frame()
        push_settings()

        if imgui.begin_main_menu_bar():
            (show_save_as, show_load_db) = draw_file_menu(show_save_as, show_load_db)

            # draw window menu
            if imgui.begin_menu("Window", True):
                for key in SHOW_VARS:
                    _, SHOW_VARS[key] = imgui.menu_item(
                        "Show " + key.title() + " View", selected=SHOW_VARS[key]
                    )

                imgui.end_menu()

            imgui.end_main_menu_bar()

        # if the menu triggered a popup, keep the popup on until we say otherwise
        if show_load_db:
            imgui.open_popup("load-db")
        if show_save_as:
            imgui.open_popup("save-as")


        # draw menu popups
        new_name = draw_ok_cancel_popup("save-as", "File Name to Save As:")
        if not new_name is None:
            if new_name:
                database_name = new_name
                eav.save_to_file(DB, database_name)
            show_save_as = False

        new_name = draw_ok_cancel_popup("load-db", "File Name to Load:")
        if not new_name is None:
            if new_name:
                database_name = new_name
                DB = eav.load_from_file(database_name)
            show_load_db = False

        # draw each gui window (from the module) if they are set to be drawn
        draw_imgui_table_database(DB)
        draw_imgui_eav_database(DB)
        draw_imgui_database_rules(DB, font_extra2)
        draw_imgui_attribute_metadata(DB)
        draw_imgui_query_box(DB, font_extra2)
        draw_imgui_constants_window(DB)

        # pop the style vars (this is required by Dear ImGui)
        imgui.pop_style_var(7)
        imgui.pop_style_color(19)

        # clear the background
        gl.glClearColor(1., 1., 1., 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()

        SDL_GL_SwapWindow(window)

        SDL_Delay(time_left(next_time))
        next_time += TICK_INTERVAL

    # close the window
    renderer.shutdown()
    SDL_GL_DeleteContext(gl_context)
    SDL_DestroyWindow(window)
    SDL_Quit()

if __name__ == "__main__":
    run()
