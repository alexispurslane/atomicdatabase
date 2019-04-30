import imgui
from sdl2 import *
import ctypes
import OpenGL.GL as gl

from sexpdata import loads, dumps
import spacy

import io
import hashlib
import sys
import copy
import traceback

import eav_database as eav
import nl_eav_interface as nl

SHOW_VARS = {
    'METADATA': False,
    'TABLE': True,
    'EAV': False,
    'EDITOR': False,
    'CONST': False
}

#  ____  _                 _         ____                                             _
# / ___|(_)_ __ ___  _ __ | | ___   / ___|___  _ __ ___  _ __   ___  _ __   ___ _ __ | |_ ___
# \___ \| | '_ ` _ \| '_ \| |/ _ \ | |   / _ \| '_ ` _ \| '_ \ / _ \| '_ \ / _ \ '_ \| __/ __|
#  ___) | | | | | | | |_) | |  __/ | |__| (_) | | | | | | |_) | (_) | | | |  __/ | | | |_\__ \
# |____/|_|_| |_| |_| .__/|_|\___|  \____\___/|_| |_| |_| .__/ \___/|_| |_|\___|_| |_|\__|___/
#                   |_|                                 |_|

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

data_entity = 0
data_attr = ""
data_type = 1
data_value = ""
query_error = ""

def draw_data_popup(DB, constant=False):
    global data_entity, data_attr, data_type, data_value, query_error
    if imgui.begin_popup("new-data"):
        if not constant:
            changed, data_entity = imgui.combo(
                "Entity##data-entity", data_entity, DB.entities
            )
        changed, data_attr = imgui.input_text(
            'Attribute##data-attr',
            data_attr,
            256,
        )
        data_attr = data_attr.lower().replace(" ", "_").replace("-", "_")
        changed, data_type = imgui.combo(
            "Value Type##data-type", data_type, DB.type_name
        )
        if changed and (data_type == 2 or data_type == 3 or data_type == 0):
            data_value = 0
        elif changed and data_type == 1:
            data_value = ""
        if data_type == 0:
            changed, data_value = imgui.combo(
                "Value##data-value-entity",
                data_value,
                DB.entities
            )
        elif data_type == 1:
            changed, data_value = imgui.input_text(
                'Value##data-value-string',
                data_value,
                256,
                imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
            )
        elif data_type == 2:
            changed, data_value = imgui.input_int(
                'Value##data-value-int',
                data_value
            )
        elif data_type == 3:
            changed, data_value = imgui.input_float(
                'Value##data-value-float',
                data_value
            )
        if imgui.button("OK") or imgui.get_io().keys_down[SDL_SCANCODE_RETURN]:
            try:
                if data_type == 0:
                    data_value = DB.entities[data_value]
                if constant:
                    DB.global_binds[data_attr] = data_value
                else:
                    DB.add((DB.entities[data_entity], data_attr, data_value))
                query_error = ""
                data_entity = 0
                data_attr = ""
                data_type = 1
                data_value = ""
                imgui.close_current_popup()
            except ValueError as e:
                query_error = "Data Error: " + str(e)
        imgui.same_line()
        if imgui.button("Cancel"):
            imgui.close_current_popup()
        imgui.end_popup()

is_unfolded = {}
def draw_eav_value(DB, ent, att, v, metadata={}):
    global is_unfolded
    iden = "##" + str((ent, att))
    metadata = metadata or DB.attribute_metadata.get(att, {})
    try:
        if (metadata and metadata.get("is_list")) or (not metadata and isinstance(v, list)):
            if not is_unfolded.get(iden):
                is_unfolded[iden] = False
            is_unfolded[iden], visible = imgui.collapsing_header("Show List"+iden, True)
            if is_unfolded[iden]:
                new_md = copy.copy(metadata)
                if new_md:
                    new_md["is_list"] = False
                changes = {}
                changed = False
                for i, (lab, val) in enumerate(v):
                    change = draw_eav_value(DB, ent, att, val, new_md)
                    if change:
                        changed = True
                        changes[i] = (lab, change[2])
                if changed:
                    return (ent, att, [changes[i] if i in changes else (v[i][0], v[i][1]) for i in range(0,len(v))])
        elif (metadata and metadata["type"] == 0) or (not metadata and v in DB.entities):
            changed, new_entity = imgui.combo(
                iden, DB.entities.index(v), DB.entities
            )
            if changed:
                return (ent, att, DB.entities[new_entity])
        elif (metadata and metadata["type"] == 2) or (not metadata and isinstance(v, int)):
            changed, new_value = imgui.input_int(iden, v)
            if changed:
                return (ent, att, new_value)
        elif (metadata and metadata["type"] == 3) or (not metadata and isinstance(v, float)):
            changed, new_value = imgui.input_float(iden, v)
            if changed:
                return (ent, att, new_value)
        elif (metadata and metadata["type"] == 1) or (not metadata and isinstance(v, str)):
            changed, new_value = imgui.input_text(
                iden,
                v,
                256,
                imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
            )
            if changed:
                return (ent, att, new_value)
    except Exception as e:
        print("--------")
        traceback.print_exc()
        print("--------")
        imgui.text_colored(str(v), 1, 0, 0, 1)
    if imgui.is_item_hovered() and metadata:
        imgui.begin_tooltip()
        imgui.text_colored("Type: ", 0, 0, 1, 1)
        imgui.same_line()
        descriptor = ""
        if metadata.get("is_list"):
            descriptor = "list"
        imgui.text(DB.type_name[metadata["type"]] + " " + descriptor)
        imgui.text(metadata["description"])
        imgui.end_tooltip()
    return None

