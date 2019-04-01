import sys
import toga
import eav_database

DB = eav_database.EAVDatabase()
DB.add("cool@gmail.com", "name", "Joe Cool")
DB.add("cool@gmail.com", "father", "pa_cool@gmail.com")
DB.add("cool@gmail.com", "mother", "mam_cool@gmail.com")

DB.add("pa_cool@gmail.com", "name", "Kent Cool")
DB.add("pa_cool@gmail.com", "father", "papa_cool@gmail.com")
DB.add("pa_cool@gmail.com", "mother", "mampa_cool@gmail.com")

DB.add("mam_cool@gmail.com", "name", "Ruby Cool")
DB.add("mam_cool@gmail.com", "father", "pamam_cool@gmail.com")
DB.add("mam_cool@gmail.com", "mother", "mammam_cool@gmail.com")

DB.add("papa_cool@gmail.com", "name", "John Cool")

DB.add("mampa_cool@gmail.com", "name", "Rose Cool")

DB.add("pamam_cool@gmail.com", "name", "Ed Cool")

DB.add("mammam_cool@gmail.com", "name", "Julie Cool")


def button_handler(widget):
    print("hello")

def build(app):
    box = toga.Box()

    evs = [DB.get_entities_values(a) for a in DB.attributes]
    table = toga.Table([''] + DB.attributes, data=evs)

    button = toga.Button("New EAV", on_press=button_handler)
    button.style.padding = 50
    button.style.flex = 1
    box.add(button)

    return box

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
