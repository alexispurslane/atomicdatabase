import io
import hashlib
import sys

from sdl2 import *
import ctypes
import OpenGL.GL as gl

import imgui

from imgui.integrations.sdl2 import SDL2Renderer

import eav_database as eav
import nl_eav_interface as nl
from sexpdata import loads, dumps
import spacy

show_eav_db = False
show_table_db = True
show_rules_db = False
show_meta_attr = False
popup_registry = {}

def draw_ok_cancel_popup(ide, message="Type a Thing:"):
    if imgui.begin_popup(ide):
        if not ide in popup_registry:
            popup_registry[ide] = ""
        imgui.text(message)
        changed, popup_registry[ide] = imgui.input_text(
            "##" + ide,
            popup_registry[ide],
            26,
            imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
        )
        if changed or imgui.button("OK"):
            imgui.close_current_popup()
            val = popup_registry[ide]
            popup_registry[ide] = ""
            imgui.end_popup()
            return val
        imgui.same_line()
        if imgui.button("Cancel"):
            imgui.close_current_popup()
            popup_registry[ide] = ""
            imgui.end_popup()
            return False
        imgui.end_popup()

database_name = "Untitled"
DB = eav.EAVDatabase()
if len(sys.argv) > 1:
    DB = eav.load_from_file(sys.argv[1])
    database_name = sys.argv[1]
nlp = spacy.load("en_core_web_sm")
matcher = nl.create_matcher(nlp)

search_query = {
    "entity": "",
    "attribute":  ""
}
def draw_imgui_table_database(DB):
    global search_query, show_table_db
    _, opened = imgui.begin("Table Database", True)
    show_table_db = show_table_db and opened

    changed, search_query["entity"] = imgui.input_text(
        "Search Entity##search",
        search_query["entity"],
        256,
        imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
    )
    changed, search_query["attribute"] = imgui.input_text(
        "Search Attribute##search-2",
        search_query["attribute"],
        26,
        imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
    )

    sqa = search_query["attribute"]
    attributes = [a for a in DB.attributes if len(sqa) == 0 or (sqa in a or a in sqa)]
    imgui.columns(len(attributes) + 1, "TblDBAttributes")
    imgui.separator()
    imgui.text("entity id")
    imgui.next_column()
    for a in attributes:
        imgui.text(a)
        imgui.next_column()
    imgui.separator()

    changes = []
    sqe = search_query["entity"]
    entities = [e for e in DB.entities if len(sqe) == 0 or (sqe in e or e in sqe)]
    for e in entities:
        imgui.text(e)
        imgui.next_column()
        for a in attributes:
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
    global show_eav_db
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
    _, opened = imgui.begin("EAV Database", True)
    show_eav_db = opened
    changed, search_query["entity"] = imgui.input_text(
        "Search Entity##search",
        search_query["entity"],
        256,
        imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
    )
    changed, search_query["attribute"] = imgui.input_text(
        "Search Attribute##search-2",
        search_query["attribute"],
        26,
        imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
    )

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
    sqa = search_query["attribute"]
    sqe = search_query["entity"]
    for (e, a, v) in DB.eavs.values():
        ent = DB.entities[e]
        att = DB.attributes[a]
        if (len(sqa) == 0 or (sqa in att or att in sqa)) and (len(sqe) == 0 or (sqe in ent or ent in sqe)):
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
query_binds = None

data_entity = 0
data_attr = ""
data_type = 1
data_value = ""