#     _   _   _        _ _           _           __  __      _            _       _
#    / \ | |_| |_ _ __(_) |__  _   _| |_ ___    |  \/  | ___| |_ __ _  __| | __ _| |_ __ _
#   / _ \| __| __| '__| | '_ \| | | | __/ _ \   | |\/| |/ _ \ __/ _` |/ _` |/ _` | __/ _` |
#  / ___ \ |_| |_| |  | | |_) | |_| | ||  __/   | |  | |  __/ || (_| | (_| | (_| | || (_| |
# /_/   \_\__|\__|_|  |_|_.__/ \__,_|\__\___|   |_|  |_|\___|\__\__,_|\__,_|\__,_|\__\__,_|

attr_expanded = {}
def draw_imgui_attribute_metadata(DB):
    global attr_expanded
    if SHOW_VARS['METADATA']:
        _, opened = imgui.begin("Database Attribute Editor", True)
        SHOW_VARS['METADATA'] = SHOW_VARS['METADATA'] and opened
        for attr, metadata in DB.attribute_metadata.items():
            attr_expanded[attr], _ = imgui.collapsing_header(attr, True)
            if not attr_expanded[attr]:
                continue
            imgui.indent()
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
                DB.type_name
            )

            clicked, metadata["is_list"] = imgui.checkbox("Is List", bool(metadata.get("is_list")))

            if metadata["type"] == 2:
                imgui.text("Leave -1s to allow an arbitrary string.")
                changed, metadata["num_limits"] = imgui.input_int2('Int Limits##'+attr, *metadata["num_limits"])
            elif metadata["type"] == 3:
                imgui.text("Leave -1s to allow an arbitrary string.")
                changed, metadata["num_limits"] = imgui.input_float2('Float Limits##'+attr, *metadata["num_limits"])
            elif metadata["type"] == 1:
                imgui.text("Leave blank to allow an arbitrary string.")
                changed, strings = imgui.input_text(
                    "Allowed Strings##" + attr,
                    ','.join(metadata["allowed_strings"]),
                    256,
                    imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
                )
                metadata["allowed_strings"] = list(filter(lambda x: len(x), strings.split(",")))
            elif metadata["type"] == 0:
                imgui.text("All entities allowed")
            imgui.unindent()
        if imgui.button("Add New Attribute Metadata"):
            imgui.open_popup("new-attribute-meta")

        new_name = draw_ok_cancel_popup("new-attribute-meta", "Attribute Name:")
        if new_name:
            new_name = new_name.lower().replace(" ", "_").replace("-", "_")
            DB.attribute_metadata[new_name] = {
                "description": "",
                "type": 5,
                "num_limits": (0,0),
                "is_list": False,
                "allowed_strings": []
            }
            attr_expanded[new_name] = False
        imgui.end()

#  ____        _        _                     __     ___
# |  _ \  __ _| |_ __ _| |__   __ _ ___  ___  \ \   / (_) _____      _____
# | | | |/ _` | __/ _` | '_ \ / _` / __|/ _ \  \ \ / /| |/ _ \ \ /\ / / __|
# | |_| | (_| | || (_| | |_) | (_| \__ \  __/   \ V / | |  __/\ V  V /\__ \
# |____/ \__,_|\__\__,_|_.__/ \__,_|___/\___|    \_/  |_|\___| \_/\_/ |___/

