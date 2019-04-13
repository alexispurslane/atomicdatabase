import io
import sys
import hashlib

from sdl2 import *
import ctypes
import OpenGL.GL as gl

import imgui

from imgui.integrations.sdl2 import SDL2Renderer

import AtomicDatabase.eav_database as eav
import AtomicDatabase.nl_eav_interface as nl
from sexpdata import loads, dumps
import spacy

DB = eav.EAVDatabase()
nlp = spacy.load("en_core_web_sm")
matcher = nl.create_matcher(nlp)

def draw_imgui_table_database(DB):
    imgui.begin("Table Database", True)
    imgui.columns(len(DB.attributes) + 1, "TblDBAttributes")
    imgui.separator()
    imgui.text("entity id")
    imgui.next_column()
    for a in DB.attributes:
        imgui.text(a)
        imgui.next_column()
    imgui.separator()

    changes = []
    for e in DB.entities:
        imgui.text(e)
        imgui.next_column()
        for a in DB.attributes:
            res = DB.get_value(e, a)
            if res:
                change = draw_eav_value(e, a, res)
                if change:
                    changes.append(change)
            else:
                imgui.text("<N/A>")
            imgui.next_column()
    for change in changes:
        DB.add(change)
    imgui.columns(1)
    imgui.end()

def draw_eav_value(ent, att, v):
    iden = "##" + str((ent, att, v))
    if v in DB.entities:
        changed, new_entity = imgui.combo(
            iden, DB.entities.index(v), DB.entities
        )
        if changed:
            return (ent, att, DB.entities[new_entity])
    elif isinstance(v, int):
        changed, new_value = imgui.input_int(iden, v)
        if changed:
            return (ent, att, new_value)
    elif isinstance(v, float):
        changed, new_value = imgui.input_float(iden, v)
        if changed:
            return (ent, att, new_value)
    elif isinstance(v, str):
        changed, new_value = imgui.input_text(
            iden,
            v,
            256,
            imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
        )
        if changed:
            return (ent, att, new_value)
    return None

def draw_imgui_eav_database(DB):
    imgui.begin("EAV Database", True)
    imgui.columns(3, "EavDBAttributes")

    imgui.separator()
    imgui.text("entity")
    imgui.next_column()
    imgui.text("attribute")
    imgui.next_column()
    imgui.text("value")
    imgui.next_column()
    imgui.separator()

    changes = []
    for (e, a, v) in DB.eavs.values():
        ent = DB.entities[e]
        att = DB.attributes[a]
        imgui.text(ent)
        imgui.next_column()
        imgui.text(att)
        imgui.next_column()

        res = draw_eav_value(ent, att, v)
        if res:
            changes.append(res)
        imgui.next_column()

    for change in changes:
        DB.add(change)

    imgui.columns(1)
    imgui.end()

def draw_query(binds):
    imgui.columns(2, "QueryBinds")

    imgui.text("Variable Name")
    imgui.next_column()
    imgui.text("Value")
    imgui.next_column()
    imgui.separator()

    for (k, v) in binds.items():
        imgui.text(str(k))
        imgui.next_column()
        imgui.text(str(v))
        imgui.next_column()

    imgui.columns(1)

query_language = 1
query_value = ""
query_result = None
query_binds = {}
def draw_imgui_query_box(DB):
    global query_language, query_value, query_result, query_binds

    imgui.begin("Query...", False)
    imgui.push_item_width(100)
    clicked, query_language = imgui.combo(
        "", query_language, ["S-Expr", "NL"]
    )
    imgui.pop_item_width()
    imgui.same_line()
    changed, query_value = imgui.input_text(
        '',
        query_value,
        256,
        imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
    )

    if query_binds:
        draw_query(query_binds)
    elif query_result:
        imgui.text("Bindings empty. Try clicking 'Next'")
    else:
        imgui.text("No results")

    if changed:
        if query_language == 0:
            query_result = eav.evaluate_rule(DB, eav.body(query_value)[0], query_binds)
            print(query_result)
        elif query_language == 1:
            matches, entities = nl.understand_predicate(nlp, matcher, query_value)
            query_result = eav.evaluate_rule(DB, nl.convert_nlast_to_rules(matches, entities), query_binds)

    if imgui.button("Clear"):
        imgui.open_popup("confirm")
    imgui.same_line()

    if imgui.button("Next"):
        try:
            query_binds = next(query_result)
        except:
            query_binds = {}
            query_result = None

    if imgui.begin_popup("confirm"):
        imgui.text("Are you sure you want to clear the bindings?")
        imgui.separator()
        if imgui.button("Yes"):
            query_binds = {}
            imgui.close_current_popup()
        if imgui.button("No"):
            imgui.close_current_popup()
        imgui.end_popup()

    imgui.end()

