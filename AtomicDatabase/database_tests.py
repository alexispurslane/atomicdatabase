import unittest
import eav_database as e

class TestEAVDatabase(unittest.TestCase):
    def setUp(self):
        self.db = e.load_from_file("../test.db.json")

    def test_validation(self):
        with self.assertRaises(TypeError):
            self.db.validate(self.db.attribute_metadata["age"], "age", "44");
        with self.assertRaises(ValueError):
            self.db.validate(self.db.attribute_metadata["age"], "age", 10);
        self.assertIsNone(self.db.validate(self.db.attribute_metadata["age"], "age", 18));

        with self.assertRaises(TypeError):
            self.db.validate(self.db.attribute_metadata["father"], "father", 1337);
        self.assertIsNone(self.db.validate(self.db.attribute_metadata["father"], "father", "cool@gmail.com"));

        fake_metadata = {
            "type": 1,
            "allowed_strings": ["Foo", "Bar", "Baz"]
        }
        for s in fake_metadata["allowed_strings"]:
            self.assertIsNone(self.db.validate(fake_metadata, "foobarbaz", s))
        with self.assertRaises(ValueError):
            self.db.validate(fake_metadata, "foobarbaz", "Nope")

    def test_add_rule(self):
        self.db.add_rule("fake-rule1", ["A", "B"]);
        self.assertEqual(self.db.rules["fake-rule1"], {
            "name": "fake-rule1",
            "lang": 0,
            "text": "",
            "body": "",
            "args": ["A", "B"]
        })
        self.db.add_rule("fake-rule1", ["A", "B"], new_rule={
            "lang": 1,
            "text": "This is a invalid fun body"
        });
        self.assertEqual(self.db.rules["fake-rule1"], {
            "name": "fake-rule1",
            "lang": 1,
            "text": "This is a invalid fun body",
            "args": ["A", "B"]
        })

    def test_get_or_add_entity_id(self):
        og_len = len(self.db.entities)
        ide = self.db.get_or_add_entity_id("cool@gmail.com")
        self.assertEqual(ide, 0)
        self.assertEqual(len(self.db.entities), og_len)

        og_len = len(self.db.entities)
        ide = self.db.get_or_add_entity_id("wat")
        self.assertEqual(ide, og_len)
        self.assertEqual(len(self.db.entities), og_len + 1)

        og_len1 = len(self.db.entities)
        ide = self.db.get_or_add_entity_id("wat")
        self.assertEqual(ide, og_len)
        self.assertEqual(len(self.db.entities), og_len1)

    def test_get_or_add_attribute_id(self):
        og_len = len(self.db.attributes)
        ide = self.db.get_or_add_attribute_id("age")
        self.assertEqual(ide, 3)
        self.assertEqual(len(self.db.attributes), og_len)

        og_len = len(self.db.attributes)
        ide = self.db.get_or_add_attribute_id("wat")
        self.assertEqual(ide, og_len)
        self.assertEqual(len(self.db.attributes), og_len + 1)

        og_len1 = len(self.db.attributes)
        ide = self.db.get_or_add_attribute_id("wat")
        self.assertEqual(ide, og_len)
        self.assertEqual(len(self.db.attributes), og_len1)

    def test_add(self):
        with self.assertRaises(TypeError):
            self.db.add(("cool@gmail.com", "father", "foo"))
        with self.assertRaises(TypeError):
            self.db.add(("cool@gmail.com", "father", [(e.LITERAL, 99)]))
        with self.assertRaises(TypeError):
            self.db.add(("cool@gmail.com", "listy", [(e.LITERAL, "A"), (e.LITERAL, "B"), (e.LITERAL, "C")]))
        self.assertEqual(self.db.add(("cool@gmail.com", "listy", [(e.LITERAL, 1), (e.LITERAL, 2), (e.LITERAL, 3)])), self.db)

    def test_get_value(self):
        self.assertEqual(self.db.get_value("cool@gmail.com", "name"), "Joe Cool")
        self.assertIsNone(self.db.get_value("cool@gmail.com", "boogaloo"))

if __name__ == '__main__':
    unittest.main()