search_query = {
    "entity": "",
    "attribute":  ""
}
table_error = ""
def draw_imgui_table_database(DB):
    global search_query, table_error
    if SHOW_VARS['TABLE']:
        _, opened = imgui.begin("Table Database", True)
        SHOW_VARS['TABLE'] = SHOW_VARS['TABLE'] and opened

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
                    change = draw_eav_value(DB, e, a, res)
                    if change:
                        changes.append(change)
                else:
                    imgui.text("<N/A>")
                imgui.next_column()
        for change in changes:
            try:
                DB.add(change)
                table_error = ""
            except ValueError as e:
                table_error = "Data Error: " + str(e)
        imgui.columns(1)
        imgui.text_colored(table_error, 1, 0, 0, 1)
        imgui.end()

def draw_imgui_eav_database(DB):
    global table_error
    if SHOW_VARS['EAV']:
        _, opened = imgui.begin("EAV Database", True)
        SHOW_VARS['EAV'] = SHOW_VARS['EAV'] and opened
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

                res = draw_eav_value(DB, ent, att, v)
                if res:
                    changes.append(res)
                imgui.next_column()

        for change in changes:
            try:
                DB.add(change)
                table_error = ""
            except ValueError as e:
                table_error = "Data Error: " + str(e)

        imgui.columns(1)
        imgui.text_colored(table_error, 1, 0, 0, 1)
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
        if isinstance(v, list):
            imgui.text(str([e[1] for e in v]))
        else:
            imgui.text(str(v))
        imgui.next_column()

    imgui.columns(1)

#  ____                                                _              __     ___
# |  _ \ _ __ ___   __ _ _ __ __ _ _ __ ___  _ __ ___ (_)_ __   __ _  \ \   / (_) _____      _____
# | |_) | '__/ _ \ / _` | '__/ _` | '_ ` _ \| '_ ` _ \| | '_ \ / _` |  \ \ / /| |/ _ \ \ /\ / / __|
# |  __/| | | (_) | (_| | | | (_| | | | | | | | | | | | | | | | (_| |   \ V / | |  __/\ V  V /\__ \
# |_|   |_|  \___/ \__, |_|  \__,_|_| |_| |_|_| |_| |_|_|_| |_|\__, |    \_/  |_|\___| \_/\_/ |___/
#                  |___/                                       |___/ 

query_language = 1
query_value = ""
query_result = None
query_binds = None
new_query_result = False

