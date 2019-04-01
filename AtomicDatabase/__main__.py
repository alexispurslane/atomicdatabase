import sys
import toga
from AtomicDatabase.eav_database import EAVDatabase

DB = EAVDatabase()
DB.add(("cool@gmail.com", "name", "Joe Cool"))
DB.add(("cool@gmail.com", "father", "pa_cool@gmail.com"))
DB.add(("cool@gmail.com", "mother", "mam_cool@gmail.com"))

DB.add(("pa_cool@gmail.com", "name", "Kent Cool"))
DB.add(("pa_cool@gmail.com", "father", "papa_cool@gmail.com"))
DB.add(("pa_cool@gmail.com", "mother", "mampa_cool@gmail.com"))

DB.add(("mam_cool@gmail.com", "name", "Ruby Cool"))
DB.add(("mam_cool@gmail.com", "father", "pamam_cool@gmail.com"))
DB.add(("mam_cool@gmail.com", "mother", "mammam_cool@gmail.com"))

DB.add(("papa_cool@gmail.com", "name", "John Cool"))

DB.add(("mampa_cool@gmail.com", "name", "Rose Cool"))

DB.add(("pamam_cool@gmail.com", "name", "Ed Cool"))

DB.add(("mammam_cool@gmail.com", "name", "Julie Cool"))


def button_handler(widget, table):
    eav_boxes = widget.parent.children
    entity = eav_boxes[1].value
    attr = eav_boxes[2].value
    value = ""
    try:
        value = float(eav_boxes[3].value)
    except ValueError:
        value = eav_boxes[3].value

    if len(entity) > 0 and len(attr) > 0 and len(value) > 0:
        print(entity, attr, value)
        DB.add((entity, attr, value))

        table.data = DB.create_table_data()
        table.refresh()

def build(app):
    splitc = toga.SplitContainer()

    table = toga.Table(["entity"] + DB.attributes, data=DB.create_table_data())
    table.style.flex = 1

    eavc = toga.Box()
    eavc.style.direction = "column"

    button = toga.Button("Add/Set EAV", on_press=lambda w: button_handler(w, table))
    button.style.flex = 0
    button.style.padding = 50
    button.style.width = 100
    eavc.add(button)

    entity = toga.TextInput(placeholder='Entity Name')
    entity.style.width = 100
    entity.style.padding_left = 50
    entity.style.padding_right = 50
    eavc.add(entity)

    attr = toga.TextInput(placeholder='Attribute Name')
    attr.style.width = 100
    attr.style.padding_left = 50
    attr.style.padding_right = 50
    eavc.add(attr)

    value = toga.TextInput(placeholder='Value')
    value.style.width = 100
    value.style.padding_left = 50
    value.style.padding_right = 50
    eavc.add(value)

    eavc.style.width = 200
    splitc.content = [table, eavc]

    return splitc

def main(args=None):
    """Start up Atomic Database"""
    if args is None:
        args = sys.argv[1:]

    print("Starting up Atomic Database 2.0...")

    return toga.App("Atomic Database 2.0", "org.christopherdumas.atomicdb", startup=build)

def run():
    main().main_loop()

if __name__ == "__main__":
    run()
