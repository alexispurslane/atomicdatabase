use lazy_regex::*;
use num_bigint::{BigInt, BigUint, Sign};

use super::{
    unification::{Constraint, Value},
    DBValue,
};

pub type VariableName = String;

pub fn parse_query(tokens: Vec<String>) -> Result<Constraint, String> {
    if let Some(alt_split_point) = tokens.iter().position(|tok| *tok == "|") {
        let (tokens_left, tokens_right) = tokens.split_at(alt_split_point);
        let (tokens_left, mut tokens_right) = (tokens_left.to_vec(), tokens_right.to_vec());
        tokens_right.remove(0);
        let parse_left = parse_query(tokens_left)?;
        let parse_right = parse_query(tokens_right)?;
        let mut left_relations = match parse_left {
            rel @ Constraint::Relation(_, _) => vec![rel],
            uni @ Constraint::Unification(_, _) => vec![uni],
            comp @ Constraint::Comparison(_, _, _) => vec![comp],
            int @ Constraint::Intersections(_) => vec![int],
            not @ Constraint::Not(_) => vec![not],
            Constraint::Alternatives(v) => v,
        };
        let right_relations = match parse_right {
            rel @ Constraint::Relation(_, _) => vec![rel],
            uni @ Constraint::Unification(_, _) => vec![uni],
            comp @ Constraint::Comparison(_, _, _) => vec![comp],
            int @ Constraint::Intersections(_) => vec![int],
            not @ Constraint::Not(_) => vec![not],
            Constraint::Alternatives(v) => v,
        };
        left_relations.extend(right_relations);
        Ok(Constraint::Alternatives(left_relations))
    } else {
        let mut parsed_tokens = vec![];
        for tok in tokens {
            let parsed_tok = parse_token(&tok)?;
            parsed_current_token = parsed_tok;
        }
        Constraint::new_relation(parsed_tokens)
    }
}

pub fn parse_fact(tokens: Vec<String>) -> Result<Vec<DBValue>, String> {
    let mut parsed_tokens = vec![];
    for tok in tokens {
        let parsed_tok = parse_token(&tok)?;
        match parsed_tok {
            Value::Literal(dbval) => { parsed_current_token = dbval },
            _ => {return Err("Cannot push variable relation as fact to database. Relations with variables can only be queries.".to_string())}
        }
    }
    Ok(parsed_tokens)
}
