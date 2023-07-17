use std::{cell::RefCell, collections::HashMap, rc::Rc};

use database::{
    backtracking::BacktrackingQuery,
    evaluator::{parse_fact, parse_query, tokenize},
    Database,
};

use crate::database::{unification::Value, DBValue};

mod database;

macro_rules! fact {
    ($db: ident, $($t:tt)*) => {
        Rc::<Database>::get_mut(&mut $db).unwrap().insert_fact(parse_fact(tokenize(stringify!($($t)*).to_string())).unwrap())
    };
}

macro_rules! query_relation {
    ($($t:tt)+) => {
        parse_query(tokenize(stringify!($($t)*).to_string())).unwrap()
    }
}

fn main() {
    let mut db = Rc::new(Database::new());
    fact!(db, "James" parent of "John");
    fact!(db, "James" parent of "Jesse");
    fact!(db, "James" parent of "Lucifer");
    fact!(db, "Jack" parent of "Jesse");
    fact!(db, "Ellen" parent of "John");
    fact!(db, "Jesse" parent of "Zack");
    fact!(db, "John" parent of "Matt");
    fact!(db, "Lisa" parent of "Zack");
    fact!(db, "Joyce" parent of "Lisa");
    fact!(db, "Joyce" parent of "Gottard");
    fact!(db, "Joyce" parent of "Mew");

    Rc::<Database>::get_mut(&mut db).unwrap().insert_rule(
        "grandparent".to_string(),
        vec![
            Value::Variable("X".to_string()),
            Value::Literal(DBValue::RelationID("OF".to_string())),
            Value::Variable("Y".to_string()),
        ],
        vec![
            query_relation!(X parent of T),
            query_relation!(T parent of Y),
        ],
    );

    let bindings = Rc::new(HashMap::new());
    let constraints = [
        query_relation!(A parent of B),
        query_relation!(B parent of C),
    ];
    let query = BacktrackingQuery::new(&constraints, db, bindings.clone());
    for solution in query {
        println!("SOLUTION FOUND: {:?}", solution);
    }
}
