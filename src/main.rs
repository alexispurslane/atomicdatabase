use std::{cell::RefCell, collections::HashMap, sync::Arc};

use database::{backtracking::BacktrackingQuery, parser::parse_fact, parser::parse_line, Database};

use crate::database::{unification::Value, DBValue};

mod database;

macro_rules! fact {
    ($db: ident, $($t:tt)*) => {
        $db.insert_fact(parse_fact(stringify!($($t)*).to_string()).unwrap())
    };
}

macro_rules! query_relation {
    ($($t:tt)+) => {
        parse_line(stringify!($($t)*).to_string()).unwrap()
    }
}

fn main() {
    let mut db = Arc::new(Database::new());
    fact!(db, "Rudolf I" father of "Frederik III");
    fact!(db, "Frederick III" father of "Maximiliaan I");
    fact!(db, "Jan II" mother of "Filips de Stoute");
    fact!(db, "Jan II" mother of "Karel V1");
    fact!(db, "Karel V" father of "Frans I");
    fact!(db, "Filips de Stoute" father of "Jan zonder Vrees");
    fact!(db, "Jan zonder Vrees" mother of "Filips de Goede");
    fact!(db, "Filips de Goede" father of "Karel de Stoute");
    fact!(db, "Karel de Stoute" father of "Maria");
    fact!(db, "Maria" mother of "Filips I de Schone");
    fact!(db, "Maximiliaan I" father of "Filips I de Schone");
    fact!(db, "Johan II v Kastilie" father of "Hendrik IV");
    fact!(db, "Johan II v Kastilie" father of "Isabella I");
    fact!(db, "Johan II v Aragon" father of "Ferdinand V");
    fact!(db, "Ferdinand V" father of "Johanna de Waanzinnige");
    fact!(db, "Isabella I" mother of "Johanna de Waanzinnige");
    fact!(db, "Filips I de Schone" father of "Eleonora");
    fact!(db, "Johanna de Waanzinnige" mother of "Eleonora");
    fact!(db, "Filips I de Schone" father of "Karel V");
    fact!(db, "Johanna de Waanzinnige" mother of "Karel V");
    fact!(db, "Filips I de Schone" father of "Ferdinand I");
    fact!(db, "Johanna de Waanzinnige" mother of "Ferdinand I");
    fact!(db, "Filips I de Schone" father of "Maria v Hongarije");
    fact!(db, "Johanna de Waanzinnige" mother of "Maria v Hongarije");

    Arc::<Database>::get_mut(&mut db).unwrap().insert_rule(
        "grandparent".to_string(),
        vec![
            Value::Variable("X".to_string()),
            Value::Literal(DBValue::RelationID("OF".to_string())),
            Value::Variable("Y".to_string()),
        ],
        vec![
            query_relation!(X parent of T),
            query_relation!(Y parent of T),
        ],
    );

    let bindings = Arc::new(HashMap::new());
    let constraints = [
        query_relation!(A father of B),
        query_relation!(B father of C),
    ];
    let query = BacktrackingQuery::new(&constraints, db, bindings.clone());
    for solution in query {
        println!("SOLUTION FOUND: {:?}", solution);
    }

    let _ = parse_line(
        "
X Foo B1 1B > < <= >= = ~ !
[\"a\", \"b\", \"c\"] foo,bar 12339844398938493859535898
         \"cockaDoodLE do!#[]\"baz, 4.5"
            .to_string(),
    )
    .unwrap();
}