def draw_imgui_query_box(DB, monospace_font):
    global query_language, query_value, query_result, query_binds, data_entity, data_attr, data_type, data_value, query_error, new_query_result

    imgui.begin("Query...", False)
    imgui.push_item_width(100)
    clicked, query_language = imgui.combo(
        "##query-language", query_language, ["S-Expr", "NL"]
    )
    imgui.pop_item_width()
    imgui.same_line()
    if query_language == 0:
        imgui.push_font(monospace_font)
    changed, query_value = imgui.input_text(
        '##query-box',
        query_value,
        256,
        imgui.INPUT_TEXT_ENTER_RETURNS_TRUE
    )
    if query_language == 0:
        imgui.pop_font()

    if query_binds == {}:
        imgui.text_colored("The results match, but no bindings were created", 0, 1, 0, 1)
    elif query_binds:
        draw_query(query_binds)
    elif query_binds is None and query_result:
        imgui.text_colored("Bindings empty but backtracker still present. Try clicking 'Next'", 0, 0, 1, 1)
    else:
        imgui.text("No results")

    if changed:
        if query_language == 0:
            try:
                query_result = eav.evaluate_rule(DB, eav.body(query_value)[0], query_binds or {})
                query_error = ""
                new_query_result = True
            except Exception as e:
                query_error = "Parse Error: " + str(e)
                new_query_result = False
        elif query_language ==  1:
            try:
                matches, entities = nl.understand_predicate(nlp, matcher, query_value)
                query_result = eav.evaluate_rule(DB, nl.convert_nlast_to_rules(matches, entities), query_binds or {})
                query_error = ""
                new_query_result = True
            except Exception as e:
                query_error = "Parse Error: " + str(e)
                new_query_result = False
                traceback.print_exc()


    imgui.push_font(monospace_font)
    imgui.text_colored(query_error, 1, 0, 0, 1)
    imgui.pop_font()

    if imgui.button("Clear"):
        imgui.open_popup("confirm")
    imgui.same_line()
    if imgui.button("Next") and query_result or new_query_result:
        new_query_result = False
        print("--- NEXT")
        try:
            query_binds = next(query_result)
            print("Query Binds: " + str(query_binds))
        except StopIteration:
            print("No more results")
            query_binds = None
            query_result = None
        except Exception as e:
            query_error = "Excecution Error: " + str(e)
            traceback.print_exc()

    if imgui.button("Add New Entity"):
        imgui.open_popup("add-entity")
    imgui.same_line()
    if imgui.button("+##new-data"):
        imgui.open_popup("new-data")

    ent_value = draw_ok_cancel_popup("add-entity", "New Entity Name:")
    if ent_value:
        print("New entity created: " + str(ent_value))
        DB.entities.append(ent_value)

    draw_data_popup(DB)

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
rules_changed = {}
rule_error = ""
def draw_imgui_database_rules(DB, monospaced_font):
    global rule_expanded, rule_error, rules_changed
    if SHOW_VARS['EDITOR']:
        to_delete = []
        _, opened = imgui.begin("Database Rules", True)
        SHOW_VARS['EDITOR'] = SHOW_VARS['EDITOR'] and opened
        for name, rule in DB.rules.items():
            imgui.push_font(monospaced_font)
            rule_expanded[name], closed = imgui.collapsing_header(name, True)
            imgui.pop_font()
            if not closed:
                to_delete.append(name)

            if rule_expanded[name]:
                imgui.indent()
                imgui.push_item_width(100)
                rule_args = rule["args"] or []
                rule_lang = rule["lang"]
                rule_text = rule["text"]
                rule_body = rule["body"]
                arg_changed = False

                imgui.push_font(monospaced_font)
                for i, arg in enumerate(rule_args):
                    changed, rule_args[i] = imgui.input_text(
                        "##" + str(i) + "arg-" + name,
                        arg,
                        26,
                    )
                    if changed and " " in rule_args[i]:
                        rule_args[i] = rule_args[i].title().replace(" ", "")
                    arg_changed = changed or arg_changed
                    imgui.same_line()
                imgui.pop_font()

                if imgui.button("+##new" + name):
                    rule_args.append("NewArgument")
                    arg_changed = True
                imgui.same_line()
                if imgui.button("-##del" + name):
                    if len(rule_args) != 0:
                        del rule_args[-1]
                    arg_changed = True
                imgui.same_line()

                clicked, rule_lang = imgui.combo(
                    "##lang-" + name,
                    rule_lang,
                    ["S-Expr", "NL"]
                )
                imgui.pop_item_width()
                if rule_lang == 0:
                    imgui.push_font(monospaced_font)
                changed, rule_text = imgui.input_text_multiline(
                    '##body-' + name,
                    rule_text,
                    2056,
                    500,
                    300,
                )
                if rule_lang == 0:
                    imgui.pop_font()

                rules_changed[name] = rules_changed.get(name, False) or changed
                if rules_changed[name]:
                    imgui.push_text_wrap_pos()
                    imgui.text_colored(("This rule has been changed. "
                    "The text is saved, but if you want to save the excecutable code, "
                    "click the button below."), 0, 0, 1, 1)
                    imgui.pop_text_wrap_pos()
                if imgui.button("Save Code##"+name):
                    rules_changed[name] = False
                    try:
                        if rule_lang == 0:
                            rule_body, rule_text = eav.body(rule_text)
                        elif rule_lang == 1:
                            matches, entities = nl.understand_predicate(nlp, matcher, rule_text)
                            rule_body = nl.convert_nlast_to_rules(matches, entities)
                        rule_error = ""
                    except Exception as e:
                        rule_error = str(e)

                DB.add_rule(name, rule_args, {
                    "lang": rule_lang,
                    "text": rule_text,
                    "body": rule_body
                })
                imgui.unindent()

        if len(rule_error) > 0:
            imgui.push_text_wrap_pos()
            imgui.push_font(monospaced_font)
            imgui.text_colored("Parse Error: " + rule_error, 1, 0, 0, 1)
            imgui.pop_font()
            imgui.pop_text_wrap_pos()

        for n in to_delete:
            del DB.rules[n]
        to_delete = []

        if imgui.button("New Rule"):
            imgui.open_popup("new-rule")

        new_name = draw_ok_cancel_popup("new-rule", "New Rule Name:")
        if new_name:
            if len(new_name) > 0:
                DB.add_rule(new_name.lower().replace(" ", "_").replace("-", "_"))
        imgui.end()


const_expanded = {}
def draw_imgui_constants_window(DB):
    if SHOW_VARS['CONST']:
        to_delete = []
        _, opened = imgui.begin("Database Constants", True)
        SHOW_VARS['CONST'] = SHOW_VARS['CONST'] and opened

        for name, value in DB.global_binds.items():
            const_expanded[name], closed = imgui.collapsing_header(name.replace("*", ""), True)
            if const_expanded[name]:
                imgui.indent()
                change = draw_eav_value(DB, "CONST", name, value)
                if change:
                    (_, _, new_val) = change
                    if new_val:
                        DB.global_binds[name] = new_val
                imgui.unindent()

        if imgui.button("New Constant"):
            imgui.open_popup("new-data")
        draw_data_popup(DB, True)
        imgui.end()