def draw_imgui_query_box(DB):
    global query_language, query_value, query_result, query_binds, data_entity, data_attr, data_type, data_value

    imgui.begin("Query...", False)
    imgui.push_item_width(100)
    clicked, query_language = imgui.combo(
        "##query-language", query_language, ["S-Expr", "NL"]
    )
    imgui.pop_item_width()
    imgui.same_line()
    changed, query_value = imgui.input_text(
        '##query-box',
        query_value,
        256,
        imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
    )

    if query_binds == {}:
        imgui.text("The results match, but no bindings were created")
    elif query_binds:
        draw_query(query_binds)
    elif query_binds is None and query_result:
        imgui.text("Bindings empty but backtracker still present. Try clicking 'Next'")
    else:
        imgui.text("No results")

    if changed:
        if query_language == 0:
            query_result = eav.evaluate_rule(DB, eav.body(query_value)[0], query_binds or {})
        elif query_language ==  1:
            matches, entities = nl.understand_predicate(nlp, matcher, query_value)
            query_result = eav.evaluate_rule(DB, nl.convert_nlast_to_rules(matches, entities), query_binds or {})

    if imgui.button("Clear"):
        imgui.open_popup("confirm")
    imgui.same_line()
    if imgui.button("Next") and query_result:
        print("--- NEXT")
        try:
            query_binds = next(query_result)
            print("Query Binds: " + str(query_binds))
        except StopIteration:
            print("No more results")
            query_binds = None
            query_result = None

    if imgui.button("Add New Entity"):
        imgui.open_popup("add-entity")
    imgui.same_line()
    if imgui.button("+##new-data"):
        imgui.open_popup("new-data")

    ent_value = draw_ok_cancel_popup("add-entity", "New Entity Name:")
    if ent_value:
        print("New entity created: " + str(ent_value))
        DB.entities.append(ent_value)

    if imgui.begin_popup("new-data"):
        changed, data_entity = imgui.combo(
            "Entity##data-entity", data_entity, DB.entities
        )
        changed, data_attr = imgui.input_text(
            'Attribute##data-attr',
            data_attr,
            256,
        )
        changed, data_type = imgui.combo(
            "Value Type##data-type", data_type, ['int', 'string']
        )
        if changed and data_type == 0:
            data_value = 0
        elif changed and data_type == 1:
            data_value = ""
        if data_type == 0:
            changed, data_value = imgui.input_int(
                "Value##data-value-int",
                data_value
            )
        else:
            changed, data_value = imgui.input_text(
                'Value##data-value-string',
                data_value,
                256,
                imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
            )
        if imgui.button("OK"):
            DB.add((DB.entities[data_entity], data_attr, data_value))
            imgui.close_current_popup()
        imgui.same_line()
        if imgui.button("Cancel"):
            imgui.close_current_popup()
        imgui.end_popup()

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
def draw_imgui_database_rules(DB):
    global rule_expanded, show_rules_db
    to_delete = []
    _, opened = imgui.begin("Database Rules", True)
    show_rules_db = opened
    for name, rule in DB.rules.items():
        rule_expanded[name], _ = imgui.collapsing_header(name, True)

        if rule_expanded[name]:
            imgui.push_item_width(100)
            rule_args = rule["args"] or []
            rule_lang = rule["lang"]
            rule_text = rule["text"]
            rule_body = rule["body"]
            uuid = "-"+hashlib.md5(name.encode()).hexdigest()
            arg_changed = False
            if imgui.button("Delete Rule##"+uuid):
                to_delete.append(name)
            for i, arg in enumerate(rule_args):
                arg = arg.split("-")[0]
                changed, rule_args[i] = imgui.input_text(
                    "##" + str(i) + "arg-" + uuid,
                    arg,
                    26,
                )
                arg_changed = changed or arg_changed
                imgui.same_line()

            if imgui.button("+##new" + uuid):
                rule_args.append("NewArgument")
                arg_changed = True
            imgui.same_line()
            if imgui.button("-##del" + uuid):
                del rule_args[-1]
                arg_changed = True
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
            )
            if imgui.button("Save Code##"+uuid):
                if rule_lang == 0:
                    rule_body, rule_text = eav.body(rule_text, uuid)
                elif rule_lang == 1:
                    matches, entities = nl.understand_predicate(nlp, matcher, rule_text)
                    rule_body = nl.convert_nlast_to_rules(matches, entities, uuid)
            DB.add_rule(name, rule_args, uuid, {
                "lang": rule_lang,
                "text": rule_text,
                "body": rule_body
            })

    for n in to_delete:
        del DB.rules[n]
    to_delete = []

    if imgui.button("New Rule"):
        imgui.open_popup("new-rule")

    new_name = draw_ok_cancel_popup("new-rule", "New Rule Name:")
    if new_name:
        if len(new_name) > 0:
            DB.add_rule(new_name.lower().replace(" ", "-"))
    imgui.end()

