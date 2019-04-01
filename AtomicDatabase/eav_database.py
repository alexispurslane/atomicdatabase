from collections import namedtuple

def eav_hash(a, b):
    return 0.5*(a + b)*(a + b + 1)+b

class EAVDatabase:
    def __init__(self):
        self.attributes = []
        self.entities = []
        self.eavs = {}

    def get_or_add_entity_id(self, entity):
        forein_entity = -1
        try:
            forein_entity = self.entities.index(entity)
        except:
            self.entities.append(entity)
            forein_entity = len(self.entities) - 1
        return forein_entity

    def get_or_add_attribute_id(self, attr):
        forein_attr = -1
        try:
            forein_attr = self.attributes.index(attr)
        except:
            self.attributes.append(attr)
            forein_attr = len(self.attributes) - 1
        return forein_attr

    def add(self, eav):
        (entity, attr, value) = eav
        forein_entity = self.get_or_add_entity_id(entity)
        forein_attr = self.get_or_add_attribute_id(attr)

        self.eavs[eav_hash(forein_entity, forein_attr)] = (forein_entity, forein_attr, value)

        return self

    def remove_value(self, entity, attr):
        try:
            h = eav_hash(self.entities.index(entity), self.attributes.index(attr))
            if h in self.eavs: del self.eavs[h]
        except:
            print("Entity or Attribute " + str((entity, attr)) + " not found in database.")

    def get_attributes_values(self, entity):
        e = self.entities.index(entity)
        return (eav for (h, eav) in self.eavs.items() if eav[0] == e)

    def get_entities_values(self, attribute):
        ai = self.attributes.index(attribute)
        return (eav for (h, eav) in self.eavs.items() if eav[1] == ai)

    def get_value(self, entity, attr):
        h = eav_hash(self.entities.index(entity), self.attributes.index(attr))
        return self.eavs[h]

    def create_hashmaps_data(self):
        data = []
        for (entity, attribute, value) in sorted(self.eavs.values(), key=lambda x: x[0]):
            if entity >= len(data):
                print("creating entity " + str(entity))
                data.insert(entity, { "entity": self.entities[entity] })
            data[entity][self.attributes[attribute]] = value

        return data

    def create_table_data(self):
        data = self.create_hashmaps_data()

        for h in data:
            for attr in self.attributes:
                if not attr in h.keys():
                    h[attr] = False

        return data