rule_expanded = {}
new_rules = {}
def draw_imgui_database_rules(DB):
    global rule_expanded, new_rules
    imgui.begin("Database Rules", False)
    for name, rule in DB.rules.items():
        rule_expanded[name], _ = imgui.collapsing_header(name, True)

        if rule_expanded[name]:
            imgui.push_item_width(100)
            use_rule = rule
            if name in new_rules:
                use_rule = new_rules[name]
            rule_args = use_rule["args"] or []
            rule_lang = use_rule["lang"]
            rule_text = use_rule["text"]
            rule_body = use_rule["body"]
            uuid = "-"+hashlib.md5(name.encode()).hexdigest()
            for i, arg in enumerate(rule_args):
                arg = arg.split("-")[0]
                changed, rule_args[i] = imgui.input_text(
                    "##" + str(i) + "arg-" + uuid,
                    arg,
                    26,
                    imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
                )
                imgui.same_line()

            if imgui.button("+##" + uuid):
                rule_args.append("NewArgument")
                print(rule_args)
            imgui.same_line()

            clicked, rule_lang = imgui.combo(
                "##lang-" + uuid,
                rule_lang,
                ["S-Expr", "NL"]
            )
            imgui.pop_item_width()
            changed, rule_text = imgui.input_text_multiline(
                '##body-' + uuid,
                rule_text,
                2056,
                500,
                300,
                imgui.INPUT_TEXT_ENTER_RETURNS_TRUE,
            )
            if imgui.button("Done##"+uuid):
                if rule_lang == 0:
                    rule_body, rule_text = eav.body(rule_text, uuid)
                elif rule_lang == 1:
                    matches, entities = nl.understand_predicate(nlp, matcher, rule_text)
                    rule_body = nl.convert_nlast_to_rules(matches, entities, uuid)
            new_rules[name] = {
                "name": name,
                "args": [arg+uuid for arg in rule_args],
                "lang": rule_lang,
                "text": rule_text,
                "body": rule_body
            }
    if len(new_rules) > 0:
        for (name, rule) in new_rules.items():
            DB.rules[name] = rule
        new_rules = {}

    if imgui.button("New Rule"):
        imgui.open_popup("new-rule")

    if imgui.begin_popup("new-rule"):
        imgui.text("New Rule Name:")
        imgui.separator()
        changed, new_name = imgui.input_text(
            "##new-rule-name",
            "",
            26,
            imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
        )
        imgui.separator()
        if changed or imgui.button("OK"):
            if len(new_name) > 0:
                new_rules[new_name] = {
                    "name": new_name,
                    "args": [],
                    "lang": 0,
                    "text": "",
                    "body": []
                }
                imgui.close_current_popup()
        if imgui.button("Cancel"):
            imgui.close_current_popup()
        imgui.end_popup()
    imgui.end()

database_name = "Untitled"
def run():
    global DB, database_name
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

    show_eav_db = False
    show_table_db = True
    show_rules_db = False
    show_save_as = False
    show_load_db = False

    while running:
        imgui.styled(imgui.STYLE_CHILD_WINDOW_ROUNDING, 0)
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
                break
            renderer.process_event(event)
        renderer.process_inputs()

        #imgui.push_font(font_extra)
        imgui.new_frame()

        if imgui.begin_main_menu_bar():
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

            if imgui.begin_menu("Window", True):
                _, show_eav_db = imgui.menu_item(
                    "Show EAV Database View", selected=show_eav_db
                )
                _, show_table_db = imgui.menu_item(
                    "Show Table Database View", selected=show_table_db
                )
                _, show_rules_db = imgui.menu_item(
                    "Show Database Rules", selected=show_rules_db
                )

                imgui.end_menu()

            imgui.end_main_menu_bar()

        if show_load_db:
            imgui.open_popup("load-db")
        if show_save_as:
            imgui.open_popup("save-as")

        if imgui.begin_popup("save-as"):
            imgui.text("Database Filename:")
            imgui.separator()
            changed, new_name = imgui.input_text(
                "##database-name",
                "",
                26,
                imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
            )
            if changed or imgui.button("OK"):
                database_name = new_name
                eav.save_to_file(DB, database_name)
                show_save_as = False
                imgui.close_current_popup()
            if imgui.button("Cancel"):
                show_save_as = False
                imgui.close_current_popup()
            imgui.end_popup()

        if imgui.begin_popup("load-db"):
            imgui.text("Database Filename:")
            imgui.separator()
            changed, new_name = imgui.input_text(
                "##database-name",
                "",
                26,
                imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
            )
            if changed or imgui.button("OK"):
                database_name = new_name
                DB = eav.load_from_file(database_name)
                show_load_db = False
                imgui.close_current_popup()
            if imgui.button("Cancel"):
                show_load_db = False
                imgui.close_current_popup()
            imgui.end_popup()

        if show_table_db:
            draw_imgui_table_database(DB)
        if show_eav_db:
            draw_imgui_eav_database(DB)
        if show_rules_db:
            imgui.push_font(font_extra2)
            draw_imgui_database_rules(DB)
            imgui.pop_font()
        draw_imgui_query_box(DB)

        gl.glClearColor(1., 1., 1., 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()

        SDL_GL_SwapWindow(window)
    renderer.shutdown()
    SDL_GL_DeleteContext(gl_context)
    SDL_DestroyWindow(window)
    SDL_Quit()

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
    SDL_SetHint(SDL_HINT_VIDEO_HIGHDPI_DISABLED, b"1")

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

if __name__ == "__main__":
    run()