attr_expanded = {}
def draw_imgui_attribute_metadata(DB):
    global attr_expanded, show_meta_attr
    _, opened = imgui.begin("Database Attribute Editor", False)
    show_meta_attr = opened
    for attr, metadata in DB.attribute_metadata.items():
        attr_expanded[attr], _ = imgui.collapsing_header(attr, True)
        if not attr_expanded[attr]:
            continue
        changed, metadata["description"] = imgui.input_text_multiline(
            'Description##desc-' + attr,
            metadata["description"],
            2056,
            500,
            300,
        )
        clicked, metadata["type"] = imgui.combo(
            "Attribute Type##type-"+attr,
            metadata["type"],
            ["entity", "string", "int", "float"]
        )
        if metadata["type"] == 2:
            imgui.text("Leave 0s to allow an arbitrary string.")
            changed, metadata["num_limits"] = imgui.input_int2('Int Limits##'+attr, *metadata["num_limits"])
        elif metadata["type"] == 3:
            imgui.text("Leave 0s to allow an arbitrary string.")
            changed, metadata["num_limits"] = imgui.input_float2('Float Limits##'+attr, *metadata["num_limits"])
        elif metadata["type"] == 1:
            imgui.text("Leave blank to allow an arbitrary string.")
            changed, strings = imgui.input_text(
                "Allowed Strings##" + attr,
                ','.join(metadata["allowed_strings"]),
                26,
                imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
            )
            metadata["allowed_strings"] = strings.split(",")
        elif metadata["type"] == 0:
            imgui.text("All entities allowed")
    if imgui.button("Add New Attribute Metadata"):
        imgui.open_popup("new-attribute-meta")

    new_name = draw_ok_cancel_popup("new-attribute-meta", "Attribute Name:")
    if new_name:
        DB.attribute_metadata[new_name] = {
            "description": "",
            "type": 0,
            "num_limits": (0,0),
            "allowed_strings": []
        }
        attr_expanded[new_name] = False
    imgui.end()

def time_left(next_time):
    now = SDL_GetTicks()
    if next_time <= now:
        return 0
    else:
        return next_time - now

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

    while running:
        while SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT:
                running = False
                break
            renderer.process_event(event)
        renderer.process_inputs()

        #imgui.push_font(font_extra)
        imgui.new_frame()
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
                    "Show EAV View", selected=show_eav_db
                )
                _, show_table_db = imgui.menu_item(
                    "Show Table View", selected=show_table_db
                )
                _, show_rules_db = imgui.menu_item(
                    "Show Rules Editor", selected=show_rules_db
                )

                _, show_meta_attr = imgui.menu_item(
                    "Show Attribute Metadata Editor", selected=show_meta_attr
                )

                imgui.end_menu()

            imgui.end_main_menu_bar()

        if show_load_db:
            imgui.open_popup("load-db")
        if show_save_as:
            imgui.open_popup("save-as")

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

        if show_table_db:
            draw_imgui_table_database(DB)
        if show_eav_db:
            draw_imgui_eav_database(DB)
        if show_rules_db:
            imgui.push_font(font_extra2)
            draw_imgui_database_rules(DB)
            imgui.pop_font()
        if show_meta_attr:
            draw_imgui_attribute_metadata(DB)
        draw_imgui_query_box(DB)

        imgui.pop_style_var(7)
        imgui.pop_style_color(19)
        gl.glClearColor(1., 1., 1., 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()

        SDL_GL_SwapWindow(window)

        SDL_Delay(time_left(next_time))
        next_time += TICK_INTERVAL
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

    window = SDL_CreateWindow(window_name.encode('utf-8'),
                              SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                              width, height,
                              SDL_WINDOW_OPENGL|SDL_WINDOW_RESIZABLE)

    SDL_GL_SetSwapInterval(1)

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
