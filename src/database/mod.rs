pub mod backtracking;
pub mod parser;
pub mod unification;

use dashmap::DashMap;

use std::{
    collections::HashMap,
    fmt,
    sync::{Arc, RwLock},
};

use num_bigint::{BigInt, BigUint, ToBigUint};

use self::{
    backtracking::{BacktrackingQuery, Constraint},
    parser::MetaAST,
    unification::{ASTValue, Bindings, RelationID},
};

#[derive(Clone, Debug)]
pub enum DBValue {
    Text(String),
    Number(BigInt),
    Float(BigInt, BigUint),
    RelationID(String),
    List(Vec<DBValue>),
}

impl fmt::Display for DBValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DBValue::Text(s) => write!(f, "\"{}\"", s),
            DBValue::Number(n) => write!(f, "{}", n),
            DBValue::Float(a, b) => write!(f, "{}.{}", a, b),
            DBValue::RelationID(rel) => write!(f, "{}", rel),
            DBValue::List(l) => {
                write!(f, "[ ")?;
                for val in l {
                    write!(f, "{} ", val)?;
                }
                write!(f, "]")
            }
        }
    }
}

impl PartialEq for DBValue {
    fn eq(&self, other: &Self) -> bool {
        use DBValue::*;
        let zero = 0.to_biguint().unwrap();
        match (self, other) {
            (&Text(ref s1), &Text(ref s2)) => s1 == s2,
            (&Number(ref n1), &Number(ref n2)) => n1 == n2,
            (&Number(ref n1), &Float(ref n2, ref n2d)) => *n2d == zero && n1 == n2,
            (&Float(ref n1, ref n1d), &Number(ref n2)) => *n1d == zero && n1 == n2,
            (&Float(ref n1, ref n1d), &Float(ref n2, ref n2d)) => n1d == n2d && n1 == n2,
            (&RelationID(ref r1), &RelationID(ref r2)) => r1.to_uppercase() == r2.to_uppercase(),
            _ => false,
        }
    }
}

impl Eq for DBValue {}

impl PartialOrd for DBValue {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        use DBValue::*;
        let zero = 0.to_biguint().unwrap();
        match (self, other) {
            (&Text(ref s1), &Text(ref s2)) => Some(s1.cmp(s2)),
            (&Number(ref n1), &Number(ref n2)) => Some(n1.cmp(n2)),
            (&Number(ref n1), &Float(ref n2, ref n2d)) => {
                if n1 == n2 {
                    Some(zero.cmp(n2d))
                } else {
                    Some(n1.cmp(n2))
                }
            }
            (&Float(ref n1, ref n1d), &Number(ref n2)) => {
                if n1 == n2 {
                    Some(zero.cmp(n1d))
                } else {
                    Some(n1.cmp(n2))
                }
            }
            (&Float(ref n1, ref n1d), &Float(ref n2, ref n2d)) => {
                if n1 == n2 {
                    Some(n1d.cmp(n2d))
                } else {
                    Some(n1.cmp(n2))
                }
            }
            _ => None,
        }
    }
}

pub struct Database {
    pub facts: DashMap<RelationID, Vec<Vec<DBValue>>>,
    pub rules: RwLock<HashMap<RelationID, (Vec<ASTValue>, Vec<Arc<Constraint>>)>>,
}

impl Database {
    pub fn new() -> Self {
        Database {
            facts: DashMap::new(),
            rules: RwLock::new(HashMap::new()),
        }
    }

    pub fn insert_rule(
        &self,
        id: RelationID,
        args: Vec<ASTValue>,
        constraints: Vec<Arc<Constraint>>,
    ) -> Result<(), String> {
        self.rules
            .write()
            .map_err(|e| format!("Error writing rule {} to database: '{}'. ", id, e))?
            .insert(id.to_uppercase(), (args, constraints.clone()));
        Ok(())
    }

    pub fn insert_fact(&self, vs: Vec<DBValue>) -> Result<(), String> {
        match vs.get(1) {
            Some(DBValue::RelationID(rel)) => {
                let rel = rel.to_uppercase();
                let mut vs = vs.clone();
                vs.remove(1);
                if let Some(mut rels) = self.facts.get_mut(&rel) {
                    rels.push(vs);
                } else {
                    self.facts.insert(rel, vec![vs]);
                }
                Ok(())
            }
            Some(v) => Err(format!(
                "Expected second term in database relation to be a valid relation ID, not {:?}. ",
                v
            )),
            None => Err(format!(
                "Not enough terms in database relation to construct a meaningful relation. "
            )),
        }
    }

    pub fn evaluate<'a>(
        db: Arc<Database>,
        bindings: Arc<Bindings>,
        statement: MetaAST,
    ) -> Result<Option<BacktrackingQuery<'a>>, String> {
        match statement {
            MetaAST::Constraint(c) => Ok(Some(BacktrackingQuery::new(
                vec![Arc::new(c)],
                db.clone(),
                bindings.clone(),
            ))),
            MetaAST::Fact(fact) => db.insert_fact(fact).map(|_| None),
            MetaAST::Rule(mut signature, body) => {
                if let ASTValue::Literal(DBValue::RelationID(name)) = signature.remove(1) {
                    db.insert_rule(
                        name,
                        signature,
                        body.into_iter().map(|x| Arc::new(x)).collect(),
                    )
                    .map(|_| None)
                } else {
                    return Err(format!(
                        "Need at least one relation-id keyword in rule signature. "
                    ));
                }
            }
        }
    }
}
